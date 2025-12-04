"""
Image Quality Processing Module
Ensures all images meet catalog standard:
- 1024x1024 px square
- JPG/PNG format
- 200-350 KB size
- White background
- Clean e-commerce style
- AEU Yazilim watermark for admin images
"""

import os
import io
import uuid
from datetime import datetime
from PIL import Image, ImageOps, ImageDraw, ImageFont
import requests

UPLOAD_BASE = 'static/uploads'
CUSTOMER_DIR = f'{UPLOAD_BASE}/customers'
PENDING_DIR = f'{UPLOAD_BASE}/pending'
ADMIN_DIR = f'{UPLOAD_BASE}/admin'
ADMIN_STOCK_DIR = 'admin_stock'

TARGET_SIZE = (1024, 1024)
MIN_FILE_SIZE = 200 * 1024  # 200 KB
MAX_FILE_SIZE = 350 * 1024  # 350 KB
INITIAL_QUALITY = 90
MIN_QUALITY = 60

WATERMARK_TEXT = "AEU Yazilim"
WATERMARK_OPACITY = 25  # 10% opacity = 25/255

QUALITY_THRESHOLDS = {
    'high': 1024,
    'medium': 512,
    'low': 0
}

def ensure_directories():
    """Ensure all upload directories exist"""
    for d in [CUSTOMER_DIR, PENDING_DIR, ADMIN_DIR]:
        os.makedirs(d, exist_ok=True)

def get_customer_dir(user_id):
    """Get customer-specific upload directory"""
    path = f'{CUSTOMER_DIR}/{user_id}'
    os.makedirs(path, exist_ok=True)
    return path

def get_pending_path(unique_id=None):
    """Get path for pending AI-generated image"""
    ensure_directories()
    if not unique_id:
        unique_id = str(uuid.uuid4())[:8]
    return f'{PENDING_DIR}/{unique_id}.jpg', unique_id

def get_admin_path(barcode, sector='supermarket'):
    """Get path for admin archive image with sector support"""
    sector_dir = os.path.join(ADMIN_DIR, sector, barcode)
    os.makedirs(sector_dir, exist_ok=True)
    return os.path.join(sector_dir, 'product.jpg')

def get_customer_image_path(user_id, barcode):
    """Get path for customer-specific image"""
    customer_dir = get_customer_dir(user_id)
    return f'{customer_dir}/{barcode}.jpg'

def download_image(url):
    """Download image from URL and return PIL Image"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def is_white_background(image, threshold=240, coverage=0.7):
    """Check if image has predominantly white background"""
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        edge_pixels = []
        
        for x in range(width):
            edge_pixels.append(image.getpixel((x, 0)))
            edge_pixels.append(image.getpixel((x, height - 1)))
        for y in range(height):
            edge_pixels.append(image.getpixel((0, y)))
            edge_pixels.append(image.getpixel((width - 1, y)))
        
        white_count = sum(1 for p in edge_pixels if all(c >= threshold for c in p))
        return white_count / len(edge_pixels) >= coverage
    except:
        return True

def make_white_background(image):
    """Convert transparent or non-white backgrounds to white"""
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        return background
    elif image.mode != 'RGB':
        return image.convert('RGB')
    return image

def resize_to_square(image, size=1024):
    """Resize image to square, padding with white if needed"""
    image = make_white_background(image)
    
    original_width, original_height = image.size
    max_dim = max(original_width, original_height)
    
    square = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
    offset_x = (max_dim - original_width) // 2
    offset_y = (max_dim - original_height) // 2
    square.paste(image, (offset_x, offset_y))
    
    if max_dim != size:
        square = square.resize((size, size), Image.Resampling.LANCZOS)
    
    return square

def optimize_file_size(image, target_min=MIN_FILE_SIZE, target_max=MAX_FILE_SIZE):
    """Optimize image to achieve target file size range"""
    quality = INITIAL_QUALITY
    
    while quality >= MIN_QUALITY:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        file_size = buffer.tell()
        
        if target_min <= file_size <= target_max:
            return buffer.getvalue(), quality
        elif file_size > target_max:
            quality -= 5
        else:
            quality += 5
            if quality > INITIAL_QUALITY:
                buffer.seek(0)
                return buffer.getvalue(), INITIAL_QUALITY
    
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=MIN_QUALITY, optimize=True)
    return buffer.getvalue(), MIN_QUALITY

def process_image_to_catalog_standard(image_source, output_path=None):
    """
    Process image to meet catalog quality standards:
    - 1024x1024 square
    - JPG format
    - 200-350 KB
    - White background
    
    Args:
        image_source: PIL Image, file path, or URL
        output_path: Optional output path (auto-generated if not provided)
    
    Returns:
        dict with 'success', 'path', 'size', 'quality' or 'error'
    """
    try:
        if isinstance(image_source, str):
            if image_source.startswith(('http://', 'https://')):
                image = download_image(image_source)
                if not image:
                    return {'success': False, 'error': 'Failed to download image'}
            else:
                image = Image.open(image_source)
        elif isinstance(image_source, Image.Image):
            image = image_source
        else:
            return {'success': False, 'error': 'Invalid image source'}
        
        processed = resize_to_square(image, 1024)
        
        image_data, quality = optimize_file_size(processed)
        
        if not output_path:
            output_path, _ = get_pending_path()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return {
            'success': True,
            'path': output_path,
            'url': '/' + output_path,
            'size': len(image_data),
            'quality': quality,
            'dimensions': '1024x1024'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_customer_image_from_url(user_id, barcode, image_url):
    """Download and save image to customer's directory"""
    output_path = get_customer_image_path(user_id, barcode)
    result = process_image_to_catalog_standard(image_url, output_path)
    return result

