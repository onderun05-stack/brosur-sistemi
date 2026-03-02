# -*- coding: utf-8 -*-
"""
External API Service - Multi-API Integration for Product Data and Images

Search Hierarchy for PRODUCT INFO:
1. Customer depot (local)
2. Admin depot (local)
3. CAMGOZ/JoJAPI (Turkish products - name, category, price)
4. N11 API (future)

Search Hierarchy for IMAGES:
1. Customer depot (local uploads)
2. Admin depot (admin uploads)
3. Google Custom Search (product name search)

Features:
- Product info from CAMGOZ API
- Professional product images from Google Search
- Image quality scoring
- Cache management (24 hours)
- Rate limiting
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from services.image_bank import (
    search_image_hierarchy,
    save_to_admin_depot,
    save_to_customer_depot,
    CACHE_PATH
)
from utils.constants import SECTORS

# ============= API CONFIGURATIONS =============

# CAMGOZ/JoJAPI (Turkish products - for product info)
CAMGOZ_API_URL = os.environ.get('CAMGOZ_API_URL', 'https://nhghk.jojapi.net/api/external')
CAMGOZ_API_KEY = os.environ.get('CAMGOZ_API_KEY', '')

# Google Custom Search API (for product images)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
GOOGLE_SEARCH_CX = os.environ.get('GOOGLE_SEARCH_CX', '')
GOOGLE_SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'

# N11 API (Future - Hook Ready)
N11_API_URL = os.environ.get('N11_API_URL', '')
N11_API_KEY = os.environ.get('N11_API_KEY', '')
N11_API_SECRET = os.environ.get('N11_API_SECRET', '')

# Trendyol API (Future - Hook Ready)
TRENDYOL_API_URL = os.environ.get('TRENDYOL_API_URL', '')
TRENDYOL_API_KEY = os.environ.get('TRENDYOL_API_KEY', '')

# Hepsiburada API (Future - Hook Ready)
HEPSIBURADA_API_URL = os.environ.get('HEPSIBURADA_API_URL', '')
HEPSIBURADA_API_KEY = os.environ.get('HEPSIBURADA_API_KEY', '')

# GittiGidiyor API (Future - Hook Ready)
GITTIGIDIYOR_API_URL = os.environ.get('GITTIGIDIYOR_API_URL', '')
GITTIGIDIYOR_API_KEY = os.environ.get('GITTIGIDIYOR_API_KEY', '')

# ============= CACHE & RATE LIMITING =============

CACHE_DURATION_HOURS = 24
MAX_CACHE_SIZE_MB = 100
API_CALLS_PER_MINUTE = 60  # Increased for parallel queries
_api_call_times = []
_api_lock = threading.Lock()


def _check_rate_limit():
    """Thread-safe rate limit check"""
    global _api_call_times
    with _api_lock:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        _api_call_times = [t for t in _api_call_times if t > minute_ago]
        
        if len(_api_call_times) >= API_CALLS_PER_MINUTE:
            return False
        
        _api_call_times.append(now)
        return True


def _get_cache_path(barcode, api_source='combined'):
    """Get cache file path for a barcode"""
    return os.path.join(CACHE_PATH, f'{barcode}_{api_source}.json')


def _get_from_cache(barcode, api_source='combined'):
    """Get cached API response for a barcode"""
    cache_file = _get_cache_path(barcode, api_source)
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_time > timedelta(hours=CACHE_DURATION_HOURS):
            os.remove(cache_file)
            return None
        
        return cached.get('data')
        
    except Exception as e:
        logging.error(f"Cache read error: {e}")
        return None


def _save_to_cache(barcode, data, api_source='combined'):
    """Save API response to cache"""
    try:
        os.makedirs(CACHE_PATH, exist_ok=True)
        cache_file = _get_cache_path(barcode, api_source)
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'cached_at': datetime.now().isoformat(),
                'data': data
            }, f, ensure_ascii=False)
            
    except Exception as e:
        logging.error(f"Cache write error: {e}")


# ============= IMAGE QUALITY SCORING =============

def calculate_image_quality_score(width, height, has_background_removed=False):
    """
    Calculate image quality score (0-100)
    Higher score = better quality
    """
    min_dim = min(width, height)
    max_dim = max(width, height)
    
    # Resolution score (0-50)
    if min_dim >= 1024:
        resolution_score = 50
    elif min_dim >= 800:
        resolution_score = 45
    elif min_dim >= 600:
        resolution_score = 40
    elif min_dim >= 400:
        resolution_score = 30
    elif min_dim >= 200:
        resolution_score = 20
    else:
        resolution_score = 10
    
    # Aspect ratio score (0-20) - Square images are preferred
    aspect_ratio = max_dim / min_dim if min_dim > 0 else 999
    if aspect_ratio <= 1.2:
        aspect_score = 20
    elif aspect_ratio <= 1.5:
        aspect_score = 15
    elif aspect_ratio <= 2.0:
        aspect_score = 10
    else:
        aspect_score = 5
    
    # Background score (0-30)
    background_score = 30 if has_background_removed else 15
    
    total_score = resolution_score + aspect_score + background_score
    
    return {
        'score': total_score,
        'resolution_score': resolution_score,
        'aspect_score': aspect_score,
        'background_score': background_score,
        'quality_level': 'high' if total_score >= 70 else 'medium' if total_score >= 40 else 'low',
        'quality_indicator': '🟢' if total_score >= 70 else '🟡' if total_score >= 40 else '🔴'
    }


# ============= GOOGLE CUSTOM SEARCH API (FOR IMAGES) =============

def search_google_images(product_name, barcode=None):
    """
    Search Google for professional product images.
    
    Args:
        product_name: Product name to search
        barcode: Optional barcode for more specific search
    
    Returns:
        dict: {success, images: [{url, width, height, title}]}
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        logging.warning("Google Search API not configured")
        return {'success': False, 'error': 'Google API not configured', 'skip': True}
    
    if not _check_rate_limit():
        return {'success': False, 'error': 'Rate limit exceeded'}
    
    try:
        # Build search query - product name + "ürün" for better results
        search_query = f"{product_name} ürün beyaz arka plan"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_CX,
            'q': search_query,
            'searchType': 'image',
            'num': 5,  # Get top 5 results
            'imgSize': 'large',  # Prefer large images
            'imgType': 'photo',  # Prefer photos
            'safe': 'active'
        }
        
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                images = []
                for item in items:
                    image_info = item.get('image', {})
                    images.append({
                        'url': item.get('link', ''),
                        'thumbnail': image_info.get('thumbnailLink', ''),
                        'width': image_info.get('width', 0),
                        'height': image_info.get('height', 0),
                        'title': item.get('title', ''),
                        'source': item.get('displayLink', '')
                    })
                
                logging.info(f"✅ Google Search: Found {len(images)} images for '{product_name}'")
                return {
                    'success': True,
                    'images': images,
                    'query': search_query
                }
            else:
                return {
                    'success': True,
                    'images': [],
                    'message': 'No images found'
                }
        
        elif response.status_code == 403:
            return {'success': False, 'error': 'Google API quota exceeded or invalid key'}
        else:
            return {'success': False, 'error': f'Google API returned status {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Google Search timeout'}
    except Exception as e:
        logging.error(f"Google Search error: {e}")
        return {'success': False, 'error': str(e)}


