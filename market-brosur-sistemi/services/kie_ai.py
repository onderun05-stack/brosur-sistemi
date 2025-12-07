# -*- coding: utf-8 -*-
"""
Kie.ai API Service - Multi-Model AI Integration

Kie.ai provides access to multiple AI models through a single API:
- 4o Image API (OpenAI GPT-4o Vision for images)
- Flux Kontext API (High-quality image generation)
- Veo 3.1 / Runway (Video generation)
- Suno API (Music generation)
- LLM Chat APIs

Documentation: https://kie.ai/tr
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============= KIE.AI CONFIGURATION =============

KIE_API_KEY = os.environ.get('KIE_API_KEY', '')
KIE_API_BASE_URL = os.environ.get('KIE_API_BASE_URL', 'https://api.kie.ai/v1')

# Model endpoints
KIE_ENDPOINTS = {
    'image_4o': '/images/generations',      # 4o Image API
    'flux': '/images/flux',                  # Flux Kontext
    'video_veo': '/videos/veo',              # Veo 3.1
    'video_runway': '/videos/runway',        # Runway Aleph
    'chat': '/chat/completions',             # LLM Chat
    'music': '/audio/suno',                  # Suno Music
}

# Default headers
def _get_headers():
    return {
        'Authorization': f'Bearer {KIE_API_KEY}',
        'Content-Type': 'application/json'
    }


def is_kie_available() -> bool:
    """Check if Kie.ai API is configured"""
    return bool(KIE_API_KEY)


# ============= IMAGE GENERATION =============

def generate_image_4o(prompt: str, size: str = "1024x1024", quality: str = "hd") -> Dict:
    """
    Generate image using 4o Image API (GPT-4o based)
    
    Args:
        prompt: Image description
        size: "1024x1024", "1792x1024", "1024x1792"
        quality: "standard" or "hd"
    
    Returns:
        dict with success, image_url or error
    """
    if not is_kie_available():
        return {'success': False, 'error': 'Kie.ai API key not configured'}
    
    try:
        response = requests.post(
            f"{KIE_API_BASE_URL}{KIE_ENDPOINTS['image_4o']}",
            headers=_get_headers(),
            json={
                'model': '4o-image',
                'prompt': prompt,
                'size': size,
                'quality': quality,
                'n': 1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                return {
                    'success': True,
                    'image_url': data['data'][0].get('url'),
                    'model': '4o-image'
                }
        
        return {
            'success': False,
            'error': f"API error: {response.status_code} - {response.text}"
        }
    
    except Exception as e:
        logging.error(f"Kie.ai 4o Image error: {e}")
        return {'success': False, 'error': str(e)}


def generate_image_flux(prompt: str, aspect_ratio: str = "16:9") -> Dict:
    """
    Generate image using Flux Kontext API
    High-quality, consistent character/style images
    
    Args:
        prompt: Image description
        aspect_ratio: "1:1", "16:9", "9:16", "4:3", "3:4"
    
    Returns:
        dict with success, image_url or error
    """
    if not is_kie_available():
        return {'success': False, 'error': 'Kie.ai API key not configured'}
    
    try:
        response = requests.post(
            f"{KIE_API_BASE_URL}{KIE_ENDPOINTS['flux']}",
            headers=_get_headers(),
            json={
                'model': 'flux-kontext',
                'prompt': prompt,
                'aspect_ratio': aspect_ratio,
                'num_outputs': 1
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                return {
                    'success': True,
                    'image_url': data['data'][0].get('url'),
                    'model': 'flux-kontext'
                }
        
        return {
            'success': False,
            'error': f"API error: {response.status_code} - {response.text}"
        }
    
    except Exception as e:
        logging.error(f"Kie.ai Flux error: {e}")
        return {'success': False, 'error': str(e)}


# ============= VIDEO GENERATION =============

def generate_video_veo(prompt: str, duration: int = 8) -> Dict:
    """
    Generate video using Google Veo 3.1
    
    Args:
        prompt: Video description
        duration: 5-16 seconds
    
    Returns:
        dict with success, video_url or error
    """
    if not is_kie_available():
        return {'success': False, 'error': 'Kie.ai API key not configured'}
    
    try:
        response = requests.post(
            f"{KIE_API_BASE_URL}{KIE_ENDPOINTS['video_veo']}",
            headers=_get_headers(),
            json={
                'model': 'veo-3.1',
                'prompt': prompt,
                'duration': min(max(duration, 5), 16),
                'resolution': '1080p'
            },
            timeout=180  # Video generation takes longer
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'video_url': data.get('video_url'),
                'duration': duration,
                'model': 'veo-3.1'
            }
        
        return {
            'success': False,
            'error': f"API error: {response.status_code} - {response.text}"
        }
    
    except Exception as e:
        logging.error(f"Kie.ai Veo error: {e}")
        return {'success': False, 'error': str(e)}


def generate_video_runway(prompt: str, image_url: str = None) -> Dict:
    """
    Generate video using Runway Aleph
    Can use an image as starting frame
    
    Args:
        prompt: Video description
        image_url: Optional starting frame image
    
    Returns:
        dict with success, video_url or error
    """
    if not is_kie_available():
        return {'success': False, 'error': 'Kie.ai API key not configured'}
    
    try:
        payload = {
            'model': 'runway-aleph',
            'prompt': prompt,
            'duration': 10
        }
        
        if image_url:
            payload['image_url'] = image_url
        
        response = requests.post(
            f"{KIE_API_BASE_URL}{KIE_ENDPOINTS['video_runway']}",
            headers=_get_headers(),
            json=payload,
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'video_url': data.get('video_url'),
                'model': 'runway-aleph'
            }
        
        return {
            'success': False,
            'error': f"API error: {response.status_code} - {response.text}"
        }
    
    except Exception as e:
        logging.error(f"Kie.ai Runway error: {e}")
        return {'success': False, 'error': str(e)}


# ============= BROCHURE-SPECIFIC FUNCTIONS =============

def generate_brochure_background(
    purpose: str,
    theme: str = 'discount',
    colors: List[str] = None
) -> Dict:
    """
    Generate professional brochure background
    
    Args:
        purpose: 'discount', 'holiday', 'job_posting', 'grocery', 'butcher'
        theme: Color theme name
        colors: Optional list of hex colors to use
    
    Returns:
        dict with success, image_url or error
    """
    
    # Purpose-specific prompts
    prompts = {
        'discount': """
            Professional Turkish supermarket discount banner background.
            - Vibrant gradient from red (#e63946) to orange (#f4a261)
            - Dynamic burst effects and sale badge shapes
            - Empty center area for text and products
            - High contrast, eye-catching design
            - Professional retail advertising quality
            - No text, no products, background only
            - 8K quality, crisp edges
        """,
        'holiday_ramazan': """
            Elegant Ramadan themed background for Turkish market brochure.
            - Deep purple and gold color palette
            - Subtle crescent moon and star motifs
            - Lantern silhouettes in corners
            - Empty center for content
            - Respectful, festive atmosphere
            - Professional quality, no text
        """,
        'holiday_kurban': """
            Professional Eid al-Adha themed background for Turkish market.
            - Warm earth tones: brown, cream, gold
            - Subtle geometric Islamic patterns
            - Empty center area for products
            - Celebratory yet professional feel
            - High quality, no text or animals
        """,
        'holiday_newyear': """
            Festive New Year celebration background for Turkish supermarket.
            - Red, gold, and silver color scheme
            - Sparkles and bokeh effects
            - Confetti and celebration elements in corners
            - Large empty center for products
            - Party atmosphere, professional quality
        """,
        'job_posting': """
            Professional job recruitment poster background.
            - Clean corporate blue and white gradient
            - Subtle professional pattern
            - Modern, trustworthy appearance
            - Large empty area for job details
            - HR/recruitment style
            - No people, no text
        """,
        'grocery': """
            Fresh produce market background for grocery brochure.
            - Bright green and fresh colors
            - Subtle fruit and vegetable shapes in background
            - Clean, healthy, organic feel
            - Empty center for products
            - Farm-fresh atmosphere
            - Professional photography style
        """,
        'butcher': """
            Premium butcher shop background for meat products brochure.
            - Rich red and dark wood tones
            - Subtle marble texture
            - Professional, premium feel
            - Empty center for meat products
            - High-end steakhouse aesthetic
            - Clean, appetizing design
        """
    }
    
    prompt = prompts.get(purpose, prompts['discount'])
    
    # Add custom colors if provided
    if colors:
        color_str = ", ".join(colors)
        prompt += f"\nUse these specific colors: {color_str}"
    
    # Try Flux first (better quality), fallback to 4o
    result = generate_image_flux(prompt, aspect_ratio="16:9")
    
    if not result['success']:
        # Fallback to 4o Image
        result = generate_image_4o(prompt, size="1792x1024", quality="hd")
    
    return result


def generate_3d_slogan(slogan_text: str, style: str = 'gold') -> Dict:
    """
    Generate 3D promotional slogan text image
    
    Args:
        slogan_text: The slogan text to render
        style: 'gold', 'red', 'blue', 'neon'
    
    Returns:
        dict with success, image_url or error
    """
    
    style_configs = {
        'gold': "golden metallic finish, luxury gold gradient, warm highlights",
        'red': "vibrant red gradient, glossy finish, white highlights",
        'blue': "electric blue, neon glow effect, cool tones",
        'neon': "neon pink and cyan, glowing edges, cyberpunk style"
    }
    
    style_desc = style_configs.get(style, style_configs['gold'])
    
    prompt = f"""
    Create a 3D promotional text image for Turkish supermarket advertising.
    
    TEXT TO RENDER: "{slogan_text}"
    
    STYLE REQUIREMENTS:
    - {style_desc}
    - Bold, thick 3D extruded letters
    - Professional retail signage quality
    - Strong shadow for depth
    - Sharp, crisp edges (8K quality)
    - Text clearly readable
    - TRANSPARENT BACKGROUND
    - NO other elements, ONLY the text
    - Commercial advertising quality
    
    The text "{slogan_text}" must be rendered exactly as written in Turkish.
    """
    
    return generate_image_4o(prompt, size="1024x1024", quality="hd")


def generate_promo_video(
    products: List[Dict],
    slogan: str,
    purpose: str = 'discount',
    duration: int = 8
) -> Dict:
    """
    Generate promotional video for brochure
    
    Args:
        products: List of product dicts with name, price, discount_price
        slogan: Campaign slogan
        purpose: Video purpose type
        duration: Video length in seconds
    
    Returns:
        dict with success, video_url or error
    """
    
    # Build product showcase text
    product_list = ", ".join([p.get('name', '') for p in products[:5]])
    
    prompts = {
        'discount': f"""
            Professional Turkish supermarket TV commercial style video.
            
            SCENE: Clean white studio background
            CONTENT: Products smoothly rotating/sliding into frame
            PRODUCTS: {product_list}
            
            STYLE:
            - Professional product showcase
            - Smooth camera movements
            - Clean transitions between products
            - Price tags appearing dynamically
            - Final frame: Campaign slogan "{slogan}"
            
            QUALITY: TV commercial, 1080p, professional lighting
            NO weird effects, NO surreal elements
            DURATION: {duration} seconds
        """,
        'holiday': f"""
            Festive holiday celebration video for Turkish market.
            
            SCENE: Warm, festive background with subtle decorations
            CONTENT: Gift boxes and products revealed elegantly
            
            STYLE:
            - Celebratory atmosphere
            - Smooth reveal animations
            - Sparkle effects (subtle)
            - Final frame: "{slogan}"
            
            QUALITY: Professional, family-friendly
            DURATION: {duration} seconds
        """
    }
    
    prompt = prompts.get(purpose, prompts['discount'])
    
    return generate_video_veo(prompt, duration)


# ============= WIZARD HELPER FUNCTIONS =============

def analyze_products_for_brochure(products: List[Dict]) -> Dict:
    """
    Analyze products and return insights for brochure wizard
    This uses OpenAI (not Kie.ai) for text analysis
    
    Args:
        products: List of product dictionaries
    
    Returns:
        Analysis dict with categories, top discounts, suggestions
    """
    from collections import defaultdict
    
    if not products:
        return {
            'success': False,
            'error': 'No products provided',
            'product_count': 0
        }
    
    # Analyze locally first
    categories = defaultdict(list)
    discounts = []
    
    for p in products:
        category = p.get('product_group', p.get('category', 'Genel'))
        categories[category].append(p)
        
        normal = p.get('normal_price', 0) or 0
        discount = p.get('discount_price', 0) or 0
        
        if normal > 0 and discount > 0:
            discount_percent = ((normal - discount) / normal) * 100
            discounts.append({
                'name': p.get('name', 'Ürün'),
                'percent': discount_percent,
                'product': p
            })
    
    # Sort by discount
    top_discounts = sorted(discounts, key=lambda x: x['percent'], reverse=True)[:5]
    
    # Build summary
    category_summary = []
    for cat, items in categories.items():
        avg_discount = 0
        if items:
            discounts_in_cat = [
                ((p.get('normal_price', 0) - p.get('discount_price', 0)) / p.get('normal_price', 1) * 100)
                for p in items if p.get('normal_price', 0) > 0
            ]
            avg_discount = sum(discounts_in_cat) / len(discounts_in_cat) if discounts_in_cat else 0
        
        category_summary.append({
            'name': cat,
            'count': len(items),
            'avg_discount': round(avg_discount, 1)
        })
    
    # Sort categories by count
    category_summary.sort(key=lambda x: x['count'], reverse=True)
    
    return {
        'success': True,
        'product_count': len(products),
        'categories': category_summary,
        'top_discounts': [
            {
                'name': d['name'],
                'percent': round(d['percent'], 0)
            } for d in top_discounts
        ],
        'suggested_pages': min(4, max(1, len(products) // 6))
    }


def get_ai_brochure_suggestion(
    products_analysis: Dict,
    purpose: str,
    user_message: str = None
) -> Dict:
    """
    Get AI suggestion for brochure layout
    Uses OpenAI GPT-4o for intelligent suggestions
    
    Args:
        products_analysis: Output from analyze_products_for_brochure
        purpose: Brochure purpose (discount, holiday, etc.)
        user_message: Optional user description of what they want
    
    Returns:
        AI suggestion dict
    """
    import os
    from openai import OpenAI
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'OpenAI API key not configured'}
    
    client = OpenAI(api_key=api_key)
    
    # Build context
    categories_text = "\n".join([
        f"- {c['name']}: {c['count']} ürün (ort. %{c['avg_discount']} indirim)"
        for c in products_analysis.get('categories', [])
    ])
    
    top_discounts_text = "\n".join([
        f"- {d['name']}: %{d['percent']} indirim"
        for d in products_analysis.get('top_discounts', [])
    ])
    
    purpose_context = {
        'discount': "İndirim/kampanya broşürü",
        'holiday_ramazan': "Ramazan Bayramı özel broşürü",
        'holiday_kurban': "Kurban Bayramı özel broşürü",
        'holiday_newyear': "Yılbaşı özel broşürü",
        'job_posting': "İş ilanı broşürü",
        'grocery': "Manav/sebze-meyve broşürü",
        'butcher': "Kasap/et ürünleri broşürü"
    }
    
    system_prompt = """Sen bir Türk süpermarketi için profesyonel broşür tasarım danışmanısın.
Müşteriye samimi ve yardımsever bir şekilde önerilerde bulunuyorsun.
Yanıtların kısa, net ve Türkçe olmalı. JSON formatında yanıt ver."""

    user_prompt = f"""
Müşterinin ürün listesi analizi:
Toplam {products_analysis.get('product_count', 0)} ürün

Kategoriler:
{categories_text}

En yüksek indirimli ürünler:
{top_discounts_text}

Broşür amacı: {purpose_context.get(purpose, 'Genel kampanya')}

{f'Müşteri notu: {user_message}' if user_message else ''}

Lütfen şu formatta öneri sun:
{{
    "greeting": "Samimi bir karşılama mesajı",
    "analysis": "Ürün analizinin kısa özeti",
    "suggestion": "Broşür için ana öneriniz",
    "layout": {{
        "pages": [
            {{"title": "Sayfa başlığı", "products": ["ürün kategorileri"], "highlight": "öne çıkarılacak şey"}}
        ]
    }},
    "slogan": "Önerilen kampanya sloganı",
    "color_theme": {{"primary": "#hex", "secondary": "#hex", "accent": "#hex"}}
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            result['success'] = True
            return result
        
        return {'success': False, 'error': 'No response from AI'}
    
    except Exception as e:
        logging.error(f"AI suggestion error: {e}")
        return {'success': False, 'error': str(e)}


# ============= API STATUS CHECK =============

def check_kie_api_status() -> Dict:
    """Check Kie.ai API status and available credits"""
    if not is_kie_available():
        return {
            'available': False,
            'error': 'API key not configured'
        }
    
    try:
        response = requests.get(
            f"{KIE_API_BASE_URL}/account/status",
            headers=_get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'available': True,
                'credits': data.get('credits', 0),
                'plan': data.get('plan', 'unknown')
            }
        
        return {
            'available': False,
            'error': f"API returned {response.status_code}"
        }
    
    except Exception as e:
        return {
            'available': False,
            'error': str(e)
        }





