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

def generate_background_with_dalle(theme='market', season='summer', product_category='food', custom_prompt=None):
    """
    Generate professional Turkish supermarket brochure background using DALL-E 3
    Referans: Kırmızı Market, BIM, A101, ŞOK tarzı profesyonel broşür arka planı
    Theme: 'market', 'discount', 'tea', 'fresh', 'butcher', 'classic_red', 'modern_blue', 'grid_clean', 'garden_green', 'premium_dark', 'fresh_produce'
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        # Gerçek Türk market broşürlerine benzer basit ve etkili prompt'lar
        prompts = {
            # ===== YENİ STİLLER (styles.json ile uyumlu) =====
            'classic_red': """
                Simple clean background for Turkish supermarket brochure.
                
                EXACTLY LIKE: Kırmızı Market, BIM, A101 weekly flyers
                
                DESIGN:
                - Solid white or very light cream (#FFFEF0) background
                - Simple red header banner at top (10% height)
                - Clean empty space in middle for products
                - Optional: very subtle grid lines (barely visible)
                
                COLORS: White background, Red (#E31837) header, Green (#228B22) accents
                
                REQUIREMENTS:
                - VERY SIMPLE, CLEAN, MINIMAL
                - NO complex patterns, NO gradients in main area
                - NO decorations, NO textures
                - Just clean solid colors
                - Vertical A4 format (595x842 ratio)
                - NO text, NO products, ONLY background
            """,
            
            'modern_blue': """
                Modern blue gradient background for Turkish supermarket brochure.
                
                EXACTLY LIKE: AEU Yazılım style modern market flyer
                
                DESIGN:
                - Blue gradient from top (#0077b6) to bottom (#48cae4)
                - Yellow/gold header banner at very top
                - Green grass strip at very bottom (5% height)
                - Large empty center for products
                
                COLORS: Blue gradient, Yellow (#FFD60A) header, Green (#06D6A0) footer
                
                REQUIREMENTS:
                - Smooth clean gradient, no texture
                - Simple solid color bands
                - Professional retail poster look
                - Vertical A4 format
                - NO text, NO products, ONLY background
            """,
            
            'grid_clean': """
                Clean cream/beige background for Turkish supermarket brochure.
                
                EXACTLY LIKE: Show Supermarket, Migros weekly flyers
                
                DESIGN:
                - Solid cream/beige color (#F5F5DC)
                - Very subtle shadow zones where products will go
                - Simple header strip area at top
                - Clean footer area at bottom
                
                COLORS: Cream (#F5F5DC) main, Orange (#FF6B35) accents
                
                REQUIREMENTS:
                - FLAT solid color, no gradients
                - NO patterns, NO decorations
                - Super clean minimal design
                - Vertical A4 format
                - NO text, NO products, ONLY background
            """,
            
            'garden_green': """
                Green garden/grass background for Turkish home/garden store brochure.
                
                EXACTLY LIKE: Hedef Yapı Market, Koçtaş garden flyers
                
                DESIGN:
                - Lush green grass lawn filling bottom 60%
                - Light blue sky at top 20%
                - Yellow banner strip between sky and grass
                - Grass texture realistic but not busy
                
                COLORS: Green grass (#2D6A4F), Blue sky (#87CEEB), Yellow (#FFD60A) banner
                
                REQUIREMENTS:
                - Realistic grass texture
                - Clean sky, few or no clouds
                - Outdoor summer feeling
                - Vertical A4 format
                - NO text, NO products, ONLY background
            """,
            
            'premium_dark': """
                Dark premium background for Turkish butcher shop brochure.
                
                EXACTLY LIKE: Premium kasap, steakhouse advertisements
                
                DESIGN:
                - Dark burgundy/maroon background (#370617)
                - Subtle wood grain texture overlay
                - Warm amber lighting from corners
                - Rich, luxurious feeling
                
                COLORS: Dark burgundy (#370617), Maroon (#6A040F), Gold (#FFD60A) accents
                
                REQUIREMENTS:
                - Dark but warm colors
                - Subtle texture, not distracting
                - Premium luxury feel
                - Vertical A4 format
                - NO text, NO products, ONLY background
            """,
            
            'fresh_produce': """
                Fresh light green background for Turkish produce market brochure.
                
                EXACTLY LIKE: Fresh manav, organic market flyers
                
                DESIGN:
                - Very light mint green (#E9F5E9) solid background
                - Simple green leaf decorations at corners only
                - Clean white/cream center area
                - Fresh, healthy, organic feeling
                
                COLORS: Light mint (#E9F5E9), Leaf green (#06D6A0), White center
                
                REQUIREMENTS:
                - Very light, airy, fresh colors
                - Minimal leaf decorations (corners only)
                - Clean open space for products
                - Vertical A4 format
                - NO text, NO products, ONLY background
            """,
            
            # ===== ESKİ STİLLER (backward compatibility) =====
            'market': """
                Simple clean white/cream background for Turkish supermarket brochure.
                Like Kırmızı Market, BIM, A101 flyers.
                Solid cream (#FFFEF0) color, red header strip, clean empty center.
                NO patterns, NO textures, just clean solid colors.
                Vertical A4 format, NO text, NO products.
            """,
            
            'discount': """
                Red and yellow sale/discount background for Turkish supermarket.
                Like ŞOK market "İNDİRİM" flyers.
                Red-yellow gradient burst, starburst pattern from center.
                Yellow (#FFD700) and Red (#E31837) colors.
                Empty zones for products, NO text, NO products.
                Vertical A4 format.
            """,
            
            'tea': """
                Green tea plantation themed background for Turkish market.
                Rize/Karadeniz tea fields style.
                Green tea hills at top 40%, fade to cream at bottom.
                Forest green (#228B22) and cream (#FFF8DC) colors.
                Clean zones for tea products, NO text, NO products.
                Vertical A4 format.
            """,
            
            'fresh': """
                Fresh produce green background for Turkish manav/market.
                Light green (#E9F5E9) with leaf decorations at corners.
                Fresh, organic, healthy feeling.
                Clean center for vegetables and fruits.
                NO text, NO products, Vertical A4 format.
            """,
            
            'butcher': """
                Dark premium butcher shop background.
                Dark burgundy (#370617) with wood texture.
                Premium kasap/steakhouse style.
                Warm amber lighting, luxurious feel.
                NO text, NO products, Vertical A4 format.
            """
        }
        
        # Özel prompt varsa onu kullan
        if custom_prompt:
            selected_prompt = custom_prompt
        else:
            selected_prompt = prompts.get(theme, prompts['market'])
        
        # DALL-E 3 ile arka plan oluştur
        response = client.images.generate(
            model="dall-e-3",
            prompt=selected_prompt,
            size="1024x1792",  # Vertical A4-like
            quality="hd",
            n=1
        )
        
        if response.data and len(response.data) > 0:
            return {
                'success': True,
                'background_url': response.data[0].url,
                'theme': theme,
                'model': 'dall-e-3'
            }
        
        return {'success': False, 'error': 'No image generated'}
        
    except Exception as e:
        logging.error(f"DALL-E background generation error: {e}")
        return {'success': False, 'error': str(e)}


def generate_background_with_dalle_OLD(theme='market', season='summer', product_category='food'):
    """
    ESKİ VERSİYON - Karmaşık prompt'lar (yedek olarak saklıyoruz)
    """
    if not client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        prompts_old = {
            'market_old': f"""Professional Turkish supermarket brochure background...""",
            'discount_old': f"""Explosive Turkish supermarket SALE brochure background...""",
            'butcher_old': f"""Turkish butcher shop brochure background, premium quality.
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