def get_best_google_image(product_name, barcode=None, user_id=None, sector='supermarket'):
    """
    Search Google and download the best quality image.
    
    Returns:
        dict: {success, image_url, quality_score, ...}
    """
    # Search Google
    search_result = search_google_images(product_name, barcode)
    
    if not search_result.get('success') or not search_result.get('images'):
        return {'success': False, 'error': search_result.get('error', 'No images found')}
    
    images = search_result['images']
    
    # Score each image and find the best one
    best_image = None
    best_score = -1
    
    for img in images:
        width = img.get('width', 0)
        height = img.get('height', 0)
        
        if width > 0 and height > 0:
            quality = calculate_image_quality_score(width, height)
            score = quality['score']
            
            # Bonus for certain domains (e-commerce sites usually have good product photos)
            source = img.get('source', '').lower()
            if any(domain in source for domain in ['trendyol', 'hepsiburada', 'n11', 'amazon', 'migros', 'a101', 'bim', 'sok']):
                score += 15
            
            if score > best_score:
                best_score = score
                best_image = img
                best_image['quality_score'] = score
    
    if not best_image:
        return {'success': False, 'error': 'No suitable image found'}
    
    # Download and save the best image
    try:
        image_result = download_and_process_image(
            image_url=best_image['url'],
            barcode=barcode or product_name.replace(' ', '_'),
            user_id=user_id or 0,
            sector=sector,
            source='google_search'
        )
        
        if image_result.get('success'):
            return {
                'success': True,
                'image_url': image_result['image_url'],
                'original_url': best_image['url'],
                'quality_score': best_score,
                'quality': image_result.get('quality', 'unknown'),
                'quality_indicator': image_result.get('quality_indicator', '🟡'),
                'source': 'google_search',
                'search_query': search_result.get('query', '')
            }
        else:
            return image_result
            
    except Exception as e:
        logging.error(f"Google image download error: {e}")
        return {'success': False, 'error': str(e)}


# ============= CAMGOZ/JOJAPI =============

def query_camgoz_api(barcode):
    """Query CAMGOZ/JoJAPI for Turkish products"""
    if not _check_rate_limit():
        return {'success': False, 'error': 'Rate limit exceeded'}
    
    if not CAMGOZ_API_KEY:
        return {'success': False, 'error': 'CAMGOZ API key not configured', 'skip': True}
    
    try:
        response = requests.get(
            f"{CAMGOZ_API_URL}/search",
            params={'query': barcode},
            headers={'X-JoJAPI-Key': CAMGOZ_API_KEY},
            timeout=15
        )
        
        if response.status_code == 200:
            api_response = response.json()
            
            if isinstance(api_response, dict):
                results = api_response.get('content') or api_response.get('results') or []
            elif isinstance(api_response, list):
                results = api_response
            else:
                results = []
            
            if results and len(results) > 0:
                product_data = results[0]
                
                normalized = {
                    'barcode': product_data.get('barcode', barcode),
                    'name': product_data.get('name', ''),
                    'category': product_data.get('category', ''),
                    'brand': product_data.get('brand', ''),
                    'price': float(product_data.get('price', 0) or 0),
                    'price_with_tax': float(product_data.get('total', 0) or 0),
                    'image_url': product_data.get('imageUrl', ''),
                    'image_width': 0,
                    'image_height': 0,
                    'description': product_data.get('description', ''),
                    'unit': product_data.get('unit', ''),
                    'source': 'camgoz',
                    'last_modified': 0
                }
                
                return {
                    'success': True,
                    'source': 'camgoz',
                    'product': normalized
                }
            else:
                return {
                    'success': True,
                    'source': 'camgoz',
                    'product': None,
                    'message': 'Product not found in CAMGOZ database'
                }
                
        elif response.status_code == 401:
            return {'success': False, 'error': 'Invalid CAMGOZ API key'}
        elif response.status_code == 429:
            return {'success': False, 'error': 'CAMGOZ rate limit exceeded'}
        else:
            return {'success': False, 'error': f'CAMGOZ returned status {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'CAMGOZ API timeout'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Could not connect to CAMGOZ'}
    except Exception as e:
        logging.error(f"CAMGOZ API error: {e}")
        return {'success': False, 'error': str(e)}


# ============= N11 API (HOOK - FUTURE) =============

def query_n11_api(barcode):
    """
    N11 API Hook - E-Ticaret entegrasyonu (Madde 7)
    Set N11_API_URL, N11_API_KEY, N11_API_SECRET environment variables to enable
    
    NOT: Dış fiyatlar sadece Ghost içinde kalite analizinde kullanılır.
    Frontend'e fiyat rakamı GÖNDERİLMEZ.
    """
    if not N11_API_KEY or not N11_API_URL:
        return {
            'success': False, 
            'error': 'N11 API not configured', 
            'skip': True,
            'status': 'not_available'
        }
    
    try:
        # N11 SOAP API entegrasyonu
        # Reference: https://api.n11.com/
        # Zeep library gerekli: pip install zeep
        
        try:
            from zeep import Client
            from zeep.wsse.username import UsernameToken
        except ImportError:
            return {
                'success': False, 
                'error': 'zeep library required for N11 API', 
                'skip': True
            }
        
        # N11 SOAP client
        client = Client(
            N11_API_URL,
            wsse=UsernameToken(N11_API_KEY, N11_API_SECRET)
        )
        
        # Barkod ile ürün ara
        response = client.service.GetProductByBarcode(barcode=barcode)
        
        if response and hasattr(response, 'product'):
            product_data = response.product
            
            # Fiyat bilgisi sadece dahili kullanım için
            # (Frontend'e gönderilmeyecek)
            internal_price = float(getattr(product_data, 'price', 0))
            
            return {
                'success': True,
                'product': {
                    'name': getattr(product_data, 'title', ''),
                    'category': getattr(product_data, 'category', ''),
                    'image_url': getattr(product_data, 'imageUrl', ''),
                    'brand': getattr(product_data, 'brand', ''),
                    # Dahili fiyat - Ghost analizi için
                    '_internal_price': internal_price,
                    'source': 'n11'
                }
            }
        
        return {'success': False, 'found': False, 'error': 'Product not found on N11'}
        
    except Exception as e:
        logging.error(f"N11 API error: {e}")
        return {'success': False, 'error': str(e), 'skip': True}


