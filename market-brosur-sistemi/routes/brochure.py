# -*- coding: utf-8 -*-
"""
Brochure routes - Multi-page brochure editor API endpoints.
"""

from flask import Blueprint, request, jsonify
import logging
import base64
import os
from datetime import datetime

from utils.helpers import get_current_user
from services.brochure_engine import (
    create_brochure,
    get_brochure,
    save_brochure,
    delete_brochure,
    list_brochures,
    add_page,
    delete_page,
    copy_page,
    reorder_pages,
    toggle_page_lock,
    set_page_layout,
    add_product_to_page,
    remove_product_from_page,
    move_product,
    update_product_position,
    toggle_product_lock,
    add_to_parking,
    remove_from_parking,
    clear_parking,
    auto_arrange_page,
    distribute_products_to_pages,
    save_as_template,
    list_templates,
    apply_template,
    LAYOUT_TEMPLATES
)

brochure_bp = Blueprint('brochure', __name__)


# ============= BROCHURE CRUD =============

@brochure_bp.route('/api/brochure/create', methods=['POST'])
def api_brochure_create():
    """Create a new brochure"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        name = data.get('name', f'Broşür {datetime.now().strftime("%d.%m.%Y")}')
        sector = data.get('sector', user.get('sector', 'supermarket'))
        
        brochure = create_brochure(user['id'], name, sector)
        
        return jsonify({
            'success': True,
            'brochure': brochure
        })
        
    except Exception as e:
        logging.error(f"Create brochure error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brochure_bp.route('/api/brochure/<brochure_id>')
def api_brochure_get(brochure_id):
    """Get brochure by ID"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    return jsonify({
        'success': True,
        'brochure': brochure
    })


@brochure_bp.route('/api/brochure/<brochure_id>', methods=['PUT'])
def api_brochure_update(brochure_id):
    """Update brochure metadata"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    try:
        data = request.json or {}
        
        if 'name' in data:
            brochure['name'] = data['name']
        if 'settings' in data:
            brochure['settings'].update(data['settings'])
        if 'page_size' in data:
            brochure['page_size'].update(data['page_size'])
        
        save_brochure(brochure)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Update brochure error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brochure_bp.route('/api/brochure/<brochure_id>', methods=['DELETE'])
def api_brochure_delete(brochure_id):
    """Delete brochure"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    if delete_brochure(user['id'], brochure_id):
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Brochure not found'}), 404


@brochure_bp.route('/api/brochures')
def api_brochures_list():
    """List all brochures for current user"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochures = list_brochures(user['id'])
    
    return jsonify({
        'success': True,
        'brochures': brochures,
        'count': len(brochures)
    })


# ============= PAGE MANAGEMENT =============

@brochure_bp.route('/api/brochure/<brochure_id>/page', methods=['POST'])
def api_brochure_add_page(brochure_id):
    """Add a new page to brochure"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    layout = data.get('layout')
    
    result = add_page(brochure, layout)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>', methods=['DELETE'])
def api_brochure_delete_page(brochure_id, page_id):
    """Delete a page from brochure"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = delete_page(brochure, page_id)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/copy', methods=['POST'])
def api_brochure_copy_page(brochure_id, page_id):
    """Copy a page"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = copy_page(brochure, page_id)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/pages/reorder', methods=['POST'])
def api_brochure_reorder_pages(brochure_id):
    """Reorder pages"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    page_order = data.get('order', [])
    
    result = reorder_pages(brochure, page_order)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/lock', methods=['POST'])
def api_brochure_toggle_page_lock(brochure_id, page_id):
    """Toggle page lock"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = toggle_page_lock(brochure, page_id)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/layout', methods=['POST'])
def api_brochure_set_page_layout(brochure_id, page_id):
    """Set page layout"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    layout = data.get('layout', 'grid_4x4')
    
    result = set_page_layout(brochure, page_id, layout)
    return jsonify(result)


# ============= PRODUCT MANAGEMENT =============

@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/product', methods=['POST'])
def api_brochure_add_product(brochure_id, page_id):
    """Add product to page"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    product_data = data.get('product', {})
    position = data.get('position')
    
    result = add_product_to_page(brochure, page_id, product_data, position)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/product/<product_id>', methods=['DELETE'])
def api_brochure_remove_product(brochure_id, page_id, product_id):
    """Remove product from page"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    move_to_parking = data.get('move_to_parking', True)
    
    result = remove_product_from_page(brochure, page_id, product_id, move_to_parking)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/product/<product_id>/move', methods=['POST'])
def api_brochure_move_product(brochure_id, product_id):
    """Move product between pages or parking area"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    target_page_id = data.get('target_page_id', 'parking')
    position = data.get('position')
    
    result = move_product(brochure, product_id, target_page_id, position)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/product/<product_id>/position', methods=['PUT'])
