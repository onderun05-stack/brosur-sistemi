# -*- coding: utf-8 -*-
"""
Ghost Assistant Routes - API endpoints for Ghost Assistant functionality.

The Ghost (Hayalet) is a 64x64 cloud-like 3D model with lightning bolt icon
that provides real-time AI assistance for brochure design.
"""

from flask import Blueprint, request, jsonify, session
import logging

from utils.helpers import login_required, get_current_user
from services import ghost_assistant
from services import brochure_engine

ghost_bp = Blueprint('ghost', __name__)


# ============= GREETING & STATUS =============

@ghost_bp.route('/api/ghost/greeting', methods=['GET'])
@login_required
def api_ghost_greeting():
    """Get personalized Ghost greeting"""
    user = get_current_user()
    user_name = user.get('name', '').split()[0] if user else None
    
    greeting = ghost_assistant.get_greeting(user_name)
    
    return jsonify({
        'success': True,
        'greeting': greeting,
        'ghost_icon': '⚡',
        'ghost_avatar': '/static/images/ghost_avatar.png'
    })


@ghost_bp.route('/api/ghost/status', methods=['GET'])
@login_required
def api_ghost_status():
    """Get Ghost assistant status"""
    return jsonify({
        'success': True,
        'status': 'active',
        'name': 'Hayalet',
        'icon': '⚡',
        'description': 'AI Tasarım Asistanı',
        'features': [
            'Sayfa analizi',
            'Layout önerileri',
            'Fiyat karşılaştırma',
            'Otomatik düzenleme',
            'Kalite puanlama'
        ]
    })


# ============= PAGE ANALYSIS =============

@ghost_bp.route('/api/ghost/analyze-page', methods=['POST'])
@login_required
def api_ghost_analyze_page():
    """Analyze a single page design"""
    data = request.get_json() or {}
    page_data = data.get('page', {})
    
    if not page_data:
        return jsonify({'success': False, 'error': 'Sayfa verisi gerekli'}), 400
    
    analysis = ghost_assistant.analyze_page_design(page_data)
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })


@ghost_bp.route('/api/ghost/analyze-brochure', methods=['POST'])
@login_required
def api_ghost_analyze_brochure():
    """Analyze full brochure design"""
    data = request.get_json() or {}
    brochure_id = data.get('brochure_id')
    
    if brochure_id:
        # Load brochure from storage
        brochure_data = brochure_engine.get_brochure(brochure_id)
        if not brochure_data:
            return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    else:
        brochure_data = data.get('brochure', {})
    
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür verisi gerekli'}), 400
    
    analysis = ghost_assistant.analyze_brochure_design(brochure_data)
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })


@ghost_bp.route('/api/ghost/analyze-brochure/<brochure_id>', methods=['GET'])
@login_required
def api_ghost_analyze_brochure_by_id(brochure_id):
    """Analyze brochure by ID"""
    brochure_data = brochure_engine.get_brochure(brochure_id)
    
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    
    analysis = ghost_assistant.analyze_brochure_design(brochure_data)
    
    return jsonify({
        'success': True,
        'brochure_id': brochure_id,
        'analysis': analysis
    })


# ============= SUGGESTIONS =============

@ghost_bp.route('/api/ghost/suggest-layout', methods=['POST'])
@login_required
def api_ghost_suggest_layout():
    """Get layout suggestion for products"""
    data = request.get_json() or {}
    products = data.get('products', [])
    sector = data.get('sector', 'supermarket')
    
    if not products:
        return jsonify({'success': False, 'error': 'Ürün listesi gerekli'}), 400
    
    suggestion = ghost_assistant.get_layout_recommendation(products, sector)
    
    return jsonify({
        'success': True,
        'suggestion': suggestion
    })


@ghost_bp.route('/api/ghost/suggest-next-action', methods=['POST'])
@login_required
def api_ghost_suggest_next_action():
    """Get next action suggestion based on brochure state"""
    data = request.get_json() or {}
    brochure_state = data.get('brochure_state', {})
    
    suggestion = ghost_assistant.get_next_action_suggestion(brochure_state)
    
    return jsonify({
        'success': True,
        'suggestion': suggestion
    })