# ============= TRENDYOL API (HOOK - FUTURE) =============

def query_trendyol_api(barcode):
    """
    Trendyol API Hook - E-Ticaret entegrasyonu (Madde 7)
    Set TRENDYOL_API_URL, TRENDYOL_API_KEY environment variables to enable
    
    NOT: Dış fiyatlar sadece Ghost içinde kalite analizinde kullanılır.
    """
    if not TRENDYOL_API_KEY or not TRENDYOL_API_URL:
        return {
            'success': False, 
            'error': 'Trendyol API not configured', 
            'skip': True,
            'status': 'not_available'
        }
    
    try:
        # Trendyol REST API entegrasyonu
        # Reference: https://developers.trendyol.com/
        
        headers = {
            'Authorization': f'Basic {TRENDYOL_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'AEU-Brosur-Sistemi/1.0'
        }
        
        # Barkod ile ürün ara
        search_url = f"{TRENDYOL_API_URL}/products?barcode={barcode}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('content') and len(data['content']) > 0:
                product_data = data['content'][0]
                
                # Fiyat bilgisi sadece dahili kullanım için
                internal_price = float(product_data.get('salePrice', 0))
                
                return {
                    'success': True,
                    'product': {
                        'name': product_data.get('title', ''),
                        'category': product_data.get('categoryName', ''),
                        'image_url': product_data.get('images', [{}])[0].get('url', '') if product_data.get('images') else '',
                        'brand': product_data.get('brand', ''),
                        # Dahili fiyat - Ghost analizi için
                        '_internal_price': internal_price,
                        'source': 'trendyol'
                    }
                }
        
        return {'success': False, 'found': False, 'error': 'Product not found on Trendyol'}
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Trendyol API timeout', 'skip': True}
    except Exception as e:
        logging.error(f"Trendyol API error: {e}")
        return {'success': False, 'error': str(e), 'skip': True}


# ============= HEPSİBURADA API (HOOK - FUTURE) =============

def query_hepsiburada_api(barcode):
    """
    Hepsiburada API Hook - E-Ticaret entegrasyonu (Madde 7)
    Set HEPSIBURADA_API_URL, HEPSIBURADA_API_KEY environment variables to enable
    
    NOT: Dış fiyatlar sadece Ghost içinde kalite analizinde kullanılır.
    """
    if not HEPSIBURADA_API_KEY or not HEPSIBURADA_API_URL:
        return {
            'success': False, 
            'error': 'Hepsiburada API not configured', 
            'skip': True,
            'status': 'not_available'
        }
    
    try:
        # Hepsiburada REST API entegrasyonu
        # Reference: https://developers.hepsiburada.com/
        
        headers = {
            'Authorization': f'Bearer {HEPSIBURADA_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'AEU-Brosur-Sistemi/1.0'
        }
        
        # Barkod ile ürün ara
        search_url = f"{HEPSIBURADA_API_URL}/products/search?barcode={barcode}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('products') and len(data['products']) > 0:
                product_data = data['products'][0]
                
                # Fiyat bilgisi sadece dahili kullanım için
                internal_price = float(product_data.get('price', 0))
                
                return {
                    'success': True,
                    'product': {
                        'name': product_data.get('name', ''),
                        'category': product_data.get('categoryPath', ''),
                        'image_url': product_data.get('imageUrl', ''),
                        'brand': product_data.get('brand', ''),
                        # Dahili fiyat - Ghost analizi için
                        '_internal_price': internal_price,
                        'source': 'hepsiburada'
                    }
                }
        
        return {'success': False, 'found': False, 'error': 'Product not found on Hepsiburada'}
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Hepsiburada API timeout', 'skip': True}
    except Exception as e:
        logging.error(f"Hepsiburada API error: {e}")
        return {'success': False, 'error': str(e), 'skip': True}


# ============= GİTTİGİDİYOR API (HOOK - FUTURE) =============

def query_gittigidiyor_api(barcode):
    """
    GittiGidiyor API Hook - E-Ticaret entegrasyonu (Madde 7)
    Set GITTIGIDIYOR_API_URL, GITTIGIDIYOR_API_KEY environment variables to enable
    
    NOT: Dış fiyatlar sadece Ghost içinde kalite analizinde kullanılır.
    NOT: GittiGidiyor, eBay Türkiye tarafından kapatıldı (2022).
    Bu hook ileride yeni platform entegrasyonları için kullanılabilir.
    """
    if not GITTIGIDIYOR_API_KEY or not GITTIGIDIYOR_API_URL:
        return {
            'success': False, 
            'error': 'GittiGidiyor API not configured (service discontinued)', 
            'skip': True,
            'status': 'not_available'
        }
    
    # GittiGidiyor 2022'de kapatıldı
    # Bu hook başka platformlar için kullanılabilir
    return {
        'success': False, 
        'error': 'GittiGidiyor service discontinued', 
        'skip': True,
        'status': 'discontinued'
    }


# ============= API QUERY (MULTI-SOURCE) =============
# Search order: CAMGOZ → N11 → Trendyol → Hepsiburada
# Future APIs can be enabled with environment variables

