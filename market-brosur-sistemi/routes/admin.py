# -*- coding: utf-8 -*-
"""
Admin routes - Admin panel, user management, product approval
"""

from flask import Blueprint, render_template, request, jsonify, redirect, send_file, make_response
from datetime import datetime
from io import BytesIO
from PIL import Image
import sqlite3
import logging
import shutil
import json
import os
import re

import database
from utils.helpers import get_current_user, safe_join, ensure_sector_dirs
from utils.constants import SECTORS, get_product_groups_for_sector

admin_bp = Blueprint('admin', __name__)

def normalize_image_url(image_url):
    if not image_url:
        return None
    image_url = image_url.strip()
    if not image_url:
        return None
    if image_url.startswith('http://') or image_url.startswith('https://'):
        return image_url
    # Normalize filesystem paths to web paths
    normalized = image_url.replace('\\', '/')
    if normalized.startswith('/'):
        return normalized
    normalized = normalized.lstrip('/')
    if normalized.startswith('static/'):
        return '/' + normalized
    return f'/static/{normalized}'

def format_db_product(row):
    sector = row['sector'] or 'supermarket'
    sector_name = SECTORS.get(sector, sector.capitalize())
    image_url = normalize_image_url(row['image_url'])
    source_label = row['image_source'] or ('admin' if row['user_role'] == 'admin' else 'customer')
    
    return {
        'barcode': row['barcode'],
        'product_name': row['name'],
        'sector': sector,
        'sector_name': sector_name,
        'product_group': row['product_group'] or 'Genel',
        'source': source_label,
        'customer_id': row['user_id'],
        'last_modified': row['created_at'],
        'has_image': bool(image_url),
        'image_quality': 'unknown',
        'image_handler': 'url' if image_url else 'fs',
        'image_url': image_url,
        'image_source': source_label,
        'market_price': row['market_price'] or 0,
        'market_price_tax': row['market_price_tax'] or 0,
        'normal_price': row['normal_price'] or 0,
        'discount_price': row['discount_price'] or 0,
        'owner_name': row['user_name'],
        'owner_role': row['user_role'],
        'allow_edit': True,
    }

def format_admin_product(row):
    sector = row['sector'] or 'supermarket'
    sector_name = SECTORS.get(sector, sector.capitalize())
    image_url = normalize_image_url(row['image_path'])
    return {
        'barcode': row['barcode'],
        'product_name': row['full_name'],
        'sector': sector,
        'sector_name': sector_name,
        'product_group': row['product_group'] or 'Genel',
        'source': 'admin',
        'customer_id': None,
        'last_modified': row['updated_at'] or row['created_at'],
        'has_image': bool(image_url),
        'image_quality': row['image_quality'] or 'unknown',
        'image_handler': 'url' if image_url else 'fs',
        'image_url': image_url,
        'image_source': 'admin',
        'market_price': row['market_price'] or 0,
        'market_price_tax': row['market_price_tax'] or 0,
        'normal_price': 0,
        'discount_price': 0,
        'owner_name': 'Admin',
        'owner_role': 'admin',
        'allow_edit': True,
    }


# ============= ADMIN DASHBOARD =============

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Admin Dashboard - Main Panel"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return redirect('/dashboard')
        
        ensure_sector_dirs()
        
        pending_count = len([f for f in os.listdir(os.path.join('static', 'uploads', 'pending')) 
                           if os.path.isdir(os.path.join('static', 'uploads', 'pending', f))]) \
                       if os.path.exists(os.path.join('static', 'uploads', 'pending')) else 0
        
        return render_template('admin_dashboard.html', 
                             sectors=SECTORS,
                             pending_count=pending_count)
    except Exception as e:
        logging.error(f"❌ Admin dashboard error: {str(e)}")
        return redirect('/dashboard')


@admin_bp.route('/admin/desinger')
def admin_desinger_test():
    """Standalone Desınger test sayfası (sadece admin için, canlı akışı etkilemez)."""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return redirect('/dashboard')
        return render_template('desinger.html')
    except Exception as e:
        logging.error(f"❌ Desinger test sayfası hatası: {str(e)}")
        return redirect('/admin/dashboard')


@admin_bp.route('/admin/githb')
def admin_githb_test():
    """Gıthb Test 2 sayfası (sadece admin için, canlı akışı etkilemez)."""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return redirect('/dashboard')
        return render_template('githb.html')
    except Exception as e:
        logging.error(f"❌ Githb test sayfası hatası: {str(e)}")
        return redirect('/admin/dashboard')


