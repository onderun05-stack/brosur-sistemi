# -*- coding: utf-8 -*-
"""
AI Product Categorization Service

Provides AI-powered product categorization and smart suggestions:
- Auto-categorize products by name
- Suggest prices based on market data
- Learn from user preferences
"""

import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import database


# ============= CATEGORY DEFINITIONS =============

CATEGORY_KEYWORDS = {
    'meyve_sebze': {
        'keywords': ['elma', 'armut', 'portakal', 'muz', 'üzüm', 'domates', 'biber', 'salatalık', 
                     'patates', 'soğan', 'havuç', 'patlıcan', 'kabak', 'marul', 'limon', 'mandalina',
                     'kivi', 'çilek', 'kiraz', 'şeftali', 'kayısı', 'erik', 'nar', 'kavun', 'karpuz'],
        'color': '#22c55e',  # Yeşil
        'icon': '🥬',
        'name': 'Meyve & Sebze'
    },
    'et_balik': {
        'keywords': ['et', 'tavuk', 'balık', 'kıyma', 'biftek', 'sucuk', 'salam', 'sosis',
                     'dana', 'kuzu', 'hindi', 'köfte', 'pirzola', 'kanat', 'but', 'göğüs',
                     'somon', 'levrek', 'hamsi', 'palamut', 'mezgit', 'karidesler'],
        'color': '#ef4444',  # Kırmızı
        'icon': '🥩',
        'name': 'Et & Balık'
    },
    'sut_urunleri': {
        'keywords': ['süt', 'yoğurt', 'peynir', 'tereyağı', 'kaymak', 'ayran', 'kefir',
                     'beyaz peynir', 'kaşar', 'tulum', 'lor', 'çökelek', 'krema'],
        'color': '#3b82f6',  # Mavi
        'icon': '🥛',
        'name': 'Süt Ürünleri'
    },
    'icecekler': {
        'keywords': ['su', 'maden suyu', 'kola', 'fanta', 'sprite', 'meyve suyu', 'çay',
                     'kahve', 'enerji içeceği', 'gazoz', 'şerbet', 'ayran', 'bira', 'şarap'],
        'color': '#06b6d4',  # Cyan
        'icon': '🥤',
        'name': 'İçecekler'
    },
    'temizlik': {
        'keywords': ['deterjan', 'sabun', 'şampuan', 'krem', 'diş macunu', 'tuvalet kağıdı',
                     'çamaşır suyu', 'yumuşatıcı', 'bulaşık', 'cam sil', 'çöp poşeti',
                     'havlu', 'mendil', 'peçete', 'bez', 'sünger', 'fırça'],
        'color': '#8b5cf6',  # Mor
        'icon': '🧴',
        'name': 'Temizlik'
    },
    'atistirmalik': {
        'keywords': ['cips', 'çikolata', 'bisküvi', 'kraker', 'gofret', 'şeker', 'lokum',
                     'kuruyemiş', 'fıstık', 'fındık', 'badem', 'ceviz', 'kuru üzüm',
                     'çekirdek', 'kurabiye', 'kek', 'pasta'],
        'color': '#f59e0b',  # Turuncu
        'icon': '🍫',
        'name': 'Atıştırmalık'
    },
    'baharatlar': {
        'keywords': ['tuz', 'karabiber', 'pul biber', 'kimyon', 'kekik', 'nane', 'tarçın',
                     'zerdeçal', 'zencefil', 'defne', 'sumak', 'köri', 'baharat'],
        'color': '#eab308',  # Sarı
        'icon': '🌶️',
        'name': 'Baharatlar'
    },
    'konserve': {
        'keywords': ['konserve', 'salça', 'turşu', 'zeytin', 'reçel', 'bal', 'pekmez',
                     'ton balığı', 'bezelye', 'mısır', 'fasulye', 'nohut',
                     'yağ', 'ayçiçek', 'zeytinyağı', 'sıvı yağ', 'mısır yağı', 'fındık yağı'],
        'color': '#78716c',  # Gri
        'icon': '🥫',
        'name': 'Konserve'
    },
    'unlu_mamul': {
        'keywords': ['ekmek', 'pide', 'simit', 'poğaça', 'börek', 'makarna', 'pirinç',
                     'bulgur', 'un', 'irmik', 'nişasta', 'galeta'],
        'color': '#d97706',  # Kahverengi
        'icon': '🍞',
        'name': 'Unlu Mamul'
    },
    'dondurulmus': {
        'keywords': ['dondurma', 'donuk', 'frozen', 'pizza', 'patates kızartması',
                     'nugget', 'köfte', 'manti', 'börek', 'pide'],
        'color': '#0ea5e9',  # Açık mavi
        'icon': '🧊',
        'name': 'Dondurulmuş'
    },
    'bebek': {
        'keywords': ['bebek bezi', 'bebek maması', 'biberon', 'emzik', 'bebek pudrası',
                     'bebek şampuanı', 'bebek kremi', 'bebek bisküvisi'],
        'color': '#ec4899',  # Pembe
        'icon': '👶',
        'name': 'Bebek Ürünleri'
    },
    'diger': {
        'keywords': [],
        'color': '#6b7280',  # Gri
        'icon': '📦',
        'name': 'Diğer'
    }
}