def parallel_api_query(barcode):
    """
    Query configured APIs for product info (Madde 7 - Tam Entegrasyon).
    
    Search Order:
    1. CAMGOZ API (Turkish market - active)
    2. N11 API (when configured)
    3. Trendyol API (when configured)
    4. Hepsiburada API (when configured)
    
    Returns product info WITHOUT images (images searched separately).
    
    NOT: E-ticaret sitelerinden gelen fiyatlar sadece dahili Ghost
    analizinde kullanılır. Kullanıcıya gösterilmez.
    """
    api_statuses = []
    
    # 1. Primary: CAMGOZ API (Türk ürünleri)
    camgoz_result = query_camgoz_api(barcode)
    api_statuses.append({
        'api': 'camgoz',
        'status': 'success' if camgoz_result.get('success') else 'failed',
        'found': camgoz_result.get('success', False)
    })
    
    if camgoz_result.get('success') and camgoz_result.get('product'):
        return {
            'success': True,
            'found': True,
            'source': 'camgoz',
            'product': camgoz_result['product'],
            'api_statuses': api_statuses
        }
    
    # 2. N11 API (when configured)
    n11_result = query_n11_api(barcode)
    api_statuses.append({
        'api': 'n11',
        'status': n11_result.get('status', 'not_available') if not n11_result.get('success') else 'success',
        'found': n11_result.get('success', False) and n11_result.get('product')
    })
    
    if n11_result.get('success') and n11_result.get('product'):
        # Dahili fiyatı temizle (frontend'e gönderilmeyecek)
        product = n11_result['product'].copy()
        product.pop('_internal_price', None)
        
        return {
            'success': True,
            'found': True,
            'source': 'n11',
            'product': product,
            '_ghost_internal_price': n11_result['product'].get('_internal_price'),
            'api_statuses': api_statuses
        }
    
    # 3. Trendyol API (when configured)
    trendyol_result = query_trendyol_api(barcode)
    api_statuses.append({
        'api': 'trendyol',
        'status': trendyol_result.get('status', 'not_available') if not trendyol_result.get('success') else 'success',
        'found': trendyol_result.get('success', False) and trendyol_result.get('product')
    })
    
    if trendyol_result.get('success') and trendyol_result.get('product'):
        product = trendyol_result['product'].copy()
        product.pop('_internal_price', None)
        
        return {
            'success': True,
            'found': True,
            'source': 'trendyol',
            'product': product,
            '_ghost_internal_price': trendyol_result['product'].get('_internal_price'),
            'api_statuses': api_statuses
        }
    
    # 4. Hepsiburada API (when configured)
    hb_result = query_hepsiburada_api(barcode)
    api_statuses.append({
        'api': 'hepsiburada',
        'status': hb_result.get('status', 'not_available') if not hb_result.get('success') else 'success',
        'found': hb_result.get('success', False) and hb_result.get('product')
    })
    
    if hb_result.get('success') and hb_result.get('product'):
        product = hb_result['product'].copy()
        product.pop('_internal_price', None)
        
        return {
            'success': True,
            'found': True,
            'source': 'hepsiburada',
            'product': product,
            '_ghost_internal_price': hb_result['product'].get('_internal_price'),
            'api_statuses': api_statuses
        }
    
    # Hiçbir API'da bulunamadı
    return {
        'success': True,
        'found': False,
        'source': None,
        'product': None,
        'message': 'Ürün bulunamadı - Manuel giriş yapın veya AI arama kullanın',
        'api_statuses': api_statuses
    }


# ============= IMAGE DOWNLOAD & PROCESSING =============

def download_and_process_image(image_url, barcode, user_id, sector='supermarket', source='api'):
    """
    Download image from URL, analyze quality, and save to depot
    """
    try:
        response = requests.get(
            image_url, 
            timeout=30,
            headers={'User-Agent': 'AEU-Brosur-Sistemi/1.0'}
        )
        response.raise_for_status()
        
        image_data = response.content
        
        # Analyze quality
        img = Image.open(BytesIO(image_data))
        width, height = img.size
        
        quality_info = calculate_image_quality_score(width, height)
        
        # Save to admin depot
        result = save_to_admin_depot(
            sector=sector,
            barcode=barcode,
            image_data=image_data,
            filename='product.png',
            metadata={
                'barcode': barcode,
                'source': source,
                'original_url': image_url,
                'quality': quality_info['quality_level'],
                'quality_score': quality_info['score'],
                'original_width': width,
                'original_height': height,
                'downloaded_at': datetime.now().isoformat()
            }
        )
        
        if result['success']:
            return {
                'success': True,
                'image_url': result['admin_url'],
                'quality': quality_info['quality_level'],
                'quality_score': quality_info['score'],
                'quality_indicator': quality_info['quality_indicator'],
                'source': 'admin_depot',
                'width': width,
                'height': height
            }
        else:
            return result
            
    except Exception as e:
        logging.error(f"Image download error: {e}")
        return {'success': False, 'error': str(e)}


# ============= MAIN LOOKUP FUNCTION =============