@admin_bp.route('/admin/partial/<section>')
def admin_partial(section):
    """Load admin partial templates via AJAX"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return 'Unauthorized', 403
        
        valid_sections = ['products', 'pending', 'customers', 'settings', 'users']
        if section not in valid_sections:
            return 'Invalid section', 400
        
        template_map = {
            'products': 'partials/admin_products.html',
            'pending': 'partials/admin_pending.html',
            'customers': 'partials/admin_customers.html',
            'settings': 'partials/admin_site_settings.html',
            'users': 'partials/admin_users.html'
        }
        
        return render_template(template_map[section])
    except Exception as e:
        logging.error(f"❌ Admin partial error: {str(e)}")
        return f'Error loading section: {str(e)}', 500


@admin_bp.route('/admin/site-management')
def site_management():
    """Site management - redirect to unified admin dashboard"""
    return redirect('/admin/dashboard')


# ============= ADMIN SETTINGS =============

@admin_bp.route('/api/admin/settings/ai-pricing', methods=['GET', 'POST'])
def admin_ai_pricing_settings():
    """Get/Set AI pricing settings"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        settings_file = 'data/ai_pricing.json'
        os.makedirs('data', exist_ok=True)
        
        if request.method == 'GET':
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {
                    'gpt4o_price': 10,
                    'gpt4o_mini_price': 2,
                    'dalle3_price': 50,
                    'default_credits': 100
                }
            return jsonify({'success': True, 'settings': settings})
        else:
            data = request.get_json()
            settings = {
                'gpt4o_price': data.get('gpt4o_price', 10),
                'gpt4o_mini_price': data.get('gpt4o_mini_price', 2),
                'dalle3_price': data.get('dalle3_price', 50),
                'default_credits': data.get('default_credits', 100)
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
            return jsonify({'success': True})
    except Exception as e:
        logging.error(f"❌ AI pricing settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/settings/general', methods=['GET', 'POST'])
def admin_general_settings():
    """Get/Set general site settings"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        settings_file = 'data/general_settings.json'
        os.makedirs('data', exist_ok=True)
        
        if request.method == 'GET':
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {
                    'site_title': 'AEU Yazilim Brosur Sistemi',
                    'company_name': 'AEU Yazilim',
                    'primary_color': '#667eea',
                    'secondary_color': '#764ba2'
                }
            
            # Check if admin logo exists
            if os.path.exists('static/aeu_logo.png'):
                settings['logo_url'] = '/static/aeu_logo.png?t=' + str(int(datetime.now().timestamp()))
            
            return jsonify({'success': True, 'settings': settings})
        else:
            data = request.get_json()
            settings = {
                'site_title': data.get('site_title', 'AEU Yazilim Brosur Sistemi'),
                'company_name': data.get('company_name', 'AEU Yazilim'),
                'primary_color': data.get('primary_color', '#667eea'),
                'secondary_color': data.get('secondary_color', '#764ba2')
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
            return jsonify({'success': True})
    except Exception as e:
        logging.error(f"❌ General settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/upload-logo', methods=['POST'])
def admin_upload_logo():
    """Upload site logo"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if 'logo' not in request.files:
            return jsonify({'success': False, 'error': 'Logo dosyası bulunamadı'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
        
        # Dosya uzantısı kontrolü
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Geçersiz dosya tipi'}), 400
        
        # Logo'yu static klasörüne kaydet
        logo_path = os.path.join('static', 'aeu_logo.png')
        file.save(logo_path)
        
        logging.info(f"✅ Logo uploaded: {logo_path}")
        return jsonify({
            'success': True, 
            'message': 'Logo yüklendi',
            'logo_url': '/static/aeu_logo.png'
        })
        
    except Exception as e:
        logging.error(f"❌ Upload logo error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= USER MANAGEMENT =============

@admin_bp.route('/api/admin/users/add-credits', methods=['POST'])
def admin_add_credits():
    """Add credits to a user"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount', 0)
        
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        new_credits = target_user.get('credits', 0) + amount
        database.update_user_credits(user_id, new_credits)
        
        return jsonify({'success': True, 'new_credits': new_credits})
    except Exception as e:
        logging.error(f"❌ Add credits error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/users/update-role', methods=['POST'])
def admin_update_role():
    """Update user role"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        new_role = data.get('role', 'customer')
        
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        database.update_user(user_id, {'role': new_role})
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"❌ Update role error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/customers')
def admin_get_customers():
    """Get all customers (non-admin users)"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        all_users = database.get_all_users()
        customers = [u for u in all_users if u.get('role') != 'admin']
        
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        logging.error(f"❌ Get customers error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= API ADMIN USERS =============

@admin_bp.route('/api/admin/users')
def api_admin_users():
    """Get all users (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    users = database.get_all_users()
    return jsonify({'success': True, 'users': users})


@admin_bp.route('/api/admin/users', methods=['POST'])
def api_admin_create_user():
    """Create new user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'customer')
        sector = data.get('sector', 'supermarket')
        credits = int(data.get('credits', 0))
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email ve şifre gerekli'}), 400
        
        existing = database.get_user_by_email(email)
        if existing:
            return jsonify({'success': False, 'error': 'Bu email zaten kayıtlı'}), 400
        
        new_user = database.create_user_full(name, email, password, role, sector, credits)
        if not new_user:
            return jsonify({'success': False, 'error': 'Kullanici olusturulamadi'}), 500
        return jsonify({'success': True, 'user': new_user})
        
    except Exception as e:
        logging.error(f"Create user error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def api_admin_update_user(user_id):
    """Update user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        updates = {}
        if 'name' in data:
            updates['name'] = data['name'].strip()
        if 'email' in data:
            updates['email'] = data['email'].strip()
        if 'password' in data and data['password']:
            updates['password'] = data['password']
        if 'role' in data:
            updates['role'] = data['role']
        if 'sector' in data:
            updates['sector'] = data['sector']
        if 'credits' in data:
            updates['credits'] = int(data['credits'])
        
        database.update_user(user_id, updates)
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Update user error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def api_admin_delete_user(user_id):
    """Delete user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if target_user.get('role') == 'admin' and target_user.get('id') == user.get('id'):
            return jsonify({'success': False, 'error': 'Kendinizi silemezsiniz'}), 400
        
        database.delete_user(user_id)
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Delete user error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/users/<int:user_id>/credits', methods=['POST'])
def api_admin_user_credits(user_id):
    """Add credits to specific user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        amount = int(data.get('amount', 0))
        
        target_user = database.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        new_credits = target_user.get('credits', 0) + amount
        database.update_user_credits(user_id, new_credits)
        
        return jsonify({'success': True, 'new_credits': new_credits})
        
    except Exception as e:
        logging.error(f"Add user credits error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/add-credits', methods=['POST'])
def api_admin_add_credits():
    """Add credits to user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        target_user_id = data.get('user_id')
        credits = float(data.get('credits', 0))
        
        target_user = database.get_user_by_id(target_user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        new_credits = target_user.get('credits', 0) + credits
        database.update_user_credits(target_user_id, new_credits)
        
        return jsonify({'success': True, 'new_credits': new_credits})
        
    except Exception as e:
        logging.error(f"Add credits error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= PRODUCT MANAGEMENT =============

@admin_bp.route('/api/admin/product-groups')
def admin_product_groups():
    """Get product groups for a specific sector"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        sector = request.args.get('sector', 'supermarket')
        product_groups = get_product_groups_for_sector(sector)
        
        return jsonify({'success': True, 'product_groups': product_groups})
    except Exception as e:
        logging.error(f"Get product groups error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/products-by-sector')
def admin_products_by_sector():
    """Get all products in a sector from admin catalog"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        sector = request.args.get('sector', 'supermarket')
        sector_path = os.path.join('static', 'uploads', 'admin', sector)
        
        products = []
        if os.path.exists(sector_path):
            for barcode in os.listdir(sector_path):
                barcode_path = os.path.join(sector_path, barcode)
                if os.path.isdir(barcode_path):
                    img_files = [f for f in os.listdir(barcode_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                    if img_files:
                        products.append({
                            'barcode': barcode,
                            'sector': sector,
                            'image_url': f'/static/uploads/admin/{sector}/{barcode}/{img_files[0]}'
                        })
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        logging.error(f"❌ Products by sector error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/pending-approvals')
def admin_pending_approvals():
    """Get pending products from DB (approval_status='pending')"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # DB'den pending ürünleri al
        pending_products = database.get_pending_products()
        
        pending_items = []
        for product in pending_products:
            barcode = product.get('barcode', '')
            sector = product.get('user_sector', 'supermarket')
            group = product.get('product_group', 'Genel')
            
            # Pending klasöründe resim var mı kontrol et
            pending_path = os.path.join('static', 'uploads', 'pending', sector, group, barcode)
            image_url = product.get('image_url', '')
            
            if os.path.exists(pending_path):
                img_files = [f for f in os.listdir(pending_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                if img_files:
                    image_url = f'/static/uploads/pending/{sector}/{group}/{barcode}/{img_files[0]}'
            
            pending_items.append({
                'id': product.get('id'),
                'barcode': barcode,
                'name': product.get('name', ''),
                'sector': sector,
                'group': group,
                'normal_price': product.get('normal_price', 0),
                'discount_price': product.get('discount_price', 0),
                'image_url': image_url,
                'user_name': product.get('user_name', ''),
                'user_email': product.get('user_email', ''),
                'created_at': product.get('created_at', ''),
                'approval_status': 'pending'
            })
        
        return jsonify({
            'success': True, 
            'pending': pending_items,
            'count': len(pending_items)
        })
    except Exception as e:
        logging.error(f"❌ Pending approvals error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_product_info(folder_path, barcode, sector, source, customer_id):
    """Extract product info from a folder"""
    try:
        if not os.path.exists(folder_path):
            return None
        
        # Önce metadata kontrolü yap - metadata varsa ürünü döndür (resim olmasa bile)
        metadata_path = os.path.join(folder_path, 'metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as meta_error:
                logging.warning(f"Pending metadata parse error for {barcode}: {meta_error}")
        
        # Resim dosyalarını kontrol et
        img_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        if not img_files:
            return None
        
        stat = os.stat(folder_path)
        last_modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Resim kalitesini kontrol et
        image_quality = 'unknown'
        if img_files:
            try:
                img_path = os.path.join(folder_path, img_files[0])
                with Image.open(img_path) as img:
                    width, height = img.size
                    min_dim = min(width, height)
                    if min_dim >= 1024:
                        image_quality = 'high'
                    elif min_dim >= 512:
                        image_quality = 'medium'
                    else:
                        image_quality = 'low'
            except:
                pass
        
        product_name = metadata.get('product_name') or metadata.get('name') or barcode
        product_group = metadata.get('product_group') or metadata.get('group') or 'Belirtilmedi'
        image_file = img_files[0]
        image_url = f'/static/uploads/pending/{sector}/{barcode}/{image_file}'
        
        return {
            'barcode': barcode,
            'product_name': product_name,
            'sector': sector,
            'sector_name': SECTORS.get(sector, sector.capitalize()),
            'product_group': product_group,
            'source': source,
            'customer_id': customer_id,
            'last_modified': last_modified,
            'has_image': True,
            'image_quality': image_quality,
            'image_handler': 'fs',
            'image_url': image_url,
            'allow_edit': True
        }
    except Exception as e:
        logging.error(f"Get product info error: {str(e)}")
        return None


@admin_bp.route('/api/admin/all-products')
def admin_all_products():
    """Get all products from all sources (customers/pending/admin) with filtering"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        search = request.args.get('search', '').lower().strip()
        sector_filter = request.args.get('sector', '')
        source_filter = request.args.get('source', '')
        
        products = []
        base_path = os.path.join('static', 'uploads')
        
        # 1. Scan ADMIN folders
        admin_base = os.path.join(base_path, 'admin')
        if os.path.exists(admin_base):
            for sector in os.listdir(admin_base):
                sector_path = os.path.join(admin_base, sector)
                if os.path.isdir(sector_path) and sector in SECTORS:
                    for barcode in os.listdir(sector_path):
                        barcode_path = os.path.join(sector_path, barcode)
                        if os.path.isdir(barcode_path):
                            product = get_product_info(barcode_path, barcode, sector, 'admin', None)
                            if product:
                                products.append(product)
        
        # 2. PENDING klasörü artık taranmıyor
        # Pending ürünler /api/admin/pending-approvals endpoint'inden geliyor
        # (approval_status='pending' olan DB kayıtları)
        
        # 3. Scan CUSTOMERS folders
        customers_base = os.path.join(base_path, 'customers')
        if os.path.exists(customers_base):
            for customer_id in os.listdir(customers_base):
                customer_path = os.path.join(customers_base, customer_id)
                if os.path.isdir(customer_path):
                    for sector in os.listdir(customer_path):
                        sector_path = os.path.join(customer_path, sector)
                        if os.path.isdir(sector_path):
                            if sector in SECTORS:
                                for barcode in os.listdir(sector_path):
                                    barcode_path = os.path.join(sector_path, barcode)
                                    if os.path.isdir(barcode_path):
                                        product = get_product_info(barcode_path, barcode, sector, 'customer', customer_id)
                                        if product:
                                            products.append(product)
                            elif sector == 'ai_generated':
                                for img_file in os.listdir(sector_path):
                                    if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                        img_path = os.path.join(sector_path, img_file)
                                        barcode = os.path.splitext(img_file)[0]
                                        stat = os.stat(img_path)
                                        image_quality = 'unknown'
                                        try:
                                            with Image.open(img_path) as img:
                                                width, height = img.size
                                                min_dim = min(width, height)
                                                if min_dim >= 1024:
                                                    image_quality = 'high'
                                                elif min_dim >= 512:
                                                    image_quality = 'medium'
                                                else:
                                                    image_quality = 'low'
                                        except:
                                            pass
                                        products.append({
                                            'barcode': barcode,
                                            'product_name': 'AI Generated',
                                            'sector': 'ai_generated',
                                            'sector_name': 'AI Uretim',
                                            'product_group': 'AI',
                                            'source': 'customer',
                                            'customer_id': customer_id,
                                            'last_modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                                            'has_image': True,
                                            'image_quality': image_quality
                                        })
        
        # 4. Fetch products from database (customer & admin depots)
        # NOT: Sadece onaylanmış ürünleri getir (pending olanlar ayrı listede)
        try:
            with database.get_db() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                db_rows = cursor.execute("""
                    SELECT p.id, p.barcode, p.name, p.product_group, p.normal_price, p.discount_price,
                           p.image_url, p.image_source, p.market_price, p.market_price_tax,
                           p.created_at, p.user_id, p.approval_status,
                           u.name AS user_name, u.role AS user_role,
                           COALESCE(u.sector, 'supermarket') AS sector
                    FROM products p
                    LEFT JOIN users u ON p.user_id = u.id
                    WHERE p.approval_status IS NULL OR p.approval_status = 'approved'
                """).fetchall()
                
                for row in db_rows:
                    products.append(format_db_product(row))
                
                admin_rows = cursor.execute("""
                    SELECT id, barcode, full_name, product_group, sector, image_path,
                           image_quality, market_price, market_price_tax,
                           created_at, updated_at
                    FROM admin_products
                """).fetchall()
                
                for row in admin_rows:
                    products.append(format_admin_product(row))
        except Exception as db_error:
            logging.error(f"❌ Error loading database products: {db_error}")
        
        # Apply filters
        filtered_products = []
        for p in products:
            if search:
                if search not in p['barcode'].lower() and search not in p['product_name'].lower():
                    continue
            if sector_filter and p['sector'] != sector_filter:
                continue
            if source_filter and p['source'] != source_filter:
                continue
            filtered_products.append(p)
        
        filtered_products.sort(key=lambda x: x['last_modified'], reverse=True)
        
        return jsonify({
            'success': True, 
            'products': filtered_products,
            'total': len(filtered_products)
        })
        
    except Exception as e:
        logging.error(f"All products error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/admin/get-image')
def admin_get_image():
    """Secure image endpoint - serves images without direct folder access"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        sector = request.args.get('sector', '')
        path_type = request.args.get('path', '')
        barcode = request.args.get('barcode', '')
        customer_id = request.args.get('customer_id', '')
        size = request.args.get('size', 'thumb')
        
        safe_pattern = re.compile(r'^[a-zA-Z0-9_\-]+$')
        
        if barcode and not safe_pattern.match(barcode):
            return jsonify({'success': False, 'error': 'Invalid barcode format'}), 400
        
        if customer_id and not safe_pattern.match(customer_id):
            return jsonify({'success': False, 'error': 'Invalid customer_id format'}), 400
        
        if path_type not in ['customer', 'pending', 'admin']:
            return jsonify({'success': False, 'error': 'Invalid path type'}), 400
        
        valid_sectors = list(SECTORS.keys()) + ['ai_generated']
        if sector and sector not in valid_sectors:
            return jsonify({'success': False, 'error': 'Invalid sector'}), 400
        
        base_path = os.path.abspath(os.path.join('static', 'uploads'))
        
        if path_type == 'admin':
            folder_path = safe_join(base_path, 'admin', sector, barcode)
        elif path_type == 'pending':
            folder_path = safe_join(base_path, 'pending', sector, barcode)
        elif path_type == 'customer':
            if sector == 'ai_generated':
                ai_dir = safe_join(base_path, 'customers', customer_id, 'ai_generated')
                if ai_dir is None:
                    return jsonify({'success': False, 'error': 'Invalid path'}), 400
                
                file_path = safe_join(ai_dir, barcode)
                if file_path is None:
                    return jsonify({'success': False, 'error': 'Invalid path'}), 400
                
                for ext in ['', '.jpg', '.png', '.jpeg', '.gif', '.webp']:
                    test_path = file_path + ext if ext else file_path
                    if os.path.exists(test_path) and os.path.isfile(test_path):
                        if not os.path.abspath(test_path).startswith(base_path):
                            return jsonify({'success': False, 'error': 'Invalid path'}), 400
                        return send_file(test_path)
                
                return jsonify({'success': False, 'error': 'Image not found'}), 404
            else:
                folder_path = safe_join(base_path, 'customers', customer_id, sector, barcode)
        else:
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        if folder_path is None:
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        resolved_path = os.path.abspath(folder_path)
        if not resolved_path.startswith(base_path):
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return jsonify({'success': False, 'error': 'Folder not found'}), 404
        
        img_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        if not img_files:
            return jsonify({'success': False, 'error': 'No image found'}), 404
        
        image_path = safe_join(folder_path, img_files[0])
        if image_path is None or not os.path.abspath(image_path).startswith(base_path):
            return jsonify({'success': False, 'error': 'Invalid image path'}), 400
        
        if size == 'thumb':
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
                img_io = BytesIO()
                img.save(img_io, 'JPEG', quality=85)
                img_io.seek(0)
                
                response = make_response(send_file(img_io, mimetype='image/jpeg'))
                response.headers['Cache-Control'] = 'public, max-age=3600'
                return response
            except Exception as e:
                logging.error(f"Thumbnail error: {str(e)}")
                return send_file(image_path)
        
        return send_file(image_path)
        
    except Exception as e:
        logging.error(f"Get image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/approve-product', methods=['POST'])
def admin_approve_product():
    """
    Approve pending product:
    - Update DB status to 'approved'
    - MOVE image from customer depot to admin depot (for all customers to access)
    - Customer copy is DELETED - sistemde tek kopya kalır (admin deposunda)
    """
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        barcode = data.get('barcode', '') if data else ''
        sector = data.get('sector', '') if data else ''
        product_id = data.get('id') if data else None
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Missing barcode'}), 400
        
        # 1. DB'de ürünü bul
        admin_id = user['id']
        
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Ürünü bul
        if product_id:
            c.execute("SELECT * FROM products WHERE id = ? AND approval_status = 'pending'", (product_id,))
        else:
            c.execute("SELECT * FROM products WHERE barcode = ? AND approval_status = 'pending'", (barcode,))
        
        product = c.fetchone()
        
        if not product:
            conn.close()
            return jsonify({'success': False, 'error': 'Pending product not found'}), 404
        
        product = dict(product)
        product_user_id = product.get('user_id')
        product_group = product.get('product_group', 'Genel')
        product_sector = sector or 'supermarket'
        current_image_url = product.get('image_url', '')
        
        # 2. Resmi müşteri deposundan ADMIN DEPOSUNA TAŞI (kopyala değil!)
        # Sistemde tek kopya kalır - admin deposunda
        admin_image_url = None
        try:
            from services.image_bank import move_to_admin_depot
            move_result = move_to_admin_depot(
                user_id=product_user_id,
                sector=product_sector,
                barcode=barcode,
                group=product_group
            )
            if move_result.get('success'):
                admin_image_url = move_result.get('admin_url')
                logging.info(f"Image MOVED to admin depot: {barcode} -> {admin_image_url}")
        except Exception as e:
            logging.warning(f"Image move to admin warning (non-critical): {e}")
        
        # 3. DB'de approval_status ve image_url güncelle
        # image_url artık admin deposunu göstermeli
        from datetime import datetime
        if admin_image_url:
            c.execute("""
                UPDATE products 
                SET approval_status = 'approved', approved_at = ?, approved_by = ?, image_url = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), admin_id, admin_image_url, product['id']))
        else:
            c.execute("""
                UPDATE products 
                SET approval_status = 'approved', approved_at = ?, approved_by = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), admin_id, product['id']))
        conn.commit()
        conn.close()
        
        logging.info(f"Product {barcode} approved by admin {admin_id}")
        return jsonify({
            'success': True, 
            'message': 'Ürün onaylandı ve genel depoya taşındı',
            'admin_depot_url': admin_image_url
        })
        
    except Exception as e:
        logging.error(f"Approve product error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/reject-product', methods=['POST'])
def admin_reject_product():
    """Reject pending product - update DB and remove files"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        barcode = data.get('barcode', '') if data else ''
        sector = data.get('sector', '') if data else ''
        product_id = data.get('id') if data else None
        reason = data.get('reason', '') if data else ''
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Missing barcode'}), 400
        
        admin_id = user['id']
        
        # 1. DB'de ürünü bul ve approval_status güncelle
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if product_id:
            c.execute("SELECT * FROM products WHERE id = ? AND approval_status = 'pending'", (product_id,))
        else:
            c.execute("SELECT * FROM products WHERE barcode = ? AND approval_status = 'pending'", (barcode,))
        
        product = c.fetchone()
        
        if not product:
            conn.close()
            return jsonify({'success': False, 'error': 'Pending product not found'}), 404
        
        product = dict(product)
        product_group = product.get('product_group', 'Genel')
        product_sector = sector or 'supermarket'
        
        # 2. DB'de approval_status güncelle
        from datetime import datetime
        c.execute("""
            UPDATE products 
            SET approval_status = 'rejected', approved_at = ?, approved_by = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), admin_id, product['id']))
        conn.commit()
        conn.close()
        
        # 3. Pending'deki resmi sil
        try:
            from services.image_bank import delete_from_pending
            delete_from_pending(
                sector=product_sector,
                barcode=barcode,
                group=product_group
            )
        except Exception as e:
            logging.warning(f"Pending file delete warning: {e}")
        
        logging.info(f"Product {barcode} rejected by admin {admin_id}")
        return jsonify({'success': True, 'message': 'Ürün reddedildi'})
        
    except Exception as e:
        logging.error(f"Reject product error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/update-product', methods=['POST'])
def admin_update_product():
    """Update product metadata"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        barcode = data.get('barcode', '')
        sector = data.get('sector', '').strip()
        source = data.get('source', 'admin')
        customer_id = data.get('customer_id', '')
        product_name = data.get('product_name', '')
        product_group = data.get('product_group', 'Genel')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        # Sector boşsa varsayılan olarak 'supermarket' kullan
        if not sector:
            sector = 'supermarket'
        
        # Sector'in geçerli olup olmadığını kontrol et
        if sector not in SECTORS:
            sector = 'supermarket'
        
        base_path = os.path.abspath(os.path.join('static', 'uploads'))
        
        if source == 'admin':
            folder_path = safe_join(base_path, 'admin', sector, barcode)
        elif source == 'pending':
            folder_path = safe_join(base_path, 'pending', sector, barcode)
        elif source == 'customer':
            folder_path = safe_join(base_path, 'customers', customer_id, sector, barcode)
        else:
            return jsonify({'success': False, 'error': 'Invalid source'}), 400
        
        if folder_path is None:
            return jsonify({'success': False, 'error': 'Invalid path'}), 400
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        # VALIDATION: Check if product_group is valid (not empty and not 'Genel')
        if not product_group or product_group.strip() == '' or product_group.strip() == 'Genel':
            return jsonify({'success': False, 'error': 'Ürün grubu seçilmelidir. Lütfen sektöre uygun bir ürün grubu seçin.'}), 400
        
        # VALIDATION: Check if image exists in folder
        img_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))] if os.path.exists(folder_path) else []
        
        if not img_files:
            return jsonify({'success': False, 'error': 'Ürün resmi zorunludur. Lütfen önce ürün resmini yükleyin.'}), 400
        
        metadata_path = os.path.join(folder_path, 'metadata.json')
        
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass
        
        metadata['product_name'] = product_name
        metadata['name'] = product_name
        metadata['product_group'] = product_group
        metadata['group'] = product_group
        metadata['updated_at'] = datetime.now().isoformat()
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Product {barcode} updated: {product_name} in sector {sector} at {folder_path}")
        logging.info(f"Metadata file created: {metadata_path}")
        
        # Klasörün ve metadata dosyasının oluşturulduğunu doğrula
        if os.path.exists(metadata_path):
            logging.info(f"✅ Metadata file verified: {metadata_path}")
        else:
            logging.error(f"❌ Metadata file NOT found: {metadata_path}")
        
        return jsonify({'success': True, 'message': 'Product updated', 'sector': sector, 'barcode': barcode})
        
    except Exception as e:
        logging.error(f"Update product error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/delete-product', methods=['POST'])
def admin_delete_product():
    """Delete a product"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        barcode = data.get('barcode')
        sector = data.get('sector', 'supermarket')
        source = data.get('source', 'admin_depot')
        customer_id = data.get('customer_id', '')
        
        logging.info(f"🗑️ Delete request: barcode={barcode}, sector={sector}, source={source}, customer_id={customer_id}")
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        deleted = False
        import shutil
        import glob
        
        # TÜM SEKTÖRLERDE ve TÜM KAYNAKLARDA ara ve sil
        base_path = os.path.abspath(os.path.join('static', 'uploads'))
        data_path = os.path.abspath('data')
        
        # Tüm sektörler listesi
        all_sectors = list(SECTORS.keys()) if 'SECTORS' in globals() else ['supermarket', 'giyim', 'teknoloji', 'kozmetik', 'evyasam', 'elsanatlari', 'restoran', 'diger']
        
        # 1. ADMIN klasörlerinden sil (tüm sektörlerde)
        admin_base = os.path.join(base_path, 'admin')
        if os.path.exists(admin_base):
            for sec in all_sectors:
                product_path = os.path.join(admin_base, sec, barcode)
                if os.path.exists(product_path):
                    try:
                        shutil.rmtree(product_path)
                        deleted = True
                        logging.info(f"🗑️ Deleted from admin/{sec}: {barcode}")
                    except Exception as e:
                        logging.error(f"Error deleting {product_path}: {e}")
        
        # 2. PENDING klasörlerinden sil (tüm sektörlerde)
        pending_base = os.path.join(base_path, 'pending')
        if os.path.exists(pending_base):
            for sec in all_sectors:
                product_path = os.path.join(pending_base, sec, barcode)
                if os.path.exists(product_path):
                    try:
                        shutil.rmtree(product_path)
                        deleted = True
                        logging.info(f"🗑️ Deleted from pending/{sec}: {barcode}")
                    except Exception as e:
                        logging.error(f"Error deleting {product_path}: {e}")
        
        # 3. CUSTOMERS klasörlerinden sil (tüm müşteriler, tüm sektörler)
        customers_base = os.path.join(base_path, 'customers')
        if os.path.exists(customers_base):
            for customer_dir in os.listdir(customers_base):
                customer_path = os.path.join(customers_base, customer_dir)
                if os.path.isdir(customer_path):
                    for sec in all_sectors:
                        product_path = os.path.join(customer_path, sec, barcode)
                        if os.path.exists(product_path):
                            try:
                                shutil.rmtree(product_path)
                                deleted = True
                                logging.info(f"🗑️ Deleted from customers/{customer_dir}/{sec}: {barcode}")
                            except Exception as e:
                                logging.error(f"Error deleting {product_path}: {e}")
        
        # 4. data/ klasöründen sil (eğer varsa)
        if os.path.exists(data_path):
            for root, dirs, files in os.walk(data_path):
                if barcode in dirs:
                    product_path = os.path.join(root, barcode)
                    try:
                        shutil.rmtree(product_path)
                        deleted = True
                        logging.info(f"🗑️ Deleted from data: {product_path}")
                    except Exception as e:
                        logging.error(f"Error deleting {product_path}: {e}")
        
        # 5. Cache dosyalarını sil
        cache_dir = os.path.join(base_path, 'cache')
        if os.path.exists(cache_dir):
            cache_patterns = [
                os.path.join(cache_dir, f'{barcode}*.json'),
                os.path.join(cache_dir, f'{barcode}*.png'),
                os.path.join(cache_dir, f'{barcode}*.jpg'),
                os.path.join(cache_dir, f'{barcode}*.jpeg'),
            ]
            for pattern in cache_patterns:
                for cache_file in glob.glob(pattern):
                    try:
                        os.remove(cache_file)
                        deleted = True
                        logging.info(f"🗑️ Deleted cache: {cache_file}")
                    except Exception as ce:
                        logging.warning(f"Cache delete warning: {ce}")
        
        # 6. VERİTABANINDAN TAMAMEN SİL (tüm tablolardan)
        try:
            conn = sqlite3.connect('brosur.db')
            c = conn.cursor()
            
            # Tüm tablolardan sil
            tables_to_clean = [
                'products',
                'customer_images',
                'admin_images',
                'admin_products',
                'barcode_verifications'
            ]
            
            for table in tables_to_clean:
                try:
                    c.execute(f"DELETE FROM {table} WHERE barcode = ?", (barcode,))
                    if c.rowcount > 0:
                        deleted = True
                        logging.info(f"🗑️ Deleted from database table {table}: {barcode} ({c.rowcount} rows)")
                except Exception as table_e:
                    logging.warning(f"Could not delete from {table}: {table_e}")
            
            conn.commit()
            conn.close()
            logging.info(f"✅ Database cleanup completed for barcode: {barcode}")
        except Exception as db_e:
            logging.error(f"Database delete error: {db_e}")
        
        if deleted:
            return jsonify({'success': True, 'message': 'Ürün silindi'})
        else:
            # Log what paths were checked
            logging.warning(f"❌ Product not found in any path: {possible_paths}")
            return jsonify({'success': False, 'error': 'Ürün bulunamadı'}), 404
        
    except Exception as e:
        logging.error(f"Delete product error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= IMAGE APPROVAL =============

@admin_bp.route('/api/admin/pending-images')
def api_admin_pending_images():
    """Get pending images for approval (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        conn = sqlite3.connect('brosur.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        images = c.execute("""
            SELECT ci.*, u.name as user_name, u.email as user_email 
            FROM customer_images ci 
            LEFT JOIN users u ON ci.user_id = u.id 
            WHERE ci.approved = 0 
            ORDER BY ci.created_at DESC
        """).fetchall()
        conn.close()
        
        return jsonify({'success': True, 'images': [dict(img) for img in images]})
        
    except Exception as e:
        logging.error(f"Get pending images error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/approve-image', methods=['POST'])
def api_admin_approve_image():
    """Approve customer image (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        image_id = data.get('image_id')
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("UPDATE customer_images SET approved=1 WHERE id=?", (image_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Approve image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/reject-image', methods=['POST'])
def api_admin_reject_image():
    """Reject customer image (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        image_id = data.get('image_id')
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("DELETE FROM customer_images WHERE id=?", (image_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Reject image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= ADMIN SETTINGS API =============

@admin_bp.route('/api/admin/ai-pricing', methods=['GET', 'POST'])
def api_admin_ai_pricing():
    """Get or set AI pricing (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ai_pricing 
                     (id INTEGER PRIMARY KEY, pricing TEXT)''')
        
        if request.method == 'POST':
            data = request.json
            pricing = json.dumps(data.get('pricing', {}))
            c.execute("INSERT OR REPLACE INTO ai_pricing (id, pricing) VALUES (1, ?)", (pricing,))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        else:
            c.execute("SELECT pricing FROM ai_pricing WHERE id=1")
            row = c.fetchone()
            conn.close()
            
            default_pricing = {
                'slogan': 5.0,
                'image': 10.0,
                'template': 15.0,
                'background': 8.0
            }
            
            if row and row[0]:
                return jsonify({'success': True, 'pricing': json.loads(row[0])})
            return jsonify({'success': True, 'pricing': default_pricing})
            
    except Exception as e:
        logging.error(f"AI pricing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/admin/site-settings', methods=['GET', 'POST'])
def api_admin_site_settings():
    """Get or set site settings (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS site_settings 
                     (id INTEGER PRIMARY KEY, settings TEXT)''')
        
        if request.method == 'POST':
            data = request.json
            settings = json.dumps(data.get('settings', {}))
            c.execute("INSERT OR REPLACE INTO site_settings (id, settings) VALUES (1, ?)", (settings,))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        else:
            c.execute("SELECT settings FROM site_settings WHERE id=1")
            row = c.fetchone()
            conn.close()
            
            if row and row[0]:
                return jsonify({'success': True, 'settings': json.loads(row[0])})
            return jsonify({'success': True, 'settings': {}})
            
    except Exception as e:
        logging.error(f"Site settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= CUSTOMER FORM LINKS =============

@admin_bp.route('/api/admin/generate-customer-link', methods=['POST'])
def api_generate_customer_link():
    """Generate unique link for customer to submit products"""
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app
    
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        customer_id = data.get('customer_id')
        expires_hours = data.get('expires_hours', 24)
        
        if not customer_id:
            return jsonify({'success': False, 'error': 'Customer ID required'}), 400
        
        serializer = URLSafeTimedSerializer(current_app.secret_key)
        token = serializer.dumps({'customer_id': customer_id}, salt='customer-form')
        
        domain = os.environ.get('REPL_SLUG', 'localhost:5000')
        if 'REPL_OWNER' in os.environ:
            link = f"https://{domain}.{os.environ['REPL_OWNER']}.repl.co/musteri-form/{token}"
        else:
            link = f"http://localhost:5000/musteri-form/{token}"
        
        return jsonify({
            'success': True,
            'token': token,
            'link': link,
            'expires_hours': expires_hours
        })
        
    except Exception as e:
        logging.error(f"Generate customer link error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