@ghost_bp.route('/api/ghost/idle-tip', methods=['POST'])
@login_required
def api_ghost_idle_tip():
    """Get tip for idle user"""
    data = request.get_json() or {}
    idle_seconds = data.get('idle_seconds', 0)
    current_page = data.get('current_page')
    
    tip = ghost_assistant.get_idle_suggestion(idle_seconds, current_page)
    
    if tip:
        return jsonify({
            'success': True,
            'has_tip': True,
            'tip': tip
        })
    else:
        return jsonify({
            'success': True,
            'has_tip': False
        })


# ============= PRICE INSIGHTS =============

@ghost_bp.route('/api/ghost/price-insight', methods=['POST'])
@login_required
def api_ghost_price_insight():
    """Get friendly price insight"""
    data = request.get_json() or {}
    customer_price = data.get('customer_price', 0)
    market_price = data.get('market_price', 0)
    product_name = data.get('product_name', '')
    
    insight = ghost_assistant.get_price_insight(customer_price, market_price, product_name)
    
    return jsonify({
        'success': True,
        'insight': insight
    })


@ghost_bp.route('/api/ghost/batch-price-insights', methods=['POST'])
@login_required
def api_ghost_batch_price_insights():
    """Get price insights for multiple products"""
    data = request.get_json() or {}
    products = data.get('products', [])
    
    insights = []
    for product in products:
        customer_price = product.get('price', 0)
        market_price = product.get('market_price', 0)
        product_name = product.get('name', '')
        
        insight = ghost_assistant.get_price_insight(customer_price, market_price, product_name)
        insights.append({
            'barcode': product.get('barcode'),
            'name': product_name,
            'insight': insight
        })
    
    return jsonify({
        'success': True,
        'insights': insights
    })


# ============= SHADOW PLANNER =============

@ghost_bp.route('/api/ghost/create-auto-plan', methods=['POST'])
@login_required
def api_ghost_create_auto_plan():
    """Create automatic brochure plan"""
    user = get_current_user()
    data = request.get_json() or {}
    products = data.get('products', [])
    settings = data.get('settings', {})
    
    # Add user sector if not provided
    if 'sector' not in settings:
        settings['sector'] = user.get('sector', 'supermarket') if user else 'supermarket'
    
    plan = ghost_assistant.create_auto_brochure_plan(products, settings)
    
    return jsonify({
        'success': True,
        'plan': plan
    })


@ghost_bp.route('/api/ghost/workflow-progress', methods=['POST'])
@login_required
def api_ghost_workflow_progress():
    """Get workflow progress"""
    data = request.get_json() or {}
    brochure_state = data.get('brochure_state', {})
    
    progress = ghost_assistant.get_workflow_progress(brochure_state)
    
    return jsonify({
        'success': True,
        'progress': progress
    })


@ghost_bp.route('/api/ghost/workflow-progress/<brochure_id>', methods=['GET'])
@login_required
def api_ghost_workflow_progress_by_id(brochure_id):
    """Get workflow progress for specific brochure"""
    brochure_data = brochure_engine.get_brochure(brochure_id)
    
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    
    progress = ghost_assistant.get_workflow_progress(brochure_data)
    
    return jsonify({
        'success': True,
        'brochure_id': brochure_id,
        'progress': progress
    })


# ============= AI ACTIONS =============

@ghost_bp.route('/api/ghost/auto-arrange-page', methods=['POST'])
@login_required
def api_ghost_auto_arrange_page():
    """Auto-arrange products on a page using Ghost suggestions"""
    data = request.get_json() or {}
    brochure_id = data.get('brochure_id')
    page_id = data.get('page_id')
    
    if not brochure_id or not page_id:
        return jsonify({'success': False, 'error': 'brochure_id ve page_id gerekli'}), 400
    
    # Get brochure and page
    brochure_data = brochure_engine.get_brochure(brochure_id)
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    
    # Find page
    page = None
    for p in brochure_data.get('pages', []):
        if p.get('id') == page_id:
            page = p
            break
    
    if not page:
        return jsonify({'success': False, 'error': 'Sayfa bulunamadı'}), 404
    
    if page.get('locked'):
        return jsonify({'success': False, 'error': 'Sayfa kilitli, düzenlenemez'}), 400
    
    # Get layout suggestion
    products = page.get('products', [])
    user = get_current_user()
    sector = user.get('sector', 'supermarket') if user else 'supermarket'
    
    layout_suggestion = ghost_assistant.get_layout_recommendation(products, sector)
    suggested_layout = layout_suggestion.get('suggested_layout', 'grid_4x4')
    
    # Apply auto-arrange
    result = brochure_engine.auto_arrange_page(brochure_id, page_id, suggested_layout)
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'message': f"Sayfa '{suggested_layout}' düzeniyle yeniden düzenlendi",
            'layout': suggested_layout,
            'layout_reason': layout_suggestion.get('reason'),
            'page': result.get('page')
        })
    else:
        return jsonify(result), 400


