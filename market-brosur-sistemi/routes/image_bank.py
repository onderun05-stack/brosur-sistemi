# -*- coding: utf-8 -*-
"""
Image Bank routes - Image depot management, upload, approval workflow
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging
import os

from utils.helpers import get_current_user, safe_join
from utils.constants import SECTORS, ALLOWED_IMAGE_EXTENSIONS
from services.image_bank import (
    search_image_hierarchy,
    save_to_customer_depot,
    save_to_admin_depot,
    approve_pending_image,
    reject_pending_image,
    get_pending_images_list,
    get_admin_images_by_sector,
    get_customer_images,
    delete_image_from_depot
)

image_bank_bp = Blueprint('image_bank', __name__)


# ============= IMAGE SEARCH =============

@image_bank_bp.route('/api/image-bank/search', methods=['POST'])
def api_image_bank_search():
    """
    Search for product image in the depot hierarchy.
    
    Request body:
        barcode: str - Product barcode
        sector: str - Product sector (default: supermarket)
    
    Returns:
        found: bool
        source: str - 'customer_depot', 'admin_depot', or null
        image_url: str - URL to the image
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        barcode = data.get('barcode', '').strip()
        sector = data.get('sector', 'supermarket')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        if sector not in SECTORS:
            sector = 'supermarket'
        
        result = search_image_hierarchy(barcode, user['id'], sector)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logging.error(f"Image search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/batch-search', methods=['POST'])
def api_image_bank_batch_search():
    """
    Batch search for multiple product images.
    
    Request body:
        barcodes: list - List of barcode strings
        sector: str - Product sector
    
    Returns:
        results: dict - {barcode: {found, source, image_url}}
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        barcodes = data.get('barcodes', [])
        sector = data.get('sector', 'supermarket')
        
        if not barcodes:
            return jsonify({'success': False, 'error': 'Barcodes required'}), 400
        
        if sector not in SECTORS:
            sector = 'supermarket'
        
        results = {}
        for barcode in barcodes:
            barcode = str(barcode).strip()
            if barcode:
                results[barcode] = search_image_hierarchy(barcode, user['id'], sector)
        
        return jsonify({
            'success': True,
            'results': results,
            'found_count': sum(1 for r in results.values() if r['found']),
            'total': len(results)
        })
        
    except Exception as e:
        logging.error(f"Batch image search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= CUSTOMER UPLOAD =============

@image_bank_bp.route('/api/image-bank/upload', methods=['POST'])
def api_image_bank_upload():
    """
    Upload product image to customer's depot.
    Image is also sent to pending for admin approval.
    
    Request form:
        image: file - Image file
        barcode: str - Product barcode
        sector: str - Product sector
    
    Returns:
        image_url: str - URL to the saved image
        pending: bool - Whether image is pending approval
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        barcode = request.form.get('barcode', '').strip()
        sector = request.form.get('sector', 'supermarket')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({'success': False, 'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'}), 400
        
        if sector not in SECTORS:
            sector = 'supermarket'
        
        # Read file data
        image_data = file.read()
        
        # Save to customer depot (also copies to pending)
        result = save_to_customer_depot(
            user_id=user['id'],
            sector=sector,
            barcode=barcode,
            image_data=image_data,
            filename='product.png'
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'image_url': result['customer_url'],
                'pending': result['pending'],
                'message': 'Image uploaded and sent for approval'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Upload failed')}), 500
        
    except Exception as e:
        logging.error(f"Image upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= ADMIN OPERATIONS =============

@image_bank_bp.route('/api/image-bank/admin/upload', methods=['POST'])
def api_image_bank_admin_upload():
    """
    Admin uploads product image directly to admin depot.
    Bypasses pending approval.
    
    Request form:
        image: file - Image file
        barcode: str - Product barcode
        sector: str - Product sector
        product_name: str - Optional product name
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        barcode = request.form.get('barcode', '').strip()
        sector = request.form.get('sector', 'supermarket')
        product_name = request.form.get('product_name', '').strip()
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({'success': False, 'error': f'Invalid file type'}), 400
        
        if sector not in SECTORS:
            sector = 'supermarket'
        
        image_data = file.read()
        
        metadata = {
            'product_name': product_name or barcode,
            'uploaded_by': 'admin',
            'sector': sector
        }
        
        result = save_to_admin_depot(
            sector=sector,
            barcode=barcode,
            image_data=image_data,
            filename='product.png',
            metadata=metadata
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'image_url': result['admin_url'],
                'message': 'Image saved to admin depot'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Upload failed')}), 500
        
    except Exception as e:
        logging.error(f"Admin image upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/admin/pending')
def api_image_bank_pending():
    """
    Get list of images pending admin approval.
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        pending_list = get_pending_images_list()
        
        return jsonify({
            'success': True,
            'pending': pending_list,
            'count': len(pending_list)
        })
        
    except Exception as e:
        logging.error(f"Get pending images error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/admin/approve', methods=['POST'])
def api_image_bank_approve():
    """
    Approve pending image and move to admin depot.
    
    Request body:
        barcode: str - Product barcode
        sector: str - Product sector
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.json or {}
        barcode = data.get('barcode', '').strip()
        sector = data.get('sector', 'supermarket')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        result = approve_pending_image(sector, barcode)
        
        if result['success']:
            return jsonify({
                'success': True,
                'admin_url': result['admin_url'],
                'message': 'Image approved and moved to admin depot'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Approval failed')}), 500
        
    except Exception as e:
        logging.error(f"Approve image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/admin/reject', methods=['POST'])
def api_image_bank_reject():
    """
    Reject pending image.
    
    Request body:
        barcode: str - Product barcode
        sector: str - Product sector
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.json or {}
        barcode = data.get('barcode', '').strip()
        sector = data.get('sector', 'supermarket')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        result = reject_pending_image(sector, barcode)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image rejected'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Rejection failed')}), 500
        
    except Exception as e:
        logging.error(f"Reject image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/admin/by-sector')
def api_image_bank_by_sector():
    """
    Get all approved images in a sector.
    
    Query params:
        sector: str - Product sector
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        sector = request.args.get('sector', 'supermarket')
        
        if sector not in SECTORS:
            return jsonify({'success': False, 'error': 'Invalid sector'}), 400
        
        images = get_admin_images_by_sector(sector)
        
        return jsonify({
            'success': True,
            'images': images,
            'count': len(images),
            'sector': sector,
            'sector_name': SECTORS[sector]
        })
        
    except Exception as e:
        logging.error(f"Get images by sector error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= CUSTOMER DEPOT =============

@image_bank_bp.route('/api/image-bank/my-images')
def api_image_bank_my_images():
    """
    Get current user's uploaded images.
    
    Query params:
        sector: str - Optional sector filter
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        sector = request.args.get('sector')
        
        if sector and sector not in SECTORS:
            return jsonify({'success': False, 'error': 'Invalid sector'}), 400
        
        images = get_customer_images(user['id'], sector)
        
        return jsonify({
            'success': True,
            'images': images,
            'count': len(images)
        })
        
    except Exception as e:
        logging.error(f"Get my images error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@image_bank_bp.route('/api/image-bank/delete', methods=['POST'])
def api_image_bank_delete():
    """
    Delete image from depot.
    
    Request body:
        depot_type: str - 'admin', 'customer', or 'pending'
        barcode: str - Product barcode
        sector: str - Product sector
        user_id: int - Required for customer depot (admin can specify)
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        depot_type = data.get('depot_type', 'customer')
        barcode = data.get('barcode', '').strip()
        sector = data.get('sector', 'supermarket')
        target_user_id = data.get('user_id', user['id'])
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        # Only admin can delete from admin depot or other users' depots
        if depot_type == 'admin' or (depot_type == 'customer' and target_user_id != user['id']):
            if user.get('role') != 'admin':
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        result = delete_image_from_depot(depot_type, sector, barcode, target_user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Image deleted'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Delete failed')}), 500
        
    except Exception as e:
        logging.error(f"Delete image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