class AIProductCategorizer:
    """
    AI-powered product categorization.
    """
    
    def __init__(self):
        self.categories = CATEGORY_KEYWORDS
        self.user_overrides = {}  # User-specific category overrides
    
    def categorize(self, product_name: str) -> Dict[str, Any]:
        """
        Categorize a product by its name.
        
        Args:
            product_name: Product name to categorize
        
        Returns:
            dict with category, color, icon, confidence
        """
        if not product_name:
            return self._get_default_category()
        
        name_lower = product_name.lower()
        
        # Check each category
        best_match = None
        best_score = 0
        
        for category_id, category_data in self.categories.items():
            score = 0
            
            for keyword in category_data['keywords']:
                if keyword in name_lower:
                    # Exact word match scores higher
                    if re.search(rf'\b{keyword}\b', name_lower):
                        score += 2
                    else:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = category_id
        
        # Determine confidence
        if best_score >= 3:
            confidence = 'high'
        elif best_score >= 1:
            confidence = 'medium'
        else:
            confidence = 'low'
            best_match = 'diger'
        
        category = self.categories.get(best_match, self.categories['diger'])
        
        return {
            'category_id': best_match,
            'category_name': category['name'],
            'color': category['color'],
            'icon': category['icon'],
            'confidence': confidence,
            'score': best_score
        }
    
    def categorize_batch(self, products: List[Dict]) -> List[Dict]:
        """
        Categorize multiple products.
        
        Args:
            products: List of products with 'name' field
        
        Returns:
            Products with category info added
        """
        for product in products:
            category_info = self.categorize(product.get('name', ''))
            product['category'] = category_info['category_name']
            product['category_color'] = category_info['color']
            product['category_icon'] = category_info['icon']
        
        return products
    
    def suggest_category(self, product_name: str) -> List[Dict]:
        """
        Suggest multiple possible categories for a product.
        
        Args:
            product_name: Product name
        
        Returns:
            List of suggested categories with scores
        """
        if not product_name:
            return [self._get_default_category()]
        
        name_lower = product_name.lower()
        suggestions = []
        
        for category_id, category_data in self.categories.items():
            if category_id == 'diger':
                continue
                
            score = 0
            matched_keywords = []
            
            for keyword in category_data['keywords']:
                if keyword in name_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                suggestions.append({
                    'category_id': category_id,
                    'category_name': category_data['name'],
                    'color': category_data['color'],
                    'icon': category_data['icon'],
                    'score': score,
                    'matched_keywords': matched_keywords
                })
        
        # Sort by score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        # Always include "Diğer" as last option
        suggestions.append({
            'category_id': 'diger',
            'category_name': 'Diğer',
            'color': '#6b7280',
            'icon': '📦',
            'score': 0,
            'matched_keywords': []
        })
        
        return suggestions[:5]  # Return top 5
    
    def _get_default_category(self) -> Dict:
        """Get default category"""
        return {
            'category_id': 'diger',
            'category_name': 'Diğer',
            'color': '#6b7280',
            'icon': '📦',
            'confidence': 'low',
            'score': 0
        }
    
    def get_category_colors(self) -> Dict[str, str]:
        """Get all category colors for CSS"""
        return {
            cat_id: cat_data['color']
            for cat_id, cat_data in self.categories.items()
        }
    
    def get_all_categories(self) -> List[Dict]:
        """Get all available categories"""
        return [
            {
                'id': cat_id,
                'name': cat_data['name'],
                'color': cat_data['color'],
                'icon': cat_data['icon']
            }
            for cat_id, cat_data in self.categories.items()
        ]


