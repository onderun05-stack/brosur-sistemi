# -*- coding: utf-8 -*-
"""
Product routes - Product CRUD, upload, image management
"""

from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import sqlite3
import logging
import json
import csv
import os
import shutil
from io import StringIO
from pathlib import Path
from collections import defaultdict

import database
from utils.helpers import get_current_user, parse_turkish_float
from utils.constants import SECTORS, validate_and_fix_product_group
from services.excel_io import parse_excel_file
from services.external_api import (
    full_barcode_lookup,
    batch_barcode_lookup,
    get_market_price_comparison
)
from services.image_bank import search_image_hierarchy
from services.ai_categorizer import AIProductCategorizer

products_bp = Blueprint('products', __name__)

STAGE_ONE_MAX_PRODUCTS = 500
STAGE_ONE_PAGE_CAPACITY = 12
PENDING_ROOT = Path('static') / 'uploads' / 'pending'
_stage_one_categorizer = AIProductCategorizer()
DEPOT_SOURCES = {'customer_depot', 'admin_depot'}


def _parse_price(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _normalize_stage_one_product(raw_product, index):
    client_id = raw_product.get('id') or raw_product.get('client_id') or f'row_{index}'
    barcode = str(raw_product.get('barcode', '') or '').strip()
    name = (raw_product.get('name') or '').strip()
    image_url = (raw_product.get('image_url') or '').strip()
    product_group = (raw_product.get('product_group') or '').strip()
    source_type = str(raw_product.get('source_type') or '').lower()
    source_type = 'depo' if source_type == 'depo' else 'external'

    return {
        'client_id': str(client_id),
        'barcode': barcode,
        'name': name,
        'normal_price': _parse_price(raw_product.get('normal_price')),
        'discount_price': _parse_price(raw_product.get('discount_price')),
        'image_url': image_url,
        'product_group': product_group,
        'market_price': _parse_price(raw_product.get('market_price')),
        'market_price_tax': _parse_price(raw_product.get('market_price_tax')),
        'source_type': source_type,
        'image_source': (raw_product.get('image_source') or '').strip(),
        'order': index,
        'page_no': None
    }


def _auto_assign_pages(products, selected_ids):
    plan = {}
    selected_ids = {str(pid) for pid in selected_ids}
    selected_products = [
        product for product in products
        if product['client_id'] in selected_ids or (product['barcode'] and product['barcode'] in selected_ids)
    ]
    remaining_products = [product for product in products if product not in selected_products]

    current_page = 1
    slots_used = 0
    for product in selected_products:
        if slots_used >= STAGE_ONE_PAGE_CAPACITY:
            current_page += 1
            slots_used = 0
        plan[str(product['client_id'])] = current_page
        slots_used += 1

    current_page = 2 if selected_products else 1
    slots_used = 0
    for product in remaining_products:
        if slots_used >= STAGE_ONE_PAGE_CAPACITY:
            current_page += 1
            slots_used = 0
        plan[str(product['client_id'])] = current_page
        slots_used += 1

    return plan


def _fill_remaining_pages(products, existing_plan):
    plan = dict(existing_plan)
    counts = defaultdict(int)
    for page in plan.values():
        counts[page] += 1

    current_page = max(counts.keys()) if counts else 1

    for product in products:
        pid = str(product['client_id'])
        if pid in plan:
            continue

        target_page = None
        for page in sorted(counts.keys()):
            if counts[page] < STAGE_ONE_PAGE_CAPACITY:
                target_page = page
                break

        if target_page is None:
            target_page = current_page + 1 if counts else 1
            if target_page not in counts:
                counts[target_page] = 0
            current_page = target_page

        plan[pid] = target_page
        counts[target_page] += 1

    return plan


def _assign_pages(products, explicit_assignments, selected_ids, auto_fill_ok):
    normalized_assignments = {}
    for key, value in (explicit_assignments or {}).items():
        try:
            normalized_assignments[str(key)] = max(1, int(value))
        except (TypeError, ValueError):
            continue

    manual_count = len(normalized_assignments)
    total = len(products)

    if manual_count and manual_count < total and not auto_fill_ok:
        raise ValueError('partial_assignment_requires_confirmation')

    if manual_count == 0:
        return _auto_assign_pages(products, selected_ids)

    return _fill_remaining_pages(products, normalized_assignments)


def _categorize_external_product(product, sector):
    current_group = product.get('product_group') or ''
    validated = validate_and_fix_product_group(current_group, sector)
    if validated and validated != 'Genel':
        return validated

    ai_result = _stage_one_categorizer.categorize(product.get('name', ''))
    if ai_result:
        validated = validate_and_fix_product_group(ai_result.get('category_name'), sector)
        if validated:
            return validated
    return 'Genel'


def _build_update_diff(existing, new_payload):
    tracked_fields = ['name', 'discount_price', 'product_group', 'image_url']
    changes = {}
    for field in tracked_fields:
        old_value = existing.get(field)
        new_value = new_payload.get(field)
        if isinstance(old_value, float):
            old_value = round(old_value, 2)
        if isinstance(new_value, float):
            new_value = round(new_value, 2)
        if (old_value or '') != (new_value or ''):
            changes[field] = {'old': old_value, 'new': new_value}
    return changes


def _clear_pending_storage(user_id):
    pending_dir = PENDING_ROOT / str(user_id)
    if pending_dir.exists():
        shutil.rmtree(pending_dir, ignore_errors=True)


def _prepare_canvas_payload(products):
    summary_map = defaultdict(int)
    sorted_products = sorted(
        products,
        key=lambda item: ((item.get('page_no') or 0), item.get('order', 0))
    )
    payload = []
    for product in sorted_products:
        page_no = product.get('page_no')
        if page_no:
            summary_map[page_no] += 1
        payload.append({
            'barcode': product['barcode'],
            'name': product['name'],
            'normal_price': product['normal_price'],
            'discount_price': product['discount_price'],
            'image_url': product['image_url'],
            'product_group': product['product_group'],
            'page_no': page_no,
            'source_type': product['source_type']
        })

    summary = [
        {'page': page, 'count': summary_map[page]}
        for page in sorted(summary_map.keys())
    ]
    return payload, summary


@products_bp.route('/api/products')
def api_get_products():
    """Get user's products"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    products = database.get_products(user['id'])
    return jsonify({'success': True, 'products': products})


@products_bp.route('/api/upload-products', methods=['POST'])
def api_upload_products():
    """Upload products from Excel file"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Read Excel file
        df = pd.read_excel(file)
        products = []
        
        for idx, row in df.iterrows():
            barcode = str(row.get('Barkod', row.get('barcode', ''))).strip()
            name = str(row.get('Ürün Adı', row.get('name', row.get('Ürün', '')))).strip()
            normal_price = float(row.get('Normal Fiyat', row.get('normal_price', 0)) or 0)
            discount_price = float(row.get('İndirimli Fiyat', row.get('discount_price', 0)) or 0)
            product_group = str(row.get('Grup', row.get('group', ''))).strip()
            
            if barcode and name:
                # Find image for product
                image_info = database.find_image(barcode, user['id'])
                image_url = image_info['url'] if image_info else ''
                image_source = image_info['source'] if image_info else 'none'
                
                product_id = database.add_product(
                    user['id'], barcode, name, normal_price, discount_price,
                    image_url, image_source, product_group, idx
                )
                products.append({
                    'id': product_id,
                    'barcode': barcode,
                    'name': name,
                    'normal_price': normal_price,
                    'discount_price': discount_price,
                    'image_url': image_url,
                    'product_group': product_group
                })
        
        return jsonify({'success': True, 'products': products, 'count': len(products)})
        
    except Exception as e:
        logging.error(f"Upload products error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/find-product-image', methods=['POST'])
def api_find_product_image():
    """Find image for product by barcode"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        barcode = data.get('barcode', '')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        image_info = database.find_image(barcode, user['id'])
        
        if image_info:
            return jsonify({'success': True, 'found': True, 'image': image_info})
        return jsonify({'success': True, 'found': False})
        
    except Exception as e:
        logging.error(f"Find image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/update-product-image', methods=['POST'])
def api_update_product_image():
    """Update product image"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        product_id = data.get('product_id')
        image_url = data.get('image_url', '')
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("UPDATE products SET image_url=? WHERE id=? AND user_id=?",
                  (image_url, product_id, user['id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Update image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/upload-product-image', methods=['POST'])
def api_upload_product_image():
    """Upload a product image"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        barcode = request.form.get('barcode', '')
        sector = request.form.get('sector', 'supermarket')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        # Validate sector
        if sector not in SECTORS:
            sector = 'supermarket'
        
        # Save to pending folder
        folder_path = os.path.join('static', 'uploads', 'pending', sector, barcode)
        os.makedirs(folder_path, exist_ok=True)
        
        filename = 'product.jpg'
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)
        
        image_url = f'/static/uploads/pending/{sector}/{barcode}/{filename}'
        
        return jsonify({'success': True, 'image_url': image_url})
        
    except Exception as e:
        logging.error(f"Upload product image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= PRE-APPROVAL API =============

@products_bp.route('/api/pre-approval/approve', methods=['POST'])
def api_pre_approval_approve():
    """Approve products from pre-approval"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        products = data.get('products', [])
        
        if not isinstance(products, list) or not products:
            return jsonify({'success': False, 'error': 'Ürün listesi boş olamaz'}), 400
        
        if len(products) > STAGE_ONE_MAX_PRODUCTS:
            return jsonify({
                'success': False,
                'error': f'Maksimum {STAGE_ONE_MAX_PRODUCTS} ürün onaylanabilir'
            }), 400
        
        sanitized_products = [
            _normalize_stage_one_product(product, idx)
            for idx, product in enumerate(products)
        ]
        
        selected_ids = {str(pid) for pid in data.get('selectedProductIds', []) if pid is not None}
        page_assignments = data.get('pageAssignments', {}) or {}
        auto_fill_ok = bool(data.get('autoFillAccepted'))
        
        try:
            page_plan = _assign_pages(sanitized_products, page_assignments, selected_ids, auto_fill_ok)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'PAGE_CONFIRMATION_REQUIRED',
                'message': 'Sayfa seçimi kısmen yapılmış. Otomatik doldurma izni vermeden devam edemezsiniz.'
            }), 400
        
        validation_errors = []
        for product in sanitized_products:
            product_id = product['client_id']
            product['page_no'] = page_plan.get(product_id, 1)
            missing = []
            if not product['barcode']:
                missing.append('barcode')
            if product['discount_price'] <= 0:
                missing.append('discount_price')
            if product['source_type'] == 'external':
                if not product['name']:
                    missing.append('name')
                if not product['image_url']:
                    missing.append('image_url')
            if missing:
                validation_errors.append({
                    'id': product_id,
                    'barcode': product['barcode'],
                    'missing': missing
                })
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_FAILED',
                'invalid_products': validation_errors
            }), 400
        
        sector = user.get('sector', 'supermarket') or 'supermarket'
        
        for product in sanitized_products:
            if product['source_type'] == 'external':
                product['product_group'] = _categorize_external_product(product, sector)
            else:
                product['product_group'] = validate_and_fix_product_group(product.get('product_group'), sector) or 'Genel'
            
            if not product['normal_price']:
                product['normal_price'] = product['discount_price']
            
            if not product['image_source']:
                product['image_source'] = 'depo' if product['source_type'] == 'depo' else 'customer'
        
        inserted = 0
        updated = 0
        update_requests = 0
        
        for product in sanitized_products:
            barcode = product['barcode']
            existing = database.get_product_by_barcode(user['id'], barcode)
            
            payload = {
                'name': product['name'],
                'product_group': product['product_group'],
                'normal_price': product['normal_price'],
                'discount_price': product['discount_price'],
                'image_url': product['image_url'],
                'image_source': product['image_source'],
                'market_price': product['market_price'],
                'market_price_tax': product['market_price_tax'],
                'source_type': product['source_type'],
                'page_no': product['page_no'],
                'upload_order': product['order']
            }
            
            if existing:
                database.update_product_fields(user['id'], barcode, payload)
                updated += 1
                
                if product['source_type'] == 'depo':
                    diff = _build_update_diff(existing, payload)
                    if diff:
                        database.log_product_update_request(user['id'], barcode, diff)
                        update_requests += 1
            else:
                # "Onayla ve Aktar" direkt approved olarak kaydeder (Canvas'a gidiyor)
                database.add_product(
                    user['id'], barcode, product['name'],
                    product['normal_price'], product['discount_price'],
                    product['image_url'], product['image_source'],
                    product_group=product['product_group'],
                    upload_order=product['order'],
                    market_price=product['market_price'],
                    market_price_tax=product['market_price_tax'],
                    source_type=product['source_type'],
                    page_no=product['page_no'],
                    approval_status='approved'  # Direkt onaylı
                )
                inserted += 1
        
        _clear_pending_storage(user['id'])
        canvas_payload, page_summary = _prepare_canvas_payload(sanitized_products)
        
        return jsonify({
            'success': True,
            'count': len(sanitized_products),
            'inserted': inserted,
            'updated': updated,
            'update_requests': update_requests,
            'canvas_payload': canvas_payload,
            'page_summary': page_summary
        })
        
    except Exception as e:
        logging.error(f"Pre-approval approve error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= BROŞÜRE AKTAR (YENİ) =============

@products_bp.route('/api/products/transfer-to-canvas', methods=['POST'])
def api_transfer_to_canvas():
    """
    Broşüre Aktar - Kayıtlı ürünleri Canvas'a gönder
    
    Veri Kaynakları:
    - Resim, İsim, Grup → DB'den (depot)
    - Eski Fiyat, İndirimli Fiyat → Listeden
    
    Akış:
    1. Listedeki her barkodu DB'de ara
    2. Kayıtlı değilse → Hata: "Önce kaydet"
    3. Kayıtlıysa → Canvas payload oluştur
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Oturum açmanız gerekiyor'}), 401
    
    try:
        data = request.json or {}
        list_products = data.get('products', [])
        
        if not list_products:
            return jsonify({'success': False, 'error': 'Ürün listesi boş'}), 400
        
        user_id = user['id']
        
        # ============= FİYAT VALİDASYONU =============
        # Kural 1: İndirim fiyatı 0/boş olamaz
        # Kural 2: İndirim fiyatı > Normal fiyat olamaz (fiyat yükseltme yasak)
        price_errors = []
        for item in list_products:
            barcode = str(item.get('barcode', '')).strip()
            if not barcode:
                continue
            
            discount_price = float(item.get('discount_price', 0) or 0)
            normal_price = float(item.get('normal_price', 0) or 0)
            product_name = item.get('name', '')
            
            # Kural 1: İndirim fiyatı 0 veya boş
            if discount_price <= 0:
                price_errors.append({
                    'barcode': barcode,
                    'name': product_name,
                    'reason': 'İndirim fiyatı 0 veya boş'
                })
                continue
            
            # Kural 2: İndirim fiyatı > Normal fiyat (normal fiyat girilmişse)
            if normal_price > 0 and discount_price > normal_price:
                price_errors.append({
                    'barcode': barcode,
                    'name': product_name,
                    'reason': f'İndirim fiyatı ({discount_price:.2f}₺) normal fiyattan ({normal_price:.2f}₺) yüksek'
                })
        
        # Fiyat hatası varsa hemen döndür
        if price_errors:
            return jsonify({
                'success': False,
                'error': 'PRICE_VALIDATION_FAILED',
                'message': f'{len(price_errors)} üründe fiyat hatası var. Lütfen düzeltin.',
                'price_errors': price_errors
            }), 400
        
        # ============= DB KONTROLÜ =============
        # Her ürün için DB kontrolü yap
        missing_products = []
        canvas_products = []
        
        for item in list_products:
            barcode = str(item.get('barcode', '')).strip()
            if not barcode:
                continue
            
            # Listeden gelen fiyatlar
            list_normal_price = float(item.get('normal_price', 0) or 0)
            list_discount_price = float(item.get('discount_price', 0) or 0)
            list_page_no = item.get('page_no', 1)
            
            # DB'de ara (approved veya eski kayıtlar - approval_status NULL olanlar da dahil)
            db_product = database.get_product_by_barcode(user_id, barcode)
            
            if not db_product:
                missing_products.append({
                    'barcode': barcode,
                    'name': item.get('name', ''),
                    'reason': 'DB\'de kayıt yok'
                })
                continue
            
            # Approval status kontrolü
            # YENİ KURAL: Müşteri kendi yüklediği ürünü hemen kullanabilir (pending dahil)
            # pending = Admin onayı bekliyor (admin deposuna kopyalama için)
            # rejected = Admin tarafından reddedildi - kullanılamaz
            approval_status = db_product.get('approval_status')
            product_user_id = db_product.get('user_id')
            
            # Sadece reddedilen ürünler engellensin
            if approval_status == 'rejected':
                missing_products.append({
                    'barcode': barcode,
                    'name': db_product.get('name', ''),
                    'reason': 'Admin tarafından reddedildi'
                })
                continue
            
            # Müşteri kendi ürününü (pending dahil) veya onaylı ürünleri kullanabilir
            # Başka müşterinin pending ürünü kullanılamaz
            if approval_status == 'pending' and product_user_id != user_id:
                missing_products.append({
                    'barcode': barcode,
                    'name': db_product.get('name', ''),
                    'reason': 'Bu ürün henüz genel depoya eklenmedi'
                })
                continue
            
            # Canvas payload oluştur
            # Resim, İsim, Grup → DB'den
            # Fiyatlar → Listeden
            canvas_products.append({
                'barcode': barcode,
                'name': db_product.get('name', ''),
                'image_url': db_product.get('image_url', ''),
                'product_group': db_product.get('product_group', 'Genel'),
                'normal_price': list_normal_price if list_normal_price > 0 else db_product.get('normal_price', 0),
                'discount_price': list_discount_price if list_discount_price > 0 else db_product.get('discount_price', 0),
                'page_no': list_page_no,
                'source_type': db_product.get('source_type', 'external')
            })
        
        # Eksik ürün varsa hata döndür
        if missing_products:
            return jsonify({
                'success': False,
                'error': 'MISSING_PRODUCTS',
                'message': f'{len(missing_products)} ürün kayıtlı değil veya onay bekliyor. Önce "Kaydet" butonuna basın.',
                'missing_products': missing_products,
                'valid_count': len(canvas_products)
            }), 400
        
        if not canvas_products:
            return jsonify({'success': False, 'error': 'Canvas\'a gönderilecek ürün yok'}), 400
        
        # Sayfa özeti oluştur
        page_summary = {}
        for p in canvas_products:
            page = p.get('page_no', 1)
            page_summary[page] = page_summary.get(page, 0) + 1
        
        summary_list = [{'page': k, 'count': v} for k, v in sorted(page_summary.items())]
        
        logging.info(f"Transfer to canvas: {len(canvas_products)} products for user {user_id}")
        
        return jsonify({
            'success': True,
            'canvas_payload': canvas_products,
            'page_summary': summary_list,
            'count': len(canvas_products),
            'message': f'{len(canvas_products)} ürün Canvas\'a aktarılıyor'
        })
        
    except Exception as e:
        logging.error(f"Transfer to canvas error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/pre-approval/upload-csv', methods=['POST'])
def api_pre_approval_upload_csv():
    """Upload CSV file for pre-approval"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files are allowed'}), 400
        
        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        MAX_FILE_SIZE = 5 * 1024 * 1024
        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File size cannot exceed 5MB'}), 400
        
        # Parse CSV
        csv_content = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        fieldnames = csv_reader.fieldnames or []
        fieldnames_set = set(fieldnames)
        
        has_barcode = 'Barkod' in fieldnames_set
        has_name = ('Ürün Adı' in fieldnames_set or 'Urun Adi' in fieldnames_set)
        has_discount_price = ('İndirim Fiyatı' in fieldnames_set or 'Indirim Fiyati' in fieldnames_set)
        
        missing = []
        if not has_barcode:
            missing.append('Barkod')
        if not has_name:
            missing.append('Ürün Adı / Urun Adi')
        if not has_discount_price:
            missing.append('İndirim Fiyatı / Indirim Fiyati')
        
        if missing:
            return jsonify({
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing)}'
            }), 400
        
        # Store products in pending storage
        user_id = user['id']
        pending_dir = f'static/uploads/pending/{user_id}/'
        os.makedirs(pending_dir, exist_ok=True)
        
        metadata_file = os.path.join(pending_dir, 'pending_products.json')
        existing_products = []
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_products = json.load(f)
        
        existing_barcodes = {p.get('barcode') for p in existing_products if p.get('barcode')}
        
        products = []
        duplicates_skipped = 0
        validation_errors = []
        
        for idx, row in enumerate(csv_reader, start=2):
            try:
                barcode = row.get('Barkod', '').strip()
                
                if not barcode:
                    validation_errors.append(f"Row {idx}: Barcode cannot be empty")
                    continue
                
                if barcode in existing_barcodes:
                    duplicates_skipped += 1
                    continue
                
                name = row.get('Ürün Adı', row.get('Urun Adi', '')).strip()
                
                try:
                    discount_price = parse_turkish_float(row.get('İndirim Fiyatı', row.get('Indirim Fiyati', '0')))
                    if discount_price <= 0:
                        validation_errors.append(f"Row {idx}: İndirim Fiyatı must be greater than 0")
                        continue
                    
                    normal_price = parse_turkish_float(row.get('Normal Fiyat', '0'))
                except ValueError as e:
                    validation_errors.append(f"Row {idx}: {str(e)}")
                    continue
                
                products.append({
                    'barcode': barcode,
                    'name': name,
                    'normal_price': normal_price,
                    'discount_price': discount_price,
                    'product_group': '',
                    'image_url': '',
                    'status': 'pending'
                })
                
                existing_barcodes.add(barcode)
                
            except Exception as e:
                validation_errors.append(f"Row {idx}: {str(e)}")
        
        if not products and not duplicates_skipped:
            return jsonify({
                'success': False, 
                'error': 'No valid products found in CSV',
                'validation_errors': validation_errors[:10]
            }), 400
        
        if products:
            existing_products.extend(products)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_products, f, ensure_ascii=False, indent=2)
        
        message_parts = []
        if products:
            message_parts.append(f'{len(products)} products added')
        if duplicates_skipped > 0:
            message_parts.append(f'{duplicates_skipped} duplicates skipped')
        if validation_errors:
            message_parts.append(f'{len(validation_errors)} errors')
        
        return jsonify({
            'success': len(products) > 0,
            'count': len(products),
            'duplicates': duplicates_skipped,
            'errors': validation_errors[:10],
            'message': ', '.join(message_parts) if message_parts else 'No products added'
        })
        
    except Exception as e:
        logging.error(f"CSV upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/pre-approval/upload-excel', methods=['POST'])
def api_pre_approval_upload_excel():
    """Upload Excel file with product data to pre-approval storage"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Only Excel files (.xlsx, .xls) are allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = 2 * 1024 * 1024
        if file_size > max_size:
            return jsonify({'success': False, 'error': f'File too large. Maximum size is {max_size / (1024*1024)}MB'}), 400
        
        # Save file temporarily
        temp_dir = 'static/temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, f'{user["id"]}_{temp_filename}')
        
        file.save(temp_path)
        
        logging.info(f"Excel upload: User {user['id']} uploaded {file.filename} ({file_size} bytes)")
        
        try:
            products, validation_errors, stats = parse_excel_file(temp_path, max_rows=5000)
            
            if not products and not stats['duplicates_skipped']:
                return jsonify({
                    'success': False,
                    'error': 'No valid products found in Excel file',
                    'validation_errors': validation_errors[:10],
                    'stats': stats
                }), 400
            
            # Store products in pending storage
            user_id = user['id']
            pending_dir = f'static/uploads/pending/{user_id}/'
            os.makedirs(pending_dir, exist_ok=True)
            
            metadata_file = os.path.join(pending_dir, 'pending_products.json')
            existing_products = []
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_products = json.load(f)
            
            existing_barcodes = {p.get('barcode') for p in existing_products if p.get('barcode')}
            new_products = []
            existing_in_list = []  # Listede zaten var olanlar (güncelleme için)
            
            for product in products:
                product['status'] = 'pending'
                product['image_url'] = ''
                
                if product['barcode'] in existing_barcodes:
                    # Duplicate - ama yine de ekle (güncelleme için kullanılabilir)
                    existing_in_list.append(product)
                else:
                    new_products.append(product)
                    existing_barcodes.add(product['barcode'])
            
            # Hem yeni hem mevcut ürünleri listeye ekle
            all_products_to_add = new_products + existing_in_list
            
            if all_products_to_add:
                existing_products.extend(all_products_to_add)
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_products, f, ensure_ascii=False, indent=2)
            
            message_parts = []
            if new_products:
                message_parts.append(f'{len(new_products)} yeni ürün')
            if existing_in_list:
                message_parts.append(f'{len(existing_in_list)} mevcut (güncelleme için)')
            if stats['errors'] > 0:
                message_parts.append(f'{stats["errors"]} hata')
            
            total_added = len(all_products_to_add)
            
            return jsonify({
                'success': total_added > 0,
                'count': total_added,
                'new_count': len(new_products),
                'existing_count': len(existing_in_list),
                'products': all_products_to_add,  # Ürün listesi döndür
                'errors': validation_errors[:10],
                'stats': stats,
                'message': ', '.join(message_parts) if message_parts else 'İşlem tamamlandı'
            })
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logging.error(f"Excel upload error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/pre-approval/import', methods=['POST'])
def api_pre_approval_import():
    """Import products from standalone form (JSON) to pre-approval storage"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'success': False, 'error': 'No products data provided'}), 400
        
        products_data = data['products']
        if not isinstance(products_data, list):
            return jsonify({'success': False, 'error': 'Products must be an array'}), 400
        
        products = []
        validation_errors = []
        
        for idx, item in enumerate(products_data, start=1):
            try:
                barcode = str(item.get('barcode', '')).strip()
                if not barcode:
                    validation_errors.append(f"Row {idx}: Barcode cannot be empty")
                    continue
                
                name = str(item.get('name', '')).strip()
                
                discount_price = float(item.get('discount_price', 0))
                if discount_price <= 0:
                    validation_errors.append(f"Row {idx}: Discount price must be greater than 0")
                    continue
                
                normal_price = float(item.get('normal_price', 0))
                
                products.append({
                    'barcode': barcode,
                    'name': name,
                    'discount_price': discount_price,
                    'normal_price': normal_price,
                    'product_group': '',
                    'image_url': '',
                    'status': 'pending'
                })
                
            except (ValueError, TypeError) as e:
                validation_errors.append(f"Row {idx}: Invalid data format - {str(e)}")
                continue
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'No valid products to import',
                'validation_errors': validation_errors[:10]
            }), 400
        
        # Store products in pending storage
        user_id = user['id']
        pending_dir = f'static/uploads/pending/{user_id}/'
        os.makedirs(pending_dir, exist_ok=True)
        
        metadata_file = os.path.join(pending_dir, 'pending_products.json')
        existing_products = []
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_products = json.load(f)
        
        existing_barcodes = {p.get('barcode') for p in existing_products if p.get('barcode')}
        new_products = []
        duplicates_skipped = 0
        
        for product in products:
            if product['barcode'] in existing_barcodes:
                duplicates_skipped += 1
            else:
                new_products.append(product)
                existing_barcodes.add(product['barcode'])
        
        if new_products:
            existing_products.extend(new_products)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_products, f, ensure_ascii=False, indent=2)
        
        message_parts = []
        if new_products:
            message_parts.append(f'{len(new_products)} products imported')
        if duplicates_skipped > 0:
            message_parts.append(f'{duplicates_skipped} duplicates skipped')
        if validation_errors:
            message_parts.append(f'{len(validation_errors)} errors')
        
        success = len(new_products) > 0
        
        if not success:
            error_msg = 'No products imported'
            if duplicates_skipped > 0:
                error_msg = f'All products are duplicates ({duplicates_skipped} barcodes already exist)'
            elif validation_errors:
                error_msg = f'All products have validation errors ({len(validation_errors)} errors)'
            
            return jsonify({
                'success': False,
                'error': error_msg,
                'count': 0,
                'duplicates': duplicates_skipped,
                'errors': validation_errors[:10]
            }), 400
        
        return jsonify({
            'success': True,
            'count': len(new_products),
            'duplicates': duplicates_skipped,
            'errors': validation_errors[:10],
            'message': ', '.join(message_parts)
        })
        
    except Exception as e:
        logging.error(f"Import error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= BARCODE LOOKUP (CAMGOZ API) =============

@products_bp.route('/api/barkod-sorgula', methods=['POST'])
def api_barkod_sorgula():
    """
    Full barcode lookup using external_api service.
    Searches: Customer depot → Admin depot → CAMGOZ API
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        barcode = data.get('barcode', '').strip()
        sector = data.get('sector', user.get('sector', 'supermarket'))
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        # Use external_api service for full lookup
        result = full_barcode_lookup(
            barcode=barcode,
            user_id=user['id'],
            sector=sector,
            auto_download=True
        )
        
        # Format response
        response = {
            'success': True,
            'found': result['found'],
            'source': result['source']
        }
        
        if result['found']:
            product_info = {
                'barcode': barcode,
                'name': result['product']['name'] if result.get('product') else '',
                'product_group': result['product']['category'] if result.get('product') else '',
                'brand': result['product'].get('brand', '') if result.get('product') else '',
                'image_url': result['image']['url'] if result.get('image') else '',
                'quality_indicator': result['image']['quality_indicator'] if result.get('image') else '⚪',
                'market_price': result.get('market_price', 0),
                'market_price_tax': result.get('market_price_tax', 0)
            }
            response['product'] = product_info
        else:
            response['message'] = 'Ürün bulunamadı, manuel yükleyiniz'
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Barcode lookup error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/barkod-sorgula/batch', methods=['POST'])
def api_barkod_sorgula_batch():
    """
    Batch barcode lookup for multiple products.
    Used when uploading Excel with multiple barcodes.
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        barcodes = data.get('barcodes', [])
        sector = data.get('sector', user.get('sector', 'supermarket'))
        auto_download = data.get('auto_download', True)
        
        if not barcodes:
            return jsonify({'success': False, 'error': 'Barcodes required'}), 400
        
        # Limit batch size
        if len(barcodes) > 100:
            barcodes = barcodes[:100]
        
        result = batch_barcode_lookup(
            barcodes=barcodes,
            user_id=user['id'],
            sector=sector,
            auto_download=auto_download
        )
        
        return jsonify({
            'success': True,
            'results': result['results'],
            'total': result['total'],
            'found': result['found'],
            'with_images': result['with_images'],
            'not_found': result['not_found']
        })
        
    except Exception as e:
        logging.error(f"Batch barcode lookup error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def verify_images_with_openai(images, barcode, product_name):
    """
    OpenAI Vision ile resimleri doğrula.
    Hangisi gerçek ürün resmi?
    """
    import openai
    import os
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logging.warning("OpenAI API key not set, skipping verification")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Resimleri mesaja ekle
        content = [
            {
                "type": "text",
                "text": f"""Bu resimlere bak. Hangisi "{product_name}" (barkod: {barcode}) ürününün GERÇEK ambalaj/ürün fotoğrafı?

Sadece numara döndür (1, 2 veya 3). Hiçbiri uygun değilse "0" döndür.
Açıklama yazma, sadece numara."""
            }
        ]
        
        for i, img in enumerate(images[:3]):
            content.append({
                "type": "image_url",
                "image_url": {"url": img['url'], "detail": "low"}
            })
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": content}],
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Sadece sayı al
        for char in answer:
            if char.isdigit():
                idx = int(char)
                if 1 <= idx <= len(images):
                    return idx - 1  # 0-indexed
                elif idx == 0:
                    return None
        
        return None
        
    except Exception as e:
        logging.error(f"OpenAI verification error: {e}")
        return None


@products_bp.route('/api/google-image-search', methods=['POST'])
def api_google_image_search():
    """
    Manuel Google Image Search - Image butonundan çağrılır
    Barkod + ürün adı ile Google'da resim arar, 3 öneri döner
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        query = data.get('query', '').strip()
        barcode = data.get('barcode', '').strip()
        num_results = min(data.get('num_results', 3), 6)  # Max 6
        
        if not query and not barcode:
            return jsonify({'success': False, 'error': 'Query veya barcode gerekli'}), 400
        
        # Arama sorgusu oluştur
        search_query = query if query else barcode
        
        # Google'da ara
        from services.external_api import search_with_google
        results = search_with_google(search_query, max_results=num_results)
        
        if results:
            images = []
            for r in results[:num_results]:
                images.append({
                    'url': r.get('image_url', ''),
                    'thumbnail': r.get('thumbnail_url', ''),
                    'title': r.get('title', ''),
                    'source': r.get('source', 'Google'),
                    'width': r.get('width', 0),
                    'height': r.get('height', 0)
                })
            
            # OpenAI Vision doğrulaması (opsiyonel)
            verify = data.get('verify', False)
            verified_index = None
            
            if verify and images:
                try:
                    verified_index = verify_images_with_openai(images, barcode, query)
                except Exception as e:
                    logging.warning(f"OpenAI verification failed: {e}")
            
            return jsonify({
                'success': True,
                'images': images,
                'query': search_query,
                'count': len(images),
                'verified_index': verified_index
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Resim bulunamadı',
                'query': search_query
            })
        
    except Exception as e:
        logging.error(f"Google image search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/price-comparison', methods=['POST'])
def api_price_comparison():
    """
    Compare customer price with market price.
    Used by Hayalet assistant for price insights.
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        barcode = data.get('barcode', '').strip()
        customer_price = float(data.get('price', 0))
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        if customer_price <= 0:
            return jsonify({'success': False, 'error': 'Valid price required'}), 400
        
        comparison = get_market_price_comparison(barcode, customer_price)
        
        return jsonify({
            'success': True,
            **comparison
        })
        
    except Exception as e:
        logging.error(f"Price comparison error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/api/product-intel/search', methods=['POST'])
def api_product_intel_search():
    """Search product intelligence"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        barcode = data.get('barcode', '')
        
        if not barcode:
            return jsonify({'success': False, 'error': 'Barcode required'}), 400
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admin_images WHERE barcode=?", (barcode,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'found': True,
                'product': {
                    'barcode': row[1],
                    'name': row[2],
                    'image_url': row[3]
                }
            })
        
        return jsonify({'success': True, 'found': False})
        
    except Exception as e:
        logging.error(f"Product intel search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= CUSTOMER FORM =============

@products_bp.route('/musteri-form/<token>')
def musteri_form(token):
    """Customer product entry form via unique token"""
    return render_template('musteri_form.html', token=token)


@products_bp.route('/api/musteri-form/<token>')
def api_musteri_form_info(token):
    """Get customer info from token"""
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    from flask import current_app
    
    try:
        serializer = URLSafeTimedSerializer(current_app.secret_key)
        try:
            data = serializer.loads(token, salt='customer-form', max_age=86400)
            user_id = data.get('customer_id')
        except (SignatureExpired, BadSignature):
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        user = database.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        return jsonify({
            'success': True,
            'customer': {
                'id': user['id'],
                'name': user.get('name', 'Müşteri'),
                'email': user.get('email', ''),
                'sector': user.get('sector', 'supermarket')
            }
        })
    except Exception as e:
        logging.error(f"Customer form info error: {str(e)}")
        return jsonify({'success': False, 'error': 'Invalid token'}), 400


@products_bp.route('/api/musteri-form/<token>/submit', methods=['POST'])
def api_musteri_form_submit(token):
    """Submit products from customer form"""
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    from flask import current_app
    
    try:
        serializer = URLSafeTimedSerializer(current_app.secret_key)
        try:
            data_token = serializer.loads(token, salt='customer-form', max_age=86400)
            user_id = data_token.get('customer_id')
        except (SignatureExpired, BadSignature):
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        user = database.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        data = request.json
        products = data.get('products', [])
        
        for product in products:
            barcode = product.get('barcode', '')
            name = product.get('name', '')
            product_group = product.get('product_group', '')
            normal_price = float(product.get('normal_price', 0) or 0)
            discount_price = float(product.get('discount_price', 0) or 0)
            
            if barcode and name:
                database.add_product(
                    user_id, barcode, name, normal_price, discount_price,
                    '', 'customer', product_group, 0, 0, 0
                )
        
        return jsonify({
            'success': True,
            'count': len(products),
            'message': f'{len(products)} products added successfully'
        })
        
    except Exception as e:
        logging.error(f"Customer form submit error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= KAYDET BUTONU - AŞAMA 2 =============

@products_bp.route('/api/products/save', methods=['POST'])
def api_products_save():
    """
    Kaydet butonu - Aşama 1 + 2 birleşik akış
    
    AŞAMA 1: Resim İşleme
    - Resmi indir
    - rembg ile arka planı kaldır (şeffaf)
    - 1024x1024 resize
    - PNG olarak kaydet
    
    AŞAMA 2: Kategorileme + Kayıt
    - GPT-4o Vision ile resim + isim analiz
    - Sektör whitelist'inden grup seç
    - Pending depot'a kaydet
    - DB'ye approval_status='pending' olarak ekle
    
    ID'leme: Her ürün barcode ile benzersiz tanımlanır
    Canvas: barcode ile çağrılır
    """
    from services.openai_categorizer import categorize_with_vision, categorize_with_openai, is_openai_available
    from services.image_bank import save_to_customer_depot
    from services.image_processor import process_product_image
    
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Oturum açmanız gerekiyor'}), 401
    
    data = request.json or {}
    products = data.get('products', [])
    
    if not products:
        return jsonify({'success': False, 'error': 'Ürün listesi boş'}), 400
    
    sector = user.get('sector', 'supermarket')
    user_id = user['id']
    
    saved_products = []
    skipped_products = []
    updated_products = []
    errors = []
    depot_updates = []
    
    for idx, product in enumerate(products):
        barcode = str(product.get('barcode', '')).strip()
        name = (product.get('name') or '').strip()
        image_url = (product.get('image_url') or '').strip()
        source_type = (product.get('source_type') or 'external').lower()
        normal_price = float(product.get('normal_price', 0) or 0)
        discount_price = float(product.get('discount_price', 0) or 0)
        market_price = float(product.get('market_price', 0) or 0)
        market_price_tax = float(product.get('market_price_tax', 0) or 0)
        existing_group = product.get('product_group', '')
        
        # Depodan gelen ürün - Aşama 1 muaf
        if source_type == 'depo':
            depot_updates.append({
                'barcode': barcode,
                'name': name,
                'status': 'depo_urun_guncelleme_talebi'
            })
            continue
        
        # Depoda zaten var mı kontrol et
        existing = database.get_product_by_barcode(user_id, barcode)
        image_changed = False  # Resim değişti mi flag'i
        
        if existing:
            # Hangi alanlar değişti?
            name_changed = existing.get('name') != name
            normal_price_changed = existing.get('normal_price') != normal_price
            discount_price_changed = existing.get('discount_price') != discount_price
            image_changed = image_url and existing.get('image_url') != image_url
            
            has_changes = name_changed or normal_price_changed or discount_price_changed or image_changed
            
            if not has_changes:
                skipped_products.append({
                    'barcode': barcode,
                    'name': name,
                    'reason': 'Depoda mevcut, değişiklik yok'
                })
                continue
        
        # External ürün - zorunlu alan kontrolü
        if not name:
            errors.append({'barcode': barcode, 'error': 'İsim eksik', 'index': idx})
            continue
        if not image_url:
            errors.append({'barcode': barcode, 'error': 'Resim eksik', 'index': idx})
            continue
        
        # ============= AŞAMA 1: RESİM İŞLEME (DEVRE DIŞI) =============
        # Orijinal resim zaten PNG olarak geliyor, işleme gerek yok
        processed_image = None
        image_processed = False
        logging.info(f"[{barcode}] Resim işleme atlandı - orijinal URL kullanılacak: {image_url[:50]}...")
        
        # ============= AŞAMA 2: KATEGORİLEME =============
        product_group = 'Genel'
        ai_source = 'fallback'
        
        try:
            logging.info(f"[{barcode}] AŞAMA 2: Kategorileme...")
            
            if processed_image and is_openai_available():
                # Vision API ile resim + isim analiz
                ai_result = categorize_with_vision(
                    product_name=name,
                    image_data=processed_image,
                    sector=sector,
                    existing_group=existing_group
                )
                product_group = ai_result.get('group', 'Genel')
                ai_source = ai_result.get('source', 'vision')
                logging.info(f"[{barcode}] Vision kategorileme: '{name}' → '{product_group}'")
            else:
                # Fallback: sadece isimle kategorileme
                ai_result = categorize_with_openai(name, sector)
                product_group = ai_result.get('group', 'Genel')
                short_name = ai_result.get('short_name', name[:30])  # Kısaltılmış isim
                ai_source = ai_result.get('source', 'text')
                logging.info(f"[{barcode}] Text kategorileme: '{name}' → Grup: '{product_group}', Kısa: '{short_name}'")
                
        except Exception as e:
            logging.error(f"[{barcode}] Kategorileme hatası: {e}")
            product_group = 'Genel'
            short_name = name[:30]  # Hata durumunda basit kısaltma
            ai_source = 'error'
        
        # ============= DEPOYA KAYDET =============
        image_saved = False
        depot_url = None
        
        if processed_image:
            try:
                save_result = save_to_customer_depot(
                    user_id=user_id,
                    sector=sector,
                    barcode=barcode,
                    image_data=processed_image,
                    filename='product.png',  # PNG formatında
                    group=product_group,
                    skip_processing=True  # Aşama 1'de zaten işlendi
                )
                if save_result.get('success'):
                    image_saved = True
                    depot_url = save_result.get('pending_url') or save_result.get('customer_url')
                    logging.info(f"[{barcode}] Resim pending'e kaydedildi: {depot_url}")
            except Exception as e:
                logging.warning(f"[{barcode}] Depo kayıt hatası: {e}")
        
        # ============= DB'YE KAYDET =============
        try:
            is_update = existing is not None
            
            if is_update:
                database.update_product(
                    user_id, barcode,
                    name=name,
                    short_name=short_name,  # Kısaltılmış isim
                    normal_price=normal_price,
                    discount_price=discount_price,
                    image_url=depot_url or image_url,
                    product_group=product_group
                )
                updated_products.append({
                    'barcode': barcode,
                    'name': name,
                    'short_name': short_name,
                    'group': product_group,
                    'ai_source': ai_source,
                    'image_saved': image_saved,
                    'image_processed': image_processed,
                    'depot_url': depot_url
                })
            else:
                # Yeni kayıt - Admin onayı bekleyecek
                database.add_product(
                    user_id=user_id,
                    barcode=barcode,
                    name=name,
                    short_name=short_name,  # Kısaltılmış isim
                    normal_price=normal_price,
                    discount_price=discount_price,
                    image_url=depot_url or image_url,
                    image_source='depot' if image_saved else 'external',
                    product_group=product_group,
                    upload_order=idx,
                    market_price=market_price,
                    market_price_tax=market_price_tax,
                    approval_status='pending'
                )
                saved_products.append({
                    'barcode': barcode,
                    'name': name,
                    'short_name': short_name,
                    'group': product_group,
                    'ai_source': ai_source,
                    'image_saved': image_saved,
                    'image_processed': image_processed,
                    'depot_url': depot_url,
                    'approval_status': 'pending'
                })
            
        except Exception as e:
            logging.error(f"[{barcode}] DB kayıt hatası: {e}")
            errors.append({'barcode': barcode, 'error': str(e), 'index': idx})
    
    # Mesaj oluştur
    msg_parts = []
    if saved_products:
        msg_parts.append(f'{len(saved_products)} yeni ürün kaydedildi (onay bekliyor)')
    if updated_products:
        msg_parts.append(f'{len(updated_products)} ürün güncellendi')
    if skipped_products:
        msg_parts.append(f'{len(skipped_products)} ürün atlandı')
    if errors:
        msg_parts.append(f'{len(errors)} hata')
    
    pending_count = database.get_pending_count() if saved_products else 0
    
    return jsonify({
        'success': len(errors) == 0,
        'saved_count': len(saved_products),
        'updated_count': len(updated_products),
        'skipped_count': len(skipped_products),
        'pending_count': pending_count,
        'saved_products': saved_products,
        'updated_products': updated_products,
        'skipped_products': skipped_products,
        'depot_updates': depot_updates,
        'errors': errors,
        'message': ', '.join(msg_parts) if msg_parts else 'İşlem yok',
        'ai_enabled': is_openai_available(),
        'requires_approval': len(saved_products) > 0,
        'stage1_enabled': True,  # Resim işleme aktif
        'stage2_enabled': True   # Vision kategorileme aktif
    })


# ============= ADMIN ONAY ENDPOINT'LERİ =============

@products_bp.route('/api/admin/pending-products', methods=['GET'])
def api_get_pending_products():
    """
    Admin: Onay bekleyen ürünleri listele
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yetki yok'}), 403
    
    sector = request.args.get('sector')  # Optional filter
    pending = database.get_pending_products(sector)
    
    return jsonify({
        'success': True,
        'count': len(pending),
        'products': pending
    })


@products_bp.route('/api/admin/pending-count', methods=['GET'])
def api_get_pending_count():
    """
    Admin: Onay bekleyen ürün sayısı (badge için)
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yetki yok'}), 403
    
    count = database.get_pending_count()
    return jsonify({
        'success': True,
        'count': count
    })


@products_bp.route('/api/admin/approve-product/<int:product_id>', methods=['POST'])
def api_approve_product(product_id):
    """
    Admin: Ürünü onayla
    
    Onaylandığında:
    - approval_status = 'approved'
    - Resim pending'den customer depot'a taşınır
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yetki yok'}), 403
    
    admin_id = user['id']
    
    # Önce ürün bilgisini al
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        return jsonify({'success': False, 'error': 'Ürün bulunamadı'}), 404
    
    if product['approval_status'] != 'pending':
        return jsonify({'success': False, 'error': 'Ürün zaten işlenmiş'}), 400
    
    # Onayla
    success = database.approve_product(product_id, admin_id)
    
    if success:
        # Resmi pending'den customer depot'a taşı (eğer pending'de varsa)
        try:
            from services.image_bank import move_from_pending_to_customer
            move_from_pending_to_customer(
                user_id=product['user_id'],
                sector=product.get('product_group', 'supermarket'),  # sector bilgisi için user'a bakılabilir
                barcode=product['barcode'],
                group=product['product_group']
            )
        except Exception as e:
            logging.warning(f"Resim taşıma hatası (kritik değil): {e}")
        
        return jsonify({
            'success': True,
            'message': f"Ürün onaylandı: {product['name']}"
        })
    else:
        return jsonify({'success': False, 'error': 'Onay işlemi başarısız'}), 500


@products_bp.route('/api/admin/reject-product/<int:product_id>', methods=['POST'])
def api_reject_product(product_id):
    """
    Admin: Ürünü reddet
    
    Reddedildiğinde:
    - approval_status = 'rejected'
    - Resim pending'den silinir
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yetki yok'}), 403
    
    admin_id = user['id']
    data = request.json or {}
    reason = data.get('reason', '')
    
    # Önce ürün bilgisini al
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        return jsonify({'success': False, 'error': 'Ürün bulunamadı'}), 404
    
    if product['approval_status'] != 'pending':
        return jsonify({'success': False, 'error': 'Ürün zaten işlenmiş'}), 400
    
    # Reddet
    success = database.reject_product(product_id, admin_id, reason)
    
    if success:
        # Pending'deki resmi sil
        try:
            from services.image_bank import delete_from_pending
            delete_from_pending(
                sector=product.get('product_group', 'supermarket'),
                barcode=product['barcode'],
                group=product['product_group']
            )
        except Exception as e:
            logging.warning(f"Pending resim silme hatası (kritik değil): {e}")
        
        return jsonify({
            'success': True,
            'message': f"Ürün reddedildi: {product['name']}"
        })
    else:
        return jsonify({'success': False, 'error': 'Red işlemi başarısız'}), 500


@products_bp.route('/api/admin/bulk-approve', methods=['POST'])
def api_bulk_approve_products():
    """
    Admin: Toplu onay
    """
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Yetki yok'}), 403
    
    data = request.json or {}
    product_ids = data.get('product_ids', [])
    
    if not product_ids:
        return jsonify({'success': False, 'error': 'Ürün ID listesi boş'}), 400
    
    admin_id = user['id']
    approved_count = 0
    errors = []
    
    for pid in product_ids:
        try:
            if database.approve_product(pid, admin_id):
                approved_count += 1
            else:
                errors.append({'id': pid, 'error': 'Onay başarısız'})
        except Exception as e:
            errors.append({'id': pid, 'error': str(e)})
    
    return jsonify({
        'success': len(errors) == 0,
        'approved_count': approved_count,
        'errors': errors,
        'message': f'{approved_count} ürün onaylandı' + (f', {len(errors)} hata' if errors else '')
    })