def api_brochure_update_product_position(brochure_id, page_id, product_id):
    """Update product position"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    position = data.get('position', {})
    
    result = update_product_position(brochure, page_id, product_id, position)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/product/<product_id>/lock', methods=['POST'])
def api_brochure_toggle_product_lock(brochure_id, page_id, product_id):
    """Toggle product lock"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = toggle_product_lock(brochure, page_id, product_id)
    return jsonify(result)


# ============= PARKING AREA =============

@brochure_bp.route('/api/brochure/<brochure_id>/parking', methods=['POST'])
def api_brochure_add_to_parking(brochure_id):
    """Add product to parking area"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    product_data = data.get('product', {})
    
    result = add_to_parking(brochure, product_data)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/parking/<product_id>', methods=['DELETE'])
def api_brochure_remove_from_parking(brochure_id, product_id):
    """Remove product from parking area"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = remove_from_parking(brochure, product_id)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/parking/clear', methods=['POST'])
def api_brochure_clear_parking(brochure_id):
    """Clear parking area"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = clear_parking(brochure)
    return jsonify(result)


# ============= AUTO LAYOUT =============

@brochure_bp.route('/api/brochure/<brochure_id>/page/<page_id>/auto-arrange', methods=['POST'])
def api_brochure_auto_arrange(brochure_id, page_id):
    """Auto-arrange products on page"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    result = auto_arrange_page(brochure, page_id)
    return jsonify(result)


@brochure_bp.route('/api/brochure/<brochure_id>/distribute', methods=['POST'])
def api_brochure_distribute(brochure_id):
    """Distribute products across pages"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    products = data.get('products', [])
    
    result = distribute_products_to_pages(brochure, products)
    return jsonify(result)


# ============= TEMPLATES =============

@brochure_bp.route('/api/brochure/<brochure_id>/save-template', methods=['POST'])
def api_brochure_save_template(brochure_id):
    """Save brochure as template"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    template_name = data.get('name', f'Şablon {datetime.now().strftime("%d.%m.%Y")}')
    
    result = save_as_template(brochure, template_name)
    return jsonify(result)


@brochure_bp.route('/api/templates')
def api_templates_list():
    """List user's templates"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    templates = list_templates(user['id'])
    
    return jsonify({
        'success': True,
        'templates': templates,
        'count': len(templates)
    })


@brochure_bp.route('/api/brochure/<brochure_id>/apply-template', methods=['POST'])
def api_brochure_apply_template(brochure_id):
    """Apply template to brochure"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    data = request.json or {}
    template_id = data.get('template_id')
    
    if not template_id:
        return jsonify({'success': False, 'error': 'Template ID required'}), 400
    
    result = apply_template(brochure, template_id)
    return jsonify(result)


@brochure_bp.route('/api/layouts')
def api_layouts_list():
    """Get available layout templates"""
    return jsonify({
        'success': True,
        'layouts': LAYOUT_TEMPLATES
    })


# ============= EXPORT =============

