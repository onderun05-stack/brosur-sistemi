# -*- coding: utf-8 -*-
"""
Ghost Assistant Service (Hayalet Asistan) - AI-powered design assistant.

The Ghost Assistant is a 64x64 cloud-like 3D model with a lightning bolt icon
that constantly analyzes user actions and offers proactive suggestions.

Features:
- Real-time design analysis
- Quality scoring for layouts
- Product placement suggestions
- Price comparison insights
- Auto-layout recommendations
- Theme and color suggestions
- Workflow tracking (Shadow Planner)
- User behavior learning
- Multi-AI module coordination
- Product name normalization
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import random

# ============= NAME NORMALIZER CONFIG =============

# Gereksiz kelimeler - temizlenecek
UNNECESSARY_WORDS = [
    'yeni', 'büyük boy', 'küçük boy', 'orta boy', 'plastik şişe', 
    'cam şişe', 'avantaj paketi', 'avantaj', 'ekstra', 'taptaze', 
    'süper', 'kampanya', 'kampanyalı', 'indirimli', 'özel', 'fırsat',
    'ekonomik', 'mega', 'maksi', 'mini', 'jumbo', 'dev', 'xl', 'xxl',
    'family', 'aile', 'aile boyu', 'aile paketi', 'paket', 'kutu',
    'poşet', 'torba', 'kavanoz', 'teneke', 'koli', 'set', 'tanımı',
    'premium', 'gold', 'silver', 'platin', 'klasik', 'special',
    'limited', 'edition', 'seri', 'serisi', 'koleksiyon', 'yenilendi',
    'geliştirilmiş', 'formül', 'konsantre', 'ultra', 'max', 'plus',
    'pro', 'lite', 'zero', 'light', 'free', 'doğal', 'organik',
    'taze', 'ev yapımı', 'anne eli', 'geleneksel', 'otantik'
]

# Kısaltma kuralları
ABBREVIATIONS = {
    'çikolatalı': 'çik.',
    'çikolata': 'çik.',
    'fındıklı': 'fınd.',
    'fındık': 'fınd.',
    'kakaolu': 'kak.',
    'kakao': 'kak.',
    'kreması': 'krm.',
    'krema': 'krm.',
    'deterjan': 'det.',
    'şampuan': 'şamp.',
    'yumuşatıcı': 'yumuş.',
    'bulaşık': 'bul.',
    'çamaşır': 'çam.',
    'beyazlatıcı': 'byz.',
    'temizleyici': 'tmz.',
    'bisküvi': 'bsk.',
    'gofret': 'gof.',
    'makarna': 'mak.',
    'pirinç': 'prn.',
    'bulgur': 'blg.',
    'mercimek': 'mrc.',
    'nohut': 'nht.',
    'fasulye': 'fas.',
    'zeytinyağı': 'zyt.yağ',
    'ayçiçek': 'ayç.',
    'margarin': 'mrg.',
    'tereyağı': 'tyağ.',
    'peynir': 'pyn.',
    'yoğurt': 'yğrt.',
    'süt': 'süt',
    'meyve': 'myv.',
    'sebze': 'sbz.',
    'dondurma': 'dond.',
    'çorba': 'çrb.',
    'konserve': 'kns.',
    'salça': 'slç.',
    'reçel': 'rçl.',
    'bal': 'bal',
    'kahve': 'khv.',
    'çay': 'çay',
    'maden suyu': 'm.suyu',
    'gazlı içecek': 'gaz.iç.',
    'meyve suyu': 'myv.su',
    'limonata': 'lim.',
    'aromalı': 'arm.',
    'tatlandırıcı': 'tatlnd.',
    'tahin': 'thn.',
    'helva': 'hlv.',
    'lokum': 'lkm.',
    'baklava': 'bklv.'
}

# Gramaj standardizasyonu
WEIGHT_PATTERNS = {
    r'(\d+)\s*gr(?:am)?': r'\1g',
    r'(\d+)\s*kg': r'\1kg',
    r'(\d+)\s*ml': r'\1ml',
    r'(\d+)\s*lt?': r'\1L',
    r'(\d+)\s*adet': r'\1ad',
    r'(\d+)\s*\'?l[iı]': r'\1li',
    r'(\d+)\s*x\s*(\d+)': r'\1x\2'
}

# Ghost personality messages
GHOST_GREETINGS = [
    "Merhaba! Ben Hayalet, tasarım asistanınızım. Size nasıl yardımcı olabilirim?",
    "Selam! Broşürünüzü birlikte harika yapalım!",
    "Hoş geldiniz! Bugün nasıl bir broşür oluşturacağız?",
]

GHOST_TIPS = {
    'empty_page': "Bu sayfa boş görünüyor. Ürün eklemek ister misiniz?",
    'crowded_page': "Bu sayfa biraz kalabalık. Bazı ürünleri başka sayfaya taşıyabilirsiniz.",
    'unbalanced': "Sayfa dengesi bozuk görünüyor. Otomatik düzenleme yapayım mı?",
    'low_quality_image': "Bu ürün görseli düşük çözünürlüklü. Yeni versiyon üreteyim mi?",
    'price_insight': "Bu ürün piyasa ortalamasının altında! Müşterileriniz için harika bir fırsat.",
    'parking_full': "Park alanında bekleyen ürünler var. Yerleştirmek ister misiniz?",
    'no_slogan': "Bu sayfada slogan yok. AI ile bir slogan oluşturayım mı?",
    'theme_mismatch': "Seçtiğiniz tema bu ürünlerle uyumsuz görünüyor.",
    'idle_user': "Bir yerde mi takıldınız? Size yardımcı olabilirim!",
}

# Design quality weights
QUALITY_WEIGHTS = {
    'balance': 0.25,      # Page balance
    'spacing': 0.20,      # Product spacing
    'alignment': 0.15,    # Product alignment
    'image_quality': 0.20, # Image quality average
    'readability': 0.10,  # Text readability
    'theme_consistency': 0.10  # Theme consistency
}

# Shadow Planner task types
TASK_TYPES = [
    'upload_excel',
    'search_images',
    'arrange_products',
    'generate_slogan',
    'select_theme',
    'export_brochure',
    'review_design'
]


# ============= NAME NORMALIZER CLASS =============

class NameNormalizer:
    """
    Ürün adı normalizasyon ve kısaltma motoru.
    Marka + Ürün + Gramaj formatına çevirir ve max 22-26 karakter kısaltır.
    """
    
    MAX_LENGTH = 26
    MIN_LENGTH = 22
    
    def __init__(self):
        self.unnecessary_words = [w.lower() for w in UNNECESSARY_WORDS]
        self.abbreviations = {k.lower(): v for k, v in ABBREVIATIONS.items()}
        self.weight_patterns = WEIGHT_PATTERNS
    
    def normalize(self, product_name: str, max_length: int = None) -> str:
        """
        Ürün adını normalize et ve kısalt.
        
        Args:
            product_name: Orijinal ürün adı
            max_length: Maksimum karakter sayısı (default: 26)
        
        Returns:
            str: Normalize edilmiş ürün adı
        
        Örnek:
            "Torku Banada Kakaolu Fındık Kreması 1000 Gr Plastik Şişe" 
            → "Torku Banada 1000g"
        """
        if not product_name:
            return product_name
        
        max_len = max_length or self.MAX_LENGTH
        
        # Adım 1: Temel temizlik
        name = self._basic_cleanup(product_name)
        
        # Adım 2: Gramaj standardizasyonu
        name = self._standardize_weight(name)
        
        # Adım 3: Gereksiz kelimeleri temizle
        name = self._remove_unnecessary_words(name)
        
        # Adım 4: Parçalara ayır (Marka, Ürün, Gramaj)
        brand, product, weight = self._extract_components(name)
        
        # Adım 5: Birleştir ve kısalt
        result = self._combine_and_shorten(brand, product, weight, max_len)
        
        return result
    
    def _basic_cleanup(self, name: str) -> str:
        """Temel temizlik: fazla boşluklar, özel karakterler"""
        # Birden fazla boşluğu tek boşluğa çevir
        name = re.sub(r'\s+', ' ', name)
        # Başındaki ve sonundaki boşlukları temizle
        name = name.strip()
        # Özel karakterleri temizle (-, _, /, vb.)
        name = re.sub(r'[-_/\\|]+', ' ', name)
        return name
    
    def _standardize_weight(self, name: str) -> str:
        """Gramaj formatını standartlaştır"""
        for pattern, replacement in self.weight_patterns.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        return name
    
    def _remove_unnecessary_words(self, name: str) -> str:
        """Gereksiz kelimeleri temizle"""
        words = name.split()
        cleaned_words = []
        
        for word in words:
            word_lower = word.lower()
            # Tek kelime kontrolü
            if word_lower not in self.unnecessary_words:
                # Çoklu kelime kontrolü (örn: "büyük boy")
                is_unnecessary = False
                for unnecessary in self.unnecessary_words:
                    if ' ' in unnecessary:
                        # Bu çoklu kelime ise name içinde tam arama yap
                        continue
                    if word_lower == unnecessary:
                        is_unnecessary = True
                        break
                
                if not is_unnecessary:
                    cleaned_words.append(word)
        
        # Çoklu kelime gruplarını temizle
        result = ' '.join(cleaned_words)
        for unnecessary in self.unnecessary_words:
            if ' ' in unnecessary:
                result = re.sub(
                    r'\b' + re.escape(unnecessary) + r'\b', 
                    '', 
                    result, 
                    flags=re.IGNORECASE
                )
        
        return ' '.join(result.split())  # Boşlukları düzelt
    
    def _extract_components(self, name: str) -> Tuple[str, str, str]:
        """
        Marka, ürün adı ve gramajı ayır.
        
        Returns:
            (marka, ürün_adı, gramaj)
        """
        # Gramaj pattern'i
        weight_regex = r'(\d+(?:x\d+)?(?:g|kg|ml|L|lt|li|ad))'
        
        # Gramajı bul ve ayır
        weight_match = re.search(weight_regex, name, re.IGNORECASE)
        weight = weight_match.group(1) if weight_match else ''
        
        # Gramajı çıkar
        name_without_weight = re.sub(weight_regex, '', name, flags=re.IGNORECASE).strip()
        
        # İlk kelime genellikle marka
        parts = name_without_weight.split()
        if len(parts) >= 2:
            brand = parts[0]
            product = ' '.join(parts[1:])
        elif len(parts) == 1:
            brand = parts[0]
            product = ''
        else:
            brand = ''
            product = ''
        
        return brand, product, weight
    
    def _combine_and_shorten(self, brand: str, product: str, weight: str, max_len: int) -> str:
        """Parçaları birleştir ve gerekirse kısalt"""
        # Önce tam hali dene
        full_name = f"{brand} {product} {weight}".strip()
        full_name = ' '.join(full_name.split())  # Ekstra boşlukları temizle
        
        if len(full_name) <= max_len:
            return full_name
        
        # Kısaltma gerekiyor
        # Adım 1: Ürün adında kısaltmalar uygula
        shortened_product = self._apply_abbreviations(product)
        
        short_name = f"{brand} {shortened_product} {weight}".strip()
        short_name = ' '.join(short_name.split())
        
        if len(short_name) <= max_len:
            return short_name
        
        # Adım 2: Ürün adını kırp
        available_len = max_len - len(brand) - len(weight) - 2  # 2 boşluk için
        if available_len > 3:
            truncated_product = shortened_product[:available_len-1] + '.'
        else:
            truncated_product = ''
        
        final_name = f"{brand} {truncated_product} {weight}".strip()
        final_name = ' '.join(final_name.split())
        
        # Son kontrol
        if len(final_name) > max_len:
            return final_name[:max_len-1] + '.'
        
        return final_name
    
    def _apply_abbreviations(self, text: str) -> str:
        """Kısaltmaları uygula"""
        result = text
        for word, abbr in self.abbreviations.items():
            result = re.sub(
                r'\b' + re.escape(word) + r'\b', 
                abbr, 
                result, 
                flags=re.IGNORECASE
            )
        return result
    
    def batch_normalize(self, product_names: List[str]) -> List[Dict[str, str]]:
        """
        Toplu ürün adı normalizasyonu.
        
        Args:
            product_names: Ürün adları listesi
        
        Returns:
            List[Dict]: Her ürün için {original, normalized, shortened} dict listesi
        """
        results = []
        for name in product_names:
            normalized = self.normalize(name)
            results.append({
                'original': name,
                'normalized': normalized,
                'shortened': len(normalized) < len(name),
                'char_count': len(normalized)
            })
        return results
    
    def get_normalization_stats(self, product_names: List[str]) -> Dict:
        """
        Normalizasyon istatistikleri.
        
        Args:
            product_names: Ürün adları listesi
        
        Returns:
            dict: İstatistikler
        """
        results = self.batch_normalize(product_names)
        
        total = len(results)
        shortened = sum(1 for r in results if r['shortened'])
        avg_original = sum(len(name) for name in product_names) / total if total > 0 else 0
        avg_normalized = sum(r['char_count'] for r in results) / total if total > 0 else 0
        
        return {
            'total_products': total,
            'shortened_count': shortened,
            'avg_original_length': round(avg_original, 1),
            'avg_normalized_length': round(avg_normalized, 1),
            'space_saved_percent': round((1 - avg_normalized / avg_original) * 100, 1) if avg_original > 0 else 0
        }


# Singleton instance
name_normalizer = NameNormalizer()


class GhostAssistant:
    """Ghost Assistant singleton for managing AI suggestions"""
    
    def __init__(self):
        self.session_data = {}
        self.suggestions_log = []
        self.user_preferences = {}
        self._name_normalizer = name_normalizer
    
    def get_greeting(self, user_name: str = None) -> str:
        """Get a personalized greeting"""
        greeting = random.choice(GHOST_GREETINGS)
        if user_name:
            greeting = greeting.replace("Merhaba!", f"Merhaba {user_name}!")
        return greeting
    
    def normalize_product_name(self, product_name: str, max_length: int = None) -> str:
        """
        Ürün adını normalize et ve kısalt.
        
        Args:
            product_name: Orijinal ürün adı
            max_length: Maksimum karakter sayısı (default: 26)
        
        Returns:
            str: Normalize edilmiş ürün adı
        """
        return self._name_normalizer.normalize(product_name, max_length)
    
    def batch_normalize_names(self, product_names: List[str]) -> List[Dict]:
        """Toplu ürün adı normalizasyonu"""
        return self._name_normalizer.batch_normalize(product_names)
    
    def analyze_page(self, page_data: Dict) -> Dict:
        """
        Analyze a brochure page and return suggestions.
        Detaylı kalite skoru ve ürün bazlı uyarılar içerir.
        
        Args:
            page_data: Page dictionary with products, layout, etc.
        
        Returns:
            dict: Analysis results with score, suggestions and product warnings
        """
        suggestions = []
        warnings = []
        product_warnings = []  # Ürün bazlı uyarılar (Madde 3)
        score = 100
        score_breakdown = {}  # Skor detayları
        
        products = page_data.get('products', [])
        layout = page_data.get('layout', 'grid_4x4')
        locked = page_data.get('locked', False)
        page_size = page_data.get('page_size', {'width': 595, 'height': 842})
        
        # ===== TEMEL KONTROLLER =====
        
        # Check if page is empty
        if len(products) == 0:
            suggestions.append({
                'type': 'empty_page',
                'message': GHOST_TIPS['empty_page'],
                'action': 'add_products',
                'priority': 'medium'
            })
            score -= 20
            score_breakdown['empty_page'] = -20
        
        # Check if page is crowded (-15)
        max_products = self._get_max_products_for_layout(layout)
        if len(products) > max_products * 1.2:
            warnings.append({
                'type': 'crowded_page',
                'message': GHOST_TIPS['crowded_page'],
                'action': 'redistribute',
                'priority': 'high'
            })
            score -= 15
            score_breakdown['crowded_page'] = -15
        
        # Check product balance (-20 max)
        if len(products) > 2:
            balance_score = self._calculate_balance(products, page_size)
            if balance_score < 0.6:
                suggestions.append({
                    'type': 'unbalanced',
                    'message': GHOST_TIPS['unbalanced'],
                    'action': 'auto_arrange',
                    'priority': 'medium'
                })
                penalty = int((1 - balance_score) * 20)
                score -= penalty
                score_breakdown['layout_unbalanced'] = -penalty
        
        # ===== ÜRÜN BAZLI ANALİZ (Madde 3 & 8) =====
        
        low_quality_count = 0
        long_name_count = 0
        clean_name_count = 0
        
        for product in products:
            product_id = product.get('id') or product.get('product_id')
            product_name = product.get('name', '')
            
            # Ürün adı uzunluğu kontrolü (-10)
            if len(product_name) > 30:
                long_name_count += 1
                product_warnings.append({
                    'product_id': product_id,
                    'type': 'long_name',
                    'message': f"Ürün adı çok uzun ({len(product_name)} karakter). Kısaltmamı ister misin?",
                    'severity': 'warning',
                    'suggestion': self.normalize_product_name(product_name)
                })
            elif len(product_name) <= 26:
                clean_name_count += 1
            
            # Görsel kalitesi kontrolü (-15)
            img_quality = product.get('image_quality', 'medium')
            img_resolution = product.get('image_resolution', {})
            
            if img_quality == 'low' or (img_resolution.get('width', 200) < 150):
                low_quality_count += 1
                product_warnings.append({
                    'product_id': product_id,
                    'type': 'low_quality_image',
                    'message': "Görsel kalitesi düşük görünüyor. Yeni görsel önerebilirim.",
                    'severity': 'warning'
                })
            
            # Fiyat alanı kontrolü (-5)
            price = product.get('price', 0)
            price_font_size = product.get('price_font_size', 16)
            
            if price > 0:
                # Fiyat çok büyük font
                if price_font_size > 24:
                    product_warnings.append({
                        'product_id': product_id,
                        'type': 'price_too_large',
                        'message': "Fiyat fontu biraz büyük, dengeli görünmeyebilir.",
                        'severity': 'info'
                    })
                # Fiyat çok küçük font
                elif price_font_size < 10:
                    product_warnings.append({
                        'product_id': product_id,
                        'type': 'price_too_small',
                        'message': "Fiyat fontu çok küçük, okunması zor olabilir.",
                        'severity': 'info'
                    })
        
        # Skor cezaları uygula
        if long_name_count > 0:
            penalty = min(long_name_count * 10, 30)  # Max -30
            score -= penalty
            score_breakdown['long_names'] = -penalty
        
        if low_quality_count > 0:
            penalty = min(low_quality_count * 15, 45)  # Max -45
            score -= penalty
            score_breakdown['low_quality_images'] = -penalty
            warnings.append({
                'type': 'low_quality_image',
                'message': f"{low_quality_count} ürün görseli düşük kaliteli. İyileştirme önerebilirim.",
                'action': 'improve_images',
                'priority': 'medium',
                'count': low_quality_count
            })
        
        # Temiz isim bonusu (+5)
        if clean_name_count > 0 and len(products) > 0:
            bonus = min(int(clean_name_count / len(products) * 5), 5)
            score += bonus
            score_breakdown['clean_names_bonus'] = bonus
        
        # Aynı satırda sıkışma kontrolü (-15)
        row_crowding = self._check_row_crowding(products, page_size)
        if row_crowding > 0.3:  # %30'dan fazla sıkışma
            score -= 15
            score_breakdown['row_crowding'] = -15
            suggestions.append({
                'type': 'row_crowding',
                'message': "Bazı satırlarda ürünler sıkışık görünüyor. Düzenlememi ister misin?",
                'action': 'redistribute_rows',
                'priority': 'medium'
            })
        
        # Check for slogans
        has_slogan = any(p.get('slogan') for p in products)
        if not has_slogan and len(products) > 0:
            suggestions.append({
                'type': 'no_slogan',
                'message': GHOST_TIPS['no_slogan'],
                'action': 'generate_slogan',
                'priority': 'low'
            })
        
        # Final score clamp
        final_score = max(0, min(100, score))
        
        return {
            'score': final_score,
            'grade': self._score_to_grade(final_score),
            'suggestions': suggestions,
            'warnings': warnings,
            'product_warnings': product_warnings,  # Ürün bazlı uyarılar (Madde 3)
            'score_breakdown': score_breakdown,  # Skor detayları (Madde 8)
            'product_count': len(products),
            'is_locked': locked,
            'style_hints': self._generate_style_hints(products, page_size, layout),  # Madde 2
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _check_row_crowding(self, products: List[Dict], page_size: Dict) -> float:
        """Satırlardaki sıkışmayı kontrol et"""
        if len(products) < 2:
            return 0.0
        
        page_width = page_size.get('width', 595)
        row_threshold = 50  # Y pozisyonu farkı bu kadarsa aynı satırda sayılır
        
        # Ürünleri satırlara grupla
        rows = {}
        for product in products:
            pos = product.get('position', {})
            y = pos.get('y', 0)
            # En yakın satırı bul
            found_row = None
            for row_y in rows.keys():
                if abs(y - row_y) < row_threshold:
                    found_row = row_y
                    break
            
            if found_row is not None:
                rows[found_row].append(product)
            else:
                rows[y] = [product]
        
        # Her satırdaki sıkışmayı hesapla
        crowded_rows = 0
        for row_y, row_products in rows.items():
            if len(row_products) > 1:
                # Toplam genişlik kontrolü
                total_width = sum(
                    p.get('position', {}).get('width', 100) 
                    for p in row_products
                )
                if total_width > page_width * 0.95:  # %95'den fazla doluluk
                    crowded_rows += 1
        
        return crowded_rows / len(rows) if rows else 0.0
    
    def _generate_style_hints(self, products: List[Dict], page_size: Dict, layout: str) -> Dict:
        """
        Ghost stil önerileri üret (Madde 2).
        Canvas için font, boyut, spacing önerileri.
        """
        hints = {
            'font_adjustments': [],
            'size_adjustments': [],
            'spacing_adjustments': [],
            'general': []
        }
        
        if not products:
            hints['general'].append({
                'type': 'empty_page',
                'action': 'add_products',
                'message': 'Sayfa boş, ürün eklemeyi düşünebilirsin.'
            })
            return hints
        
        product_count = len(products)
        max_products = self._get_max_products_for_layout(layout)
        
        # Sayfa doluluk oranı
        fill_ratio = product_count / max_products if max_products > 0 else 0
        
        # Boş sayfa → kartları büyüt
        if fill_ratio < 0.4:
            hints['size_adjustments'].append({
                'target': 'cards',
                'action': 'increase',
                'percentage': 15,
                'reason': 'Sayfa boş görünüyor, kartlar büyütülebilir.'
            })
            hints['spacing_adjustments'].append({
                'target': 'card_margin',
                'action': 'increase',
                'pixels': 10,
                'reason': 'Daha fazla boşluk daha ferah görünür.'
            })
        
        # Kalabalık sayfa → kartları küçült
        elif fill_ratio > 0.9:
            hints['size_adjustments'].append({
                'target': 'cards',
                'action': 'decrease',
                'percentage': 15,
                'reason': 'Sayfa kalabalık, kartlar küçültülebilir.'
            })
            hints['spacing_adjustments'].append({
                'target': 'card_margin',
                'action': 'decrease',
                'pixels': 5,
                'reason': 'Boşlukları azaltarak yer açabiliriz.'
            })
        
        # Ürün bazlı font önerileri
        for product in products:
            product_id = product.get('id') or product.get('product_id')
            name = product.get('name', '')
            name_font_size = product.get('name_font_size', 14)
            price_font_size = product.get('price_font_size', 18)
            
            # Uzun isim → font küçült
            if len(name) > 25 and name_font_size > 10:
                hints['font_adjustments'].append({
                    'product_id': product_id,
                    'target': 'name',
                    'current': name_font_size,
                    'suggested': max(10, name_font_size - 2),
                    'reason': 'İsim uzun, font küçültülebilir.'
                })
            
            # Fiyat çok baskın → font düşür
            if price_font_size > 20 and fill_ratio > 0.6:
                hints['font_adjustments'].append({
                    'product_id': product_id,
                    'target': 'price',
                    'current': price_font_size,
                    'suggested': 16,
                    'reason': 'Fiyat fontu biraz baskın görünüyor.'
                })
            
            # Görsel çok büyük → küçült
            img_scale = product.get('image_scale', 1.0)
            if img_scale > 1.0 and fill_ratio > 0.7:
                hints['size_adjustments'].append({
                    'product_id': product_id,
                    'target': 'image',
                    'current_scale': img_scale,
                    'suggested_scale': img_scale * 0.8,
                    'reason': 'Görsel büyük, %20 küçültülebilir.'
                })
        
        return hints
    
    def analyze_brochure(self, brochure_data: Dict) -> Dict:
        """
        Analyze entire brochure and return comprehensive suggestions.
        
        Args:
            brochure_data: Full brochure dictionary
        
        Returns:
            dict: Comprehensive analysis with per-page and overall scores
        """
        pages = brochure_data.get('pages', [])
        parking_area = brochure_data.get('parking_area', [])
        
        page_analyses = []
        total_score = 0
        all_suggestions = []
        all_warnings = []
        
        for page in pages:
            analysis = self.analyze_page(page)
            page_analyses.append({
                'page_id': page.get('id'),
                'page_number': page.get('number'),
                **analysis
            })
            total_score += analysis['score']
            all_suggestions.extend(analysis['suggestions'])
            all_warnings.extend(analysis['warnings'])
        
        # Check parking area
        if len(parking_area) > 0:
            all_suggestions.append({
                'type': 'parking_full',
                'message': f"Park alanında {len(parking_area)} ürün bekliyor. Yerleştirmek ister misiniz?",
                'action': 'place_parking_items',
                'priority': 'medium',
                'count': len(parking_area)
            })
        
        # Calculate overall score
        overall_score = total_score / len(pages) if pages else 0
        
        # Generate summary message
        summary = self._generate_summary(overall_score, all_suggestions, all_warnings)
        
        return {
            'overall_score': round(overall_score, 1),
            'overall_grade': self._score_to_grade(overall_score),
            'page_count': len(pages),
            'total_products': sum(len(p.get('products', [])) for p in pages),
            'parking_count': len(parking_area),
            'page_analyses': page_analyses,
            'suggestions': all_suggestions[:5],  # Top 5 suggestions
            'warnings': all_warnings[:3],  # Top 3 warnings
            'summary': summary,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def get_layout_suggestion(self, products: List[Dict], sector: str = 'supermarket') -> Dict:
        """
        Suggest optimal layout based on products.
        
        Args:
            products: List of product dictionaries
            sector: Product sector
        
        Returns:
            dict: Layout suggestion with reasoning
        """
        count = len(products)
        
        # Sector-based suggestions
        sector_layouts = {
            'supermarket': 'grid_4x4',
            'giyim': 'grid_3x3',
            'teknoloji': 'grid_2x3',
            'kozmetik': 'grid_3x3',
            'evyasam': 'grid_3x3',
            'elsanatlari': 'grid_3x3',
            'restoran': 'grid_2x3',
            'diger': 'grid_3x3'
        }
        
        # Count-based adjustments
        if count <= 4:
            suggested_layout = 'campaign'
            reason = "Az sayıda ürün için kampanya düzeni daha etkili."
        elif count <= 6:
            suggested_layout = 'grid_2x3'
            reason = "6 ürüne kadar 2x3 grid düzeni ideal."
        elif count <= 9:
            suggested_layout = 'grid_3x3'
            reason = "9 ürüne kadar 3x3 grid düzeni öneriyorum."
        elif count <= 12 and sector == 'supermarket':
            suggested_layout = 'manav'
            reason = "Market ürünleri için manav düzeni uygun."
        else:
            suggested_layout = sector_layouts.get(sector, 'grid_4x4')
            reason = f"{sector.capitalize()} sektörü için standart düzen."
        
        return {
            'suggested_layout': suggested_layout,
            'reason': reason,
            'product_count': count,
            'sector': sector,
            'alternatives': self._get_alternative_layouts(count)
        }
    
    def get_price_insight(self, customer_price: float, market_price: float, product_name: str = '') -> Dict:
        """
        Generate friendly price insight message.
        SAMİMİ MOD: Dış fiyat rakamı ASLA gösterilmez.
        
        Args:
            customer_price: Customer's selling price
            market_price: Market average price (sadece dahili analiz için)
            product_name: Optional product name
        
        Returns:
            dict: Price insight with friendly Ghost message (no external prices shown)
        """
        if market_price <= 0:
            return {
                'has_insight': False,
                'message': "Fiyat bilgisi şu an için mevcut değil."
            }
        
        # Dahili hesaplama (kullanıcıya gösterilmeyecek)
        percentage = ((customer_price - market_price) / market_price) * 100
        
        # SAMİMİ UYARI MESAJLARI - Dış fiyat rakamı YOK
        product_ref = product_name or 'Bu ürün'
        
        if percentage < -20:
            emoji = "🎉"
            tone = "excited"
            message = f"Vay be! {product_ref} çok cazip bir fiyatta! Müşterileriniz bayılacak!"
        elif percentage < -10:
            emoji = "✨"
            tone = "positive"
            message = f"Harika! {product_ref} gayet uygun görünüyor."
        elif percentage < 0:
            emoji = "👍"
            tone = "good"
            message = f"{product_ref} güzel bir fiyat noktasında."
        elif percentage < 10:
            emoji = "📊"
            tone = "neutral"
            message = f"{product_ref} makul bir fiyatta görünüyor."
        elif percentage < 20:
            emoji = "💡"
            tone = "suggestion"
            message = f"Fiyat biraz sıra dışı duruyor, istersen kontrol et."
        elif percentage < 35:
            emoji = "🤔"
            tone = "gentle_warning"
            message = f"Bu fiyat beklenenden farklı olabilir, bir göz atmak ister misin?"
        else:
            emoji = "💬"
            tone = "friendly_alert"
            message = f"Fiyat tutarsız görünüyor. Gözden geçirmek isteyebilirsin."
        
        return {
            'has_insight': True,
            'emoji': emoji,
            'tone': tone,
            'message': message,
            # NOT: market_price ve percentage frontend'e GÖNDERİLMEYECEK
            # Sadece dahili analiz için saklanıyor
            '_internal_analysis': {
                'percentage': round(percentage, 1),
                'customer_price': customer_price
            }
        }
    
    def suggest_next_action(self, brochure_state: Dict, user_activity: Dict = None) -> Dict:
        """
        Suggest next action based on current state (Shadow Planner).
        
        Args:
            brochure_state: Current brochure state
            user_activity: Recent user activity data
        
        Returns:
            dict: Suggested next action
        """
        pages = brochure_state.get('pages', [])
        parking = brochure_state.get('parking_area', [])
        total_products = sum(len(p.get('products', [])) for p in pages)
        
        # Determine workflow stage
        if total_products == 0 and len(parking) == 0:
            return {
                'action': 'upload_excel',
                'message': "Başlamak için Excel dosyası yükleyin veya ürün ekleyin.",
                'button_text': "Excel Yükle",
                'priority': 'high',
                'stage': 'start'
            }
        
        if len(parking) > 0:
            return {
                'action': 'place_products',
                'message': f"Park alanında {len(parking)} ürün var. Sayfalara yerleştirmek ister misiniz?",
                'button_text': "Otomatik Yerleştir",
                'priority': 'high',
                'stage': 'arrangement'
            }
        
        # Check for pages without images
        products_without_images = 0
        for page in pages:
            for product in page.get('products', []):
                if not product.get('image_url'):
                    products_without_images += 1
        
        if products_without_images > 0:
            return {
                'action': 'search_images',
                'message': f"{products_without_images} ürünün görseli eksik. Resim aramak ister misiniz?",
                'button_text': "Resim Ara",
                'priority': 'high',
                'stage': 'images'
            }
        
        # Check design quality
        has_unbalanced = False
        for page in pages:
            if not page.get('locked'):
                analysis = self.analyze_page(page)
                if analysis['score'] < 70:
                    has_unbalanced = True
                    break
        
        if has_unbalanced:
            return {
                'action': 'optimize_design',
                'message': "Bazı sayfalar optimize edilebilir. Düzenlememi ister misiniz?",
                'button_text': "Otomatik Düzenle",
                'priority': 'medium',
                'stage': 'optimization'
            }
        
        # Ready for export
        return {
            'action': 'export',
            'message': "Broşürünüz hazır görünüyor! Dışa aktarmak ister misiniz?",
            'button_text': "Dışa Aktar",
            'priority': 'low',
            'stage': 'export'
        }
    
    def get_idle_tip(self, idle_seconds: int, current_page: Dict = None) -> Optional[Dict]:
        """
        Get a tip for idle user.
        
        Args:
            idle_seconds: Seconds user has been idle
            current_page: Currently viewed page data
        
        Returns:
            dict: Tip suggestion or None
        """
        if idle_seconds < 5:
            return None
        
        tips = []
        
        if idle_seconds >= 5 and idle_seconds < 15:
            tips = [
                "💡 İpucu: Ürünleri sürükleyerek taşıyabilirsiniz.",
                "💡 İpucu: Sayfa kilitlemek için kilit ikonuna tıklayın.",
                "💡 İpucu: Park alanına ürün sürükleyerek geçici olarak saklayabilirsiniz."
            ]
        elif idle_seconds >= 15:
            tips = [
                GHOST_TIPS['idle_user'],
                "🤔 Bir sorun mu var? Yardıma ihtiyacınız olursa buradayım!",
                "✨ Otomatik düzenleme için 'Düzenle' butonunu deneyin."
            ]
        
        if tips:
            return {
                'type': 'idle_tip',
                'message': random.choice(tips),
                'idle_seconds': idle_seconds
            }
        
        return None
    
    # ============= PRIVATE HELPERS =============
    
    def _get_max_products_for_layout(self, layout: str) -> int:
        """Get maximum products for a layout"""
        layout_max = {
            'grid_4x4': 16,
            'grid_3x3': 9,
            'grid_2x3': 6,
            'campaign': 4,
            'manav': 12,
            'free': 20
        }
        return layout_max.get(layout, 16)
    
    def _calculate_balance(self, products: List[Dict], page_size: Dict) -> float:
        """Calculate page balance score (0-1)"""
        if len(products) < 2:
            return 1.0
        
        width = page_size.get('width', 595)
        height = page_size.get('height', 842)
        center_x = width / 2
        center_y = height / 2
        
        # Calculate center of mass
        total_x = 0
        total_y = 0
        for product in products:
            pos = product.get('position', {})
            px = pos.get('x', 0) + pos.get('width', 100) / 2
            py = pos.get('y', 0) + pos.get('height', 100) / 2
            total_x += px
            total_y += py
        
        avg_x = total_x / len(products)
        avg_y = total_y / len(products)
        
        # Calculate deviation from center
        deviation_x = abs(avg_x - center_x) / center_x
        deviation_y = abs(avg_y - center_y) / center_y
        
        balance = 1 - (deviation_x + deviation_y) / 2
        return max(0, min(1, balance))
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_summary(self, score: float, suggestions: List, warnings: List) -> str:
        """Generate friendly summary message"""
        if score >= 90:
            return "🌟 Harika! Broşürünüz mükemmel görünüyor!"
        elif score >= 80:
            return "✨ Çok iyi! Birkaç küçük iyileştirme yapılabilir."
        elif score >= 70:
            return "👍 İyi gidiyorsunuz! Bazı önerilerime göz atın."
        elif score >= 60:
            return "💡 Fena değil, ama geliştirilebilir. Yardımcı olabilir miyim?"
        else:
            return "🔧 Bu broşür biraz çalışma istiyor. Birlikte düzeltelim!"
    
    def _get_alternative_layouts(self, product_count: int) -> List[Dict]:
        """Get alternative layout suggestions"""
        alternatives = []
        
        if product_count <= 16:
            alternatives.append({'layout': 'grid_4x4', 'fit': product_count <= 16})
        if product_count <= 12:
            alternatives.append({'layout': 'manav', 'fit': product_count <= 12})
        if product_count <= 9:
            alternatives.append({'layout': 'grid_3x3', 'fit': product_count <= 9})
        if product_count <= 6:
            alternatives.append({'layout': 'grid_2x3', 'fit': product_count <= 6})
        if product_count <= 4:
            alternatives.append({'layout': 'campaign', 'fit': product_count <= 4})
        
        return alternatives


# ============= SHADOW PLANNER =============

class ShadowPlanner:
    """
    Shadow Planner - Background task planning and workflow tracking.
    Tracks user workflow and suggests optimal task sequences.
    """
    
    def __init__(self):
        self.task_history = []
        self.current_plan = []
    
    def create_auto_brochure_plan(self, products: List[Dict], settings: Dict = None) -> Dict:
        """
        Create a complete auto-brochure plan.
        Used for "Tam Otomatik Broşür" feature.
        
        Args:
            products: List of products to include
            settings: User preferences
        
        Returns:
            dict: Complete execution plan
        """
        settings = settings or {}
        sector = settings.get('sector', 'supermarket')
        
        plan = {
            'id': f'plan_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'steps': []
        }
        
        # Step 1: Validate and prepare products
        plan['steps'].append({
            'step': 1,
            'action': 'validate_products',
            'description': 'Ürün verilerini doğrula',
            'status': 'pending',
            'data': {'count': len(products)}
        })
        
        # Step 2: Search for images
        products_without_images = [p for p in products if not p.get('image_url')]
        plan['steps'].append({
            'step': 2,
            'action': 'search_images',
            'description': f'{len(products_without_images)} ürün için resim ara',
            'status': 'pending',
            'data': {'missing_images': len(products_without_images)}
        })
        
        # Step 3: Determine optimal layout
        ghost = GhostAssistant()
        layout_suggestion = ghost.get_layout_suggestion(products, sector)
        plan['steps'].append({
            'step': 3,
            'action': 'select_layout',
            'description': f'Düzen seç: {layout_suggestion["suggested_layout"]}',
            'status': 'pending',
            'data': layout_suggestion
        })
        
        # Step 4: Calculate pages needed
        max_per_page = ghost._get_max_products_for_layout(layout_suggestion['suggested_layout'])
        pages_needed = (len(products) + max_per_page - 1) // max_per_page
        plan['steps'].append({
            'step': 4,
            'action': 'create_pages',
            'description': f'{pages_needed} sayfa oluştur',
            'status': 'pending',
            'data': {'pages': pages_needed}
        })
        
        # Step 5: Distribute products
        plan['steps'].append({
            'step': 5,
            'action': 'distribute_products',
            'description': 'Ürünleri sayfalara dağıt',
            'status': 'pending'
        })
        
        # Step 6: Auto-arrange each page
        plan['steps'].append({
            'step': 6,
            'action': 'auto_arrange',
            'description': 'Sayfaları otomatik düzenle',
            'status': 'pending'
        })
        
        # Step 7: Generate slogans (optional)
        if settings.get('generate_slogans', True):
            plan['steps'].append({
                'step': 7,
                'action': 'generate_slogans',
                'description': 'AI ile slogan oluştur',
                'status': 'pending'
            })
        
        # Step 8: Quality check
        plan['steps'].append({
            'step': 8,
            'action': 'quality_check',
            'description': 'Kalite kontrolü yap',
            'status': 'pending'
        })
        
        plan['total_steps'] = len(plan['steps'])
        plan['estimated_time'] = f"{len(plan['steps']) * 2}-{len(plan['steps']) * 5} saniye"
        
        self.current_plan = plan
        return plan
    
    def get_workflow_progress(self, brochure_state: Dict) -> Dict:
        """
        Calculate workflow progress percentage.
        
        Args:
            brochure_state: Current brochure state
        
        Returns:
            dict: Progress information
        """
        stages = {
            'products_added': False,
            'images_found': False,
            'layout_selected': False,
            'pages_arranged': False,
            'quality_checked': False,
            'ready_to_export': False
        }
        
        pages = brochure_state.get('pages', [])
        total_products = sum(len(p.get('products', [])) for p in pages)
        
        # Check each stage
        if total_products > 0:
            stages['products_added'] = True
        
        products_with_images = 0
        for page in pages:
            for product in page.get('products', []):
                if product.get('image_url'):
                    products_with_images += 1
        
        if total_products > 0 and products_with_images / total_products > 0.8:
            stages['images_found'] = True
        
        if any(p.get('layout') != 'free' for p in pages):
            stages['layout_selected'] = True
        
        # Check if products are arranged (not all at 0,0)
        arranged = 0
        for page in pages:
            for product in page.get('products', []):
                pos = product.get('position', {})
                if pos.get('x', 0) > 0 or pos.get('y', 0) > 0:
                    arranged += 1
        
        if total_products > 0 and arranged / total_products > 0.5:
            stages['pages_arranged'] = True
        
        # Quality check (score > 70)
        ghost = GhostAssistant()
        analysis = ghost.analyze_brochure(brochure_state)
        if analysis['overall_score'] >= 70:
            stages['quality_checked'] = True
        
        # All stages complete = ready to export
        if all(stages.values()):
            stages['ready_to_export'] = True
        
        completed = sum(1 for v in stages.values() if v)
        progress = (completed / len(stages)) * 100
        
        return {
            'progress': round(progress, 1),
            'stages': stages,
            'completed_stages': completed,
            'total_stages': len(stages),
            'current_stage': self._get_current_stage(stages)
        }
    
    def _get_current_stage(self, stages: Dict) -> str:
        """Determine current workflow stage"""
        stage_order = [
            'products_added',
            'images_found',
            'layout_selected',
            'pages_arranged',
            'quality_checked',
            'ready_to_export'
        ]
        
        stage_names = {
            'products_added': 'Ürün ekleme',
            'images_found': 'Resim arama',
            'layout_selected': 'Düzen seçimi',
            'pages_arranged': 'Sayfa düzenleme',
            'quality_checked': 'Kalite kontrolü',
            'ready_to_export': 'Dışa aktarım'
        }
        
        for stage in stage_order:
            if not stages.get(stage):
                return stage_names[stage]
        
        return 'Tamamlandı'


# Singleton instances
ghost_assistant = GhostAssistant()
shadow_planner = ShadowPlanner()


# ============= PUBLIC API =============

def get_ghost_greeting(user_name: str = None) -> str:
    """Get Ghost greeting message"""
    return ghost_assistant.get_greeting(user_name)


def analyze_page_design(page_data: Dict) -> Dict:
    """Analyze single page design"""
    return ghost_assistant.analyze_page(page_data)


def analyze_brochure_design(brochure_data: Dict) -> Dict:
    """Analyze full brochure design"""
    return ghost_assistant.analyze_brochure(brochure_data)


def get_layout_recommendation(products: List[Dict], sector: str = 'supermarket') -> Dict:
    """Get layout recommendation for products"""
    return ghost_assistant.get_layout_suggestion(products, sector)


def get_price_insight(customer_price: float, market_price: float, product_name: str = '') -> Dict:
    """Get friendly price insight"""
    return ghost_assistant.get_price_insight(customer_price, market_price, product_name)


def get_next_action_suggestion(brochure_state: Dict) -> Dict:
    """Get next action suggestion"""
    return ghost_assistant.suggest_next_action(brochure_state)


def get_idle_suggestion(idle_seconds: int, current_page: Dict = None) -> Optional[Dict]:
    """Get suggestion for idle user"""
    return ghost_assistant.get_idle_tip(idle_seconds, current_page)


def create_auto_brochure_plan(products: List[Dict], settings: Dict = None) -> Dict:
    """Create automatic brochure plan"""
    return shadow_planner.create_auto_brochure_plan(products, settings)


def get_workflow_progress(brochure_state: Dict) -> Dict:
    """Get workflow progress"""
    return shadow_planner.get_workflow_progress(brochure_state)


def normalize_product_name(product_name: str, max_length: int = None) -> str:
    """Ürün adını normalize et ve kısalt"""
    return ghost_assistant.normalize_product_name(product_name, max_length)


def batch_normalize_names(product_names: List[str]) -> List[Dict]:
    """Toplu ürün adı normalizasyonu"""
    return ghost_assistant.batch_normalize_names(product_names)


def get_name_normalization_stats(product_names: List[str]) -> Dict:
    """Normalizasyon istatistikleri"""
    return name_normalizer.get_normalization_stats(product_names)


def validate_import_data(products: List[Dict]) -> Dict:
    """
    Excel/TXT import verilerini kontrol et (Madde 9).
    
    Args:
        products: Import edilen ürün listesi
    
    Returns:
        dict: Doğrulama sonuçları ve samimi öneriler
    """
    issues = []
    suggestions = []
    
    for idx, product in enumerate(products):
        product_issues = []
        
        # Eksik fiyat kontrolü
        price = product.get('price', 0)
        if not price or price <= 0:
            product_issues.append({
                'type': 'missing_price',
                'message': 'Fiyat eksik'
            })
        
        # Barkod format kontrolü
        barcode = str(product.get('barcode', ''))
        if barcode:
            # Barkod uzunluğu kontrolü (EAN-13, EAN-8, UPC-A, vb.)
            if len(barcode) not in [8, 12, 13, 14]:
                product_issues.append({
                    'type': 'invalid_barcode',
                    'message': f'Barkod formatı hatalı ({len(barcode)} karakter)'
                })
            # Sadece rakam kontrolü
            if not barcode.isdigit():
                product_issues.append({
                    'type': 'invalid_barcode_chars',
                    'message': 'Barkod sadece rakam içermeli'
                })
        
        # İsim uzunluğu kontrolü
        name = product.get('name', '')
        if len(name) > 35:
            product_issues.append({
                'type': 'long_name',
                'message': f'İsim çok uzun ({len(name)} karakter)',
                'suggestion': normalize_product_name(name)
            })
        
        # Kategori kontrolü
        category = product.get('category', '')
        if not category:
            product_issues.append({
                'type': 'missing_category',
                'message': 'Kategori belirtilmemiş'
            })
        
        if product_issues:
            issues.append({
                'index': idx,
                'barcode': barcode,
                'name': name[:30] + '...' if len(name) > 30 else name,
                'issues': product_issues
            })
    
    # Samimi mesajlar oluştur
    if issues:
        missing_prices = sum(1 for i in issues if any(p['type'] == 'missing_price' for p in i['issues']))
        long_names = sum(1 for i in issues if any(p['type'] == 'long_name' for p in i['issues']))
        invalid_barcodes = sum(1 for i in issues if any(p['type'] in ['invalid_barcode', 'invalid_barcode_chars'] for p in i['issues']))
        missing_categories = sum(1 for i in issues if any(p['type'] == 'missing_category' for p in i['issues']))
        
        if missing_prices > 0:
            suggestions.append({
                'type': 'price',
                'count': missing_prices,
                'message': f"🔢 {missing_prices} üründe fiyat eksik görünüyor, doldurman gerekebilir."
            })
        
        if long_names > 0:
            suggestions.append({
                'type': 'name',
                'count': long_names,
                'message': f"✏️ {long_names} ürün adı çok uzun, istersen Ghost kısaltabilir."
            })
        
        if invalid_barcodes > 0:
            suggestions.append({
                'type': 'barcode',
                'count': invalid_barcodes,
                'message': f"📊 {invalid_barcodes} barkod formatı hatalı görünüyor, kontrol etmeni öneririm."
            })
        
        if missing_categories > 0:
            suggestions.append({
                'type': 'category',
                'count': missing_categories,
                'message': f"📁 {missing_categories} üründe kategori yok, gruplandırma için ekleyebilirsin."
            })
    
    return {
        'valid': len(issues) == 0,
        'total_products': len(products),
        'issue_count': len(issues),
        'issues': issues[:20],  # İlk 20 sorun
        'suggestions': suggestions,
        'summary': "🎉 Tüm ürünler hazır görünüyor!" if len(issues) == 0 else f"📋 {len(issues)} üründe düzeltme gerekebilir."
    }


def full_clean_brochure(brochure_data: Dict) -> Dict:
    """
    Tam otomatik broşür temizliği (Madde 10).
    Tüm sayfaları tarar ve optimize eder.
    
    Args:
        brochure_data: Broşür verisi
    
    Returns:
        dict: Optimizasyon sonuçları
    """
    pages = brochure_data.get('pages', [])
    
    if not pages:
        return {
            'success': False,
            'message': 'Broşürde sayfa bulunamadı.',
            'optimization_percent': 0
        }
    
    total_optimizations = 0
    page_results = []
    
    for page in pages:
        page_id = page.get('id')
        products = page.get('products', [])
        page_optimizations = []
        
        for product in products:
            product_id = product.get('id') or product.get('product_id')
            
            # 1. Ürün adı optimizasyonu
            name = product.get('name', '')
            if len(name) > 26:
                normalized = normalize_product_name(name)
                if normalized != name:
                    page_optimizations.append({
                        'type': 'name_normalized',
                        'product_id': product_id,
                        'before': name,
                        'after': normalized
                    })
                    product['name'] = normalized
            
            # 2. Font boyutu optimizasyonu
            name_font = product.get('name_font_size', 14)
            price_font = product.get('price_font_size', 18)
            
            # Uzun isim için font küçült
            if len(product.get('name', '')) > 20 and name_font > 11:
                product['name_font_size'] = 11
                page_optimizations.append({
                    'type': 'font_adjusted',
                    'product_id': product_id,
                    'target': 'name',
                    'before': name_font,
                    'after': 11
                })
            
            # Baskın fiyat fontunu dengele
            if price_font > 20:
                product['price_font_size'] = 18
                page_optimizations.append({
                    'type': 'font_adjusted',
                    'product_id': product_id,
                    'target': 'price',
                    'before': price_font,
                    'after': 18
                })
            
            # 3. Görsel ölçeği optimizasyonu
            img_scale = product.get('image_scale', 1.0)
            if img_scale > 1.2:
                product['image_scale'] = 1.0
                page_optimizations.append({
                    'type': 'image_scaled',
                    'product_id': product_id,
                    'before': img_scale,
                    'after': 1.0
                })
        
        # 4. Sayfa düzeni optimizasyonu
        layout = page.get('layout', 'grid_4x4')
        max_products = ghost_assistant._get_max_products_for_layout(layout)
        
        # Sıkışık ürünleri küçült
        if len(products) > max_products * 0.9:
            page_optimizations.append({
                'type': 'layout_adjusted',
                'action': 'reduced_card_sizes',
                'reason': 'crowded_page'
            })
        
        # Boş sayfada büyüt
        elif len(products) < max_products * 0.4 and len(products) > 0:
            page_optimizations.append({
                'type': 'layout_adjusted',
                'action': 'increased_card_sizes',
                'reason': 'empty_page'
            })
        
        total_optimizations += len(page_optimizations)
        page_results.append({
            'page_id': page_id,
            'optimizations': page_optimizations,
            'optimization_count': len(page_optimizations)
        })
    
    # Optimizasyon yüzdesi hesapla
    total_products = sum(len(p.get('products', [])) for p in pages)
    optimization_percent = min(100, int((total_optimizations / max(total_products, 1)) * 100))
    
    return {
        'success': True,
        'message': f"🎨 Broşür %{optimization_percent} oranında optimize edildi!",
        'total_pages': len(pages),
        'total_products': total_products,
        'total_optimizations': total_optimizations,
        'optimization_percent': optimization_percent,
        'page_results': page_results,
        'optimized_brochure': brochure_data
    }

