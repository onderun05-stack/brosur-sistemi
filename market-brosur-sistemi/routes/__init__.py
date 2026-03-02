# -*- coding: utf-8 -*-
"""
Routes package - Core Flask blueprints
"""

from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.products import products_bp
from routes.settings import settings_bp
from routes.image_bank import image_bank_bp

__all__ = [
    'main_bp',
    'auth_bp', 
    'admin_bp',
    'products_bp',
    'settings_bp',
    'image_bank_bp'
]
