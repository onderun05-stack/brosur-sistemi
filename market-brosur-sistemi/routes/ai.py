# -*- coding: utf-8 -*-
"""
AI routes - AI services, theme management, export functionality
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import sqlite3
import logging
import base64
import json
import os

import ai_service
from services.kie_ai import (
    generate_brochure_background,
    generate_3d_slogan,
    analyze_products_for_brochure,
    get_ai_brochure_suggestion,
)
from utils.helpers import get_current_user

ai_bp = Blueprint('ai', __name__)


def _stage_two_disabled_response():
    return jsonify({
        'success': False,
        'error': 'Stage 2 özellikleri bu aşamada devre dışı'
    }), 403


# ============= AI SERVICES =============

@ai_bp.route('/api/ai/suggest-slogans')
def api_ai_suggest_slogans():
    """AI suggest slogans using OpenAI"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        result = ai_service.suggest_slogans()
        return jsonify(result)
    except Exception as e:
        logging.error(f"AI slogan error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'slogans': [
                "En uygun fiyatlar burada!",
                "Kalite ve ekonomi bir arada",
                "Aile bütçesine uygun seçenekler",
                "Taze ürünler, hesaplı fiyatlar"
            ]
        })


@ai_bp.route('/api/ai/generate-slogan-image', methods=['POST'])
def api_ai_generate_slogan_image():
    """AI generate slogan image using DALL-E"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json or {}
        slogan = data.get('slogan', 'Süper İndirim!')
        style = data.get('style', 'modern')
        
        result = ai_service.generate_slogan_image(slogan, style)
        return jsonify(result)
    except Exception as e:
        logging.error(f"AI slogan image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'image_url': None})


@ai_bp.route('/api/ai/generate-background', methods=['POST'])
def api_ai_generate_background():
    """AI generate background using DALL-E"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json or {}
        theme = data.get('theme', 'market')
        season = data.get('season', 'summer')
        category = data.get('category', 'food')
        
        result = ai_service.generate_background_with_dalle(theme, season, category)
        return jsonify(result)
    except Exception as e:
        logging.error(f"AI background error: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'background_url': None})


@ai_bp.route('/api/ai/design-template', methods=['POST'])
def api_ai_design_template():
    """AI design template using OpenAI"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json or {}
        products = data.get('products', [])
        style = data.get('style', 'modern')
        
        result = ai_service.generate_auto_brochure(products)
        return jsonify(result)
    except Exception as e:
        logging.error(f"AI template error: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'template': None})


@ai_bp.route('/api/ai/generate-product-image', methods=['POST'])
def api_ai_generate_product_image():
    """AI generate product image using DALL-E"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json or {}
        product_name = data.get('product_name', '')
        barcode = data.get('barcode', '')
        
        if not product_name:
            return jsonify({'success': False, 'error': 'Product name required'}), 400
        
        result = ai_service.generate_product_image(product_name, barcode)
        return jsonify(result)
    except Exception as e:
        logging.error(f"AI product image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'image_url': None})


@ai_bp.route('/api/ai/save-selected-image', methods=['POST'])
def api_ai_save_selected_image():
    """Save AI selected image"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json
        image_url = data.get('image_url', '')
        barcode = data.get('barcode', '')
        
        if not image_url or not barcode:
            return jsonify({'success': False, 'error': 'Missing data'}), 400
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("INSERT INTO customer_images (user_id, barcode, image_url, approved) VALUES (?, ?, ?, 0)",
                  (user['id'], barcode, image_url))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Save selected image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/ai-distribute', methods=['POST'])
def api_ai_distribute():
    """AI distribute products to template"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    if not current_app.config.get('ENABLE_STAGE2', False):
        return _stage_two_disabled_response()
    
    try:
        data = request.json
        products = data.get('products', [])
        template = data.get('template', 'grid')
        
        distributed = []
        for i, product in enumerate(products):
            row = i // 4
            col = i % 4
            distributed.append({
                **product,
                'position': {'row': row, 'col': col}
            })
        
        return jsonify({'success': True, 'distributed': distributed})
        
    except Exception as e:
        logging.error(f"AI distribute error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= DESINGER TEST API =============


@ai_bp.route('/api/desinger/layout-suggestion', methods=['POST'])
def api_desinger_layout_suggestion():
    """Desınger test sayfası için OpenAI tabanlı yerleşim / slogan önerisi.
    NOT: Bu sadece TEST endpoint'i - Stage 2 kontrolü yok, ana sistemi etkilemez.
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    # Stage 2 kontrolü kaldırıldı - test endpoint'i olduğu için

    try:
        data = request.get_json() or {}
        products = data.get('products', [])
        purpose = data.get('purpose', 'discount')
        user_message = data.get('user_message')

        analysis = analyze_products_for_brochure(products)
        if not analysis.get('success', True) and analysis.get('error'):
            return jsonify({'success': False, 'error': analysis.get('error')}), 400

        suggestion = get_ai_brochure_suggestion(
            products_analysis=analysis,
            purpose=purpose,
            user_message=user_message,
        )

        return jsonify({
            'success': True,
            'analysis': analysis,
            'result': suggestion,
        })
    except Exception as e:
        logging.error(f"Desinger layout suggestion error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/desinger/kie-background', methods=['POST'])
def api_desinger_kie_background():
    """Desınger test sayfası için OpenAI DALL-E ile broşür arka planı üret.
    NOT: Bu sadece TEST endpoint'i - Stage 2 kontrolü yok, ana sistemi etkilemez.
    KIE.ai yerine OpenAI DALL-E kullanılıyor (KIE_API_KEY gerekmez).
    Görsel CORS sorunu olmaması için sunucuya indirilip yerel URL olarak döndürülür.
    """
    import requests
    import uuid
    
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    # Stage 2 kontrolü kaldırıldı - test endpoint'i olduğu için

    try:
        data = request.get_json() or {}
        purpose = data.get('purpose', 'discount')
        
        # Purpose'a göre tema belirle (Kırmızı Market referanslı)
        theme_map = {
            'discount': 'discount',      # İndirim kampanyası - kırmızı/sarı patlama
            'market': 'market',          # Genel market - yeşil/krem profesyonel
            'tea': 'tea',                # Çay kampanyası - yeşil çay tarlası
            'fresh': 'fresh',            # Manav/sebze-meyve - taze yeşil
            'butcher': 'butcher',        # Kasap/et ürünleri - bordo/ahşap
            'holiday_ramazan': 'market',
            'holiday_kurban': 'butcher',
            'holiday_newyear': 'discount',
            'grocery': 'fresh',
        }
        theme = theme_map.get(purpose, 'market')
        
        # OpenAI DALL-E ile profesyonel Türk market broşürü arka planı üret
        result = ai_service.generate_background_with_dalle(
            theme=theme,
            season='summer',
            product_category='food'
        )
        
        # Sonuç formatını uyumlu hale getir
        if result.get('success') and result.get('background_url'):
            remote_url = result['background_url']
            
            # CORS sorunu olmaması için görseli sunucuya indir
            try:
                bg_folder = os.path.join('static', 'uploads', 'backgrounds')
                os.makedirs(bg_folder, exist_ok=True)
                
                # Benzersiz dosya adı
                filename = f"bg_{uuid.uuid4().hex[:8]}.png"
                local_path = os.path.join(bg_folder, filename)
                
                # Görseli indir
                img_response = requests.get(remote_url, timeout=30)
                if img_response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    local_url = f'/static/uploads/backgrounds/{filename}'
                    return jsonify({
                        'success': True,
                        'image_url': local_url,
                        'model': 'dall-e-3'
                    })
                else:
                    logging.warning(f"Could not download background image: {img_response.status_code}")
                    # Yine de remote URL'yi dön, belki çalışır
                    return jsonify({
                        'success': True,
                        'image_url': remote_url,
                        'model': 'dall-e-3',
                        'warning': 'CORS issues may occur'
                    })
            except Exception as download_error:
                logging.warning(f"Background download error: {download_error}")
                return jsonify({
                    'success': True,
                    'image_url': remote_url,
                    'model': 'dall-e-3',
                    'warning': 'CORS issues may occur'
                })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Desinger DALL-E background error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/desinger/kie-slogan-image', methods=['POST'])
def api_desinger_kie_slogan_image():
    """Desınger test sayfası için KIE.ai 3D slogan görseli üret.
    NOT: Bu sadece TEST endpoint'i - Stage 2 kontrolü yok, ana sistemi etkilemez.
    """
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    # Stage 2 kontrolü kaldırıldı - test endpoint'i olduğu için

    try:
        data = request.get_json() or {}
        slogan = data.get('slogan', 'Süper İndirim!')
        style = data.get('style', 'gold')

        result = generate_3d_slogan(slogan_text=slogan, style=style)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Desinger KIE slogan image error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= THEME API =============

@ai_bp.route('/api/theme')
def api_get_theme():
    """Get current theme"""
    return jsonify({
        'success': True,
        'theme': {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'background': '#fdf5e6'
        }
    })


@ai_bp.route('/api/custom-theme/active')
def api_custom_theme_active():
    """Get active custom theme"""
    user = get_current_user()
    if not user:
        return jsonify({'success': True, 'theme': None})
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT theme FROM custom_themes WHERE user_id=? AND active=1", (user['id'],))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return jsonify({'success': True, 'theme': json.loads(row[0])})
        return jsonify({'success': True, 'theme': None})
        
    except Exception as e:
        return jsonify({'success': True, 'theme': None})


@ai_bp.route('/api/custom-theme/save', methods=['POST'])
def api_custom_theme_save():
    """Save custom theme"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        theme = json.dumps(data.get('theme', {}))
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS custom_themes 
                     (id INTEGER PRIMARY KEY, user_id INTEGER, theme TEXT, active INTEGER DEFAULT 0)''')
        c.execute("INSERT INTO custom_themes (user_id, theme) VALUES (?, ?)", (user['id'], theme))
        conn.commit()
        theme_id = c.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'theme_id': theme_id})
        
    except Exception as e:
        logging.error(f"Save theme error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/api/custom-theme/activate', methods=['POST'])
def api_custom_theme_activate():
    """Activate custom theme"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        theme_id = data.get('theme_id')
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("UPDATE custom_themes SET active=0 WHERE user_id=?", (user['id'],))
        c.execute("UPDATE custom_themes SET active=1 WHERE id=? AND user_id=?", (theme_id, user['id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Activate theme error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= EXPORT API =============

@ai_bp.route('/api/export/jpeg', methods=['POST'])
def api_export_jpeg():
    """Export canvas as JPEG"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        image_data = data.get('image_data', '')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data'}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        export_folder = os.path.join('static', 'exports', str(user['id']))
        os.makedirs(export_folder, exist_ok=True)
        
        filename = f'brochure_{datetime.now().strftime("%Y%m%d%H%M%S")}.jpg'
        file_path = os.path.join(export_folder, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        download_url = f'/static/exports/{user["id"]}/{filename}'
        
        return jsonify({'success': True, 'download_url': download_url})
        
    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= AUTO LAYOUT API =============

@ai_bp.route('/api/auto-layout', methods=['POST'])
def api_auto_layout():
    """Auto layout products on canvas"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        products = data.get('products', [])
        layout_type = data.get('layout', 'grid')
        page_size = data.get('page_size', {'width': 595, 'height': 842})
        
        cols = 4
        rows = (len(products) + cols - 1) // cols
        
        cell_width = page_size['width'] // cols
        cell_height = (page_size['height'] - 100) // max(rows, 1)
        
        layout = []
        for i, product in enumerate(products):
            row = i // cols
            col = i % cols
            
            layout.append({
                **product,
                'x': col * cell_width + 10,
                'y': row * cell_height + 50,
                'width': cell_width - 20,
                'height': cell_height - 20
            })
        
        return jsonify({'success': True, 'layout': layout})
        
    except Exception as e:
        logging.error(f"Auto layout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

