# -*- coding: utf-8 -*-
"""
Brochure Wizard API Routes
AI-powered brochure creation wizard endpoints
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, session
from functools import wraps

# Import AI services
from services.kie_ai import (
    analyze_products_for_brochure,
    get_ai_brochure_suggestion,
    generate_brochure_background,
    generate_3d_slogan,
    generate_promo_video,
    is_kie_available
)

wizard_bp = Blueprint('wizard', __name__)

# ============= AUTH DECORATOR =============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Giriş yapmalısınız'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============= WIZARD ENDPOINTS =============

@wizard_bp.route('/api/wizard/ai-suggestion', methods=['POST'])
@login_required
def api_wizard_ai_suggestion():
    """
    Get AI suggestions for brochure based on products and purpose
    """
    try:
        data = request.get_json()
        
        products = data.get('products', [])
        purpose = data.get('purpose', 'discount')
        holiday = data.get('holiday')
        analysis = data.get('analysis')
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'Ürün listesi boş',
                'greeting': 'Merhaba! 👋',
                'analysis': 'Henüz ürün göremiyorum.',
                'suggestion': 'Önce ürün yükle, sonra tekrar dene!'
            })
        
        # Analyze products if not provided
        if not analysis:
            analysis = analyze_products_for_brochure(products)
        
        # Determine full purpose string
        full_purpose = purpose
        if purpose == 'holiday' and holiday:
            purpose_map = {
                'ramazan': 'holiday_ramazan',
                'kurban': 'holiday_kurban',
                'yilbasi': 'holiday_newyear',
                'okul': 'discount',  # Use discount template
                'sevgililer': 'holiday'
            }
            full_purpose = purpose_map.get(holiday, 'holiday')
        
        # Get AI suggestion
        suggestion = get_ai_brochure_suggestion(analysis, full_purpose)
        
        if suggestion.get('success'):
            return jsonify(suggestion)
        else:
            # Return fallback suggestion
            return jsonify(generate_fallback_suggestion(analysis, purpose, holiday))
        
    except Exception as e:
        logging.error(f"Wizard AI suggestion error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'greeting': 'Merhaba! 👋',
            'analysis': 'Bir sorun oluştu ama devam edebiliriz.',
            'suggestion': 'Şablon seçerek devam edebilirsin.',
            'slogan': 'Fırsatları Kaçırma!'
        })


@wizard_bp.route('/api/wizard/generate-brochure', methods=['POST'])
@login_required
def api_wizard_generate_brochure():
    """
    Generate the actual brochure with AI-generated content
    """
    try:
        data = request.get_json()
        
        purpose = data.get('purpose', 'discount')
        holiday = data.get('holiday')
        template = data.get('template', 'top-full')
        products = data.get('products', [])
        ai_suggestion = data.get('aiSuggestion', {})
        company_info = data.get('companyInfo', {})
        social_media = data.get('socialMedia', [])
        meal_cards = data.get('mealCards', [])
        logo = data.get('logo', '')
        user_note = data.get('userNote', '')
        
        # Determine theme colors
        colors = ai_suggestion.get('color_theme', {})
        primary_color = colors.get('primary', '#667eea')
        secondary_color = colors.get('secondary', '#764ba2')
        accent_color = colors.get('accent', '#10b981')
        
        # Get slogan
        slogan = ai_suggestion.get('slogan', 'Fırsatları Kaçırma!')
        
        # Determine full purpose for background generation
        full_purpose = purpose
        if purpose == 'holiday' and holiday:
            purpose_map = {
                'ramazan': 'holiday_ramazan',
                'kurban': 'holiday_kurban',
                'yilbasi': 'holiday_newyear'
            }
            full_purpose = purpose_map.get(holiday, purpose)
        
        # Generate background image (if Kie.ai is available)
        background_url = None
        if is_kie_available():
            bg_result = generate_brochure_background(
                purpose=full_purpose,
                colors=[primary_color, secondary_color, accent_color]
            )
            if bg_result.get('success'):
                background_url = bg_result.get('image_url')
        
        # Generate 3D slogan image (if Kie.ai is available)
        slogan_image_url = None
        if is_kie_available() and slogan:
            slogan_result = generate_3d_slogan(slogan)
            if slogan_result.get('success'):
                slogan_image_url = slogan_result.get('image_url')
        
        # Build brochure structure
        brochure = {
            'purpose': purpose,
            'holiday': holiday,
            'template': template,
            'theme': {
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'accent_color': accent_color
            },
            'slogan': slogan,
            'slogan_image': slogan_image_url,
            'background': background_url,
            'company_info': company_info,
            'social_media': social_media,
            'meal_cards': meal_cards,
            'logo': logo,
            'pages': build_brochure_pages(products, ai_suggestion, template)
        }
        
        logging.info(f"Generated brochure for purpose: {purpose}")
        
        return jsonify({
            'success': True,
            'brochure': brochure
        })
        
    except Exception as e:
        logging.error(f"Generate brochure error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@wizard_bp.route('/api/wizard/generate-video', methods=['POST'])
@login_required
def api_wizard_generate_video():
    """
    Generate promotional video for the brochure
    """
    try:
        data = request.get_json()
        
        brochure = data.get('brochure', {})
        purpose = data.get('purpose', 'discount')
        slogan = data.get('slogan', 'Fırsatları Kaçırma!')
        
        if not is_kie_available():
            return jsonify({
                'success': False,
                'error': 'Video üretim servisi şu an kullanılamıyor'
            })
        
        # Get products from brochure
        products = []
        for page in brochure.get('pages', []):
            products.extend(page.get('products', []))
        
        # Generate video
        video_result = generate_promo_video(
            products=products[:5],  # Use top 5 products
            slogan=slogan,
            purpose=purpose,
            duration=8
        )
        
        if video_result.get('success'):
            return jsonify({
                'success': True,
                'video_url': video_result.get('video_url')
            })
        else:
            return jsonify({
                'success': False,
                'error': video_result.get('error', 'Video oluşturulamadı')
            })
        
    except Exception as e:
        logging.error(f"Generate video error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@wizard_bp.route('/api/wizard/status', methods=['GET'])
@login_required
def api_wizard_status():
    """
    Get wizard service status
    """
    return jsonify({
        'success': True,
        'kie_ai_available': is_kie_available(),
        'openai_available': bool(os.environ.get('OPENAI_API_KEY'))
    })


# ============= AI CHAT ENDPOINT =============

@wizard_bp.route('/api/wizard/chat', methods=['POST'])
@login_required
def api_wizard_chat():
    """
    Real AI chat for brochure wizard - uses OpenAI GPT-4o
    """
    import openai
    
    try:
        data = request.get_json()
        
        user_message = data.get('message', '')
        chat_history = data.get('history', [])
        context = data.get('context', {})
        
        # Get context info
        purpose = context.get('purpose', 'general')
        products = context.get('products', [])
        company_name = context.get('companyName', 'Market')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Mesaj boş'})
        
        # Build system prompt based on purpose
        system_prompt = get_chat_system_prompt(purpose, products, company_name)
        
        # Build messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history (last 10 messages)
        for msg in chat_history[-10:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'success': True,
                'message': get_fallback_response(user_message, purpose),
                'tokens_used': 0
            })
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        # Calculate cost (GPT-4o: ~$0.005 per 1K tokens)
        cost_usd = (tokens_used / 1000) * 0.005
        
        return jsonify({
            'success': True,
            'message': ai_message,
            'tokens_used': tokens_used,
            'cost_usd': round(cost_usd, 4)
        })
        
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        return jsonify({
            'success': True,
            'message': get_fallback_response(user_message, purpose),
            'tokens_used': 0,
            'error': 'AI geçici olarak kullanılamıyor'
        })
    except Exception as e:
        logging.error(f"Wizard chat error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


def get_chat_system_prompt(purpose, products, company_name):
    """
    Generate system prompt based on brochure purpose
    """
    product_summary = ""
    if products:
        product_names = [p.get('name', 'Ürün') for p in products[:10]]
        product_summary = f"Müşterinin ürünleri: {', '.join(product_names)}"
        if len(products) > 10:
            product_summary += f" ve {len(products) - 10} ürün daha."
    
    base_prompt = f"""Sen {company_name} için profesyonel broşür tasarım asistanısın. 