def save_to_pending(image_source, unique_id=None):
    """Save image to pending directory for admin approval"""
    output_path, uid = get_pending_path(unique_id)
    result = process_image_to_catalog_standard(image_source, output_path)
    if result['success']:
        result['unique_id'] = uid
    return result

def move_pending_to_admin(pending_path, barcode, sector='supermarket', apply_watermark=True):
    """Move approved pending image to admin archive with watermark and sector structure"""
    try:
        admin_path = get_admin_path(barcode, sector)
        
        if os.path.exists(pending_path):
            image = Image.open(pending_path)
            
            processed = resize_to_square(image, 1024)
            
            if apply_watermark:
                processed = add_watermark(processed)
            
            image_data, quality_level = optimize_file_size(processed)
            
            os.makedirs(os.path.dirname(admin_path), exist_ok=True)
            with open(admin_path, 'wb') as f:
                f.write(image_data)
            
            metadata = {
                'barcode': barcode,
                'sector': sector,
                'image_quality': 'high',
                'watermarked': apply_watermark,
                'created_at': datetime.now().isoformat()
            }
            metadata_path = os.path.join(os.path.dirname(admin_path), 'metadata.json')
            try:
                import json
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            except:
                pass
            
            if os.path.isdir(pending_path):
                import shutil
                shutil.rmtree(pending_path)
            else:
                os.remove(pending_path)
            
            return {
                'success': True,
                'path': admin_path,
                'url': '/' + admin_path,
                'size': len(image_data),
                'quality': quality_level,
                'image_quality': 'high',
                'watermarked': apply_watermark,
                'sector': sector
            }
        
        return {'success': False, 'error': 'Pending image not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_pending_image(pending_path):
    """Delete rejected pending image"""
    try:
        if os.path.exists(pending_path):
            os.remove(pending_path)
            return True
    except:
        pass
    return False

def get_ai_image_prompt(product_name, sector=None):
    """Generate optimized prompt for AI image generation"""
    base_prompt = f"""Professional product photograph of {product_name}.
Pure white background (#FFFFFF), no shadows, no reflections.
Single product only, centered, high resolution.
Real commercial packaging style, authentic label design.
No studio setup, no table, no props, no decorations.
E-commerce catalog photo format, 1024x1024 square.
Sharp focus, professional product photography lighting.
Clean, minimal, catalog-ready image."""
    
    sector_hints = {
        'supermarket': 'Food/grocery packaging style with nutrition info visible.',
        'clothing': 'Fashion item on invisible mannequin or flat lay, no model.',
        'technology': 'Tech product with clean packaging, visible model name.',
        'home': 'Household item, simple presentation, practical angle.',
        'cosmetics': 'Beauty product with elegant packaging, visible brand.'
    }
    
    if sector and sector in sector_hints:
        base_prompt += f"\n{sector_hints[sector]}"
    
    return base_prompt

def get_negative_prompt():
    """Get negative prompt to avoid unwanted elements"""
    return """studio background, gradient background, colored background,
table, surface, platform, stand, tripod, lighting equipment,
human hands, people, models, mannequins visible,
multiple products, accessories not part of product,
shadows, reflections, dramatic lighting, effects,
watermarks, logos other than product brand,
low quality, blurry, pixelated, distorted,
artistic interpretation, stylized, cartoon, illustration,
3D render, CGI, fake looking, unrealistic"""


def add_watermark(image, logo_path='static/aeu_logo.png', opacity_percent=10):
    """Add AEU Yazilim logo watermark to image (bottom-right corner)"""
    try:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        width, height = image.size
        
        if not os.path.exists(logo_path):
            print(f"Logo not found: {logo_path}, using text fallback")
            txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            font_size = max(20, width // 25)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            draw.text((width - 200, height - 50), WATERMARK_TEXT, font=font, fill=(128, 128, 128, WATERMARK_OPACITY))
            watermarked = Image.alpha_composite(image, txt_layer)
            return watermarked.convert('RGB')
        
        logo = Image.open(logo_path)
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        logo_width = min(int(width * 0.15), 200)
        logo_height = int(logo.size[1] * (logo_width / logo.size[0]))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity_percent / 100))
        logo.putalpha(alpha)
        
        watermark_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
        
        x = width - logo_width - 20
        y = height - logo_height - 20
        
        watermark_layer.paste(logo, (x, y), logo)
        
        watermarked = Image.alpha_composite(image, watermark_layer)
        return watermarked.convert('RGB')
        
    except Exception as e:
        print(f"Watermark error: {e}")
        return image.convert('RGB') if image.mode == 'RGBA' else image


