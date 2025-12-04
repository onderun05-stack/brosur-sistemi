# -*- coding: utf-8 -*-
"""
Authentication routes - Login, register, session management
"""

from flask import Blueprint, request, jsonify, session
import logging

import database
from utils.helpers import get_current_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """Login user with email and password"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'E-posta ve şifre gerekli'}), 400
        
        # Get user from SQLite database
        user = database.get_user(email, password)
        
        if user:
            # Store user in session
            session['user_id'] = user['id']
            session.permanent = True
            
            logging.info(f"User logged in: {email}")
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user.get('name', 'Kullanıcı'),
                    'role': user.get('role', 'customer')
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Geçersiz e-posta veya şifre'}), 401
            
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'Giriş hatası'}), 500


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """Register new user"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        sector = data.get('sector', 'supermarket')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'E-posta ve şifre gerekli'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Şifre en az 6 karakter olmalı'}), 400
        
        # Create user in SQLite database
        user_id = database.create_user(email, password, name or email.split('@')[0], sector)
        
        if user_id:
            # Auto-login after registration
            session['user_id'] = user_id
            session.permanent = True
            
            logging.info(f"New user registered: {email}")
            return jsonify({
                'success': True,
                'user': {
                    'id': user_id,
                    'email': email,
                    'name': name or email.split('@')[0],
                    'role': 'customer'
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Bu e-posta adresi zaten kayıtlı'}), 409
            
    except Exception as e:
        logging.error(f"Register error: {str(e)}")
        return jsonify({'success': False, 'error': 'Kayıt hatası'}), 500


@auth_bp.route('/api/check-session')
def check_session():
    """Check if user is logged in"""
    user = get_current_user()
    if user:
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': {
                'id': user.get('id'),
                'email': user.get('email'),
                'name': user.get('name', 'Kullanıcı'),
                'role': user.get('role', 'customer'),
                'sector': user.get('sector', 'supermarket'),
                'credits': user.get('credits', 0)
            }
        })
    return jsonify({'success': True, 'logged_in': False})


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})


@auth_bp.route('/api/user/current')
def get_current_user_api():
    """Get current logged in user data"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.get('id'),
            'name': user.get('name', 'Kullanıcı'),
            'email': user.get('email', ''),
            'role': user.get('role', 'customer'),
            'sector': user.get('sector', 'supermarket'),
            'credits': user.get('credits', 0)
        }
    })


@auth_bp.route('/api/check-admin')
def api_check_admin():
    """Check if current user is admin"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'is_admin': False})
    
    return jsonify({'success': True, 'is_admin': user.get('role') == 'admin'})


# ============= PASSWORD RESET =============

@auth_bp.route('/api/request-password-reset', methods=['POST'])
def api_request_password_reset():
    """Request password reset - sends email with reset token"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'error': 'E-posta adresi gerekli'}), 400
        
        user = database.get_user_by_email(email)
        if not user:
            # Security: Don't reveal if email exists
            return jsonify({
                'success': True, 
                'message': 'Eğer bu e-posta kayıtlıysa, şifre sıfırlama bağlantısı gönderildi'
            })
        
        # Generate reset token (stored in database)
        import secrets
        from datetime import datetime, timedelta
        
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        # Store token in database
        import sqlite3
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets 
                     (id INTEGER PRIMARY KEY, email TEXT, token TEXT, 
                      expires_at TIMESTAMP, used BOOLEAN DEFAULT FALSE)''')
        c.execute("INSERT INTO password_resets (email, token, expires_at) VALUES (?, ?, ?)",
                  (email, reset_token, expires_at))
        conn.commit()
        conn.close()
        
        # TODO: Send email with reset link (email service integration needed)
        # For now, log the token for development
        logging.info(f"Password reset token for {email}: {reset_token}")
        
        return jsonify({
            'success': True,
            'message': 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi'
        })
        
    except Exception as e:
        logging.error(f"Password reset request error: {str(e)}")
        return jsonify({'success': False, 'error': 'Bir hata oluştu'}), 500


@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password using token"""
    try:
        data = request.json
        token = data.get('token', '')
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'success': False, 'error': 'Token ve yeni şifre gerekli'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Şifre en az 6 karakter olmalı'}), 400
        
        import sqlite3
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        
        conn = sqlite3.connect('brosur.db')
        c = conn.cursor()
        
        # Check if token is valid
        c.execute("""SELECT email FROM password_resets 
                     WHERE token=? AND used=0 AND expires_at > ?""",
                  (token, datetime.now()))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Geçersiz veya süresi dolmuş token'}), 400
        
        email = result[0]
        
        # Update password
        hashed_password = generate_password_hash(new_password)
        c.execute("UPDATE users SET password=? WHERE email=?", (hashed_password, email))
        
        # Mark token as used
        c.execute("UPDATE password_resets SET used=1 WHERE token=?", (token,))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Password reset successful for {email}")
        return jsonify({'success': True, 'message': 'Şifreniz başarıyla güncellendi'})
        
    except Exception as e:
        logging.error(f"Password reset error: {str(e)}")
        return jsonify({'success': False, 'error': 'Bir hata oluştu'}), 500


# ============= EMAIL VERIFICATION (PASSIVE) =============

@auth_bp.route('/api/send-verification-email', methods=['POST'])
def api_send_verification_email():
    """Send email verification - PASSIVE: Placeholder for future implementation"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Placeholder - email service integration needed
    logging.info(f"Email verification requested for user {user['id']}")
    
    return jsonify({
        'success': True,
        'message': 'Doğrulama e-postası gönderildi (demo mod)',
        'note': 'E-posta servisi entegrasyonu bekliyor'
    })


@auth_bp.route('/api/verify-email', methods=['POST'])
def api_verify_email():
    """Verify email with token - PASSIVE: Placeholder for future implementation"""
    try:
        data = request.json
        token = data.get('token', '')
        
        if not token:
            return jsonify({'success': False, 'error': 'Token gerekli'}), 400
        
        # Placeholder - would verify token and mark user as verified
        logging.info(f"Email verification attempted with token: {token[:10]}...")
        
        return jsonify({
            'success': True,
            'message': 'E-posta doğrulandı (demo mod)',
            'note': 'Gerçek doğrulama sistemi pasif'
        })
        
    except Exception as e:
        logging.error(f"Email verification error: {str(e)}")
        return jsonify({'success': False, 'error': 'Bir hata oluştu'}), 500


# ============= SMS VERIFICATION (PASSIVE) =============

@auth_bp.route('/api/send-sms-verification', methods=['POST'])
def api_send_sms_verification():
    """Send SMS verification - PASSIVE: Disabled, placeholder only"""
    return jsonify({
        'success': False,
        'message': 'SMS doğrulama şu an pasif durumda',
        'note': 'İleride aktif edilecek'
    })