Türkçe konuş. Kısa, öz ve yardımcı ol. Emojiler kullan.

{product_summary}

Görevin:
1. Müşterinin ne istediğini anla
2. Somut öneriler sun (slogan, renk, düzen)
3. Seçenekler ver ("A mı B mi?" gibi)
4. Müşteri takılırsa sen öneride bulun
5. Sonunda broşürü oluşturmak için yönlendir

Her yanıtta:
- Bir soru sor VEYA öneri yap
- "Oluşturalım mı?" diye sor hazır olunca"""

    purpose_additions = {
        'discount': """
Özel: Bu bir İNDİRİM broşürü. 
- En yüksek indirimleri vurgula
- "SÜPER FİYAT", "KAÇIRMA", "SON GÜNLER" gibi ifadeler öner
- Kırmızı/sarı dikkat çekici renkler öner""",
        
        'job': """
Özel: Bu bir İŞ İLANI broşürü.
Şunları sor:
- Pozisyon adı (kasiyer, reyon görevlisi, vs.)
- Çalışma şekli (tam/yarı zamanlı)
- Aranan özellikler
- İletişim bilgisi
Profesyonel ama samimi bir dil kullan.""",
        
        'holiday': """
Özel: Bu bir BAYRAM/ÖZEL GÜN broşürü.
- Hangi bayram/gün olduğunu sor
- O güne uygun tebrik mesajı öner
- Sıcak, samimi renkler öner (altın, bordo, yeşil)""",
        
        'grocery': """