def full_barcode_lookup(barcode, user_id, sector='supermarket', auto_download=True, search_google_image=False):
    """
    Complete barcode lookup:
    1. Check local depots (customer → admin) for IMAGES
    2. Query CAMGOZ API for PRODUCT INFO (name, category, price)
    3. If no local image and product name found → Search Google for image
    
    Args:
        barcode: Product barcode
        user_id: User ID
        sector: Product sector
        auto_download: Auto-download images from Google
        search_google_image: Enable Google image search
    
    Returns:
        - Product info: name, category, market_price (admin only)
        - Image: From local depots OR Google Search
    """
    result = {
        'found': False,
        'source': None,
        'product': None,
        'image': None,
        'market_price': 0,           # Piyasa fiyatı (admin için)
        'market_price_tax': 0,       # KDV dahil piyasa fiyatı
        'quality_score': 0
    }
    
    # Step 1: Check local depots for existing images
    local_result = search_image_hierarchy(barcode, user_id, sector)
    
    if local_result['found']:
        result['image'] = {
            'url': local_result['image_url'],
            'quality': 'local',
            'quality_indicator': '🟢',
            'quality_score': 100
        }
    
    # Step 2: Check cache for product info
    cached = _get_from_cache(barcode, 'camgoz')
    if cached:
        logging.info(f"📦 Cache hit for {barcode}")
        result['found'] = True
        result['source'] = 'cache'
        result['product'] = cached
        result['market_price'] = cached.get('price', 0)
        result['market_price_tax'] = cached.get('price_with_tax', 0)
        
        # Cache'den dönen veride resim varsa ekle (depolarda resim yoksa)
        if not result.get('image') and cached.get('image_url'):
            result['image'] = {
                'url': cached['image_url'],
                'quality': 'camgoz',
                'quality_indicator': '🟢',
                'quality_score': 90,
                'source': 'camgoz_cache'
            }
            logging.info(f"✅ Cache Image: {cached['image_url']}")
        
        return result
    
    # Step 3: Query CAMGOZ API for product info (ANA KAYNAK)
    api_result = query_camgoz_api(barcode)
    
    if api_result.get('success') and api_result.get('product'):
        product = api_result['product']
        
        result['found'] = True
        result['source'] = 'camgoz'
        result['product'] = product
        result['market_price'] = product.get('price', 0)
        result['market_price_tax'] = product.get('price_with_tax', 0)
        result['needs_verification'] = False  # CAMGOZ güvenilir kaynak
        
        # Cache product info
        _save_to_cache(barcode, product, 'camgoz')
        
        logging.info(f"✅ CAMGOZ: {product.get('name')} - ₺{result['market_price_tax']}")
        
        # CAMGOZ'dan resim varsa kullan (imageUrl)
        if product.get('image_url') and not result.get('image'):
            result['image'] = {
                'url': product['image_url'],
                'quality': 'camgoz',
                'quality_indicator': '🟢',
                'quality_score': 90,
                'source': 'camgoz'
            }
            logging.info(f"✅ CAMGOZ Image: {product['image_url']}")
        
        # CAMGOZ'da ürün varsa ama resim yoksa → Google'a GİTME, müşteri manuel yüklesin
        # (Google sadece CAMGOZ'da hiç bulunamayan ürünler için kullanılacak)
        elif not result.get('image'):
            logging.info(f"📷 CAMGOZ'da resim yok: {product.get('name')} - Müşteri manuel yükleyecek")
    else:
        # CAMGOZ'da ürün bulunamadı
        error_msg = api_result.get('error', 'Ürün bulunamadı')
        
        # Google'dan hem ürün bilgisi hem resim almaya çalış (sadece izin verilmişse)
        if search_google_image and auto_download:
            logging.info(f"⚠️ CAMGOZ'da bulunamadı: {error_msg}, Google'a soruyorum...")
            # Barkod ile Google'da ara
            google_result = get_best_google_image(
                product_name=barcode,  # Barkod ile ara
                barcode=barcode,
                user_id=user_id,
                sector=sector
            )
            
            if google_result.get('success'):
                result['found'] = True
                result['source'] = 'google'
                result['needs_verification'] = True  # Google'dan geldi, kontrol gerekli!
                result['product'] = {
                    'name': f'Ürün {barcode}',  # Varsayılan isim
                    'category': '',
                    'brand': '',
                    'price': 0,
                    'source': 'google'
                }
                result['image'] = {
                    'url': google_result['image_url'],
                    'quality': google_result.get('quality', 'medium'),
                    'quality_indicator': '🟠',
                    'quality_score': google_result.get('quality_score', 30),
                    'source': 'google_search'
                }
                logging.info(f"⚠️ Google'dan bulundu - KONTROL GEREKLİ!")
            else:
                logging.info(f"❌ Google'da da bulunamadı: {google_result.get('error', 'Not found')}")
        else:
            # Web arama devre dışı - sadece log yaz
            logging.info(f"⚠️ CAMGOZ'da bulunamadı: {error_msg} (AI Öner ile arayın)")
    
    return result


def batch_barcode_lookup(barcodes, user_id, sector='supermarket', auto_download=True):
    """
    Lookup multiple barcodes with proper delay between requests.
    
    Sıralama (her barkod için):
    1. Depoları kontrol et (Admin → Müşteri)
    2. CAMGOZ sorgusu yap ve cevap bekle
    3. Sonra diğer satıra geç
    """
    import time
    
    results = {}
    total = len(barcodes)
    
    for idx, barcode in enumerate(barcodes):
        barcode = str(barcode).strip()
        if barcode:
            # Her sorgu arasında 0.5 saniye bekle (rate limit için)
            # İlk sorgu için bekleme yapma
            if idx > 0:
                time.sleep(0.5)
            
            logging.info(f"[{idx+1}/{total}] Barkod sorgulanıyor: {barcode}")
            
            # Sorguyu yap - depo + CAMGOZ sırasıyla kontrol eder
            # Cevap gelene kadar bekler, sonra diğer satıra geçer
            results[barcode] = full_barcode_lookup(
                barcode=barcode,
                user_id=user_id,
                sector=sector,
                auto_download=auto_download
            )
            
            # Sonuç logla
            if results[barcode]['found']:
                source = results[barcode].get('source', 'unknown')
                logging.info(f"  ✅ Bulundu: {source}")
            else:
                logging.info(f"  ❌ Bulunamadı")
    
    found_count = sum(1 for r in results.values() if r['found'])
    with_image_count = sum(1 for r in results.values() if r.get('image'))
    
    return {
        'results': results,
        'total': len(results),
        'found': found_count,
        'with_images': with_image_count,
        'not_found': len(results) - found_count
    }


# ============= PRICE COMPARISON =============

def get_market_price_comparison(barcode, customer_price):
    """Compare customer price with market price"""
    result = full_barcode_lookup(barcode, user_id=0, auto_download=False)
    
    if not result['found'] or not result.get('product'):
        return {
            'has_comparison': False,
            'message': 'Piyasa fiyatı bulunamadı'
        }
    
    product = result['product']
    market_price = product.get('price_with_tax') or product.get('price', 0)
    
    if market_price <= 0:
        return {
            'has_comparison': False,
            'message': 'Piyasa fiyatı mevcut değil'
        }
    
    difference = customer_price - market_price
    percentage = ((customer_price - market_price) / market_price) * 100
    
    if percentage < -10:
        message = f"🎉 Bu ürün piyasa ortalamasının %{abs(percentage):.0f} altında!"
    elif percentage < 0:
        message = f"✨ Fiyatınız piyasa ortalamasından %{abs(percentage):.0f} daha uygun."
    elif percentage < 10:
        message = f"📊 Fiyatınız piyasa ortalamasına yakın (₺{market_price:.2f})."
    else:
        message = f"💡 Bu ürün piyasa ortalamasının %{percentage:.0f} üzerinde."
    
    return {
        'has_comparison': True,
        'market_price': market_price,
        'customer_price': customer_price,
        'difference': difference,
        'percentage': round(percentage, 1),
        'message': message,
        'product_name': product.get('name', ''),
        'source': result.get('source', '')
    }


# ============= CACHE MANAGEMENT =============

def clear_cache(barcode=None):
    """Clear API cache"""
    try:
        if barcode:
            count = 0
            for suffix in ['combined', 'openfoodfacts', 'camgoz']:
                cache_file = _get_cache_path(barcode, suffix)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    count += 1
            return {'success': True, 'cleared_count': count}
        else:
            count = 0
            if os.path.exists(CACHE_PATH):
                for filename in os.listdir(CACHE_PATH):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(CACHE_PATH, filename))
                        count += 1
            return {'success': True, 'cleared_count': count}
            
    except Exception as e:
        logging.error(f"Cache clear error: {e}")
        return {'success': False, 'error': str(e)}


