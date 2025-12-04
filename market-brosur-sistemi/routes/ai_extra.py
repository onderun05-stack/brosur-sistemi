# -*- coding: utf-8 -*-
"""
AI Extra Routes

Additional AI endpoints for categorization, price suggestions, and preferences.
"""

from flask import Blueprint, jsonify, request, session, current_app
from functools import wraps
import logging

from services.ai_categorizer import (
    categorize_product, categorize_products, suggest_categories,
    get_all_categories, get_category_colors, suggest_price,
    compare_prices, learn_preference, get_user_preferences
)
from services.bulk_operations import (
    bulk_update_prices, bulk_update_images, bulk_generate_slogans,
    bulk_delete_products, bulk_add_labels
)
from services.version_history import (
    save_brochure_version, get_brochure_versions, get_brochure_version,
    restore_brochure_version
)

ai_extra_bp = Blueprint('ai_extra', __name__)


@ai_extra_bp.before_request
def block_stage_two_routes():
    if not current_app.config.get('ENABLE_STAGE2', False):
        return jsonify({
            'success': False,
            'error': 'Stage 2 özellikleri bu aşamada devre dışı'
        }), 403


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Giriş yapmalısınız'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============= CATEGORIZATION =============

@ai_extra_bp.route('/api/ai/categorize', methods=['POST'])
@login_required
def categorize_single():
    """
    Categorize a single product.
    
    Request: {product_name: string}
    Response: {success: bool, category: {...}}
    """
    try:
        data = request.get_json()
        product_name = data.get('product_name', '')
        
        result = categorize_product(product_name)
        
        return jsonify({
            'success': True,
            'category': result
        })
        
    except Exception as e:
        logging.error(f"Categorization error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/ai/categorize-batch', methods=['POST'])
@login_required
def categorize_batch():
    """
    Categorize multiple products.
    
    Request: {products: [{name: string, ...}]}
    Response: {success: bool, products: [...]}
    """
    try:
        data = request.get_json()
        products = data.get('products', [])
        
        result = categorize_products(products)
        
        return jsonify({
            'success': True,
            'products': result
        })
        
    except Exception as e:
        logging.error(f"Batch categorization error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/ai/suggest-categories', methods=['POST'])
@login_required
def get_category_suggestions():
    """
    Get category suggestions for a product.
    
    Request: {product_name: string}
    Response: {success: bool, suggestions: [...]}
    """
    try:
        data = request.get_json()
        product_name = data.get('product_name', '')
        
        suggestions = suggest_categories(product_name)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logging.error(f"Category suggestions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/ai/categories', methods=['GET'])
def list_categories():
    """
    Get all available categories.
    
    Response: {success: bool, categories: [...]}
    """
    try:
        categories = get_all_categories()
        colors = get_category_colors()
        
        return jsonify({
            'success': True,
            'categories': categories,
            'colors': colors
        })
        
    except Exception as e:
        logging.error(f"List categories error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= PRICE SUGGESTIONS =============

@ai_extra_bp.route('/api/ai/suggest-price', methods=['POST'])
@login_required
def get_price_suggestion():
    """
    Get price suggestion for a product.
    
    Request: {product_name: string, category: string, market_price: float}
    Response: {success: bool, suggestion: {...}}
    """
    try:
        data = request.get_json()
        product_name = data.get('product_name', '')
        category = data.get('category')
        market_price = data.get('market_price')
        
        suggestion = suggest_price(product_name, category, market_price)
        
        return jsonify({
            'success': True,
            'suggestion': suggestion
        })
        
    except Exception as e:
        logging.error(f"Price suggestion error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/ai/compare-price', methods=['POST'])
@login_required
def compare_price():
    """
    Compare product price with market price.
    
    Request: {product_price: float, market_price: float}
    Response: {success: bool, comparison: {...}}
    """
    try:
        data = request.get_json()
        product_price = data.get('product_price', 0)
        market_price = data.get('market_price', 0)
        
        comparison = compare_prices(product_price, market_price)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logging.error(f"Price comparison error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= BULK OPERATIONS =============

@ai_extra_bp.route('/api/bulk/update-prices', methods=['POST'])
@login_required
def bulk_prices():
    """
    Bulk update product prices.
    
    Request: {products: [...], operation: string, value: float}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        products = data.get('products', [])
        operation = data.get('operation', 'set')
        value = data.get('value', 0)
        
        result = bulk_update_prices(user_id, products, operation, value)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Bulk price update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/bulk/update-images', methods=['POST'])
@login_required
def bulk_images():
    """
    Bulk update product images.
    
    Request: {products: [{barcode, image_url}, ...]}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        products = data.get('products', [])
        
        result = bulk_update_images(user_id, products)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Bulk image update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/bulk/generate-slogans', methods=['POST'])
@login_required
def bulk_slogans():
    """
    Bulk generate slogans for products.
    
    Request: {products: [{barcode, name, category}, ...]}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        products = data.get('products', [])
        
        result = bulk_generate_slogans(user_id, products)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Bulk slogan generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/bulk/delete', methods=['POST'])
@login_required
def bulk_delete():
    """
    Bulk delete products.
    
    Request: {barcodes: [string, ...]}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        barcodes = data.get('barcodes', [])
        
        result = bulk_delete_products(user_id, barcodes)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Bulk delete error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/bulk/add-labels', methods=['POST'])
@login_required
def bulk_labels():
    """
    Bulk add labels to products.
    
    Request: {products: [...], labels: [string, ...]}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        products = data.get('products', [])
        labels = data.get('labels', [])
        
        result = bulk_add_labels(user_id, products, labels)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Bulk add labels error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= VERSION HISTORY =============

@ai_extra_bp.route('/api/brochure/<brochure_id>/versions', methods=['GET'])
@login_required
def get_versions(brochure_id):
    """Get version history for a brochure."""
    try:
        user_id = session['user_id']
        limit = request.args.get('limit', 10, type=int)
        
        versions = get_brochure_versions(brochure_id, user_id, limit)
        
        return jsonify({
            'success': True,
            'versions': versions
        })
        
    except Exception as e:
        logging.error(f"Get versions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/brochure/<brochure_id>/versions/<int:version_number>', methods=['GET'])
@login_required
def get_version(brochure_id, version_number):
    """Get a specific version."""
    try:
        user_id = session['user_id']
        
        version = get_brochure_version(brochure_id, user_id, version_number)
        
        if not version:
            return jsonify({'success': False, 'error': 'Versiyon bulunamadı'}), 404
        
        return jsonify({
            'success': True,
            'version': version
        })
        
    except Exception as e:
        logging.error(f"Get version error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/brochure/<brochure_id>/versions/<int:version_number>/restore', methods=['POST'])
@login_required
def restore_version(brochure_id, version_number):
    """Restore a specific version."""
    try:
        user_id = session['user_id']
        
        result = restore_brochure_version(brochure_id, user_id, version_number)
        
        if not result:
            return jsonify({'success': False, 'error': 'Geri yükleme başarısız'}), 400
        
        return jsonify({
            'success': True,
            'restored': result
        })
        
    except Exception as e:
        logging.error(f"Restore version error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/brochure/<brochure_id>/save-version', methods=['POST'])
@login_required
def save_version(brochure_id):
    """Save current state as a version."""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        brochure_data = data.get('data', {})
        action = data.get('action', 'save')
        
        version_number = save_brochure_version(brochure_id, user_id, brochure_data, action)
        
        if not version_number:
            return jsonify({'success': False, 'error': 'Kayıt başarısız'}), 400
        
        return jsonify({
            'success': True,
            'version_number': version_number
        })
        
    except Exception as e:
        logging.error(f"Save version error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= USER PREFERENCES =============

@ai_extra_bp.route('/api/preferences/learn', methods=['POST'])
@login_required
def learn_user_preference():
    """
    Record a user preference for learning.
    
    Request: {type: string, key: string, value: string}
    """
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        pref_type = data.get('type', '')
        pref_key = data.get('key', '')
        pref_value = data.get('value', '')
        
        if not all([pref_type, pref_key, pref_value]):
            return jsonify({'success': False, 'error': 'Eksik parametre'}), 400
        
        learn_preference(user_id, pref_type, pref_key, pref_value)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Learn preference error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_extra_bp.route('/api/preferences/<pref_type>', methods=['GET'])
@login_required
def get_preferences(pref_type):
    """Get user preferences of a specific type."""
    try:
        user_id = session['user_id']
        limit = request.args.get('limit', 5, type=int)
        
        preferences = get_user_preferences(user_id, pref_type, limit)
        
        return jsonify({
            'success': True,
            'preferences': preferences
        })
        
    except Exception as e:
        logging.error(f"Get preferences error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

