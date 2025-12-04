# -*- coding: utf-8 -*-
"""
Image Bank Service - Manages product images across customer and admin depots.

Image Search Hierarchy:
1. Customer's depot (user-specific images)
2. Admin's general depot (approved images)
3. External API (CAMGOZ/JoJAPI)
4. Manual upload fallback

Storage Structure:
- /static/uploads/admin/{sector}/{barcode}/          - Admin approved images
- /static/uploads/customers/{user_id}/{sector}/{barcode}/ - Customer specific images
- /static/uploads/pending/{sector}/{barcode}/        - Awaiting admin approval
- /static/uploads/cache/{barcode}/                   - Temporary API cache
"""

import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO

from utils.constants import SECTORS, ALLOWED_IMAGE_EXTENSIONS

# Base paths
BASE_UPLOAD_PATH = 'static/uploads'
ADMIN_PATH = os.path.join(BASE_UPLOAD_PATH, 'admin')
CUSTOMERS_PATH = os.path.join(BASE_UPLOAD_PATH, 'customers')
PENDING_PATH = os.path.join(BASE_UPLOAD_PATH, 'pending')
CACHE_PATH = os.path.join(BASE_UPLOAD_PATH, 'cache')


def ensure_base_directories():
    """Ensure all base directories exist"""
    for path in [ADMIN_PATH, CUSTOMERS_PATH, PENDING_PATH, CACHE_PATH]:
        os.makedirs(path, exist_ok=True)
    
    # Create sector subdirectories in admin and pending
    for sector in SECTORS.keys():
        os.makedirs(os.path.join(ADMIN_PATH, sector), exist_ok=True)
        os.makedirs(os.path.join(PENDING_PATH, sector), exist_ok=True)


def get_customer_depot_path(user_id, sector=None, group=None, barcode=None):
    """Get path to customer's depot
    Structure: customers/{user_id}/{sector}/{group}/{barcode}/
    """
    path = os.path.join(CUSTOMERS_PATH, str(user_id))
    if sector:
        path = os.path.join(path, sector)
    if group:
        path = os.path.join(path, group)
    if barcode:
        path = os.path.join(path, barcode)
    return path


def get_admin_depot_path(sector=None, group=None, barcode=None):
    """Get path to admin depot
    Structure: admin/{sector}/{group}/{barcode}/
    """
    path = ADMIN_PATH
    if sector:
        path = os.path.join(path, sector)
    if group:
        path = os.path.join(path, group)
    if barcode:
        path = os.path.join(path, barcode)
    return path


def get_pending_path(sector=None, group=None, barcode=None):
    """Get path to pending approval folder
    Structure: pending/{sector}/{group}/{barcode}/
    """
    path = PENDING_PATH
    if sector:
        path = os.path.join(path, sector)
    if group:
        path = os.path.join(path, group)
    if barcode:
        path = os.path.join(path, barcode)
    return path