def get_cache_stats():
    """Get cache statistics"""
    try:
        if not os.path.exists(CACHE_PATH):
            return {'count': 0, 'size_mb': 0}
        
        count = 0
        total_size = 0
        
        for filename in os.listdir(CACHE_PATH):
            if filename.endswith('.json'):
                count += 1
                total_size += os.path.getsize(os.path.join(CACHE_PATH, filename))
        
        return {
            'count': count,
            'size_mb': round(total_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logging.error(f"Cache stats error: {e}")
        return {'count': 0, 'size_mb': 0, 'error': str(e)}


# ============= API STATUS =============

def get_api_status():
    """Get status of all configured APIs"""
    return {
        'camgoz': {
            'configured': bool(CAMGOZ_API_KEY),
            'active': True,
            'description': 'CAMGOZ/JoJAPI - Türk ürünleri veritabanı (ürün adı, grup, fiyat)',
            'requires_key': True,
            'provides': ['name', 'category', 'price', 'price_with_tax']
        },
        'google_search': {
            'configured': bool(GOOGLE_API_KEY and GOOGLE_SEARCH_CX),
            'active': True,
            'description': 'Google Custom Search - Profesyonel ürün görselleri',
            'requires_key': True,
            'provides': ['image'],
            'daily_limit': '100 ücretsiz / gün'
        },
        'n11': {
            'configured': bool(N11_API_KEY),
            'active': False,
            'description': 'N11 API - E-ticaret ürün veritabanı (Yakında)',
            'requires_key': True,
            'provides': ['name', 'category', 'price']
        },
        'trendyol': {
            'configured': bool(TRENDYOL_API_KEY),
            'active': False,
            'description': 'Trendyol API - E-ticaret ürün veritabanı (Yakında)',
            'requires_key': True,
            'provides': ['name', 'category', 'price']
        }
    }


def get_product_info_summary():
    """
    Explain what info comes from API vs manual entry
    """
    return {
        'from_api': {
            'camgoz': {
                'name': 'Ürün Adı',
                'category': 'Ürün Grubu (admin onayı ile kategorize edilir)',
                'price': 'Piyasa Satış Fiyatı (sadece admin görür)',
                'price_with_tax': 'KDV Dahil Fiyat (Hayalet karşılaştırma için kullanır)'
            }
        },
        'manual_entry': {
            'image': 'Ürün Resmi (manuel yükleme veya AI oluşturma)',
            'customer_price': 'Müşteri Satış Fiyatı',
            'discount_price': 'İndirimli Fiyat',
            'slogan': 'Kampanya Sloganı'
        },
        'ghost_features': {
            'price_comparison': 'Müşteri fiyatı vs Piyasa fiyatı karşılaştırması',
            'suggestions': 'Fiyat önerileri ve rekabet analizi'
        }
    }


# ============= MULTI-ENGINE IMAGE SEARCH =============
# Priority: DuckDuckGo (unlimited) → Google (100/day) → Bing (1000/month)

def search_with_duckduckgo(query, max_results=6):
    """
    Search images using DuckDuckGo (FREE, no API key, unlimited)
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            # Search for product images
            search_query = f"{query} ürün"
            images = ddgs.images(search_query, max_results=max_results)
            
            for img in images:
                # Get image info
                url = img.get('image', '')
                
                # Calculate quality score based on resolution
                width = img.get('width', 0)
                height = img.get('height', 0)
                quality = calculate_image_quality_score(width, height)
                
                # Bonus for e-commerce sources (reliable product images)
                source = img.get('source', '').lower()
                ecommerce_bonus = 0
                if any(domain in source for domain in ['trendyol', 'hepsiburada', 'n11', 'amazon', 'migros', 'a101', 'bim', 'sok', 'carrefour']):
                    ecommerce_bonus = 20
                
                results.append({
                    'image_url': url,
                    'thumbnail_url': img.get('thumbnail', url),
                    'title': img.get('title', '')[:100],
                    'source': img.get('source', 'DuckDuckGo'),
                    'width': width,
                    'height': height,
                    'quality_score': quality['score'] + ecommerce_bonus,
                    'quality_indicator': quality['quality_indicator'],
                    'search_engine': 'duckduckgo'
                })
        
        logging.info(f"✅ DuckDuckGo: Found {len(results)} images for '{query}'")
        return results
        
    except ImportError:
        logging.warning("duckduckgo_search not installed")
        return []
    except Exception as e:
        logging.error(f"DuckDuckGo search error: {e}")
        return []


# ============= BING GLOBAL SEARCH =============
# Global search without region filter - finds international products

def search_with_bing_global(query, max_results=6):
    """
    Search images using Bing (GLOBAL - no region filter)
    Uses DuckDuckGo backend which queries Bing
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            # Global search - no Turkish filter
            search_query = f"{query} product image"
            images = ddgs.images(search_query, region='wt-wt', max_results=max_results)
            
            for img in images:
                url = img.get('image', '')
                
                width = img.get('width', 0)
                height = img.get('height', 0)
                quality = calculate_image_quality_score(width, height)
                
                # Bonus for international e-commerce
                source = img.get('source', '').lower()
                ecommerce_bonus = 0
                if any(domain in source for domain in ['amazon', 'ebay', 'walmart', 'alibaba', 'aliexpress']):
                    ecommerce_bonus = 15
                
                results.append({
                    'image_url': url,
                    'thumbnail_url': img.get('thumbnail', url),
                    'title': img.get('title', '')[:100],
                    'source': img.get('source', 'Bing Global'),
                    'width': width,
                    'height': height,
                    'quality_score': quality['score'] + ecommerce_bonus,
                    'quality_indicator': quality['quality_indicator'],
                    'search_engine': 'bing_global'
                })
        
        logging.info(f"✅ Bing Global: Found {len(results)} images for '{query}'")
        return results
        
    except Exception as e:
        logging.error(f"Bing Global search error: {e}")
        return []


# ============= E-COMMERCE API HOOKS (FUTURE) =============
# These are ready to be activated when API keys are available

def search_with_n11(query, max_results=6):
    """
    N11 API Hook - Ready for future implementation
    Status: PASSIVE - Activate when API key available
    """
    if not N11_API_KEY or not N11_API_URL:
        return []  # Silently skip if not configured
    
    # TODO: Implement N11 API search
    # API Docs: https://api.n11.com/
    logging.info("N11 API hook called - not yet implemented")
    return []


def search_with_trendyol(query, max_results=6):
    """
    Trendyol API Hook - Ready for future implementation
    Status: PASSIVE - Activate when API key available
    """
    if not TRENDYOL_API_KEY or not TRENDYOL_API_URL:
        return []  # Silently skip if not configured
    
    # TODO: Implement Trendyol API search
    # API Docs: https://developers.trendyol.com/
    logging.info("Trendyol API hook called - not yet implemented")
    return []


def search_with_hepsiburada(query, max_results=6):
    """
    Hepsiburada API Hook - Ready for future implementation
    Status: PASSIVE - Activate when API key available
    """
    if not HEPSIBURADA_API_KEY or not HEPSIBURADA_API_URL:
        return []  # Silently skip if not configured
    
    # TODO: Implement Hepsiburada API search
    # API Docs: https://developers.hepsiburada.com/
    logging.info("Hepsiburada API hook called - not yet implemented")
    return []


def search_with_gittigidiyor(query, max_results=6):
    """
    GittiGidiyor API Hook - Ready for future implementation
    Status: PASSIVE - Activate when API key available
    Note: GittiGidiyor is now part of eBay Turkey
    """
    if not GITTIGIDIYOR_API_KEY or not GITTIGIDIYOR_API_URL:
        return []  # Silently skip if not configured
    
    # TODO: Implement GittiGidiyor/eBay API search
    logging.info("GittiGidiyor API hook called - not yet implemented")
    return []


# ============= E-COMMERCE SITE SCRAPING =============
# Turkish e-commerce sites for product images via Google site search

ECOMMERCE_SITES = [
    'asyasanalmarket.com',
    'eonbir.com.tr',
    'marketkarsilastir.com',
    'aykanlarkapida.com',
    'evkiba.com',
    'migros.com.tr',
    'a101.com.tr',
    'sokmarket.com.tr',
    'bizimtoptan.com.tr',
    'carrefoursa.com'
]

def search_ecommerce_sites(barcode, max_results=5):
    """
    Search Turkish e-commerce sites for product images using Google site search.
    Returns images from trusted e-commerce sources.
    """
    if not barcode or len(str(barcode)) < 8:
        return []
    
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        logging.warning("Google API not configured for e-commerce search")
        return []
    
    results = []
    
    try:
        # Build site-specific search query
        site_filter = ' OR '.join([f'site:{site}' for site in ECOMMERCE_SITES[:5]])
        search_query = f"{barcode} ({site_filter})"
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_CX,
            'q': search_query,
            'searchType': 'image',
            'num': min(max_results, 10),
            'imgSize': 'large',
            'safe': 'active'
        }
        
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                image_info = item.get('image', {})
                url = item.get('link', '')
                source = item.get('displayLink', '').lower()
                
                # Check if from our trusted e-commerce sites
                is_ecommerce = any(site in source for site in ECOMMERCE_SITES)
                
                width = image_info.get('width', 0)
                height = image_info.get('height', 0)
                quality = calculate_image_quality_score(width, height)
                
                # E-commerce bonus
                ecommerce_bonus = 40 if is_ecommerce else 0
                
                results.append({
                    'image_url': url,
                    'thumbnail_url': image_info.get('thumbnailLink', ''),
                    'title': item.get('title', '')[:100],
                    'source': item.get('displayLink', 'E-commerce'),
                    'width': width,
                    'height': height,
                    'quality_score': quality['score'] + ecommerce_bonus,
                    'quality_indicator': quality['quality_indicator'],
                    'search_engine': 'ecommerce',
                    'is_ecommerce': is_ecommerce
                })
            
            # Sort by e-commerce first, then quality
            results.sort(key=lambda x: (x.get('is_ecommerce', False), x.get('quality_score', 0)), reverse=True)
            
            logging.info(f"✅ E-commerce Search: Found {len(results)} images for barcode {barcode}")
            return results[:max_results]
        
        return []
        
    except Exception as e:
        logging.error(f"E-commerce search error: {e}")
        return []


# ============= YANDEX IMAGE SEARCH =============

def search_with_yandex(query, max_results=6):
    """
    Search images using Yandex (via DuckDuckGo backend).
    Yandex has good coverage for Turkish/Russian products.
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            # Sadece barkod veya ürün adı ile ara (fotoğraf kelimesi ekleme!)
            search_query = query
            images = ddgs.images(search_query, region='tr-tr', max_results=max_results)
            
            for img in images:
                url = img.get('image', '')
                
                width = img.get('width', 0)
                height = img.get('height', 0)
                quality = calculate_image_quality_score(width, height)
                
                # Bonus for Turkish e-commerce sources
                source = img.get('source', '').lower()
                ecommerce_bonus = 0
                if any(domain in source for domain in ECOMMERCE_SITES):
                    ecommerce_bonus = 30
                
                results.append({
                    'image_url': url,
                    'thumbnail_url': img.get('thumbnail', url),
                    'title': img.get('title', '')[:100],
                    'source': img.get('source', 'Yandex'),
                    'width': width,
                    'height': height,
                    'quality_score': quality['score'] + ecommerce_bonus,
                    'quality_indicator': quality['quality_indicator'],
                    'search_engine': 'yandex'
                })
        
        logging.info(f"✅ Yandex: Found {len(results)} images for '{query}'")
        return results
        
    except ImportError:
        logging.warning("duckduckgo_search not installed for Yandex")
        return []
    except Exception as e:
        logging.error(f"Yandex search error: {e}")
    return []


# ============= ACTIVE SEARCH ENGINES =============

def search_with_google(query, max_results=6):
    """
    Search images using Google Custom Search API (100 free/day)
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX:
        return []
    
    try:
        search_query = query  # Sadece barkod/ürün adı ile ara
        
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_CX,
            'q': search_query,
            'searchType': 'image',
            'num': min(max_results, 10),
            'imgSize': 'large',
            'imgType': 'photo',
            'safe': 'active',
            'lr': 'lang_tr'
        }
        
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            results = []
            for item in items:
                image_info = item.get('image', {})
                url = item.get('link', '')
                width = image_info.get('width', 0)
                height = image_info.get('height', 0)
                
                quality = calculate_image_quality_score(width, height)
                
                source = item.get('displayLink', '').lower()
                ecommerce_bonus = 0
                if any(domain in source for domain in ['trendyol', 'hepsiburada', 'n11', 'amazon', 'migros', 'a101', 'bim', 'sok', 'carrefour']):
                    ecommerce_bonus = 20
                
                results.append({
                    'image_url': url,
                    'thumbnail_url': image_info.get('thumbnailLink', ''),
                    'title': item.get('title', '')[:100],
                    'source': item.get('displayLink', 'Google'),
                    'width': width,
                    'height': height,
                    'quality_score': quality['score'] + ecommerce_bonus,
                    'quality_indicator': quality['quality_indicator'],
                    'search_engine': 'google'
                })
            
            logging.info(f"✅ Google: Found {len(results)} images for '{query}'")
            return results
        
        elif response.status_code == 403:
            logging.warning("Google API daily limit reached")
            return []
        else:
            return []
            
    except Exception as e:
        logging.error(f"Google search error: {e}")
        return []