Özel: Bu bir MANAV broşürü.
- Taze, doğal imajı vurgula
- Yeşil tonları öner
- "TAZE", "GÜNLÜK", "DOĞAL" ifadeler kullan""",
        
        'butcher': """
Özel: Bu bir KASAP broşürü.
- Kalite ve güven vurgula
- Kırmızı/bordo tonları öner
- "KALİTELİ", "GÜNLÜK KESİM", "HELAL" ifadeler kullan"""
    }
    
    if purpose in purpose_additions:
        base_prompt += purpose_additions[purpose]
    
    return base_prompt


def get_fallback_response(user_message, purpose):
    """
    Fallback response when OpenAI is unavailable
    """
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ['evet', 'tamam', 'olur', 'devam']):
        return "Harika! 🎉 Şimdi broşürünü oluşturmaya hazırız. 'Oluştur' butonuna tıkla!"
    
    if any(word in message_lower for word in ['kasiyer', 'eleman', 'iş', 'personel']):
        return """Anladım, eleman arıyorsunuz! 👨‍💼

Birkaç soru:
1. Pozisyon: Kasiyer mi, reyon görevlisi mi?
2. Çalışma: Tam zamanlı mı, yarı zamanlı mı?
3. Deneyim gerekli mi?

Cevapla, broşürü ona göre hazırlayalım! ✨"""

    if any(word in message_lower for word in ['indirim', 'kampanya', 'fiyat']):
        return """İndirim broşürü için harika! 🔥

Önerim:
- Slogan: "DEV İNDİRİMLER BAŞLADI!"
- Renk: Kırmızı + Sarı (dikkat çekici)
- En yüksek indirimli ürünler öne çıksın

Bu şekilde olsun mu? Yoksa farklı bir slogan mı istersin?"""
    
    if any(word in message_lower for word in ['bayram', 'ramazan', 'kurban']):
        return """Bayram broşürü 🌙

Önerim:
- Tebrik mesajı: "Bayramınız Mübarek Olsun!"
- Renk: Altın + Yeşil (zarif)
- Bayrama özel ürünler öne çıksın

Hangi bayram için hazırlıyoruz?"""
    
    return """Anladım! ✨

Ne tür bir broşür istediğini biraz daha anlat:
• İndirim kampanyası mı?
• İş ilanı mı?
• Bayram broşürü mü?
• Yoksa başka bir şey mi?