def find_image_in_depot(depot_path):
    """Find first image file in a depot folder"""
    if not os.path.exists(depot_path) or not os.path.isdir(depot_path):
        return None
    
    for filename in os.listdir(depot_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            return os.path.join(depot_path, filename)
    return None


def search_image_hierarchy(barcode, user_id, sector='supermarket'):
    """
    Search for product image following the hierarchy:
    1. Customer's depot
    2. Admin's depot
    3. Return None (caller should try external API)
    
    Returns:
        dict: {found: bool, source: str, image_path: str, image_url: str}
    """
    ensure_base_directories()
    
    # 1. Check customer's depot
    customer_path = get_customer_depot_path(user_id, sector, barcode)
    image_path = find_image_in_depot(customer_path)
    if image_path:
        relative_path = image_path.replace('\\', '/')
        return {
            'found': True,
            'source': 'customer_depot',
            'image_path': image_path,
            'image_url': f'/{relative_path}'
        }
    
    # 2. Check admin's depot
    admin_path = get_admin_depot_path(sector, barcode)
    image_path = find_image_in_depot(admin_path)
    if image_path:
        relative_path = image_path.replace('\\', '/')
        return {
            'found': True,
            'source': 'admin_depot',
            'image_path': image_path,
            'image_url': f'/{relative_path}'
        }
    
    # 3. Not found in local depots
    return {
        'found': False,
        'source': None,
        'image_path': None,
        'image_url': None
    }


def save_to_customer_depot(user_id, sector, barcode, image_data, filename='product.png', group='Genel', skip_processing=False):
    """
    Save image DIRECTLY to customer's depot.
    Customer can use immediately. Admin approval copies to admin depot later.
    
    Flow: Customer Depot (immediate use) → Admin Approval → Admin Depot (all customers)
    
    Args:
        user_id: Customer's user ID
        sector: Product sector
        barcode: Product barcode (ID)
        image_data: Image bytes or file-like object (PNG preferred)
        filename: Target filename (default: product.png)
        group: Product group from AI categorization
        skip_processing: If True, image_data is already processed (PNG from Stage 1)
    
    Returns:
        dict: {success: bool, customer_url: str}
    """
    try:
        # Eğer image_processor tarafından zaten işlendiyse, tekrar işleme
        if skip_processing and isinstance(image_data, bytes):
            image_bytes = image_data
        else:
            # Process and standardize image (fallback)
            standardized = standardize_image(image_data)
            if not standardized['success']:
                return {'success': False, 'error': standardized['error']}
            image_bytes = standardized['image_bytes']
        
        # Save DIRECTLY to customer depot (not pending!)
        customer_path = get_customer_depot_path(user_id, sector, group, barcode)
        os.makedirs(customer_path, exist_ok=True)
        customer_file = os.path.join(customer_path, filename)
        with open(customer_file, 'wb') as f:
            f.write(image_bytes)
        
        # Save metadata
        metadata = {
            'user_id': user_id,
            'sector': sector,
            'group': group,
            'barcode': barcode,
            'uploaded_at': datetime.now().isoformat(),
            'status': 'customer_depot',
            'original_filename': filename
        }
        with open(os.path.join(customer_path, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        customer_url = f'/{customer_file.replace(os.sep, "/")}'
        
        logging.info(f"Image saved to CUSTOMER DEPOT: {barcode} (user: {user_id}, group: {group})")
        
        return {
            'success': True,
            'customer_url': customer_url,
            'pending_url': customer_url,  # Backward compatibility
            'group': group
        }
        
    except Exception as e:
        logging.error(f"Save to pending depot error: {str(e)}")
        return {'success': False, 'error': str(e)}


def move_from_pending_to_customer(user_id, sector, barcode, group='Genel'):
    """
    Move approved image from pending to customer depot.
    Called after admin approves the product.
    
    Args:
        user_id: Customer's user ID
        sector: Product sector
        barcode: Product barcode
        group: Product group
    
    Returns:
        dict: {success: bool, customer_url: str}
    """
    try:
        pending_path = get_pending_path(sector, group, barcode)
        
        # PNG veya JPG dosyasını bul
        pending_file = os.path.join(pending_path, 'product.png')
        if not os.path.exists(pending_file):
            pending_file = os.path.join(pending_path, 'product.jpg')
        
        if not os.path.exists(pending_file):
            logging.warning(f"Pending image not found: {pending_file}")
            return {'success': False, 'error': 'Pending image not found'}
        
        # Create customer depot path
        customer_path = get_customer_depot_path(user_id, sector, group, barcode)
        os.makedirs(customer_path, exist_ok=True)
        
        # Aynı uzantıyı kullan
        filename = os.path.basename(pending_file)
        customer_file = os.path.join(customer_path, filename)
        
        # Move file
        shutil.move(pending_file, customer_file)
        
        # Update metadata
        metadata_file = os.path.join(pending_path, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata['status'] = 'approved'
            metadata['approved_at'] = datetime.now().isoformat()
            
            # Move metadata to customer path
            customer_metadata = os.path.join(customer_path, 'metadata.json')
            with open(customer_metadata, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            os.remove(metadata_file)
        
        # Remove empty pending folder
        try:
            os.rmdir(pending_path)
        except:
            pass
        
        customer_url = f'/{customer_file.replace(os.sep, "/")}'
        
        logging.info(f"Image moved from pending to customer depot: {barcode} (user: {user_id})")
        
        return {
            'success': True,
            'customer_url': customer_url
        }
        
    except Exception as e:
        logging.error(f"Move from pending error: {str(e)}")
        return {'success': False, 'error': str(e)}


def move_to_admin_depot(user_id, sector, barcode, group='Genel'):
    """
    MOVE image from customer depot to admin depot.
    Called after admin approves the product.
    This makes the image available to ALL customers.
    
    IMPORTANT: This MOVES, not copies. Customer depot copy is DELETED.
    Sistemde bir ürün 2 adet olamaz - tek kopya admin deposunda kalır.
    
    Args:
        user_id: Customer's user ID (source)
        sector: Product sector
        barcode: Product barcode
        group: Product group
    
    Returns:
        dict: {success: bool, admin_url: str}
    """
    try:
        # Source: Customer depot
        customer_path = get_customer_depot_path(user_id, sector, group, barcode)
        
        # Find image file (PNG or JPG)
        customer_file = os.path.join(customer_path, 'product.png')
        if not os.path.exists(customer_file):
            customer_file = os.path.join(customer_path, 'product.jpg')
        
        if not os.path.exists(customer_file):
            logging.warning(f"Customer image not found: {customer_path}")
            return {'success': False, 'error': 'Customer image not found'}
        
        # Destination: Admin depot
        admin_path = get_admin_depot_path(sector, group, barcode)
        os.makedirs(admin_path, exist_ok=True)
        
        # Same filename
        filename = os.path.basename(customer_file)
        admin_file = os.path.join(admin_path, filename)
        
        # MOVE file (not copy!) - Müşteri deposundan TAŞI
        shutil.move(customer_file, admin_file)
        
        # Customer metadata'yı admin deposuna taşı
        customer_metadata_file = os.path.join(customer_path, 'metadata.json')
        if os.path.exists(customer_metadata_file):
            with open(customer_metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            # Metadata'yı güncelle
            metadata['original_user_id'] = user_id
            metadata['approved_at'] = datetime.now().isoformat()
            metadata['status'] = 'admin_depot'
            # Admin deposuna yaz
            with open(os.path.join(admin_path, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            # Müşteri metadata'sını sil
            os.remove(customer_metadata_file)
        else:
            # Yeni metadata oluştur
            metadata = {
                'original_user_id': user_id,
                'sector': sector,
                'group': group,
                'barcode': barcode,
                'approved_at': datetime.now().isoformat(),
                'status': 'admin_depot'
            }
            with open(os.path.join(admin_path, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Müşteri klasörünü temizle (boşsa sil)
        try:
            # customer_path içinde başka dosya kalmadıysa klasörü sil
            remaining_files = os.listdir(customer_path) if os.path.exists(customer_path) else []
            if not remaining_files:
                os.rmdir(customer_path)
                logging.info(f"Empty customer folder removed: {customer_path}")
        except Exception as cleanup_error:
            logging.warning(f"Customer folder cleanup warning: {cleanup_error}")
        
        admin_url = f'/{admin_file.replace(os.sep, "/")}'
        
        logging.info(f"Image MOVED to admin depot: {barcode} (from user: {user_id}) - Customer copy DELETED")
        
        return {
            'success': True,
            'admin_url': admin_url
        }
        
    except Exception as e:
        logging.error(f"Move to admin depot error: {str(e)}")
        return {'success': False, 'error': str(e)}


# Backward compatibility alias
def copy_to_admin_depot(user_id, sector, barcode, group='Genel'):
    """DEPRECATED: Use move_to_admin_depot instead. This is kept for backward compatibility."""
    logging.warning("copy_to_admin_depot is DEPRECATED. Use move_to_admin_depot instead.")
    return move_to_admin_depot(user_id, sector, barcode, group)


def delete_from_pending(sector, barcode, group='Genel'):
    """
    Delete rejected image from pending.
    Called when admin rejects the product.
    
    Args:
        sector: Product sector
        barcode: Product barcode
        group: Product group
    
    Returns:
        dict: {success: bool}
    """
    try:
        pending_path = get_pending_path(sector, group, barcode)
        
        if os.path.exists(pending_path):
            shutil.rmtree(pending_path)
            logging.info(f"Pending image deleted: {barcode}")
            return {'success': True}
        else:
            logging.warning(f"Pending path not found: {pending_path}")
            return {'success': True, 'warning': 'Path not found'}
            
    except Exception as e:
        logging.error(f"Delete from pending error: {str(e)}")
        return {'success': False, 'error': str(e)}


def save_to_admin_depot(sector, barcode, image_data, filename='product.png', metadata=None, group='Genel'):
    """
    Save image directly to admin depot (bypasses pending).
    Used when admin uploads or when approving from API.
    
    Structure: admin/{sector}/{group}/{barcode}/product.png
    
    Args:
        sector: Product sector
        barcode: Product barcode (ID)
        image_data: Image bytes or file-like object (PNG preferred)
        filename: Target filename (default: product.png)
        metadata: Optional metadata dict
        group: Product group
    
    Returns:
        dict: {success: bool, admin_url: str}
    """
    try:
        # Ensure directory with group hierarchy
        admin_path = get_admin_depot_path(sector, group, barcode)
        os.makedirs(admin_path, exist_ok=True)
        
        # TODO: Aşama 1 - OpenAI 1024px resize buraya eklenecek
        # standardized = openai_resize_1024(image_data)
        
        # Process and standardize image
        standardized = standardize_image(image_data)
        if not standardized['success']:
            return {'success': False, 'error': standardized['error']}
        
        # Save to admin depot
        admin_file = os.path.join(admin_path, filename)
        with open(admin_file, 'wb') as f:
            f.write(standardized['image_bytes'])
        
        # Save metadata
        if metadata:
            metadata['group'] = group
            with open(os.path.join(admin_path, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        admin_url = f'/{admin_file.replace(os.sep, "/")}'
        
        logging.info(f"Image saved to admin depot: {barcode} (group: {group})")
        
        return {
            'success': True,
            'admin_url': admin_url,
            'group': group
        }
        
    except Exception as e:
        logging.error(f"Save to admin depot error: {str(e)}")
        return {'success': False, 'error': str(e)}


def approve_pending_image(sector, barcode):
    """
    Approve a pending image and move it to admin depot.
    Also removes from customer depot if exists.
    
    Args:
        sector: Product sector
        barcode: Product barcode
    
    Returns:
        dict: {success: bool, admin_url: str}
    """
    try:
        pending_path = get_pending_path(sector, barcode)
        admin_path = get_admin_depot_path(sector, barcode)
        
        if not os.path.exists(pending_path):
            return {'success': False, 'error': 'Pending image not found'}
        
        # Create admin directory
        os.makedirs(os.path.dirname(admin_path), exist_ok=True)
        
        # Remove existing admin folder if exists
        if os.path.exists(admin_path):
            shutil.rmtree(admin_path)
        
        # Move from pending to admin
        shutil.move(pending_path, admin_path)
        
        # Update metadata
        metadata_file = os.path.join(admin_path, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Remove from customer depot (image now belongs to admin)
            user_id = metadata.get('user_id')
            if user_id:
                customer_path = get_customer_depot_path(user_id, sector, barcode)
                if os.path.exists(customer_path):
                    shutil.rmtree(customer_path)
                    logging.info(f"Removed from customer depot after approval: {barcode}")
            
            metadata['status'] = 'approved'
            metadata['approved_at'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Find the image file
        image_path = find_image_in_depot(admin_path)
        admin_url = f'/{image_path.replace(os.sep, "/")}' if image_path else None
        
        logging.info(f"Image approved and moved to admin depot: {barcode}")
        
        return {
            'success': True,
            'admin_url': admin_url
        }
        
    except Exception as e:
        logging.error(f"Approve pending image error: {str(e)}")
        return {'success': False, 'error': str(e)}


def reject_pending_image(sector, barcode):
    """
    Reject a pending image and remove it.
    Customer depot copy is kept but marked as rejected.
    
    Args:
        sector: Product sector
        barcode: Product barcode
    
    Returns:
        dict: {success: bool}
    """
    try:
        pending_path = get_pending_path(sector, barcode)
        
        if not os.path.exists(pending_path):
            return {'success': False, 'error': 'Pending image not found'}
        
        # Get user_id from metadata before deleting
        metadata_file = os.path.join(pending_path, 'metadata.json')
        user_id = None
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            user_id = metadata.get('user_id')
        
        # Remove pending folder
        shutil.rmtree(pending_path)
        
        # Update customer depot metadata to show rejection
        if user_id:
            customer_path = get_customer_depot_path(user_id, sector, barcode)
            customer_metadata = os.path.join(customer_path, 'metadata.json')
            if os.path.exists(customer_metadata):
                with open(customer_metadata, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['status'] = 'rejected'
                metadata['rejected_at'] = datetime.now().isoformat()
                with open(customer_metadata, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Image rejected: {barcode}")
        
        return {'success': True}
        
    except Exception as e:
        logging.error(f"Reject pending image error: {str(e)}")
        return {'success': False, 'error': str(e)}


def standardize_image(image_data, target_format='PNG', max_size=1024):
    """
    Standardize image: resize, convert to PNG with transparent background.
    
    Args:
        image_data: Image bytes, file-like object, or file path
        target_format: Output format (PNG recommended for transparency)
        max_size: Maximum dimension (width or height)
    
    Returns:
        dict: {success: bool, image_bytes: bytes, quality: str}
    """
    try:
        # Load image
        if isinstance(image_data, bytes):
            img = Image.open(BytesIO(image_data))
        elif isinstance(image_data, str) and os.path.exists(image_data):
            img = Image.open(image_data)
        elif hasattr(image_data, 'read'):
            img = Image.open(image_data)
        else:
            return {'success': False, 'error': 'Invalid image data'}
        
        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Determine quality based on original size
        width, height = img.size
        min_dim = min(width, height)
        if min_dim >= 1024:
            quality = 'high'
        elif min_dim >= 512:
            quality = 'medium'
        else:
            quality = 'low'
        
        # Resize if too large (maintain aspect ratio)
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format=target_format, optimize=True)
        image_bytes = output.getvalue()
        
        return {
            'success': True,
            'image_bytes': image_bytes,
            'quality': quality,
            'size': (img.width, img.height)
        }
        
    except Exception as e:
        logging.error(f"Standardize image error: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_pending_images_list():
    """
    Get list of all pending images awaiting approval.
    
    Returns:
        list: List of pending image info dicts
    """
    pending_list = []
    
    if not os.path.exists(PENDING_PATH):
        return pending_list
    
    for sector in os.listdir(PENDING_PATH):
        sector_path = os.path.join(PENDING_PATH, sector)
        if not os.path.isdir(sector_path):
            continue
        
        for barcode in os.listdir(sector_path):
            barcode_path = os.path.join(sector_path, barcode)
            if not os.path.isdir(barcode_path):
                continue
            
            # Find image
            image_path = find_image_in_depot(barcode_path)
            if not image_path:
                continue
            
            # Load metadata
            metadata = {}
            metadata_file = os.path.join(barcode_path, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            pending_list.append({
                'barcode': barcode,
                'sector': sector,
                'sector_name': SECTORS.get(sector, sector),
                'image_url': f'/{image_path.replace(os.sep, "/")}',
                'user_id': metadata.get('user_id'),
                'uploaded_at': metadata.get('uploaded_at'),
                'original_filename': metadata.get('original_filename')
            })
    
    # Sort by upload date (newest first)
    pending_list.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
    
    return pending_list


def get_admin_images_by_sector(sector):
    """
    Get all approved images in a sector.
    
    Args:
        sector: Product sector
    
    Returns:
        list: List of image info dicts
    """
    images = []
    sector_path = get_admin_depot_path(sector)
    
    if not os.path.exists(sector_path):
        return images
    
    for barcode in os.listdir(sector_path):
        barcode_path = os.path.join(sector_path, barcode)
        if not os.path.isdir(barcode_path):
            continue
        
        image_path = find_image_in_depot(barcode_path)
        if not image_path:
            continue
        
        # Load metadata
        metadata = {}
        metadata_file = os.path.join(barcode_path, 'metadata.json')
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass
        
        images.append({
            'barcode': barcode,
            'sector': sector,
            'product_name': metadata.get('product_name', barcode),
            'image_url': f'/{image_path.replace(os.sep, "/")}',
            'approved_at': metadata.get('approved_at')
        })
    
    return images


def get_customer_images(user_id, sector=None):
    """
    Get all images in a customer's depot.
    
    Args:
        user_id: Customer's user ID
        sector: Optional sector filter
    
    Returns:
        list: List of image info dicts
    """
    images = []
    customer_base = get_customer_depot_path(user_id)
    
    if not os.path.exists(customer_base):
        return images
    
    sectors_to_check = [sector] if sector else os.listdir(customer_base)
    
    for sec in sectors_to_check:
        sector_path = os.path.join(customer_base, sec)
        if not os.path.isdir(sector_path):
            continue
        
        for barcode in os.listdir(sector_path):
            barcode_path = os.path.join(sector_path, barcode)
            if not os.path.isdir(barcode_path):
                continue
            
            image_path = find_image_in_depot(barcode_path)
            if not image_path:
                continue
            
            # Load metadata
            metadata = {}
            metadata_file = os.path.join(barcode_path, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            images.append({
                'barcode': barcode,
                'sector': sec,
                'sector_name': SECTORS.get(sec, sec),
                'product_name': metadata.get('product_name', barcode),
                'image_url': f'/{image_path.replace(os.sep, "/")}',
                'status': metadata.get('status', 'pending'),
                'uploaded_at': metadata.get('uploaded_at')
            })
    
    return images


def delete_image_from_depot(depot_type, sector, barcode, user_id=None):
    """
    Delete image from specified depot.
    
    Args:
        depot_type: 'admin', 'customer', or 'pending'
        sector: Product sector
        barcode: Product barcode
        user_id: Required for customer depot
    
    Returns:
        dict: {success: bool}
    """
    try:
        if depot_type == 'admin':
            path = get_admin_depot_path(sector, barcode)
        elif depot_type == 'customer':
            if not user_id:
                return {'success': False, 'error': 'user_id required for customer depot'}
            path = get_customer_depot_path(user_id, sector, barcode)
        elif depot_type == 'pending':
            path = get_pending_path(sector, barcode)
        else:
            return {'success': False, 'error': 'Invalid depot type'}
        
        if os.path.exists(path):
            shutil.rmtree(path)
            logging.info(f"Deleted from {depot_type}: {barcode}")
            return {'success': True}
        
        return {'success': False, 'error': 'Image not found'}
        
    except Exception as e:
        logging.error(f"Delete image error: {str(e)}")
        return {'success': False, 'error': str(e)}


# Initialize directories on module load
ensure_base_directories()