class SmartPriceSuggester:
    """
    Smart price suggestion based on market data.
    """
    
    def __init__(self):
        pass
    
    def suggest_price(self, product_name: str, category: str = None,
                      market_price: float = None) -> Dict[str, Any]:
        """
        Suggest a price for a product.
        
        Args:
            product_name: Product name
            category: Product category
            market_price: Current market price (from API)
        
        Returns:
            Price suggestion with reasoning
        """
        suggestion = {
            'suggested_price': None,
            'min_price': None,
            'max_price': None,
            'discount_suggestion': None,
            'reasoning': '',
            'tips': []
        }
        
        if market_price:
            # Base suggestions on market price
            suggestion['suggested_price'] = round(market_price * 0.95, 2)  # 5% below market
            suggestion['min_price'] = round(market_price * 0.85, 2)  # 15% below market
            suggestion['max_price'] = round(market_price * 1.05, 2)  # 5% above market
            suggestion['discount_suggestion'] = round((1 - suggestion['suggested_price'] / market_price) * 100, 1)
            suggestion['reasoning'] = f'Piyasa fiyatı ₺{market_price:.2f}. Rekabetçi fiyat için %5 indirim önerilir.'
            
            suggestion['tips'] = [
                f'Piyasa ortalaması: ₺{market_price:.2f}',
                'Önerilen fiyat rekabetçi bir avantaj sağlar',
                'Kampanya dönemlerinde %10-15 indirim uygulayabilirsiniz'
            ]
        else:
            # No market price available
            suggestion['reasoning'] = 'Piyasa fiyatı bulunamadı. Kategori bazlı öneri yapılıyor.'
            
            # Category-based suggestions
            category_ranges = {
                'meyve_sebze': (2, 50),
                'et_balik': (30, 500),
                'sut_urunleri': (5, 100),
                'icecekler': (2, 50),
                'temizlik': (10, 200),
                'atistirmalik': (5, 100),
                'baharatlar': (5, 50),
                'konserve': (10, 100),
                'unlu_mamul': (5, 100),
                'dondurulmus': (20, 200),
                'bebek': (30, 500),
                'diger': (5, 200)
            }
            
            if category and category in category_ranges:
                min_p, max_p = category_ranges[category]
                suggestion['min_price'] = min_p
                suggestion['max_price'] = max_p
                suggestion['suggested_price'] = round((min_p + max_p) / 2, 2)
                suggestion['tips'] = [
                    f'Bu kategoride fiyatlar genelde ₺{min_p} - ₺{max_p} arasında',
                    'Marka ve kaliteye göre ayarlama yapabilirsiniz'
                ]
        
        return suggestion
    
    def compare_with_market(self, product_price: float, market_price: float) -> Dict[str, Any]:
        """
        Compare product price with market price.
        
        Args:
            product_price: Your price
            market_price: Market/API price
        
        Returns:
            Comparison result with Ghost-style message
        """
        if not market_price or market_price <= 0:
            return {
                'comparison': 'unknown',
                'difference_percent': 0,
                'message': 'Piyasa fiyatı bulunamadı',
                'ghost_message': '🔍 Bu ürünün piyasa fiyatını bulamadım...'
            }
        
        diff = product_price - market_price
        diff_percent = (diff / market_price) * 100
        
        if diff_percent <= -20:
            comparison = 'very_cheap'
            message = 'Çok uygun fiyat!'
            ghost = f'✨ Vay! Bu fiyat piyasadan %{abs(diff_percent):.0f} daha uygun! Müşteriler bayılacak!'
        elif diff_percent <= -10:
            comparison = 'cheap'
            message = 'Uygun fiyat'
            ghost = f'😊 Güzel fiyat! Piyasa ortalaması ₺{market_price:.2f}, sen ₺{product_price:.2f} veriyorsun.'
        elif diff_percent <= 10:
            comparison = 'fair'
            message = 'Piyasa fiyatına yakın'
            ghost = f'👍 Fiyatın piyasa ile uyumlu. Piyasa ortalaması ₺{market_price:.2f}'
        elif diff_percent <= 20:
            comparison = 'expensive'
            message = 'Biraz pahalı'
            ghost = f'🤔 Hmm, bu fiyat piyasadan %{diff_percent:.0f} yüksek. İndirim yapmayı düşünebilirsin.'
        else:
            comparison = 'very_expensive'
            message = 'Piyasaya göre yüksek'
            ghost = f'😅 Bu fiyat biraz yüksek kalmış! Piyasa ₺{market_price:.2f}, sen ₺{product_price:.2f} istemişsin.'
        
        return {
            'comparison': comparison,
            'product_price': product_price,
            'market_price': market_price,
            'difference': round(diff, 2),
            'difference_percent': round(diff_percent, 1),
            'message': message,
            'ghost_message': ghost
        }


