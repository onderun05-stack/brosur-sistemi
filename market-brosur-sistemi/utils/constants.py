# -*- coding: utf-8 -*-
"""
Constants and configuration values for the application.
"""

# Sector definitions used throughout the application
SECTORS = {
    'supermarket': 'Süpermarket',
    'giyim': 'Giyim',
    'teknoloji': 'Teknoloji',
    'kozmetik': 'Kozmetik',
    'evyasam': 'Ev & Yaşam',
    'elsanatlari': 'El Sanatları',
    'restoran': 'Restoran',
    'diger': 'Diğer'
}

# Product groups for each sector
PRODUCT_GROUPS = {
    'supermarket': ['Gıda', 'İçecek', 'Et & Tavuk', 'Meyve & Sebze', 'Temizlik', 'Kişisel Bakım', 'Atıştırmalık', 'Dondurulmuş', 'Şarküteri', 'Genel'],
    'giyim': ['Giyim', 'Ayakkabı', 'Aksesuar', 'Genel'],
    'teknoloji': ['Telefon', 'Bilgisayar & Tablet', 'TV & Ses', 'Beyaz Eşya', 'Küçük Ev Aletleri', 'Oyun', 'Genel'],
    'kozmetik': ['Parfüm', 'Kişisel Bakım', 'Genel'],
    'evyasam': ['Mobilya', 'Dekorasyon', 'Bahçe', 'Genel'],
    'elsanatlari': ['Takı', 'Tekstil', 'Seramik', 'Ahşap', 'Genel'],
    'restoran': ['Yemek', 'İçecek', 'Tatlı', 'Aperatif', 'Genel'],
    'diger': ['Genel']
}


def get_all_sectors():
    """Get list of all sector keys"""
    return list(SECTORS.keys())


def get_product_groups_for_sector(sector):
    """Get product groups for a specific sector"""
    return PRODUCT_GROUPS.get(sector, PRODUCT_GROUPS.get('diger', ['Genel']))


def get_all_product_groups():
    """Get ALL product groups from ALL sectors (flat list, unique)"""
    all_groups = set()
    for groups in PRODUCT_GROUPS.values():
        all_groups.update(groups)
    return list(all_groups)


def is_valid_product_group(group, sector=None):
    """
    Check if a product group is valid (exists in our list).
    
    Args:
        group: Product group string to validate
        sector: Optional sector to check against (if None, checks all sectors)
    
    Returns:
        bool: True if group exists in our list
    """
    if not group or not group.strip():
        return False
    
    group = group.strip()
    
    if sector:
        # Check in specific sector
        valid_groups = get_product_groups_for_sector(sector)
        return group in valid_groups
    else:
        # Check in all sectors
        all_groups = get_all_product_groups()
        return group in all_groups


def validate_and_fix_product_group(group, sector='supermarket'):
    """
    Validate product group and return valid group or 'Genel'.
    
    BİZİM LİSTEMİZDE varsa → O grup döner
    BİZİM LİSTEMİZDE yoksa → 'Genel' döner
    
    Args:
        group: Product group from API or user input
        sector: User's sector
    
    Returns:
        str: Valid product group (original or 'Genel')
    """
    if not group or not group.strip():
        return 'Genel'
    
    group = group.strip()
    
    # Check if group exists in the sector's valid groups
    valid_groups = get_product_groups_for_sector(sector)
    
    if group in valid_groups:
        return group  # ✅ Bizim listemizde var
    
    # Try case-insensitive match
    group_lower = group.lower()
    for valid_group in valid_groups:
        if valid_group.lower() == group_lower:
            return valid_group  # ✅ Büyük/küçük harf farkı
    
    # ❌ Bizim listemizde yok → Genel
    return 'Genel'


# API category to product group mapping
API_CATEGORY_MAPPING = {
    # Supermarket categories
    'gida': 'Gıda',
    'icecek': 'İçecek',
    'sut': 'Süt Ürünleri',
    'et': 'Et & Tavuk',
    'meyve': 'Meyve & Sebze',
    'sebze': 'Meyve & Sebze',
    'firin': 'Fırın',
    'temizlik': 'Temizlik',
    'kisisel': 'Kişisel Bakım',
    'atistirmalik': 'Atıştırmalık',
    'dondurma': 'Dondurma',
    'sarkuteri': 'Şarküteri',
    'bebek': 'Bebek',
    # Generic
    'genel': 'Genel',
    'diger': 'Genel'
}


def map_api_category_to_product_group(api_category, sector='supermarket'):
    """
    Map API category to sector-specific product group.
    
    Args:
        api_category: Category string from API response
        sector: Current sector (default: supermarket)
    
    Returns:
        str: Mapped product group name
    """
    if not api_category:
        return 'Genel'
    
    # Normalize category
    category_lower = api_category.lower().strip()
    
    # Try direct mapping
    if category_lower in API_CATEGORY_MAPPING:
        mapped = API_CATEGORY_MAPPING[category_lower]
        # Check if mapped group exists in sector's groups
        sector_groups = get_product_groups_for_sector(sector)
        if mapped in sector_groups:
            return mapped
    
    # Try partial match
    for key, value in API_CATEGORY_MAPPING.items():
        if key in category_lower or category_lower in key:
            sector_groups = get_product_groups_for_sector(sector)
            if value in sector_groups:
                return value
    
    # Default to 'Genel'
    return 'Genel'

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# File size limits
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_EXCEL_SIZE = 5 * 1024 * 1024   # 5MB
MAX_CSV_SIZE = 5 * 1024 * 1024     # 5MB

# Default pricing for AI services
DEFAULT_AI_PRICING = {
    'slogan': 5.0,
    'image': 10.0,
    'template': 15.0,
    'background': 8.0,
    'gpt4o_price': 10,
    'gpt4o_mini_price': 2,
    'dalle3_price': 50,
    'default_credits': 100
}

# Default theme settings
DEFAULT_THEME = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'background': '#fdf5e6'
}

# Default background settings
DEFAULT_BACKGROUND_SETTINGS = {
    'login': {
        'type': 'gradient',
        'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    'dashboard': {
        'type': 'gradient',
        'gradient': 'linear-gradient(135deg, #fdf5e6 0%, #faebd7 25%, #ffe4c4 50%, #f5deb3 100%)'
    }
}

# Session configuration
SESSION_LIFETIME = 86400  # 24 hours in seconds

# Upload folder paths
UPLOAD_FOLDERS = {
    'admin': 'static/uploads/admin',
    'pending': 'static/uploads/pending',
    'customers': 'static/uploads/customers',
    'logos': 'static/uploads/logos',
    'backgrounds': 'static/uploads/backgrounds',
    'exports': 'static/exports',
    'temp': 'static/temp'
}