@ghost_bp.route('/api/ghost/optimize-brochure', methods=['POST'])
@login_required
def api_ghost_optimize_brochure():
    """Optimize entire brochure using Ghost AI"""
    data = request.get_json() or {}
    brochure_id = data.get('brochure_id')
    
    if not brochure_id:
        return jsonify({'success': False, 'error': 'brochure_id gerekli'}), 400
    
    brochure_data = brochure_engine.get_brochure(brochure_id)
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    
    # Analyze first
    analysis = ghost_assistant.analyze_brochure_design(brochure_data)
    
    # Auto-arrange unlocked pages with low scores
    optimized_pages = []
    user = get_current_user()
    sector = user.get('sector', 'supermarket') if user else 'supermarket'
    
    for page_analysis in analysis.get('page_analyses', []):
        if not page_analysis.get('is_locked') and page_analysis.get('score', 100) < 80:
            page_id = page_analysis.get('page_id')
            
            # Get products for this page
            for page in brochure_data.get('pages', []):
                if page.get('id') == page_id:
                    products = page.get('products', [])
                    layout_suggestion = ghost_assistant.get_layout_recommendation(products, sector)
                    
                    result = brochure_engine.auto_arrange_page(
                        brochure_id, page_id, 
                        layout_suggestion.get('suggested_layout', 'grid_4x4')
                    )
                    
                    if result.get('success'):
                        optimized_pages.append({
                            'page_id': page_id,
                            'old_score': page_analysis.get('score'),
                            'layout_applied': layout_suggestion.get('suggested_layout')
                        })
                    break
    
    # Re-analyze after optimization
    updated_brochure = brochure_engine.get_brochure(brochure_id)
    new_analysis = ghost_assistant.analyze_brochure_design(updated_brochure)
    
    return jsonify({
        'success': True,
        'message': f'{len(optimized_pages)} sayfa optimize edildi',
        'optimized_pages': optimized_pages,
        'before_score': analysis.get('overall_score'),
        'after_score': new_analysis.get('overall_score'),
        'new_analysis': new_analysis
    })


# ============= UNDO/REDO TRACKING =============

@ghost_bp.route('/api/ghost/can-undo', methods=['POST'])
@login_required
def api_ghost_can_undo():
    """Check if undo is available"""
    data = request.get_json() or {}
    brochure_id = data.get('brochure_id')
    
    # For now, always return false - undo stack would be implemented client-side
    # or with a separate history service
    return jsonify({
        'success': True,
        'can_undo': False,
        'can_redo': False,
        'message': 'Geri alma özelliği client tarafında yönetilmektedir'
    })


# ============= GHOST CHAT =============

@ghost_bp.route('/api/ghost/chat', methods=['POST'])
@login_required
def api_ghost_chat():
    """Chat with Ghost assistant"""
    data = request.get_json() or {}
    message = data.get('message', '')
    context = data.get('context', {})
    
    if not message:
        return jsonify({'success': False, 'error': 'Mesaj gerekli'}), 400
    
    # Simple keyword-based responses (can be enhanced with OpenAI)
    response = _generate_ghost_response(message, context)
    
    return jsonify({
        'success': True,
        'response': response
    })


