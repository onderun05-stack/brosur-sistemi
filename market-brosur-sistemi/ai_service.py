import os
import json
import requests
from openai import OpenAI
from datetime import datetime

# OpenAI configuration
# Using gpt-4o as it's more stable for text generation
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Model constant for easy updates
GPT_MODEL = "gpt-4o"

def suggest_slogan(product_name, normal_price, discount_price):
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        discount_percent = int(((normal_price - discount_price) / normal_price) * 100)
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Sen yaratıcı bir market broşürü copywriter'ısın. Türkçe, kısa ve etkili sloganlar oluşturuyorsun. JSON formatında yanıt ver."
                },
                {
                    "role": "user",
                    "content": f"'{product_name}' ürünü için 3 farklı slogan öner. Normal fiyat: {normal_price}₺, İndirimli fiyat: {discount_price}₺ (%{discount_percent} indirim). Her slogan maksimum 8 kelime olsun. JSON formatında döndür: {{\"slogans\": [\"slogan1\", \"slogan2\", \"slogan3\"]}}"
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=500
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return {
                'success': True,
                'slogans': result.get('slogans', [])
            }
        return {'success': False, 'error': 'No content received'}
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def search_product_images(product_name, barcode):
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir ürün görseli uzmanısın. Ürün adı ve barkoduna göre Unsplash'ten uygun görseller öneriyorsun."
                },
                {
                    "role": "user",
                    "content": f"'{product_name}' (barkod: {barcode}) ürünü için 3 farklı Unsplash arama terimi öner. İngilizce ve kısa olsun. JSON formatında döndür: {{\"search_terms\": [\"term1\", \"term2\", \"term3\"]}}"
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=300
        )
        
        content = response.choices[0].message.content
        if not content:
            return {'success': False, 'error': 'No content received', 'images': []}
        result = json.loads(content)
        search_terms = result.get('search_terms', [])
        
        images = []
        unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY', '')
        
        for term in search_terms[:3]:
            if unsplash_access_key:
                unsplash_api_url = f"https://api.unsplash.com/search/photos?query={term}&per_page=1&client_id={unsplash_access_key}"
                try:
                    unsplash_response = requests.get(unsplash_api_url)
                    if unsplash_response.status_code == 200:
                        data = unsplash_response.json()
                        if data.get('results') and len(data['results']) > 0:
                            image_url = data['results'][0]['urls']['regular']
                            images.append({
                                'url': image_url,
                                'term': term
                            })
                        else:
                            images.append({
                                'url': f"https://source.unsplash.com/400x400/?{term}",
                                'term': term
                            })
                    else:
                        images.append({
                            'url': f"https://source.unsplash.com/400x400/?{term}",
                            'term': term
                        })
                except:
                    images.append({
                        'url': f"https://source.unsplash.com/400x400/?{term}",
                        'term': term
                    })
            else:
                images.append({
                    'url': f"https://source.unsplash.com/400x400/?{term}",
                    'term': term
                })
        
        return {
            'success': True,
            'images': images
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'images': []
        }

def generate_price_variants(product_name, price):
    if not client:
        return {'success': False, 'error': 'OpenAI API key not configured', 'variants': []}
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{
                "role": "system",
                "content": "Fiyat etiketi varyantları oluştur. Türkçe, kısa, etkileyici."
            }, {
                "role": "user",
                "content": f"'{product_name}' ({price}₺) için 3 fiyat etiketi tasarısı öner. JSON: {{\"variants\": [\"v1\", \"v2\", \"v3\"]}}"
            }],
            response_format={"type": "json_object"},
            max_completion_tokens=200
        )
        result = json.loads(response.choices[0].message.content or '{}')
        return {'success': True, 'variants': result.get('variants', [])}
    except Exception as e:
        return {'success': False, 'error': str(e), 'variants': []}

def generate_descriptions(product_names):
    if not client:
        return {'success': False, 'error': 'OpenAI API key not configured', 'descriptions': {}}
    try:
        products_list = ', '.join(product_names[:10])
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{
                "role": "system",
                "content": "Kısa, çekici ürün açıklamaları yaz. Türkçe."
            }, {
                "role": "user",
                "content": f"Bu ürünler için birer satır açıklama: {products_list}. JSON formatında, descriptions key'i altında return et."
            }],
            response_format={"type": "json_object"},
            max_completion_tokens=300
        )
        result = json.loads(response.choices[0].message.content or '{}')
        return {'success': True, 'descriptions': result.get('descriptions', {})}
    except Exception as e:
        return {'success': False, 'error': str(e), 'descriptions': {}}

