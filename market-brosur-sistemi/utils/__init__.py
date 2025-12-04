# -*- coding: utf-8 -*-
"""
Utils package - Helper functions and constants
"""

from utils.helpers import (
    safe_join,
    get_current_user,
    login_required,
    admin_required,
    get_sector_path,
    ensure_sector_dirs,
    parse_turkish_float,
    format_price_turkish
)

from utils.constants import (
    SECTORS,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE,
    MAX_EXCEL_SIZE,
    MAX_CSV_SIZE,
    DEFAULT_AI_PRICING,
    DEFAULT_THEME,
    DEFAULT_BACKGROUND_SETTINGS,
    SESSION_LIFETIME,
    UPLOAD_FOLDERS
)

__all__ = [
    # Helpers
    'safe_join',
    'get_current_user',
    'login_required',
    'admin_required',
    'get_sector_path',
    'ensure_sector_dirs',
    'parse_turkish_float',
    'format_price_turkish',
    # Constants
    'SECTORS',
    'ALLOWED_IMAGE_EXTENSIONS',
    'MAX_IMAGE_SIZE',
    'MAX_EXCEL_SIZE',
    'MAX_CSV_SIZE',
    'DEFAULT_AI_PRICING',
    'DEFAULT_THEME',
    'DEFAULT_BACKGROUND_SETTINGS',
    'SESSION_LIFETIME',
    'UPLOAD_FOLDERS'
]