def calculate_relevance_score(title, barcode, product_name):
    """
    Calculate how relevant a search result is to the barcode/product name.
    Higher score = more relevant. Negative score = definitely unrelated.
    """
    if not title:
        return -100
    
    title_lower = title.lower()
    score = 0
    
    # Check if barcode is in title (+60)
    if barcode and barcode in title:
        score += 60
    
    # Check product name words in title
    if product_name:
        name_words = product_name.lower().split()
        for word in name_words:
            if len(word) > 2 and word in title_lower:
                score += 20  # +20 per matching word
    
    # Bonus for common product keywords (deterjan, gıda, temizlik)
    product_keywords = ['deterjan', 'detergent', 'toz', 'powder', 'sabun', 'soap', 
                        'şampuan', 'shampoo', 'çamaşır', 'laundry', 'bulaşık',
                        'kg', 'lt', 'ml', 'gr', 'adet', 'paket']
    for keyword in product_keywords:
        if keyword in title_lower:
            score += 10
    
    # Brand detection - common Turkish product brands
    brands = ['alo', 'ariel', 'persil', 'fairy', 'pril', 'domestos', 'ace', 'bingo', 
              'omo', 'rinso', 'comfort', 'yumoş', 'vernel']
    for brand in brands:
        if brand in title_lower:
            score += 25  # Strong bonus for known brands
    
    # STRONG penalty for clearly unrelated categories
    unrelated_keywords = ['kozmetik', 'cosmetic', 'makyaj', 'makeup', 'parfüm', 'perfume', 
                          'tattoo', 'kaş', 'ruj', 'lipstick', 'maskara', 'eyeliner', 'rimel',
                          'fondöten', 'foundation', 'allık', 'blush', 'oje', 'nail',
                          'maybelline', 'loreal', 'nivea', 'garnier',
                          'oyuncak', 'toy', 'kitap', 'book', 'telefon', 'phone', 'tablet',
                          'giyim', 'clothing', 'ayakkabı', 'shoe', 'çanta', 'bag']
    for keyword in unrelated_keywords:
        if keyword in title_lower:
            score -= 100  # Very strong penalty - will be filtered out
    
    return score  # Can go negative