def generate_page_titles(page_count):
    if not client:
        return {'success': False, 'error': 'OpenAI API key not configured', 'titles': []}
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{
                "role": "system",
                "content": "Market broşürü sayfa başlıkları oluştur. Türkçe, kısa, etkileyici."
            }, {
                "role": "user",
                "content": f"{page_count} sayfa için başlıklar: '1. Hafta Fırsatları', '2. Hafta Fırsatları'... JSON: {{\"titles\": [\"t1\", \"t2\", ...]}}"
            }],
            response_format={"type": "json_object"},
            max_completion_tokens=200
        )
        result = json.loads(response.choices[0].message.content or '{}')
        return {'success': True, 'titles': result.get('titles', [])}
    except Exception as e:
        return {'success': False, 'error': str(e), 'titles': []}

def generate_color_theme():
    if not client:
        return {'success': False, 'error': 'OpenAI API key not configured', 'theme': {}}
    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{
                "role": "system",
                "content": "Market broşürü için renk teması öner. Profesyonel ve çekici."
            }, {
                "role": "user",
                "content": "3 renk tema öner (hex codes): birincil, ikincil, vurgu renkleri. JSON: {\"themes\": [{\"primary\": \"#...\", \"secondary\": \"#...\", \"accent\": \"#...\"}]}"
            }],
            response_format={"type": "json_object"},
            max_completion_tokens=200
        )
        result = json.loads(response.choices[0].message.content or '{}')
        return {'success': True, 'themes': result.get('themes', [])}
    except Exception as e:
        return {'success': False, 'error': str(e), 'themes': []}

def generate_auto_brochure(products):
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        from collections import defaultdict
        
        groups = defaultdict(list)
        for i, p in enumerate(products[:20]):
            group = p.get('product_group', 'Genel')
            groups[group].append({
                'index': i,
                'name': p['name'],
                'discount': ((p.get('normal_price', 0) - p.get('discount_price', 0)) / (p.get('normal_price', 1) or 1) * 100) if p.get('normal_price') else 0
            })
        
        products_by_group = "\n".join([
            f"\n{group}:\n" + "\n".join([f"  {i+1}. {item['name']} (İndirim: {item['discount']:.0f}%)" for i, item in enumerate(group_items)])
            for group, group_items in sorted(groups.items())
        ])
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Ürün gruplarını dikkate alarak 3-4 sayfaya akıllıca dağıt. Her sayfa bir veya iki grup içerebilir."
                },
                {
                    "role": "user",
                    "content": f"Grup bazlı ürünleri en etkili şekilde 3-4 sayfaya dağıt:\n{products_by_group}\n\nFormat: {{\"pages\": [{{\"title\": \"Sayfa\", \"product_indices\": [0,1,2]}}]}}"
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=1000
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return {
                'success': True,
                'pages': result.get('pages', [])
            }
        return {'success': False, 'error': 'No content received', 'pages': []}
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'pages': []
        }

