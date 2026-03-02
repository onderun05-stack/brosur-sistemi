# -*- coding: utf-8 -*-
"""
AEU Yazılım Broşür Sistemi - Main Application Entry Point

Temizlenmiş iskelet yapı:
- Flask app initialization
- Blueprint registrations (sadece core blueprints)
- CORS and session configuration
- Rate limiting and security headers
- Database initialization
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("✅ .env dosyası yüklendi")
except ImportError:
    logging.warning("⚠️ python-dotenv yüklü değil, .env dosyası okunamıyor")

import database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)

# Set session secret with fallback
if not os.environ.get("SESSION_SECRET"):
    os.environ["SESSION_SECRET"] = "market-brosur-" + os.urandom(24).hex()
app.secret_key = os.environ.get("SESSION_SECRET")

# Add ProxyFix for HTTPS support
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Session configuration for security
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP in development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ============= RATE LIMITING =============
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "60 per minute"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    
    @limiter.limit("15 per minute")
    @app.before_request
    def limit_auth_routes():
        if request.endpoint and 'login' in request.endpoint:
            pass
    
    logging.info("✅ Rate limiting enabled")
    
except ImportError:
    logging.warning("⚠️ Flask-Limiter not installed")
    limiter = None

# Enable CORS
CORS(app)

# Initialize SQLite database
database.init_db()

# ============= CORE BLUEPRINTS =============
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.products import products_bp
from routes.settings import settings_bp
from routes.image_bank import image_bank_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(products_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(image_bank_bp)

# ============= ERROR HANDLERS =============
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'error': 'Çok fazla istek. Lütfen bekleyin.', 'retry_after': e.description}), 429

@app.errorhandler(400)
def bad_request_handler(e):
    return jsonify({'success': False, 'error': 'Geçersiz istek'}), 400

@app.errorhandler(404)
def not_found_handler(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint bulunamadı'}), 404
    return e

@app.errorhandler(500)
def internal_error_handler(e):
    logging.error(f"Internal error: {str(e)}")
    return jsonify({'success': False, 'error': 'Sunucu hatası oluştu'}), 500

# ============= SECURITY HEADERS =============
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

logging.info(f"✅ Flask app initialized with {len(list(app.url_map.iter_rules()))} routes")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