def _generate_ghost_response(message: str, context: dict) -> dict:
    """Generate Ghost chat response based on message"""
    message_lower = message.lower()
    
    # Keywords and responses
    responses = {
        'merhaba': {
            'text': 'Merhaba! Size nasıl yardımcı olabilirim?',
            'suggestions': ['Sayfa düzenle', 'Ürün ara', 'Dışa aktar']
        },
        'yardım': {
            'text': 'Elbette yardımcı olurum! Ne yapmak istiyorsunuz?',
            'suggestions': ['Layout öner', 'Kalite analizi', 'Otomatik düzenle']
        },
        'düzenle': {
            'text': 'Sayfayı düzenlemek için "Otomatik Düzenle" butonunu kullanabilirsiniz. İsterseniz ben de yapayım!',
            'action': 'auto_arrange'
        },
        'layout': {
            'text': 'Ürün sayınıza göre en uygun layout\'u önerebilirim. Kaç ürününüz var?',
            'action': 'suggest_layout'
        },
        'analiz': {
            'text': 'Broşürünüzü analiz edeyim ve öneriler sunayım.',
            'action': 'analyze'
        },
        'export': {
            'text': 'Broşürünüzü PDF veya PNG olarak dışa aktarabilirsiniz.',
            'action': 'export'
        },
        'teşekkür': {
            'text': 'Rica ederim! Başka bir konuda yardımcı olabilir miyim? 😊',
            'suggestions': []
        }
    }
    
    # Find matching response
    for keyword, response in responses.items():
        if keyword in message_lower:
            return response
    
    # Default response
    return {
        'text': 'Anlıyorum. Size şu konularda yardımcı olabilirim: sayfa düzenleme, ürün yerleştirme, layout önerileri, kalite analizi.',
        'suggestions': ['Sayfa düzenle', 'Layout öner', 'Analiz yap']
    }


# ============= NAME NORMALIZER (MADDE 6) =============

@ghost_bp.route('/api/ghost/normalize-name', methods=['POST'])
@login_required
def api_ghost_normalize_name():
    """
    Ürün adını normalize et ve kısalt (Madde 6)
    Marka + Ürün + Gramaj formatına çevirir
    Max 26 karakter
    """
    data = request.get_json() or {}
    product_name = data.get('name', '')
    max_length = data.get('max_length', 26)
    
    if not product_name:
        return jsonify({'success': False, 'error': 'Ürün adı gerekli'}), 400
    
    normalized = ghost_assistant.normalize_product_name(product_name, max_length)
    
    return jsonify({
        'success': True,
        'original': product_name,
        'normalized': normalized,
        'original_length': len(product_name),
        'normalized_length': len(normalized),
        'shortened': len(normalized) < len(product_name)
    })


@ghost_bp.route('/api/ghost/batch-normalize-names', methods=['POST'])
@login_required
def api_ghost_batch_normalize_names():
    """Toplu ürün adı normalizasyonu"""
    data = request.get_json() or {}
    product_names = data.get('names', [])
    
    if not product_names:
        return jsonify({'success': False, 'error': 'Ürün adları listesi gerekli'}), 400
    
    results = ghost_assistant.batch_normalize_names(product_names)
    stats = ghost_assistant.get_name_normalization_stats(product_names)
    
    return jsonify({
        'success': True,
        'results': results,
        'stats': stats
    })


# ============= IMPORT VALIDATION (MADDE 9) =============

@ghost_bp.route('/api/ghost/validate-import', methods=['POST'])
@login_required
def api_ghost_validate_import():
    """
    Excel/TXT import verilerini kontrol et (Madde 9)
    Eksik fiyat, bozuk barkod, uzun isim, kategori yok kontrolü
    SAMİMİ MOD: Kullanıcıya dostane mesajlar
    """
    data = request.get_json() or {}
    products = data.get('products', [])
    
    if not products:
        return jsonify({'success': False, 'error': 'Ürün listesi gerekli'}), 400
    
    validation_result = ghost_assistant.validate_import_data(products)
    
    return jsonify({
        'success': True,
        'validation': validation_result
    })