def generate_background_with_dalle(theme='market', season='summer', product_category='food'):
    """
    Generate professional Turkish supermarket brochure background using DALL-E 3
    Referans: Kırmızı Market tarzı profesyonel broşür arka planı
    Theme: 'market', 'discount', 'tea', 'fresh', 'butcher'
    Season: 'summer', 'winter', 'autumn', 'spring'
    Category: 'food', 'electronics', 'cleaning', 'beverages'
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        # Kırmızı Market tarzı profesyonel Türk market broşürü prompt'ları
        prompts = {
            'market': f"""
                Professional Turkish supermarket brochure background, print-ready quality.
                
                STYLE REFERENCE: Traditional Turkish grocery store weekly flyer (like BIM, A101, ŞOK markets)
                
                COMPOSITION:
                - TOP BANNER AREA (15% height): Golden/cream colored decorative header strip with subtle ornamental pattern
                - MAIN CONTENT AREA (70% height): Clean white/light cream background with subtle texture
                - BOTTOM STRIP (15% height): Matching footer area for store info
                
                DESIGN ELEMENTS:
                - Soft green gradient accents (like tea plantation fields - yeşil çay tarlası)
                - Subtle diagonal light rays from top corners
                - Very light watermark pattern (barely visible geometric shapes)
                - Professional drop shadows for depth
                - Clean grid layout guides (invisible but structured)
                
                COLOR PALETTE:
                - Primary: Forest green (#228B22), Golden yellow (#FFD700)
                - Secondary: Cream white (#FFFDD0), Light gray (#F5F5F5)
                - Accents: Red (#E31837) for discount highlights
                
                MUST HAVE:
                - Large empty rectangular areas for product placement (3x3 or 4x3 grid)
                - Space at top for logo and date banner
                - Professional print quality, 300 DPI look
                - NO text, NO products, NO prices - ONLY the background template
                - Turkish market aesthetic - warm, inviting, family-friendly
                
                STYLE: Clean, organized, professional retail advertising
                FORMAT: Vertical A4 proportion (595x842 pixels ratio)
            """,
            
            'discount': f"""
                Explosive Turkish supermarket SALE brochure background, premium print quality.
                
                STYLE: "SÜPER İNDİRİM" / "ŞOK FİYAT" campaign style
                
                COMPOSITION:
                - Dramatic red-to-yellow gradient burst from center
                - Starburst/explosion pattern radiating outward
                - Golden sparkle effects scattered throughout
                - White/cream product placement zones (clean rectangles)
                
                DESIGN ELEMENTS:
                - Bold red (#E31837) as dominant color
                - Yellow (#FFD700) highlight accents
                - White clean zones for product cards
                - Subtle confetti or celebration particles
                - Professional retail advertising quality
                
                MUST HAVE:
                - Empty rectangular zones for 8-12 products
                - Top banner area for "İNDİRİM" text
                - Bottom strip for store info
                - High energy, exciting, urgent feeling
                - NO text, NO products - ONLY background template
                
                FORMAT: Vertical A4 proportion
            """,
            
            'tea': f"""
                Turkish tea-themed supermarket brochure background, professional quality.
                
                STYLE: Çay kampanyası broşürü (Tea campaign flyer)
                
                MAIN VISUAL:
                - Beautiful green tea plantation hillside (Rize/Karadeniz style)
                - Rolling hills covered with lush tea bushes
                - Soft morning mist in valleys
                - Golden sunlight from top-right corner
                
                COMPOSITION:
                - Tea plantation fills 40% of background (top area)
                - Gradient fade to cream/white for product area (bottom 60%)
                - Traditional Turkish tea glass silhouette as watermark
                
                COLOR PALETTE:
                - Dominant: Tea green (#4A7C59), Forest green (#228B22)
                - Accent: Golden amber (#FFBF00) like brewed tea
                - Base: Warm cream (#FFF8DC)
                
                MUST HAVE:
                - Clean white/cream zones for product placement
                - Professional print quality
                - Warm, traditional, authentic Turkish feeling
                - NO text, NO products - ONLY background
                
                FORMAT: Vertical A4 proportion
            """,
            
            'fresh': f"""
                Fresh produce Turkish market brochure background, professional quality.
                
                STYLE: Manav/Sebze-Meyve kampanyası (Fresh produce campaign)
                
                MAIN VISUAL:
                - Wooden market stall texture at edges
                - Fresh green leaves and herbs as decorative border
                - Water droplets for freshness effect
                - Natural sunlight feeling
                
                COLOR PALETTE:
                - Fresh green (#32CD32), Leaf green (#228B22)
                - Warm wood brown (#8B4513)
                - Clean white (#FFFFFF) for product zones
                - Accent: Orange (#FF8C00), Red (#FF6347) for warmth
                
                MUST HAVE:
                - Large clean areas for product photos
                - Fresh, healthy, organic feeling
                - Farm-to-table aesthetic
                - NO text, NO products - ONLY background
                
                FORMAT: Vertical A4 proportion
            """,
            
            'butcher': f"""
                Turkish butcher shop brochure background, premium quality.
                
                STYLE: Kasap/Et kampanyası (Meat products campaign)
                
                MAIN VISUAL:
                - Rich dark wood texture border
                - Subtle marble/stone pattern in center
                - Warm amber lighting effect
                - Traditional butcher shop aesthetic
                
                COLOR PALETTE:
                - Deep burgundy red (#722F37)
                - Dark wood brown (#3E2723)
                - Cream marble (#F5F5DC)
                - Gold accents (#D4AF37)
                
                MUST HAVE:
                - Premium, high-end feeling
                - Clean zones for meat product photos
                - Trustworthy, quality impression
                - NO text, NO products - ONLY background
                
                FORMAT: Vertical A4 proportion
            """
        }
        
        # Tema seçimi
        selected_prompt = prompts.get(theme, prompts['market'])
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=selected_prompt,
            size="1024x1792",  # Vertical A4 oranı için
            quality="hd",
            n=1
        )
        
        if response.data and len(response.data) > 0:
            return {
                'success': True,
                'background_url': response.data[0].url
            }
        return {
            'success': False,
            'error': 'No image data received'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def suggest_slogans():
    """
    Generate 5 catchy campaign slogans based on current day of week
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured',
            'slogans': []
        }
    
    try:
        weekday = datetime.now().strftime('%A')
        
        day_prompts = {
            'Monday': 'Hafta Başı Fırsatları - Yeni haftaya taze başla!',
            'Tuesday': 'Salı İndirimleri - Hafta ortasına özel!',
            'Wednesday': 'Çarşamba Şöleni - Haftanın kalbi!',
            'Thursday': 'Perşembe Kampanyası - Hafta sonu hazırlığı!',
            'Friday': 'Cuma Coşkusu - Hafta Sonu Şöleni!',
            'Saturday': 'Cumartesi Fırsatları - Hafta sonu keyfi!',
            'Sunday': 'Pazar Günü Avantajları - Ailenle alışveriş zamanı!'
        }
        
        day_context = day_prompts.get(weekday, 'Özel Fırsatlar')
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Türk süpermarketleri için 5 adet kısa ve çekici indirim sloganı yaz. Her slogan tek satırda olsun. Sadece sloganları listele."
                }
            ],
            max_completion_tokens=300
        )
        
        if not response.choices:
            return {
                'success': False,
                'error': 'No choices in API response',
                'slogans': []
            }
        
        message = response.choices[0].message
        content = getattr(message, 'content', '') or ''
        
        if not content:
            return {
                'success': False,
                'error': 'No content received from API',
                'slogans': []
            }
        
        slogans = [s.strip('0123456789. -•*') for s in content.strip().split('\n') if s.strip()]
        slogans = [s for s in slogans if len(s) > 3][:5]
        
        return {
            'success': True,
            'slogans': slogans
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'slogans': []
        }

def generate_slogan_image(slogan_text, style='modern'):
    """
    Generate 3D premium slogan image using DALL-E 3
    Alias function for backward compatibility
    """
    return generate_slogan_image_dalle(slogan_text)


def generate_product_image(product_name, barcode=''):
    """
    Generate product image using DALL-E 3
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        prompt = f"""
Professional product photography of "{product_name}" for a Turkish supermarket brochure.

REQUIREMENTS:
- Clean white or transparent background
- Professional studio lighting
- High-quality product shot
- Sharp focus, 8K quality
- No text, no labels
- Product centered in frame
- Commercial advertising quality
- Realistic, not AI-looking
        """
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        if response.data and len(response.data) > 0:
            return {
                'success': True,
                'image_url': response.data[0].url,
                'barcode': barcode
            }
        return {
            'success': False,
            'error': 'No image data received'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def generate_slogan_image_dalle(slogan_text):
    """
    Generate 3D premium slogan image using DALL-E 3
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        prompt = f"""
Generate an ultra-premium 3D promotional slogan text image.

TEXT: "{slogan_text}"

REQUIREMENTS:
- 3D extruded lettering with depth and dimension
- Glossy, metallic highlights (gold, silver, or chrome effect)
- Bold supermarket-style typography, thick and impactful
- Strong outline stroke (5-8px) in contrasting color
- Dramatic shadow behind text for depth
- Vibrant gradient colors (red-orange-yellow for discount themes)
- Vector-sharp edges, no pixelation, ultra-crisp
- Render at maximum quality, 8K-ready
- TRANSPARENT BACKGROUND ONLY
- NO other objects, NO icons, NO decorations
- ONLY the text "{slogan_text}" in 3D
- Professional retail signage quality
- The text must be clearly readable and match exactly: "{slogan_text}"

Style: Premium 3D billboard advertising, high-end retail marketing
        """
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        if response.data and len(response.data) > 0:
            return {
                'success': True,
                'image_url': response.data[0].url
            }
        return {
            'success': False,
            'error': 'No image data received'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