def get_image_quality_level(image_path):
    """Determine image quality level based on dimensions"""
    try:
        if isinstance(image_path, str) and os.path.exists(image_path):
            with Image.open(image_path) as img:
                width, height = img.size
        elif isinstance(image_path, Image.Image):
            width, height = image_path.size
        else:
            return 'unknown', 0, 0
        
        min_dim = min(width, height)
        
        if min_dim >= QUALITY_THRESHOLDS['high']:
            return 'high', width, height
        elif min_dim >= QUALITY_THRESHOLDS['medium']:
            return 'medium', width, height
        else:
            return 'low', width, height
            
    except Exception as e:
        print(f"Quality check error: {e}")
        return 'unknown', 0, 0


def process_for_admin_stock(image_source, barcode, sector, product_name=None, apply_watermark=True):
    """
    Process image for admin stock:
    - Convert to PNG
    - Resize to minimum 1024px
    - Apply watermark
    - Save to admin_stock/sector/barcode.png
    """
    try:
        if isinstance(image_source, str):
            if image_source.startswith(('http://', 'https://')):
                image = download_image(image_source)
                if not image:
                    return {'success': False, 'error': 'Failed to download image'}
            else:
                image = Image.open(image_source)
        elif isinstance(image_source, Image.Image):
            image = image_source
        else:
            return {'success': False, 'error': 'Invalid image source'}
        
        processed = resize_to_square(image, 1024)
        
        if apply_watermark:
            processed = add_watermark(processed)
        
        sector_dir = os.path.join(ADMIN_STOCK_DIR, sector)
        os.makedirs(sector_dir, exist_ok=True)
        
        output_path = os.path.join(sector_dir, f"{barcode}.png")
        processed.save(output_path, 'PNG', optimize=True)
        
        quality, width, height = get_image_quality_level(processed)
        
        return {
            'success': True,
            'path': output_path,
            'url': '/' + output_path,
            'quality': quality,
            'width': width,
            'height': height,
            'watermarked': apply_watermark
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def ensure_admin_stock_sectors():
    """Create all sector directories in admin_stock"""
    sectors = ['supermarket', 'giyim', 'teknoloji', 'kozmetik', 'evyasam', 'elsanatlari', 'restoran', 'diger']
    for sector in sectors:
        os.makedirs(os.path.join(ADMIN_STOCK_DIR, sector), exist_ok=True)
    return True


def download_and_process_camgoz_image(image_url, user_id, barcode, apply_watermark=True):
    """
    Download image from CAMGOZ API, process it, and save to customer directory.
    Uses JPEG optimization pipeline for consistent quality and file size.
    
    Args:
        image_url: URL from CAMGOZ API (e.g., https://camgoz.net/image/xxx.jpeg)
        user_id: Customer user ID
        barcode: Product barcode
        apply_watermark: Whether to apply AEU watermark (default: True)
    
    Returns:
        dict with 'success', 'path', 'url', 'quality_indicator', 'width', 'height' or 'error'
    """
    try:
        image = download_image(image_url)
        if not image:
            return {'success': False, 'error': 'Failed to download CAMGOZ image'}
        
        quality_level, width, height = get_image_quality_level(image)
        
        quality_indicators = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴',
            'unknown': '⚪'
        }
        quality_indicator = quality_indicators.get(quality_level, '⚪')
        
        processed = resize_to_square(image, 1024)
        
        if apply_watermark:
            processed = add_watermark(processed, opacity_percent=10)
        
        customer_dir = get_customer_dir(user_id)
        output_path = f'{customer_dir}/{barcode}.jpg'
        
        image_data, quality = optimize_file_size(processed)
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return {
            'success': True,
            'path': output_path,
            'url': '/' + output_path,
            'quality_level': quality_level,
            'quality_indicator': quality_indicator,
            'width': width,
            'height': height,
            'watermarked': apply_watermark,
            'file_size': len(image_data),
            'jpeg_quality': quality
        }
        
    except Exception as e:
        print(f"CAMGOZ image processing error: {e}")
        return {'success': False, 'error': str(e)}
