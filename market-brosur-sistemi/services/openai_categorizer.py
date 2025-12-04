# -*- coding: utf-8 -*-
"""
OpenAI Product Categorization Service

Uses OpenAI GPT to intelligently categorize products into sector-specific groups.
Supports both text-only and Vision (image + text) categorization.
Falls back to 'Genel' if uncertain.

Aşama 2: Resim + İsim + Grup bazlı kategorileme
"""

import os
import base64
import logging
from typing import Optional, Union
from openai import OpenAI

from utils.constants import get_product_groups_for_sector, validate_and_fix_product_group

# Initialize OpenAI client
client = None

def _get_client():
    """Get or create OpenAI client"""
    global client
    if client is None:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logging.warning("OPENAI_API_KEY not set, OpenAI categorization disabled")
            return None
        client = OpenAI(api_key=api_key)
    return client


def _encode_image_to_base64(image_data: bytes) -> str:
    """Convert image bytes to base64 string for API."""
    return base64.b64encode(image_data).decode('utf-8')


def categorize_with_openai(product_name: str, sector: str = 'supermarket') -> dict:
    """
    Categorize a product AND shorten its name using OpenAI GPT.
    
    Args:
        product_name: Product name to categorize (e.g., "Oba Ayçiçek Yağı 5 LT")
        sector: User's sector (supermarket, giyim, teknoloji, etc.)
    
    Returns:
        dict: {
            'group': str,        # Valid group from whitelist or 'Genel'
            'short_name': str,   # Broşür için kısaltılmış isim
            'confidence': str,   # 'high', 'medium', 'low'
            'source': str        # 'openai' or 'fallback'
        }
    """
    # Get valid groups for this sector
    valid_groups = get_product_groups_for_sector(sector)
    groups_list = ', '.join(valid_groups)
    
    # Check if OpenAI is available
    openai_client = _get_client()
    if not openai_client:
        # Fallback to keyword-based categorization
        return _fallback_categorization(product_name, sector)
    
    try:
        # Sektör bazlı grup açıklamaları
        sector_descriptions = {
            'supermarket': """
- Gıda: Yağ, makarna, pirinç, bulgur, un, bakliyat, konserve, salça, baharat, çerez, kuruyemiş
- İçecek: Çay, kahve, su, maden suyu, meyve suyu, gazlı içecek, enerji içeceği
- Et & Tavuk: Et, tavuk, balık, sucuk, salam, sosis, köfte, şarküteri ürünleri
- Meyve & Sebze: Taze meyve, taze sebze, kuru meyve
- Temizlik: Deterjan, sabun, çamaşır suyu, yumuşatıcı, bulaşık deterjanı, temizlik malzemesi
- Kişisel Bakım: Şampuan, krem, diş macunu, deodorant, tıraş malzemesi
- Atıştırmalık: Cips, çikolata, bisküvi, kraker, gofret, şekerleme
- Dondurulmuş: Dondurma, donuk gıda, hazır yemek, pizza
- Şarküteri: Peynir, zeytin, sucuk, salam, pastırma
- Genel: Diğer tüm ürünler""",
            'giyim': """
- Giyim: Üst giyim, alt giyim, dış giyim, iç giyim
- Ayakkabı: Spor ayakkabı, klasik ayakkabı, bot, sandalet
- Aksesuar: Çanta, kemer, şapka, atkı, eldiven
- Genel: Diğer""",
            'teknoloji': """
- Telefon: Cep telefonu, akıllı telefon, telefon aksesuarı
- Bilgisayar & Tablet: Laptop, masaüstü, tablet, bilgisayar parçaları
- TV & Ses: Televizyon, hoparlör, kulaklık, ses sistemi
- Beyaz Eşya: Buzdolabı, çamaşır makinesi, bulaşık makinesi
- Küçük Ev Aletleri: Ütü, elektrikli süpürge, blender, tost makinesi
- Oyun: Oyun konsolu, oyun, oyun aksesuarı
- Genel: Diğer elektronik""",
            'restoran': """
- Yemek: Ana yemek, çorba, salata, kebap, pide, pizza
- İçecek: Soğuk içecek, sıcak içecek, alkollü içecek
- Tatlı: Pasta, dondurma, sütlü tatlı, şerbetli tatlı
- Aperatif: Meze, başlangıç, atıştırmalık
- Genel: Diğer"""
        }
        
        # Get description for current sector
        sector_desc = sector_descriptions.get(sector, "- Genel: Tüm ürünler")
        
        # Create prompt for OpenAI - kategorileme + isim kısaltma
        prompt = f"""Ürün adı: "{product_name}"
Sektör: {sector}

Bu sektördeki ürün grupları:
{sector_desc}

İZİN VERİLEN GRUPLAR: {groups_list}

GÖREV 1: Ürünü yukarıdaki gruplardan BİRİNE kategorize et.
GÖREV 2: Ürün adını BROŞÜR için kısalt (A101, BİM, ŞOK formatında).

KISALTMA KURALLARI:
- Marka adını KORU (Alo, Ülker, Coca-Cola vb.)
- AYIRT EDİCİ özellikleri KISALT ama KORU
- Gereksiz PAZARLAMA kelimelerini KALDIR (kar beyazı, dağ esintisi, özel seri, premium vb.)
- Miktar/adet KISALT (8 x 61 G → 8'li, 1000 ml → 1 lt)
- Maksimum 25 karakter

KISALTMA SÖZLÜĞÜ:
- tam yağlı → t.yağ.
- yarım yağlı → y.yağ.
- kakaolu → kak.
- sütlü → süt.
- çilekli → çil.
- kremalı → krem.
- bisküvi → (kaldır)
- kilogram → kg
- litre → lt
- gram → g

ÖRNEKLER:
- "Alo Matik Kar Beyazı 9 kg Dağ Esintisi" → "Alo Matik 9 kg"
- "Ülker Kremalı Rondo Çilekli Bisküvi 8 x 61 G" → "Ülker Rondo Çil. 8'li"
- "Coca-Cola Zero Sugar 1000 ml Pet Şişe" → "Coca-Cola Zero 1 lt"
- "Pınar Tam Yağlı Süt 1 Litre" → "Pınar Süt T.Yağ. 1 lt"
- "Pınar Yarım Yağlı Süt 1 Litre" → "Pınar Süt Y.Yağ. 1 lt"
- "Eti Tutku Kakaolu Bisküvi 280g" → "Eti Tutku Kak. 280g"
- "Eti Tutku Sütlü Bisküvi 280g" → "Eti Tutku Süt. 280g"
- "Ülker Metro Çikolatalı Bar 36g" → "Ülker Metro Çik. 36g"

CEVAP FORMATI (sadece bu formatı kullan):
GRUP: [grup adı]
KISAISIM: [kısaltılmış isim]"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=[
                {"role": "system", "content": "Sen bir market broşürü uzmanısın. Ürünleri kategorize eder ve broşüre uygun kısa isimler oluşturursun. A101, BİM, ŞOK broşürlerindeki format gibi kısa ve öz isimler yaz."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.2  # Slightly higher for creative naming
        )
        
        # Extract the response
        ai_response = response.choices[0].message.content.strip()
        
        # Parse response - GRUP: xxx ve KISAISIM: xxx formatı
        group_match = ai_response.split('GRUP:')[-1].split('KISAISIM:')[0].strip() if 'GRUP:' in ai_response else 'Genel'
        short_name_match = ai_response.split('KISAISIM:')[-1].strip() if 'KISAISIM:' in ai_response else product_name[:30]
        
        # Clean up parsed values
        validated_group = validate_and_fix_product_group(group_match, sector)
        short_name = short_name_match.strip()[:35]  # Max 35 karakter
        
        # Eğer kısa isim çok uzunsa veya orijinalle aynıysa, basit kısaltma yap
        if len(short_name) > 30 or short_name == product_name:
            short_name = _simple_shorten(product_name)
        
        # Determine confidence based on validation
        confidence = 'high' if validated_group == group_match else 'medium'
        
        logging.info(f"OpenAI: '{product_name}' → Grup: '{validated_group}', Kısa: '{short_name}'")
        
        return {
            'group': validated_group,
            'short_name': short_name,
            'confidence': confidence,
            'source': 'openai',
            'ai_response': ai_response
        }
        
    except Exception as e:
        logging.error(f"OpenAI categorization error: {e}")
        return _fallback_categorization(product_name, sector)


def _simple_shorten(name: str) -> str:
    """Basit kısaltma - OpenAI çalışmazsa fallback."""
    # Pazarlama kelimelerini kaldır
    remove_words = ['özel', 'seri', 'yeni', 'süper', 'extra', 'premium', 
                    'geleneksel', 'doğal', 'organik', 'pet', 'şişe', 'kutu',
                    'paket', 'adet', 'kar beyazı', 'dağ esintisi', 'bahar ferahlığı',
                    'özel lezzet', 'enfes', 'lezzetli', 'taptaze', 'bisküvi', 'biskuvi']
    
    result = name
    for word in remove_words:
        result = result.replace(word, '').replace(word.title(), '').replace(word.upper(), '')
    
    # Kısaltma sözlüğü - ayırt edici özellikler kısaltılarak korunur
    replacements = {
        'tam yağlı': 't.yağ.',
        'yarım yağlı': 'y.yağ.',
        'kakaolu': 'kak.',
        'sütlü': 'süt.',
        'çilekli': 'çil.',
        'kremalı': 'krem.',
        'çikolatalı': 'çik.',
        'fındıklı': 'fın.',
        'bademli': 'bad.',
        'antep fıstıklı': 'a.fıs.',
        'kilogram': 'kg',
        'litre': 'lt',
        '1000 ml': '1 lt',
        '500 ml': '500ml',
        'gram': 'g',
    }
    result_lower = result.lower()
    for full, short in replacements.items():
        result_lower = result_lower.replace(full, short)
    
    # Çoklu boşlukları temizle
    result = ' '.join(result_lower.split())
    
    # İlk harfleri büyüt (marka için)
    words = result.split()
    if words:
        words[0] = words[0].title()
    result = ' '.join(words)
    
    # Max 25 karakter
    if len(result) > 25:
        result = result[:22] + '...'
    
    return result.strip()


def _fallback_categorization(product_name: str, sector: str) -> dict:
    """
    Fallback keyword-based categorization when OpenAI is unavailable.
    """
    from services.ai_categorizer import get_sector_group
    
    group = get_sector_group(product_name, sector)
    short_name = _simple_shorten(product_name)
    
    return {
        'group': group,
        'short_name': short_name,
        'confidence': 'low',
        'source': 'fallback'
    }


def batch_categorize(products: list, sector: str = 'supermarket') -> list:
    """
    Categorize multiple products efficiently.
    
    Args:
        products: List of dicts with 'name' field
        sector: User's sector
    
    Returns:
        List of products with 'ai_group' field added
    """
    for product in products:
        name = product.get('name', '')
        if name:
            result = categorize_with_openai(name, sector)
            product['ai_group'] = result['group']
            product['ai_confidence'] = result['confidence']
            product['ai_source'] = result['source']
        else:
            product['ai_group'] = 'Genel'
            product['ai_confidence'] = 'low'
            product['ai_source'] = 'default'
    
    return products


# ============= API Functions =============

def categorize_product_openai(product_name: str, sector: str = 'supermarket') -> str:
    """
    Simple API: Categorize a product and return just the group name.
    """
    result = categorize_with_openai(product_name, sector)
    return result['group']


def is_openai_available() -> bool:
    """Check if OpenAI API is configured and available."""
    return _get_client() is not None


# ============= AŞAMA 2: VİSİON API İLE KATEGORİLEME =============

def categorize_with_vision(
    product_name: str,
    image_data: bytes,
    sector: str = 'supermarket',
    existing_group: str = None
) -> dict:
    """
    AŞAMA 2: Resim + İsim + Mevcut Grup ile kategorileme
    
    GPT-4o Vision API kullanarak ürünü analiz eder ve en uygun grubu seçer.
    
    Args:
        product_name: Ürün adı
        image_data: PNG resim verisi (bytes)
        sector: Kullanıcı sektörü
        existing_group: Varsa mevcut grup (API'den gelen)
    
    Returns:
        dict: {
            'group': str,
            'confidence': str,
            'source': 'vision',
            'reasoning': str (AI'nin açıklaması)
        }
    """
    # Get valid groups for this sector
    valid_groups = get_product_groups_for_sector(sector)
    groups_list = ', '.join(valid_groups)
    
    # Check if OpenAI is available
    openai_client = _get_client()
    if not openai_client:
        logging.warning("OpenAI unavailable, falling back to text-only categorization")
        return categorize_with_openai(product_name, sector)
    
    try:
        # Encode image to base64
        image_base64 = _encode_image_to_base64(image_data)
        
        # Build prompt with existing group info if available
        existing_info = ""
        if existing_group:
            existing_info = f"\nMevcut/Önerilen Grup: {existing_group}"
        
        # Sektör bazlı açıklamalar
        sector_hints = {
            'supermarket': """
Grup açıklamaları:
- Gıda: Yağ, makarna, pirinç, un, bakliyat, konserve, salça, baharat
- İçecek: Çay, kahve, su, meyve suyu, gazlı içecek
- Et & Tavuk: Et, tavuk, balık, sucuk, salam, sosis
- Meyve & Sebze: Taze meyve ve sebze
- Temizlik: Deterjan, sabun, çamaşır suyu
- Kişisel Bakım: Şampuan, krem, diş macunu
- Atıştırmalık: Cips, çikolata, bisküvi
- Dondurulmuş: Dondurma, donuk gıda
- Şarküteri: Peynir, zeytin, süt ürünleri, yoğurt
- Genel: Diğer""",
            'giyim': """
- Giyim: Üst, alt, dış giyim
- Ayakkabı: Her türlü ayakkabı
- Aksesuar: Çanta, kemer, şapka
- Genel: Diğer""",
            'teknoloji': """
- Telefon: Cep telefonu, aksesuar
- Bilgisayar & Tablet: PC, laptop, tablet
- TV & Ses: TV, hoparlör, kulaklık
- Beyaz Eşya: Buzdolabı, çamaşır makinesi
- Küçük Ev Aletleri: Ütü, blender
- Oyun: Konsol, oyun
- Genel: Diğer""",
            'restoran': """
- Yemek: Ana yemek, çorba
- İçecek: İçecekler
- Tatlı: Tatlılar
- Aperatif: Meze, başlangıç
- Genel: Diğer"""
        }
        
        sector_hint = sector_hints.get(sector, "- Genel: Tüm ürünler")
        
        prompt = f"""Bu ürün resmini ve bilgilerini analiz et:

Ürün Adı: "{product_name}"
Sektör: {sector}{existing_info}

{sector_hint}

İZİN VERİLEN GRUPLAR: {groups_list}

GÖREV:
1. Resme dikkatlice bak
2. Ürün adını oku
3. En uygun grubu seç

KURALLAR:
- SADECE izin verilen gruplardan birini seç
- Resim ve isim uyuşmuyorsa, RESME öncelik ver
- Emin değilsen "Genel" yaz

Sadece grup adını yaz, başka bir şey yazma.

Grup:"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Vision destekli model
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir ürün kategorileme uzmanısın. Resimleri analiz ederek doğru kategoriyi belirlersin. Kısa ve net cevaplar ver."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "low"  # Maliyet optimizasyonu
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        # Extract response
        ai_response = response.choices[0].message.content.strip()
        
        # Validate against whitelist
        validated_group = validate_and_fix_product_group(ai_response, sector)
        
        confidence = 'high' if validated_group == ai_response else 'medium'
        
        logging.info(f"Vision categorized '{product_name}' → '{validated_group}' (AI: '{ai_response}')")
        
        return {
            'group': validated_group,
            'confidence': confidence,
            'source': 'vision',
            'ai_response': ai_response
        }
        
    except Exception as e:
        logging.error(f"Vision categorization error: {e}")
        # Fallback to text-only
        logging.info("Falling back to text-only categorization")
        return categorize_with_openai(product_name, sector)


def categorize_product_with_image(
    product_name: str,
    image_url_or_bytes: Union[str, bytes],
    sector: str = 'supermarket',
    existing_group: str = None
) -> dict:
    """
    Convenience function: URL veya bytes kabul eder.
    
    Args:
        product_name: Ürün adı
        image_url_or_bytes: Resim URL'si veya bytes
        sector: Sektör
        existing_group: Mevcut grup
    
    Returns:
        dict: Kategorileme sonucu
    """
    # URL ise indir
    if isinstance(image_url_or_bytes, str):
        try:
            from services.image_processor import download_image
            image_data = download_image(image_url_or_bytes)
        except Exception as e:
            logging.error(f"Image download failed: {e}")
            # Fallback to text-only
            return categorize_with_openai(product_name, sector)
    else:
        image_data = image_url_or_bytes
    
    return categorize_with_vision(product_name, image_data, sector, existing_group)