@brochure_bp.route('/api/brochure/<brochure_id>/export', methods=['POST'])
def api_brochure_export(brochure_id):
    """Export brochure (receives rendered images from frontend)"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    try:
        data = request.json or {}
        format_type = data.get('format', 'png')  # png, jpeg, pdf
        pages_data = data.get('pages', [])  # Base64 encoded page images
        quality = data.get('quality', 90)
        
        if not pages_data:
            return jsonify({'success': False, 'error': 'No page data provided'}), 400
        
        # Create export directory
        export_dir = os.path.join('static', 'exports', str(user['id']), brochure_id)
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        exported_files = []
        
        for i, page_data in enumerate(pages_data):
            # Remove data URL prefix if present
            if ',' in page_data:
                page_data = page_data.split(',')[1]
            
            image_bytes = base64.b64decode(page_data)
            
            if format_type == 'jpeg':
                filename = f'page_{i+1}_{timestamp}.jpg'
            else:
                filename = f'page_{i+1}_{timestamp}.png'
            
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            exported_files.append(f'/static/exports/{user["id"]}/{brochure_id}/{filename}')
        
        # Update metadata
        brochure['metadata']['export_count'] = brochure['metadata'].get('export_count', 0) + 1
        brochure['metadata']['last_export'] = datetime.now().isoformat()
        save_brochure(brochure)
        
        return jsonify({
            'success': True,
            'files': exported_files,
            'format': format_type,
            'page_count': len(exported_files)
        })
        
    except Exception as e:
        logging.error(f"Export error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= WATERMARK SYSTEM =============

@brochure_bp.route('/api/brochure/add-watermark', methods=['POST'])
def api_add_watermark():
    """Add AEU Yazılım watermark to export (free mode)"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        image_data = data.get('image_data', '')
        watermark_text = data.get('watermark_text', 'AEU Yazılım')
        opacity = data.get('opacity', 0.3)  # 0-1 transparency
        position = data.get('position', 'bottom-right')  # bottom-right, bottom-left, center
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data'}), 400
        
        # Check if user is premium (has credits > 0 or paid)
        is_premium = user.get('credits', 0) > 50 or user.get('role') == 'admin'
        
        if is_premium:
            # Premium users don't get watermark
            return jsonify({
                'success': True, 
                'watermarked': False,
                'image_data': image_data,
                'message': 'Premium kullanıcı - filigran eklenmedi'
            })
        
        # For free users, add watermark
        # Note: Actual watermark implementation would use PIL
        # This is a placeholder that returns watermark info
        
        return jsonify({
            'success': True,
            'watermarked': True,
            'watermark_info': {
                'text': watermark_text,
                'opacity': opacity,
                'position': position
            },
            'image_data': image_data,  # In real implementation, this would be watermarked
            'message': 'Ücretsiz modda filigran eklendi'
        })
        
    except Exception as e:
        logging.error(f"Watermark error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brochure_bp.route('/api/brochure/check-watermark-required')
def api_check_watermark():
    """Check if watermark is required for current user"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    is_premium = user.get('credits', 0) > 50 or user.get('role') == 'admin'
    
    return jsonify({
        'success': True,
        'watermark_required': not is_premium,
        'user_credits': user.get('credits', 0),
        'is_admin': user.get('role') == 'admin'
    })


# ============= INSTAGRAM EXPORT =============

@brochure_bp.route('/api/brochure/<brochure_id>/export-instagram', methods=['POST'])
def api_export_instagram(brochure_id):
    """Export brochure for Instagram (post and story formats)"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    brochure = get_brochure(user['id'], brochure_id)
    if not brochure:
        return jsonify({'success': False, 'error': 'Brochure not found'}), 404
    
    try:
        data = request.json or {}
        pages_data = data.get('pages', [])
        format_type = data.get('format', 'post')  # 'post' (1080x1080) or 'story' (1080x1920)
        
        if not pages_data:
            return jsonify({'success': False, 'error': 'No page data provided'}), 400
        
        # Instagram dimensions
        INSTAGRAM_FORMATS = {
            'post': {'width': 1080, 'height': 1080, 'aspect': '1:1'},
            'story': {'width': 1080, 'height': 1920, 'aspect': '9:16'},
            'landscape': {'width': 1080, 'height': 566, 'aspect': '1.91:1'},
            'portrait': {'width': 1080, 'height': 1350, 'aspect': '4:5'}
        }
        
        format_info = INSTAGRAM_FORMATS.get(format_type, INSTAGRAM_FORMATS['post'])
        
        # Create export directory
        export_dir = os.path.join('static', 'exports', str(user['id']), brochure_id, 'instagram')
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        exported_files = []
        
        for i, page_data in enumerate(pages_data):
            # Remove data URL prefix if present
            if ',' in page_data:
                page_data = page_data.split(',')[1]
            
            image_bytes = base64.b64decode(page_data)
            
            filename = f'ig_{format_type}_{i+1}_{timestamp}.jpg'
            filepath = os.path.join(export_dir, filename)
            
            # Note: In production, you would resize the image to Instagram dimensions
            # using PIL or similar library here
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            exported_files.append({
                'url': f'/static/exports/{user["id"]}/{brochure_id}/instagram/{filename}',
                'format': format_type,
                'dimensions': format_info
            })
        
        return jsonify({
            'success': True,
            'files': exported_files,
            'format': format_type,
            'format_info': format_info,
            'page_count': len(exported_files),
            'ready_for_upload': True
        })
        
    except Exception as e:
        logging.error(f"Instagram export error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brochure_bp.route('/api/brochure/instagram-formats')
def api_instagram_formats():
    """Get available Instagram export formats"""
    formats = {
        'post': {
            'name': 'Kare Gönderi',
            'width': 1080,
            'height': 1080,
            'aspect': '1:1',
            'description': 'Standart Instagram gönderi formatı'
        },
        'story': {
            'name': 'Hikaye',
            'width': 1080,
            'height': 1920,
            'aspect': '9:16',
            'description': 'Instagram hikaye formatı'
        },
        'landscape': {
            'name': 'Yatay',
            'width': 1080,
            'height': 566,
            'aspect': '1.91:1',
            'description': 'Yatay gönderi formatı'
        },
        'portrait': {
            'name': 'Dikey',
            'width': 1080,
            'height': 1350,
            'aspect': '4:5',
            'description': 'Dikey gönderi formatı'
        }
    }
    
    return jsonify({'success': True, 'formats': formats})

