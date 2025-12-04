# -*- coding: utf-8 -*-
"""
Settings routes - User settings, background settings, layout management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import logging
import json
import os

from utils.helpers import get_current_user
from utils.constants import DEFAULT_BACKGROUND_SETTINGS

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/save-settings', methods=['POST'])
def api_save_settings():
    """Save user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        
        # Support both formats: { settings: {...} } and direct { logo: ..., ... }
        if 'settings' in data:
            new_settings = data.get('settings', {})
        else:
            new_settings = data
        
        # Get existing settings and merge
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_settings 
                     (user_id INTEGER PRIMARY KEY, settings TEXT)''')
        c.execute("SELECT settings FROM user_settings WHERE user_id=?", (user['id'],))
        row = c.fetchone()
        
        existing = {}
        if row and row[0]:
            try:
                existing = json.loads(row[0])
            except:
                existing = {}
        
        # Merge new settings with existing
        existing.update(new_settings)
        settings = json.dumps(existing)
        
        # Save merged settings
        conn2 = sqlite3.connect('brosur.db')
        c2 = conn2.cursor()
        c2.execute("INSERT OR REPLACE INTO user_settings (user_id, settings) VALUES (?, ?)",
                  (user['id'], settings))
        conn2.commit()
        conn2.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Save settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/get-settings')
def api_get_settings():
    """Get user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_settings 
                     (user_id INTEGER PRIMARY KEY, settings TEXT)''')
        c.execute("SELECT settings FROM user_settings WHERE user_id=?", (user['id'],))
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            settings_data = json.loads(row[0])
            return jsonify({'success': True, 'data': settings_data, 'settings': settings_data})
        return jsonify({'success': True, 'data': {}, 'settings': {}})
        
    except Exception as e:
        logging.error(f"Get settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/get-background-settings')
def get_background_settings():
    """Get admin-defined background settings for login/dashboard"""
    try:
        try:
            conn = sqlite3.connect('brosur.db')
            c = conn.cursor()
            c.execute("SELECT settings FROM background_settings WHERE id = 1")
            row = c.fetchone()
            conn.close()
            
            if row and row[0]:
                return jsonify({'success': True, 'settings': json.loads(row[0])})
        except Exception as db_error:
            logging.debug(f"Background settings not in DB, using defaults: {db_error}")
        
        return jsonify({'success': True, 'settings': DEFAULT_BACKGROUND_SETTINGS})
        
    except Exception as e:
        logging.error(f"Get background settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/save-background-settings', methods=['POST'])
def save_background_settings():
    """Save admin-defined background settings"""
    try:
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.json
        settings = data.get('settings', {})
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS background_settings 
                     (id INTEGER PRIMARY KEY, settings TEXT)''')
        
        c.execute("INSERT OR REPLACE INTO background_settings (id, settings) VALUES (1, ?)",
                  (json.dumps(settings),))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Settings saved'})
        
    except Exception as e:
        logging.error(f"Save background settings error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/save-admin-layout', methods=['POST'])
def api_save_admin_layout():
    """Save admin layout settings"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        layout = json.dumps(data.get('layout', {}))
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admin_layout 
                     (id INTEGER PRIMARY KEY, layout TEXT)''')
        c.execute("INSERT OR REPLACE INTO admin_layout (id, layout) VALUES (1, ?)", (layout,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Save admin layout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/get-admin-layout')
def api_get_admin_layout():
    """Get admin layout settings"""
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT layout FROM admin_layout WHERE id=1")
        row = c.fetchone()
        conn.close()
        
        if row and row[0]:
            return jsonify({'success': True, 'layout': json.loads(row[0])})
        return jsonify({'success': True, 'layout': {}})
        
    except Exception as e:
        return jsonify({'success': True, 'layout': {}})


@settings_bp.route('/api/upload-logo', methods=['POST'])
def api_upload_logo():
    """Upload company logo"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'error': 'No logo uploaded'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        user_folder = os.path.join('static', 'uploads', 'logos', str(user['id']))
        os.makedirs(user_folder, exist_ok=True)
        
        filename = 'logo.png'
        file_path = os.path.join(user_folder, filename)
        file.save(file_path)
        
        logo_url = f'/static/uploads/logos/{user["id"]}/{filename}'
        
        return jsonify({'success': True, 'logo_url': logo_url})
        
    except Exception as e:
        logging.error(f"Upload logo error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/upload-background', methods=['POST'])
def api_upload_background():
    """Upload background image"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        if 'background' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['background']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        bg_folder = os.path.join('static', 'uploads', 'backgrounds')
        os.makedirs(bg_folder, exist_ok=True)
        
        filename = f'bg_{datetime.now().strftime("%Y%m%d%H%M%S")}.jpg'
        file_path = os.path.join(bg_folder, filename)
        file.save(file_path)
        
        bg_url = f'/static/uploads/backgrounds/{filename}'
        
        return jsonify({'success': True, 'background_url': bg_url})
        
    except Exception as e:
        logging.error(f"Upload background error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= THEME TOGGLE =============

@settings_bp.route('/api/theme/toggle', methods=['POST'])
def api_toggle_theme():
    """Toggle dark/light theme for user"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        theme = data.get('theme', 'dark')  # 'dark' or 'light'
        
        if theme not in ['dark', 'light']:
            return jsonify({'success': False, 'error': 'Invalid theme'}), 400
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_preferences 
                     (user_id INTEGER PRIMARY KEY, theme TEXT, language TEXT)''')
        
        c.execute("INSERT OR REPLACE INTO user_preferences (user_id, theme) VALUES (?, ?)",
                  (user['id'], theme))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'theme': theme,
            'message': f'{theme.capitalize()} tema aktifleştirildi'
        })
        
    except Exception as e:
        logging.error(f"Theme toggle error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/theme/current')
def api_get_theme():
    """Get current theme for user"""
    user = get_current_user()
    if not user:
        return jsonify({'success': True, 'theme': 'dark'})  # Default for non-authenticated
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT theme FROM user_preferences WHERE user_id=?", (user['id'],))
        row = c.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'theme': row[0] if row else 'dark'
        })
        
    except Exception as e:
        return jsonify({'success': True, 'theme': 'dark'})


# ============= LANGUAGE SETTINGS =============

@settings_bp.route('/api/language/set', methods=['POST'])
def api_set_language():
    """Set language preference (TR/EN)"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        language = data.get('language', 'tr')  # 'tr' or 'en'
        
        if language not in ['tr', 'en']:
            return jsonify({'success': False, 'error': 'Invalid language'}), 400
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_preferences 
                     (user_id INTEGER PRIMARY KEY, theme TEXT, language TEXT)''')
        
        c.execute("""INSERT OR REPLACE INTO user_preferences (user_id, language) 
                     VALUES (?, ?)""", (user['id'], language))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'language': language,
            'message': f'Dil {language.upper()} olarak ayarlandı'
        })
        
    except Exception as e:
        logging.error(f"Language set error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/language/current')
def api_get_language():
    """Get current language preference"""
    user = get_current_user()
    if not user:
        return jsonify({'success': True, 'language': 'tr'})
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT language FROM user_preferences WHERE user_id=?", (user['id'],))
        row = c.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'language': row[0] if row else 'tr'
        })
        
    except Exception as e:
        return jsonify({'success': True, 'language': 'tr'})


# ============= CREDIT SYSTEM (PLACEHOLDER) =============

@settings_bp.route('/api/credits/balance')
def api_get_credits():
    """Get user's credit balance"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    return jsonify({
        'success': True,
        'credits': user.get('credits', 0),
        'is_premium': user.get('credits', 0) > 50
    })


@settings_bp.route('/api/credits/purchase', methods=['POST'])
def api_purchase_credits():
    """Purchase credits - PLACEHOLDER for payment integration"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json or {}
        package = data.get('package', 'basic')  # basic, standard, premium
        payment_method = data.get('payment_method', 'credit_card')  # credit_card, qr_code
        
        CREDIT_PACKAGES = {
            'basic': {'credits': 100, 'price': 49.99, 'currency': 'TRY'},
            'standard': {'credits': 300, 'price': 129.99, 'currency': 'TRY'},
            'premium': {'credits': 1000, 'price': 349.99, 'currency': 'TRY'}
        }
        
        if package not in CREDIT_PACKAGES:
            return jsonify({'success': False, 'error': 'Geçersiz paket'}), 400
        
        pkg = CREDIT_PACKAGES[package]
        
        # PLACEHOLDER: Payment integration would go here
        # PayTR / PayGuru integration needed
        
        return jsonify({
            'success': False,
            'message': 'Ödeme sistemi şu an bakım modunda',
            'package': {
                'name': package,
                'credits': pkg['credits'],
                'price': pkg['price'],
                'currency': pkg['currency']
            },
            'payment_methods': {
                'credit_card': 'Kredi Kartı (PayTR)',
                'qr_code': 'QR Kod ile Ödeme',
                'sms': 'SMS ile Ödeme (Pasif)'
            },
            'note': 'Ödeme entegrasyonu tamamlanınca aktif olacak'
        })
        
    except Exception as e:
        logging.error(f"Credit purchase error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/api/credits/packages')
def api_credit_packages():
    """Get available credit packages"""
    packages = {
        'basic': {
            'name': 'Başlangıç',
            'credits': 100,
            'price': 49.99,
            'currency': 'TRY',
            'features': ['100 AI işlemi', '10 PDF export', 'Temel destek']
        },
        'standard': {
            'name': 'Standart',
            'credits': 300,
            'price': 129.99,
            'currency': 'TRY',
            'features': ['300 AI işlemi', '50 PDF export', 'Öncelikli destek', 'Filigransız export']
        },
        'premium': {
            'name': 'Premium',
            'credits': 1000,
            'price': 349.99,
            'currency': 'TRY',
            'features': ['1000 AI işlemi', 'Sınırsız PDF export', 'VIP destek', 
                        'Filigransız export', 'Özel şablonlar']
        }
    }
    
    return jsonify({
        'success': True,
        'packages': packages,
        'payment_status': 'maintenance',
        'note': 'Ödeme sistemi yakında aktif olacak'
    })


@settings_bp.route('/api/credits/history')
def api_credit_history():
    """Get user's credit usage history"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute("SELECT history FROM customer_credits WHERE customer_id=?", (user['id'],))
        row = c.fetchone()
        conn.close()
        
        history = json.loads(row[0]) if row and row[0] else []
        
        return jsonify({
            'success': True,
            'history': history,
            'current_balance': user.get('credits', 0)
        })
        
    except Exception as e:
        logging.error(f"Credit history error: {str(e)}")
        return jsonify({'success': True, 'history': [], 'current_balance': 0})