class UserPreferenceLearner:
    """
    Learn from user preferences for personalized suggestions.
    """
    
    def __init__(self):
        self.init_table()
    
    def init_table(self):
        """Create user preferences table"""
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        preference_type TEXT NOT NULL,
                        preference_key TEXT NOT NULL,
                        preference_value TEXT NOT NULL,
                        count INTEGER DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, preference_type, preference_key)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to init preferences table: {e}")
    
    def learn(self, user_id: int, preference_type: str, 
              preference_key: str, preference_value: str):
        """
        Record a user preference.
        
        Args:
            user_id: User ID
            preference_type: Type (layout, font, color, category, etc.)
            preference_key: Key (e.g., 'favorite_layout')
            preference_value: Value (e.g., 'grid')
        """
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_preferences (user_id, preference_type, preference_key, preference_value, count)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(user_id, preference_type, preference_key) DO UPDATE SET
                        preference_value = excluded.preference_value,
                        count = count + 1,
                        updated_at = CURRENT_TIMESTAMP
                ''', (user_id, preference_type, preference_key, preference_value))
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to record preference: {e}")
    
    def get_preference(self, user_id: int, preference_type: str, 
                       preference_key: str) -> Optional[str]:
        """Get a user preference"""
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT preference_value FROM user_preferences
                    WHERE user_id = ? AND preference_type = ? AND preference_key = ?
                ''', (user_id, preference_type, preference_key))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logging.error(f"Failed to get preference: {e}")
            return None
    
    def get_top_preferences(self, user_id: int, preference_type: str, 
                            limit: int = 5) -> List[Dict]:
        """Get user's most used preferences of a type"""
        try:
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT preference_key, preference_value, count
                    FROM user_preferences
                    WHERE user_id = ? AND preference_type = ?
                    ORDER BY count DESC
                    LIMIT ?
                ''', (user_id, preference_type, limit))
                
                return [
                    {'key': row[0], 'value': row[1], 'count': row[2]}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Failed to get preferences: {e}")
            return []


# Global instances
categorizer = AIProductCategorizer()
price_suggester = SmartPriceSuggester()
preference_learner = UserPreferenceLearner()


# ============= SECTOR WHITELIST GROUPING =============

def get_sector_group(product_name: str, sector: str = 'supermarket') -> str:
    """
    Get product group from sector whitelist.
    Uses AI categorization then maps to valid sector groups.
    
    Args:
        product_name: Product name to categorize
        sector: User's sector (supermarket, giyim, teknoloji, etc.)
    
    Returns:
        str: Valid group from sector whitelist or 'Genel'
    """
    from utils.constants import get_product_groups_for_sector, validate_and_fix_product_group
    
    # Get AI categorization
    ai_result = categorizer.categorize(product_name)
    ai_category = ai_result.get('category_name', 'Diğer')
    
    # Map AI category to sector whitelist
    # AI uses: Meyve & Sebze, Et & Balık, Süt Ürünleri, İçecekler, Temizlik, Atıştırmalık, etc.
    # Whitelist uses: Gıda, İçecek, Et & Tavuk, Meyve & Sebze, Temizlik, etc.
    
    category_mapping = {
        'supermarket': {
            'Meyve & Sebze': 'Meyve & Sebze',
            'Et & Balık': 'Et & Tavuk',
            'Süt Ürünleri': 'Gıda',
            'İçecekler': 'İçecek',
            'Temizlik': 'Temizlik',
            'Atıştırmalık': 'Atıştırmalık',
            'Baharatlar': 'Gıda',
            'Konserve': 'Gıda',
            'Unlu Mamul': 'Gıda',
            'Dondurulmuş': 'Dondurulmuş',
            'Bebek Ürünleri': 'Kişisel Bakım',
            'Diğer': 'Genel'
        },
        'giyim': {
            'Giyim': 'Giyim',
            'Ayakkabı': 'Ayakkabı',
            'Aksesuar': 'Aksesuar',
            'Diğer': 'Genel'
        },
        'teknoloji': {
            'Telefon': 'Telefon',
            'Bilgisayar': 'Bilgisayar & Tablet',
            'TV': 'TV & Ses',
            'Diğer': 'Genel'
        },
        'kozmetik': {
            'Temizlik': 'Kişisel Bakım',
            'Parfüm': 'Parfüm',
            'Diğer': 'Genel'
        },
        'restoran': {
            'Et & Balık': 'Yemek',
            'İçecekler': 'İçecek',
            'Atıştırmalık': 'Tatlı',
            'Diğer': 'Genel'
        }
    }
    
    # Get mapping for sector
    sector_map = category_mapping.get(sector, {})
    mapped_group = sector_map.get(ai_category, 'Genel')
    
    # Validate against whitelist
    valid_group = validate_and_fix_product_group(mapped_group, sector)
    
    return valid_group


# ============= API FUNCTIONS =============

def categorize_product(product_name: str) -> Dict:
    """Categorize a product"""
    return categorizer.categorize(product_name)


def categorize_product_for_sector(product_name: str, sector: str = 'supermarket') -> Dict:
    """
    Categorize a product for a specific sector whitelist.
    
    Returns:
        dict with group (whitelist validated), ai_category, confidence
    """
    ai_result = categorizer.categorize(product_name)
    valid_group = get_sector_group(product_name, sector)
    
    return {
        'group': valid_group,
        'ai_category': ai_result.get('category_name'),
        'confidence': ai_result.get('confidence'),
        'score': ai_result.get('score')
    }


def categorize_products(products: List[Dict]) -> List[Dict]:
    """Categorize multiple products"""
    return categorizer.categorize_batch(products)


def suggest_categories(product_name: str) -> List[Dict]:
    """Get category suggestions"""
    return categorizer.suggest_category(product_name)


def get_all_categories() -> List[Dict]:
    """Get all categories"""
    return categorizer.get_all_categories()


def get_category_colors() -> Dict[str, str]:
    """Get category colors"""
    return categorizer.get_category_colors()


def suggest_price(product_name: str, category: str = None,
                  market_price: float = None) -> Dict:
    """Get price suggestion"""
    return price_suggester.suggest_price(product_name, category, market_price)


def compare_prices(product_price: float, market_price: float) -> Dict:
    """Compare with market price"""
    return price_suggester.compare_with_market(product_price, market_price)


def learn_preference(user_id: int, pref_type: str, key: str, value: str):
    """Learn user preference"""
    preference_learner.learn(user_id, pref_type, key, value)


def get_user_preferences(user_id: int, pref_type: str, limit: int = 5) -> List[Dict]:
    """Get user preferences"""
    return preference_learner.get_top_preferences(user_id, pref_type, limit)