@ghost_bp.route('/api/ghost/auto-fix-import', methods=['POST'])
@login_required
def api_ghost_auto_fix_import():
    """
    Import verilerini otomatik düzelt
    - Uzun isimleri kısalt
    - Barkod formatını düzelt (mümkünse)
    - Kategori öner
    """
    data = request.get_json() or {}
    products = data.get('products', [])
    
    if not products:
        return jsonify({'success': False, 'error': 'Ürün listesi gerekli'}), 400
    
    fixed_products = []
    fixes_applied = []
    
    for product in products:
        fixed = product.copy()
        product_fixes = []
        
        # İsim kısaltma
        name = product.get('name', '')
        if len(name) > 30:
            normalized = ghost_assistant.normalize_product_name(name)
            fixed['name'] = normalized
            product_fixes.append({
                'type': 'name_shortened',
                'before': name,
                'after': normalized
            })
        
        # Barkod format düzeltme
        barcode = str(product.get('barcode', ''))
        if barcode and not barcode.isdigit():
            # Sadece rakamları al
            clean_barcode = ''.join(c for c in barcode if c.isdigit())
            if len(clean_barcode) in [8, 12, 13, 14]:
                fixed['barcode'] = clean_barcode
                product_fixes.append({
                    'type': 'barcode_fixed',
                    'before': barcode,
                    'after': clean_barcode
                })
        
        fixed_products.append(fixed)
        if product_fixes:
            fixes_applied.append({
                'index': len(fixed_products) - 1,
                'barcode': fixed.get('barcode'),
                'fixes': product_fixes
            })
    
    return jsonify({
        'success': True,
        'fixed_products': fixed_products,
        'fixes_applied': fixes_applied,
        'total_fixes': sum(len(f['fixes']) for f in fixes_applied),
        'message': f"🔧 {sum(len(f['fixes']) for f in fixes_applied)} düzeltme yapıldı!"
    })


# ============= FULL BROCHURE CLEAN (MADDE 10) =============

@ghost_bp.route('/api/ghost/full-clean-brochure', methods=['POST'])
@login_required
def api_ghost_full_clean_brochure():
    """
    Tam otomatik broşür temizliği (Madde 10)
    
    İşlevler:
    - Tüm sayfaları tarar
    - Sıkışık ürünleri küçültür
    - Boşları büyütür
    - Ürün isimlerini optimize eder
    - Fiyat fontlarını dengeler
    - Resimleri hizalar
    
    Returns:
        "Broşür %X oranında optimize edildi."
    """
    data = request.get_json() or {}
    brochure_data = data.get('brochure', {})
    brochure_id = data.get('brochure_id')
    
    # Brochure ID varsa storage'dan al
    if brochure_id and not brochure_data:
        brochure_data = brochure_engine.get_brochure(brochure_id)
        if not brochure_data:
            return jsonify({'success': False, 'error': 'Broşür bulunamadı'}), 404
    
    if not brochure_data:
        return jsonify({'success': False, 'error': 'Broşür verisi gerekli'}), 400
    
    # Ghost full clean işlemi
    result = ghost_assistant.full_clean_brochure(brochure_data)
    
    # Brochure ID varsa storage'a kaydet
    if brochure_id and result.get('success'):
        brochure_engine.save_brochure(brochure_id, result.get('optimized_brochure'))
    
    return jsonify(result)


@ghost_bp.route('/api/ghost/quick-analyze', methods=['POST'])
@login_required
def api_ghost_quick_analyze():
    """
    Hızlı sayfa analizi - Sadece skor ve ana öneriler
    Canvas'tan sürekli çağrılabilir
    """
    data = request.get_json() or {}
    page_data = data
    
    if not page_data:
        return jsonify({'success': False, 'error': 'Sayfa verisi gerekli'}), 400
    
    analysis = ghost_assistant.analyze_page_design(page_data)
    
    # Sadece önemli bilgileri döndür
    return jsonify({
        'success': True,
        'data': {
            'score': analysis.get('score', 0),
            'grade': analysis.get('grade', 'C'),
            'product_count': analysis.get('product_count', 0),
            'style_hints': analysis.get('style_hints', {}),
            'product_warnings': analysis.get('product_warnings', [])[:5],  # İlk 5 uyarı
            'top_suggestion': analysis.get('suggestions', [{}])[0] if analysis.get('suggestions') else None
        }
    })


logging.info("✅ Ghost Assistant routes loaded (23 endpoints)")

