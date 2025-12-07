# -*- coding: utf-8 -*-
"""
Market Sites Scraper Service
2. Sorgu Sistemi - Manuel market sitelerinden görsel arama

Hedef Siteler:
- asyasanalmarket.com
- eonbir.com.tr
- marketkarsilastir.com
- aykanlarkapida.com
- evkiba.com
- Migros, A101, BİM (yedek)

%90 eşleşme filtresi uygulanır.
"""

import requests
from bs4 import BeautifulSoup
import logging
import re
import time
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

# Timeout for requests
REQUEST_TIMEOUT = 10

# User-Agent to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
}


def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings (0-100)"""
    if not str1 or not str2:
        return 0
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    return int(SequenceMatcher(None, str1, str2).ratio() * 100)


def filter_by_similarity(results, query, min_similarity=90):
    """Filter results by similarity threshold"""
    filtered = []
    for result in results:
        name = result.get('name', '')
        similarity = calculate_similarity(name, query) if query else 100
        result['similarity'] = similarity
        if similarity >= min_similarity or not query:
            filtered.append(result)
    # Sort by similarity descending
    filtered.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    return filtered


# ============= SITE SCRAPERS =============

def scrape_asyasanalmarket(barcode):
    """
    Scrape asyasanalmarket.com for product by barcode
    """
    results = []
    try:
        search_url = f"https://www.asyasanalmarket.com/arama?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product cards
            products = soup.select('.product-card, .product-item, .product, [class*="product"]')
            
            for product in products[:5]:  # Limit to 5 results
                try:
                    # Try to find image
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://www.asyasanalmarket.com', img_url)
                            
                            # Get product name
                            name_elem = product.select_one('.product-name, .title, h3, h4, [class*="name"]')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'asyasanalmarket',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except Exception as e:
                    logging.debug(f"asyasanalmarket item parse error: {e}")
                    continue
                    
    except Exception as e:
        logging.warning(f"asyasanalmarket scrape error: {e}")
    
    return results


def scrape_eonbir(barcode):
    """
    Scrape eonbir.com.tr for product by barcode
    """
    results = []
    try:
        search_url = f"https://www.eonbir.com.tr/arama?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product-card, .product-item, .product, [class*="product"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://www.eonbir.com.tr', img_url)
                            
                            name_elem = product.select_one('.product-name, .title, h3, h4')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'eonbir',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"eonbir scrape error: {e}")
    
    return results


def scrape_marketkarsilastir(barcode):
    """
    Scrape marketkarsilastir.com for product by barcode
    """
    results = []
    try:
        search_url = f"https://marketkarsilastir.com/ara?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product-card, .product-item, .product, [class*="urun"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://marketkarsilastir.com', img_url)
                            
                            name_elem = product.select_one('.product-name, .title, h3, h4, [class*="name"]')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'marketkarsilastir',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"marketkarsilastir scrape error: {e}")
    
    return results


def scrape_aykanlarkapida(barcode):
    """
    Scrape aykanlarkapida.com for product by barcode
    """
    results = []
    try:
        search_url = f"https://aykanlarkapida.com/arama?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product-card, .product-item, .product, [class*="product"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://aykanlarkapida.com', img_url)
                            
                            name_elem = product.select_one('.product-name, .title, h3, h4')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'aykanlarkapida',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"aykanlarkapida scrape error: {e}")
    
    return results


def scrape_evkiba(barcode):
    """
    Scrape evkiba.com for product by barcode
    """
    results = []
    try:
        search_url = f"https://www.evkiba.com/arama?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product-card, .product-item, .product, [class*="product"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://www.evkiba.com', img_url)
                            
                            name_elem = product.select_one('.product-name, .title, h3, h4')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'evkiba',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"evkiba scrape error: {e}")
    
    return results


# ============= YEDEK SITELER (Migros, A101, BIM) =============

def scrape_migros(barcode):
    """
    Scrape Migros Sanal Market (yedek)
    """
    results = []
    try:
        # Migros API endpoint
        search_url = f"https://www.migros.com.tr/rest/search/screens?q={barcode}&sayfa=0&sirpiala=onerilenler"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            try:
                data = response.json()
                products = data.get('data', {}).get('storeProductInfos', [])
                
                for product in products[:5]:
                    img_url = product.get('images', [{}])[0].get('urls', {}).get('PRODUCT_HD', '')
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = 'https://www.migros.com.tr' + img_url
                        
                        results.append({
                            'source': 'migros',
                            'name': product.get('name', ''),
                            'image_url': img_url,
                            'barcode': barcode
                        })
            except:
                pass
                
    except Exception as e:
        logging.warning(f"migros scrape error: {e}")
    
    return results


def scrape_a101(barcode):
    """
    Scrape A101 (yedek)
    """
    results = []
    try:
        search_url = f"https://www.a101.com.tr/arama/?q={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product-card, .product-item, [class*="product"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://www.a101.com.tr', img_url)
                            
                            name_elem = product.select_one('.product-name, .name, h3, h4')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'a101',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"a101 scrape error: {e}")
    
    return results


def scrape_bim(barcode):
    """
    Scrape BİM (yedek)
    """
    results = []
    try:
        search_url = f"https://www.bim.com.tr/Categories/100/urunler.aspx?search={barcode}"
        response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            products = soup.select('.product, .product-item, [class*="product"]')
            
            for product in products[:5]:
                try:
                    img = product.select_one('img')
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            if not img_url.startswith('http'):
                                img_url = urljoin('https://www.bim.com.tr', img_url)
                            
                            name_elem = product.select_one('.name, .title, h3, h4')
                            name = name_elem.get_text(strip=True) if name_elem else ''
                            
                            results.append({
                                'source': 'bim',
                                'name': name,
                                'image_url': img_url,
                                'barcode': barcode
                            })
                except:
                    continue
                    
    except Exception as e:
        logging.warning(f"bim scrape error: {e}")
    
    return results


# ============= MAIN SEARCH FUNCTION =============

def search_market_sites(barcode, product_name=None, include_backup=True, min_similarity=90):
    """
    Search all market sites for product image by barcode.
    
    Args:
        barcode: Product barcode to search
        product_name: Optional product name for similarity filtering
        include_backup: Include Migros, A101, BIM as backup sources
        min_similarity: Minimum similarity threshold (0-100)
    
    Returns:
        dict: {
            success: bool,
            results: [{source, name, image_url, barcode, similarity}],
            total: int,
            sources_searched: [str]
        }
    """
    all_results = []
    sources_searched = []
    
    # Primary scrapers
    scrapers = [
        ('asyasanalmarket', scrape_asyasanalmarket),
        ('eonbir', scrape_eonbir),
        ('marketkarsilastir', scrape_marketkarsilastir),
        ('aykanlarkapida', scrape_aykanlarkapida),
        ('evkiba', scrape_evkiba),
    ]
    
    # Backup scrapers
    if include_backup:
        scrapers.extend([
            ('migros', scrape_migros),
            ('a101', scrape_a101),
            ('bim', scrape_bim),
        ])
    
    # Run scrapers in parallel for speed
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_source = {
            executor.submit(scraper_func, barcode): source_name
            for source_name, scraper_func in scrapers
        }
        
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            sources_searched.append(source_name)
            
            try:
                results = future.result()
                if results:
                    all_results.extend(results)
                    logging.info(f"✅ {source_name}: {len(results)} results for {barcode}")
            except Exception as e:
                logging.warning(f"❌ {source_name} error: {e}")
    
    # Apply similarity filter if product name provided
    if product_name and min_similarity > 0:
        all_results = filter_by_similarity(all_results, product_name, min_similarity)
    
    # Remove duplicates by image URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        url = result.get('image_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    # Add quality indicator
    for result in unique_results:
        result['quality_indicator'] = '🟢' if result.get('similarity', 0) >= 90 else '🟡'
    
    return {
        'success': len(unique_results) > 0,
        'results': unique_results[:10],  # Limit to top 10
        'total': len(unique_results),
        'sources_searched': sources_searched,
        'barcode': barcode
    }


def search_single_market_site(site_name, barcode):
    """
    Search a single market site by name.
    
    Args:
        site_name: One of 'asyasanalmarket', 'eonbir', 'marketkarsilastir', 
                   'aykanlarkapida', 'evkiba', 'migros', 'a101', 'bim'
        barcode: Product barcode
    
    Returns:
        list: Results from that site
    """
    scrapers = {
        'asyasanalmarket': scrape_asyasanalmarket,
        'eonbir': scrape_eonbir,
        'marketkarsilastir': scrape_marketkarsilastir,
        'aykanlarkapida': scrape_aykanlarkapida,
        'evkiba': scrape_evkiba,
        'migros': scrape_migros,
        'a101': scrape_a101,
        'bim': scrape_bim,
    }
    
    scraper = scrapers.get(site_name.lower())
    if scraper:
        return scraper(barcode)
    return []


















