# -*- coding: utf-8 -*-
"""
Helper functions and utilities used across the application.
"""

from functools import wraps
from pathlib import Path
from flask import session, redirect, jsonify
import os

import database
from utils.constants import SECTORS


def safe_join(base, *paths):
    """Safely join paths preventing directory traversal attacks"""
    try:
        base_path = Path(base).resolve()
        final_path = base_path.joinpath(*paths).resolve()
        if str(final_path).startswith(str(base_path)):
            return str(final_path)
        return None
    except Exception:
        return None


def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        user_id = session['user_id']
        return database.get_user_by_id(user_id)
    return None


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_sector_path(sector, folder_type='admin'):
    """Get sector-based folder path"""
    return os.path.join('static', 'uploads', folder_type, sector)


def ensure_sector_dirs():
    """Ensure all sector directories exist"""
    for sector in SECTORS.keys():
        for folder in ['admin', 'pending', 'customers']:
            path = os.path.join('static', 'uploads', folder, sector)
            os.makedirs(path, exist_ok=True)


def parse_turkish_float(value):
    """Parse Turkish-formatted numbers (1.234,56 or 1234.56 or 12,50) with robust validation"""
    if not value or not str(value).strip():
        return 0.0
    
    # Remove currency symbols and whitespace
    cleaned = str(value).strip().replace('₺', '').replace('TL', '').replace(' ', '')
    
    # Handle Turkish number format: 1.234,56 → 1234.56
    # If both comma and dot exist, assume dot is thousands separator
    if ',' in cleaned and '.' in cleaned:
        # Turkish format: remove dot (thousands), replace comma (decimal) with dot
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        # Only comma: assume it's decimal separator
        cleaned = cleaned.replace(',', '.')
    # If only dot exists, assume it's decimal (already correct)
    
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Geçersiz sayı formatı: {value}")


def format_price_turkish(price):
    """Format price in Turkish format with ₺ symbol"""
    if price is None:
        return "₺0,00"
    return f"₺{price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

