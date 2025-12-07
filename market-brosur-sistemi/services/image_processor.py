# -*- coding: utf-8 -*-
"""
Image Processor Service - Aşama 1

Ürün resimlerini işler:
1. Arka planı kaldırır (şeffaf)
2. 1024x1024 boyutuna getirir
3. PNG olarak kaydeder

Önemli: Resmin orijinalliği %95-100 korunur, ekstra detay EKLENMEZ!
"""

import os
import logging
import requests
from io import BytesIO
from PIL import Image
from rembg import remove

# Hedef boyut
TARGET_SIZE = (1024, 1024)
OUTPUT_FORMAT = 'PNG'


def download_image(url: str, timeout: int = 30) -> bytes:
    """
    URL'den resim indir.
    
    Args:
        url: Resim URL'si
        timeout: İndirme timeout (saniye)
    
    Returns:
        bytes: Resim verisi
    """
    try:
        # Proxy URL'den gerçek URL'yi çıkar
        if url.startswith('/proxy-image?url='):
            from urllib.parse import unquote
            url = unquote(url.replace('/proxy-image?url=', ''))
        
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        return response.content
        
    except Exception as e:
        logging.error(f"Resim indirme hatası: {url} - {e}")
        raise


def remove_background(image_data: bytes) -> Image.Image:
    """
    Resimden arka planı kaldır (şeffaf yap).
    
    Args:
        image_data: Resim bytes verisi
    
    Returns:
        PIL.Image: Arka planı kaldırılmış resim (RGBA)
    """
    try:
        # rembg ile arka plan kaldır
        output_data = remove(image_data)
        img = Image.open(BytesIO(output_data))
        
        # RGBA moduna çevir (şeffaflık için)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        logging.info("Arka plan başarıyla kaldırıldı")
        return img
        
    except Exception as e:
        logging.error(f"Arka plan kaldırma hatası: {e}")
        raise


def resize_image(img: Image.Image, size: tuple = TARGET_SIZE) -> Image.Image:
    """
    Resmi hedef boyuta getir (oranı koruyarak).
    
    Resim kare değilse, şeffaf padding ile kare yapılır.
    
    Args:
        img: PIL Image
        size: Hedef boyut (width, height)
    
    Returns:
        PIL.Image: Yeniden boyutlandırılmış resim
    """
    try:
        # Mevcut boyut
        width, height = img.size
        target_w, target_h = size
        
        # En-boy oranını koru
        ratio = min(target_w / width, target_h / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Yüksek kaliteli resize (LANCZOS)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Şeffaf arka plan ile kare canvas oluştur
        canvas = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Resmi ortala
        x = (target_w - new_width) // 2
        y = (target_h - new_height) // 2
        canvas.paste(img_resized, (x, y), img_resized if img_resized.mode == 'RGBA' else None)
        
        logging.info(f"Resim boyutlandırıldı: {width}x{height} → {size[0]}x{size[1]}")
        return canvas
        
    except Exception as e:
        logging.error(f"Resim boyutlandırma hatası: {e}")
        raise


def to_png_bytes(img: Image.Image) -> bytes:
    """
    PIL Image'ı PNG bytes'a çevir.
    
    Args:
        img: PIL Image
    
    Returns:
        bytes: PNG formatında resim verisi
    """
    output = BytesIO()
    img.save(output, format=OUTPUT_FORMAT, optimize=True)
    return output.getvalue()


def process_product_image(image_input, barcode: str = None) -> dict:
    """
    AŞAMA 1: Ürün resmini işle
    
    1. Resmi indir (URL ise)
    2. Arka planı kaldır
    3. 1024x1024 boyutuna getir
    4. PNG olarak döndür
    
    Args:
        image_input: URL (str) veya bytes verisi
        barcode: Ürün barkodu (loglama için)
    
    Returns:
        dict: {
            'success': bool,
            'image_bytes': bytes (PNG),
            'format': 'PNG',
            'size': (1024, 1024),
            'barcode': str
        }
    """
    try:
        log_prefix = f"[{barcode}] " if barcode else ""
        
        # 1. Resmi al
        if isinstance(image_input, str):
            logging.info(f"{log_prefix}Resim indiriliyor: {image_input[:100]}...")
            image_data = download_image(image_input)
        else:
            image_data = image_input
        
        # 2. Arka planı kaldır
        logging.info(f"{log_prefix}Arka plan kaldırılıyor...")
        img_no_bg = remove_background(image_data)
        
        # 3. 1024x1024 boyutuna getir
        logging.info(f"{log_prefix}Resim boyutlandırılıyor...")
        img_resized = resize_image(img_no_bg, TARGET_SIZE)
        
        # 4. PNG bytes'a çevir
        png_bytes = to_png_bytes(img_resized)
        
        logging.info(f"{log_prefix}Resim işleme tamamlandı: {len(png_bytes)} bytes")
        
        return {
            'success': True,
            'image_bytes': png_bytes,
            'format': OUTPUT_FORMAT,
            'size': TARGET_SIZE,
            'barcode': barcode
        }
        
    except Exception as e:
        logging.error(f"Resim işleme hatası: {e}")
        return {
            'success': False,
            'error': str(e),
            'barcode': barcode
        }


def process_product_image_simple(image_input) -> bytes:
    """
    Basit API: Sadece işlenmiş PNG bytes döndür.
    
    Args:
        image_input: URL veya bytes
    
    Returns:
        bytes: İşlenmiş PNG verisi
    
    Raises:
        Exception: İşleme başarısız olursa
    """
    result = process_product_image(image_input)
    if result['success']:
        return result['image_bytes']
    else:
        raise Exception(result.get('error', 'Resim işleme hatası'))


# ============= BATCH PROCESSING =============

def process_multiple_images(images: list) -> list:
    """
    Birden fazla resmi işle.
    
    Args:
        images: List of {'url': str, 'barcode': str}
    
    Returns:
        List of processing results
    """
    results = []
    
    for item in images:
        url = item.get('url') or item.get('image_url')
        barcode = item.get('barcode', '')
        
        if url:
            result = process_product_image(url, barcode)
            results.append(result)
        else:
            results.append({
                'success': False,
                'error': 'URL bulunamadı',
                'barcode': barcode
            })
    
    return results