Söyle, sana en uygun tasarımı hazırlayalım! 🎨"""


# ============= AI LAYOUT ENDPOINT =============

@wizard_bp.route('/api/wizard/ai-layout', methods=['POST'])
@login_required
def api_wizard_ai_layout():
    """
    AI-powered layout generation for brochure page
    Returns x, y positions and styling for each product
    """
    import openai
    
    try:
        data = request.get_json()
        
        products = data.get('products', [])
        canvas_width = data.get('canvasWidth', 595)
        canvas_height = data.get('canvasHeight', 842)
        mode = data.get('mode', 'auto')
        
        if not products:
            return jsonify({'success': False, 'error': 'Ürün listesi boş'})
        
        # API key kontrolü
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            # Fallback: basit grid layout
            return jsonify({
                'success': True,
                'layout': generate_fallback_layout(products, canvas_width, canvas_height),
                'tokens_used': 0,
                'cost_usd': 0
            })
        
        # OpenAI'dan layout iste
        client = openai.OpenAI(api_key=api_key)
        
        product_list = "\n".join([
            f"- {p.get('name', 'Ürün')} ({p.get('price', 0)} TL)"
            for p in products[:12]
        ])
        
        prompt = f"""Sen profesyonel bir broşür tasarımcısısın.
        
Aşağıdaki ürünler için A4 boyutunda ({canvas_width}x{canvas_height}px) broşür yerleşimi yap.

ÜRÜNLER:
{product_list}

KURALLAR:
1. Her ürün kartı yaklaşık 180x240px
2. Header için üstte 80px alan bırak
3. Ürünler grid düzeninde olsun (3 sütun ideal)
4. Ürünler arasında 10-15px boşluk bırak
5. Fiyatı yüksek/düşük olanları stratejik yerleştir

JSON formatında döndür:
{{
    "header": {{
        "height": 80,
        "color": "#e53935",
        "slogan": "DEV İNDİRİMLER!"
    }},
    "backgroundColor": "#ffffff",
    "products": [
        {{"id": "urun_id", "x": 20, "y": 100, "scale": 1.0, "highlight": false}},
        ...
    ]
}}

