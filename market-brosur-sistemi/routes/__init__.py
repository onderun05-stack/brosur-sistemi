# -*- coding: utf-8 -*-
"""
Routes package - All Flask blueprints
"""

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

__all__ = [
    'main_bp',
    'auth_bp', 
    'admin_bp',
    'products_bp',
    'settings_bp',
    'ai_bp',
    'image_bank_bp',
    'brochure_bp',
    'ghost_bp',
    'analytics_bp',
    'ai_extra_bp'
]