def search_product_by_name(product_name, barcode=None):
    """
    Multi-engine image search with smart fallback.
    
    Search Order (2. Sorgu - AI Öner butonu):
    1. Google Image Search
    2. Yandex Image Search
    
    Note: Market siteleri (asyasanalmarket, marketkarsilastir) 
          ayrı endpoint ile aranır ve frontend'de birleştirilir.
    
    Filters results with 75% relevance threshold.
    Returns best 5 relevant images.
    """
    if not product_name or len(product_name.strip()) < 3:
        return {'success': False, 'error': 'Ürün adı en az 3 karakter olmalı'}
    
    query = product_name.strip()
    all_results = []
    engines_used = []
    
    # ============= 2. SORGU: SADECE GOOGLE + YANDEX =============
    
    # 1. GOOGLE IMAGE SEARCH
    google_results = search_with_google(query, max_results=5)
    if google_results:
        all_results.extend(google_results)
        engines_used.append('Google')
    
    # 2. YANDEX IMAGE SEARCH (good for Turkish products)
    yandex_results = search_with_yandex(query, max_results=5)
    if yandex_results:
        all_results.extend(yandex_results)
        engines_used.append('Yandex')
    
    if not all_results:
        logging.warning(f"⚠️ No images found for '{query}' in any search engine")
        return {
            'success': True,
            'results': [],
            'query': query,
            'message': 'Görsel bulunamadı',
            'barcode': barcode
        }
    
    # ============= CALCULATE RELEVANCE SCORES =============
    for result in all_results:
        relevance = calculate_relevance_score(result.get('title', ''), barcode, query)
        result['relevance_score'] = relevance
        # Combine quality and relevance for final score (relevance weighted 3x)
        result['combined_score'] = result.get('quality_score', 0) + (relevance * 3)
    
    # ============= %75 EŞLEŞME FİLTRESİ =============
    # Filter out results with relevance score below 75% of max possible
    max_relevance = max([r['relevance_score'] for r in all_results]) if all_results else 0
    relevance_threshold = max_relevance * 0.75 if max_relevance > 0 else 0
    
    # First filter: Remove definitely unrelated (negative relevance)
    filtered_results = [r for r in all_results if r['relevance_score'] >= 0]
    
    # Second filter: Apply 75% threshold (only if we have good matches)
    if max_relevance > 20:  # Only apply if we have decent matches
        high_relevance_results = [r for r in filtered_results if r['relevance_score'] >= relevance_threshold]
        if high_relevance_results:
            filtered_results = high_relevance_results
    
    # Sort by combined score (e-commerce + quality + relevance)
    filtered_results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # If all filtered out, fall back to original sorted by quality only
    if not filtered_results:
        all_results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        relevant_results = all_results
    else:
        relevant_results = filtered_results
    
    # Remove duplicates based on image URL
    seen_urls = set()
    unique_results = []
    for r in relevant_results:
        if r['image_url'] not in seen_urls:
            seen_urls.add(r['image_url'])
            unique_results.append(r)
    
    # Take best 5 results
    top_results = unique_results[:5]
    
    logging.info(f"✅ Multi-Search: Found {len(top_results)} relevant images for '{query}' using {', '.join(engines_used)}")
    
    return {
        'success': True,
        'results': top_results,
        'query': query,
        'total': len(top_results),
        'barcode': barcode,
        'engines_used': engines_used,
        'relevance_threshold': relevance_threshold
    }