Sadece JSON döndür, başka açıklama yapma."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Daha hızlı ve ucuz
            messages=[
                {"role": "system", "content": "Sen JSON formatında broşür layout döndüren bir asistansın."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        cost_usd = (tokens_used / 1000) * 0.0002  # gpt-4o-mini fiyatı
        
        # JSON parse
        try:
            # Temizle (```json ... ``` varsa kaldır)
            clean_response = ai_response.strip()
            if clean_response.startswith('```'):
                clean_response = clean_response.split('```')[1]
                if clean_response.startswith('json'):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            layout = json.loads(clean_response)
            
            return jsonify({
                'success': True,
                'layout': layout,
                'tokens_used': tokens_used,
                'cost_usd': round(cost_usd, 6)
            })
            
        except json.JSONDecodeError as e:
            logging.error(f"AI layout JSON parse error: {e}")
            return jsonify({
                'success': True,
                'layout': generate_fallback_layout(products, canvas_width, canvas_height),
                'tokens_used': tokens_used,
                'cost_usd': round(cost_usd, 6),
                'warning': 'AI yanıtı parse edilemedi, varsayılan layout kullanıldı'
            })
        
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        return jsonify({
            'success': True,
            'layout': generate_fallback_layout(products, canvas_width, canvas_height),
            'tokens_used': 0,
            'error': 'AI geçici kullanılamıyor'
        })
    except Exception as e:
        logging.error(f"AI layout error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


def generate_fallback_layout(products, canvas_width=595, canvas_height=842):
    """
    Fallback grid layout when AI is unavailable
    """
    cols = 3
    cell_width = 180
    cell_height = 240
    offset_x = 20
    offset_y = 100  # Header için alan
    gap = 10
    
    product_positions = []
    for idx, p in enumerate(products[:12]):
        col = idx % cols
        row = idx // cols
        x = offset_x + col * (cell_width + gap)
        y = offset_y + row * (cell_height + gap)
        
        product_positions.append({
            'id': p.get('id', str(idx)),
            'x': x,
            'y': y,
            'scale': 1.0,
            'highlight': idx < 3  # İlk 3 ürün highlight
        })
    
    return {
        'header': {
            'height': 80,
            'color': '#e53935',
            'slogan': 'SÜPER FIRSATLAR!'
        },
        'backgroundColor': '#ffffff',
        'products': product_positions
    }


# ============= HELPER FUNCTIONS =============

def generate_fallback_suggestion(analysis, purpose, holiday=None):
    """
    Generate fallback suggestion when AI is unavailable
    """
    purpose_messages = {
        'discount': {
            'greeting': 'Merhaba! 🛒',
            'suggestion': 'İndirim broşürü için en yüksek indirimleri öne çıkaralım!',
            'slogan': 'Dev İndirimler Başladı!'
        },
        'holiday': {
            'greeting': 'Bayramınız kutlu olsun! 🎉',
            'suggestion': 'Özel gün temalı şık bir broşür hazırlayalım.',
            'slogan': 'Bayram Fırsatları!'
        },
        'job': {
            'greeting': 'Ekibinize yeni arkadaşlar mı arıyorsunuz? 👨‍🍳',
            'suggestion': 'Profesyonel bir iş ilanı broşürü hazırlayalım.',
            'slogan': 'Ekibimize Katıl!'
        },
        'grocery': {
            'greeting': 'Taze ürünler için harika! 🥬',
            'suggestion': 'Yeşil ve canlı renklerle manav broşürü hazırlayalım.',
            'slogan': 'Taptaze Fırsatlar!'
        },
        'butcher': {
            'greeting': 'Premium et ürünleri! 🥩',
            'suggestion': 'Kaliteli ve güven veren bir kasap broşürü hazırlayalım.',
            'slogan': 'En Kaliteli Etler!'
        },
        'general': {
            'greeting': 'Merhaba! 📢',
            'suggestion': 'Genel duyuru broşürü hazırlayalım.',
            'slogan': 'Önemli Duyuru!'
        }
    }
    
    msg = purpose_messages.get(purpose, purpose_messages['general'])
    
    # Build analysis text
    analysis_text = f"{analysis.get('product_count', 0)} ürün gördüm. "
    categories = analysis.get('categories', [])
    if categories:
        top_cats = categories[:3]
        analysis_text += ', '.join([f"{c['name']}: {c['count']} ürün" for c in top_cats]) + '.'
    
    return {
        'success': True,
        'greeting': msg['greeting'],
        'analysis': analysis_text,
        'suggestion': msg['suggestion'],
        'slogan': msg['slogan'],
        'color_theme': {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#10b981'
        },
        'layout': {
            'pages': [
                {'title': 'Kapak', 'products': ['En çok indirimli ürünler'], 'highlight': 'Slogan'},
                {'title': 'İç Sayfa', 'products': ['Diğer ürünler'], 'highlight': 'Kategoriler'}
            ]
        }
    }


def build_brochure_pages(products, ai_suggestion, template):
    """
    Build brochure pages structure based on products and AI suggestion
    """
    if not products:
        return [{
            'title': 'Kapak',
            'products': [],
            'layout': template
        }]
    
    # Try to use AI suggestion layout
    ai_layout = ai_suggestion.get('layout', {})
    ai_pages = ai_layout.get('pages', [])
    
    if ai_pages:
        # Use AI suggested pages
        pages = []
        for i, page_info in enumerate(ai_pages):
            # Find products for this page
            page_products = []
            
            # Simple distribution - divide products among pages
            products_per_page = max(4, len(products) // len(ai_pages))
            start_idx = i * products_per_page
            end_idx = start_idx + products_per_page
            page_products = products[start_idx:end_idx]
            
            pages.append({
                'title': page_info.get('title', f'Sayfa {i+1}'),
                'products': page_products,
                'highlight': page_info.get('highlight', ''),
                'layout': template
            })
        
        return pages
    
    # Fallback: Simple page distribution
    products_per_page = 6
    num_pages = max(1, (len(products) + products_per_page - 1) // products_per_page)
    num_pages = min(num_pages, 4)  # Max 4 pages
    
    pages = []
    for i in range(num_pages):
        start_idx = i * products_per_page
        end_idx = start_idx + products_per_page
        page_products = products[start_idx:end_idx]
        
        title = 'Kapak' if i == 0 else f'Sayfa {i+1}'
        
        pages.append({
            'title': title,
            'products': page_products,
            'layout': template
        })
    
    return pages

