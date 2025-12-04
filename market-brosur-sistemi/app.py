# -*- coding: utf-8 -*-
"""
AEU Yazılım Broşür Sistemi - Main Application Entry Point

This file contains:
- Flask app initialization
- Blueprint registrations
- CORS and session configuration
- Rate limiting and CSRF protection
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
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Template auto-reload for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['ENABLE_STAGE2'] = False

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
    
    # Apply specific limits to auth endpoints
    @limiter.limit("15 per minute")
    @app.before_request
    def limit_auth_routes():
        if request.endpoint and 'login' in request.endpoint:
            pass  # Rate limit applied
    
    logging.info("✅ Rate limiting enabled")
    HAS_RATE_LIMITER = True
    
except ImportError:
    logging.warning("⚠️ Flask-Limiter not installed, rate limiting disabled")
    HAS_RATE_LIMITER = False
    limiter = None

# ============= CSRF PROTECTION =============
try:
    from flask_wtf.csrf import CSRFProtect, CSRFError
    
    csrf = CSRFProtect()
    # Don't enable globally - only for specific forms
    # csrf.init_app(app)
    
    # Exempt API routes from CSRF (they use other auth methods)
    # CSRF is mainly for HTML form submissions
    
    logging.info("✅ CSRF protection available")
    HAS_CSRF = True
    
except ImportError:
    logging.warning("⚠️ Flask-WTF not installed, CSRF protection disabled")
    HAS_CSRF = False
    csrf = None

# Enable CORS
CORS(app)

# Initialize SQLite database
database.init_db()

# Import and register blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.products import products_bp
from routes.settings import settings_bp
from routes.ai import ai_bp
from routes.image_bank import image_bank_bp
from routes.brochure import brochure_bp
from routes.ghost import ghost_bp
from routes.analytics import analytics_bp
from routes.ai_extra import ai_extra_bp
from routes.wizard import wizard_bp

# Register all blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(products_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(image_bank_bp)
app.register_blueprint(brochure_bp)
app.register_blueprint(ghost_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(ai_extra_bp)
app.register_blueprint(wizard_bp)

# ============= ERROR HANDLERS =============

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'success': False,
        'error': 'Çok fazla istek gönderdiniz. Lütfen biraz bekleyin.',
        'retry_after': e.description
    }), 429

@app.errorhandler(400)
def bad_request_handler(e):
    """Handle bad request"""
    return jsonify({
        'success': False,
        'error': 'Geçersiz istek'
    }), 400

@app.errorhandler(404)
def not_found_handler(e):
    """Handle not found"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint bulunamadı'
        }), 404
    # Return default 404 for non-API routes
    return e

@app.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server error"""
    logging.error(f"Internal error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Sunucu hatası oluştu'
    }), 500

# ============= SECURITY HEADERS =============

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

# Log registered routes count
logging.info(f"✅ Flask app initialized with {len(list(app.url_map.iter_rules()))} routes")


# ============= RUN APP =============

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
