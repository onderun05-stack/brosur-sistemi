/**
 * Ghost Assistant UI - Client-side JavaScript
 * AEU Yazılım Broşür Sistemi
 * 
 * Hayalet asistan: 64x64 bulut benzeri 3D model, şimşek ikonu
 * Sürekli kullanıcı eylemlerini analiz eder ve öneri sunar
 */

class GhostAssistant {
  constructor() {
    this.isOpen = false;
    this.isActive = true;
    this.idleTimer = null;
    this.idleSeconds = 0;
    this.messages = [];
    this.currentBrochureId = null;
    
    this.init();
  }
  
  init() {
    this.createUI();
    this.bindEvents();
    this.startIdleTracking();
    this.loadGreeting();
  }
  
  // ============= UI CREATION =============
  
  createUI() {
    // Create Ghost Container
    const container = document.createElement('div');
    container.className = 'ghost-container';
    container.id = 'ghost-container';
    container.innerHTML = `
      <!-- Ghost Tip Bubble -->
      <div class="ghost-tip" id="ghost-tip" style="display: none;">
        <button class="ghost-tip-close" onclick="ghost.hideTip()">×</button>
        <p id="ghost-tip-text"></p>
      </div>
      
      <!-- Ghost Chat Panel -->
      <div class="ghost-panel" id="ghost-panel">
        <div class="ghost-panel-header">
          <span class="ghost-panel-icon">⚡</span>
          <div class="ghost-panel-title">
            <h4>Hayalet</h4>
            <span>AI Tasarım Asistanı</span>
          </div>
          <button class="ghost-panel-close" onclick="ghost.toggle()">×</button>
        </div>
        
        <div class="ghost-messages" id="ghost-messages">
          <!-- Messages will be added here -->
        </div>
        
        <div class="ghost-input-area">
          <input type="text" class="ghost-input" id="ghost-input" 
                 placeholder="Bir şey sorun..." 
                 onkeypress="if(event.key === 'Enter') ghost.sendMessage()">
          <button class="ghost-send-btn" onclick="ghost.sendMessage()">➤</button>
        </div>
      </div>
      
      <!-- Ghost Avatar Button -->
      <div class="ghost-avatar" id="ghost-avatar" onclick="ghost.toggle()">
        <div class="ghost-status"></div>
      </div>
    `;
    
    document.body.appendChild(container);
  }
  
  bindEvents() {
    // Track user activity to reset idle timer
    document.addEventListener('mousemove', () => this.resetIdleTimer());
    document.addEventListener('keypress', () => this.resetIdleTimer());
    document.addEventListener('click', () => this.resetIdleTimer());
    document.addEventListener('scroll', () => this.resetIdleTimer());
    
    // Listen for brochure events
    document.addEventListener('brochure-loaded', (e) => {
      this.currentBrochureId = e.detail?.brochureId;
      this.analyzeBrochure();
    });
    
    document.addEventListener('page-changed', () => {
      this.analyzeCurrentPage();
    });
    
    document.addEventListener('product-added', () => {
      this.suggestNextAction();
    });
  }
  
  // ============= PANEL CONTROL =============
  
  toggle() {
    this.isOpen = !this.isOpen;
    const panel = document.getElementById('ghost-panel');
    const avatar = document.getElementById('ghost-avatar');
    
    if (this.isOpen) {
      panel.classList.add('active');
      avatar.classList.add('active');
      this.hideTip();
    } else {
      panel.classList.remove('active');
      avatar.classList.remove('active');
    }
  }
  
  showTip(message) {
    const tipEl = document.getElementById('ghost-tip');
    const tipText = document.getElementById('ghost-tip-text');
    
    tipText.textContent = message;
    tipEl.style.display = 'block';
    
    // Auto hide after 8 seconds
    setTimeout(() => this.hideTip(), 8000);
  }
  
  hideTip() {
    const tipEl = document.getElementById('ghost-tip');
    tipEl.style.display = 'none';
  }
  
  // ============= MESSAGING =============
  
  addMessage(text, suggestions = [], isGhost = true) {
    const messagesEl = document.getElementById('ghost-messages');
    
    const messageHtml = `
      <div class="ghost-message">
        ${isGhost ? `<div class="ghost-message-avatar">⚡</div>` : ''}
        <div class="ghost-message-content">
          <p>${text}</p>
          ${suggestions.length > 0 ? `
            <div class="ghost-suggestions">
              ${suggestions.map(s => `
                <button class="ghost-suggestion-btn" onclick="ghost.handleSuggestion('${s}')">${s}</button>
              `).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `;
    
    messagesEl.insertAdjacentHTML('beforeend', messageHtml);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    this.messages.push({ text, suggestions, isGhost, timestamp: new Date() });
  }
  
  async sendMessage() {
    const input = document.getElementById('ghost-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    this.addMessage(message, [], false);
    input.value = '';
    
    try {
      const response = await fetch('/api/ghost/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, context: { brochureId: this.currentBrochureId } })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const resp = data.response;
        this.addMessage(resp.text, resp.suggestions || []);
        
        // Handle action if present
        if (resp.action) {
          this.handleAction(resp.action);
        }
      }
    } catch (error) {
      console.error('Ghost chat error:', error);
      this.addMessage('Bir hata oluştu. Tekrar deneyin.');
    }
  }
  
  handleSuggestion(suggestion) {
    document.getElementById('ghost-input').value = suggestion;
    this.sendMessage();
  }
  
  handleAction(action) {
    switch (action) {
      case 'auto_arrange':
        if (window.editor && typeof window.editor.autoArrange === 'function') {
          window.editor.autoArrange();
        }
        break;
      case 'suggest_layout':
        this.suggestLayout();
        break;
      case 'analyze':
        this.analyzeBrochure();
        break;
      case 'export':
        if (window.editor && typeof window.editor.exportPDF === 'function') {
          window.editor.exportPDF();
        }
        break;
    }
  }
  
  // ============= API CALLS =============
  
  async loadGreeting() {
    try {
      const response = await fetch('/api/ghost/greeting');
      const data = await response.json();
      
      if (data.success) {
        this.addMessage(data.greeting, ['Sayfa düzenle', 'Ürün ara', 'Yardım']);
      }
    } catch (error) {
      console.error('Ghost greeting error:', error);
    }
  }
  
  async analyzeBrochure() {
    if (!this.currentBrochureId) return;
    
    try {
      const response = await fetch(`/api/ghost/analyze-brochure/${this.currentBrochureId}`);
      const data = await response.json();
      
      if (data.success) {
        const analysis = data.analysis;
        const score = analysis.overall_score;
        const grade = analysis.overall_grade;
        
        // Show quality badge
        this.showQualityBadge(score, grade);
        
        // Add summary message if panel is open
        if (this.isOpen) {
          this.addMessage(analysis.summary, ['Optimize et', 'Detayları gör']);
        }
        
        // Show tip for issues
        if (analysis.warnings.length > 0) {
          const warning = analysis.warnings[0];
          setTimeout(() => {
            if (!this.isOpen) {
              this.showTip(warning.message);
            }
          }, 2000);
        }
      }
    } catch (error) {
      console.error('Ghost analyze error:', error);
    }
  }
  
  async analyzeCurrentPage() {
    const pageData = this.getCurrentPageData();
    if (!pageData) return;
    
    try {
      const response = await fetch('/api/ghost/analyze-page', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page: pageData })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const analysis = data.analysis;
        
        // Show suggestions if score is low
        if (analysis.score < 70 && analysis.suggestions.length > 0) {
          const suggestion = analysis.suggestions[0];
          if (!this.isOpen) {
            this.showTip(suggestion.message);
          }
        }
      }
    } catch (error) {
      console.error('Ghost page analyze error:', error);
    }
  }
  
  async suggestLayout() {
    const pageData = this.getCurrentPageData();
    const products = pageData?.products || [];
    
    try {
      const response = await fetch('/api/ghost/suggest-layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ products, sector: window.userSector || 'supermarket' })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const suggestion = data.suggestion;
        this.addMessage(
          `${products.length} ürün için ${suggestion.suggested_layout} düzenini öneriyorum. ${suggestion.reason}`,
          ['Uygula', 'Diğer seçenekler']
        );
      }
    } catch (error) {
      console.error('Ghost layout error:', error);
    }
  }
  
  async suggestNextAction() {
    const brochureState = this.getBrochureState();
    
    try {
      const response = await fetch('/api/ghost/suggest-next-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brochure_state: brochureState })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const suggestion = data.suggestion;
        
        // Show tip if not panel open
        if (!this.isOpen && suggestion.priority === 'high') {
          this.showTip(suggestion.message);
        }
      }
    } catch (error) {
      console.error('Ghost next action error:', error);
    }
  }
  
  async getPriceInsight(customerPrice, marketPrice, productName) {
    try {
      const response = await fetch('/api/ghost/price-insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_price: customerPrice,
          market_price: marketPrice,
          product_name: productName
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.insight.has_insight) {
        return data.insight;
      }
    } catch (error) {
      console.error('Ghost price insight error:', error);
    }
    
    return null;
  }
  
  async getWorkflowProgress() {
    const brochureState = this.getBrochureState();
    
    try {
      const response = await fetch('/api/ghost/workflow-progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brochure_state: brochureState })
      });
      
      const data = await response.json();
      
      if (data.success) {
        return data.progress;
      }
    } catch (error) {
      console.error('Ghost workflow error:', error);
    }
    
    return null;
  }
  
  // ============= IDLE TRACKING =============
  
  startIdleTracking() {
    this.idleTimer = setInterval(() => {
      this.idleSeconds++;
      this.checkIdleTip();
    }, 1000);
  }
  
  resetIdleTimer() {
    this.idleSeconds = 0;
  }
  
  async checkIdleTip() {
    if (this.idleSeconds === 5 || this.idleSeconds === 15) {
      try {
        const response = await fetch('/api/ghost/idle-tip', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            idle_seconds: this.idleSeconds,
            current_page: this.getCurrentPageData()
          })
        });
        
        const data = await response.json();
        
        if (data.success && data.has_tip && !this.isOpen) {
          this.showTip(data.tip.message);
        }
      } catch (error) {
        // Silently fail
      }
    }
  }
  
  // ============= HELPERS =============
  
  getCurrentPageData() {
    // Get current page data from editor
    if (window.editor && typeof window.editor.getCurrentPage === 'function') {
      return window.editor.getCurrentPage();
    }
    return null;
  }
  
  getBrochureState() {
    // Get full brochure state from editor
    if (window.editor && typeof window.editor.getBrochureState === 'function') {
      return window.editor.getBrochureState();
    }
    return { pages: [], parking_area: [] };
  }
  
  showQualityBadge(score, grade) {
    // Find or create quality badge element
    let badge = document.getElementById('quality-badge');
    
    if (!badge) {
      badge = document.createElement('div');
      badge.id = 'quality-badge';
      badge.className = 'quality-score';
      
      // Insert near toolbar if exists
      const toolbar = document.querySelector('.editor-toolbar');
      if (toolbar) {
        toolbar.appendChild(badge);
      }
    }
    
    badge.className = `quality-score grade-${grade.toLowerCase()}`;
    badge.innerHTML = `<span>Kalite: ${Math.round(score)}</span> <span>${grade}</span>`;
  }
  
  // ============= PRODUCT HIGHLIGHT SYSTEM (Madde 3) =============
  
  /**
   * Ürün uyarılarını canvas üzerinde highlight et (Madde 3)
   * Glow efekti ve hover'da Ghost balonu göster
   * 
   * @param {Array} productWarnings - Ürün bazlı uyarılar [{product_id, type, message, severity}]
   */
  highlightProductWarnings(productWarnings) {
    if (!productWarnings || productWarnings.length === 0) return;
    
    // Eski highlight'ları temizle
    this.clearProductHighlights();
    
    productWarnings.forEach(warning => {
      const productElement = this.findProductElement(warning.product_id);
      if (productElement) {
        this.addHighlightEffect(productElement, warning);
      }
    });
  }
  
  /**
   * Ürün elementini bul
   */
  findProductElement(productId) {
    // Canvas'ta product card bul
    return document.querySelector(`[data-product-id="${productId}"]`) ||
           document.querySelector(`[data-barcode="${productId}"]`) ||
           document.querySelector(`.product-card[data-id="${productId}"]`);
  }
  
  /**
   * Highlight efekti ekle
   */
  addHighlightEffect(element, warning) {
    const glowColor = this.getWarningGlowColor(warning.severity);
    
    // Glow efekti CSS
    element.style.boxShadow = `0 0 12px 4px ${glowColor}`;
    element.style.border = `2px solid ${glowColor}`;
    element.style.transition = 'box-shadow 0.3s ease, border 0.3s ease';
    element.classList.add('ghost-highlighted');
    element.dataset.ghostWarning = JSON.stringify(warning);
    
    // Hover event'i ekle
    element.addEventListener('mouseenter', (e) => this.showWarningBubble(e, warning));
    element.addEventListener('mouseleave', () => this.hideWarningBubble());
  }
  
  /**
   * Uyarı glow rengi
   */
  getWarningGlowColor(severity) {
    const colors = {
      'error': '#ff6565',
      'warning': '#ffb347',
      'info': '#87ceeb',
      'success': '#90ee90'
    };
    return colors[severity] || '#ffb347';
  }
  
  /**
   * Ghost uyarı balonu göster
   */
  showWarningBubble(event, warning) {
    // Mevcut balonu temizle
    this.hideWarningBubble();
    
    const bubble = document.createElement('div');
    bubble.className = 'ghost-warning-bubble';
    bubble.id = 'ghost-warning-bubble';
    bubble.innerHTML = `
      <div class="ghost-bubble-icon">👻</div>
      <div class="ghost-bubble-content">
        <span class="ghost-bubble-type">${this.getWarningTypeLabel(warning.type)}</span>
        <p>${warning.message}</p>
        ${warning.suggestion ? `<small>💡 Öneri: ${warning.suggestion}</small>` : ''}
      </div>
    `;
    
    // Pozisyonu ayarla
    const rect = event.target.getBoundingClientRect();
    bubble.style.cssText = `
      position: fixed;
      left: ${rect.right + 10}px;
      top: ${rect.top}px;
      z-index: 10000;
      background: rgba(50, 50, 50, 0.95);
      color: white;
      padding: 12px 16px;
      border-radius: 10px;
      max-width: 280px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      font-size: 13px;
      line-height: 1.4;
      display: flex;
      gap: 10px;
      align-items: flex-start;
      animation: ghostBubbleFadeIn 0.2s ease;
    `;
    
    document.body.appendChild(bubble);
  }
  
  /**
   * Uyarı balonunu gizle
   */
  hideWarningBubble() {
    const bubble = document.getElementById('ghost-warning-bubble');
    if (bubble) {
      bubble.remove();
    }
  }
  
  /**
   * Uyarı tipi etiketi
   */
  getWarningTypeLabel(type) {
    const labels = {
      'long_name': '📝 Uzun İsim',
      'low_quality_image': '🖼️ Düşük Kalite',
      'price_too_large': '💰 Büyük Fiyat',
      'price_too_small': '💰 Küçük Fiyat',
      'missing_price': '❌ Fiyat Yok',
      'missing_image': '❌ Resim Yok'
    };
    return labels[type] || '⚠️ Uyarı';
  }
  
  /**
   * Tüm highlight'ları temizle
   */
  clearProductHighlights() {
    document.querySelectorAll('.ghost-highlighted').forEach(el => {
      el.style.boxShadow = '';
      el.style.border = '';
      el.classList.remove('ghost-highlighted');
      delete el.dataset.ghostWarning;
    });
    this.hideWarningBubble();
  }
  
  /**
   * Name normalizer API çağrısı
   */
  async normalizeProductName(productName) {
    try {
      const response = await fetch('/api/ghost/normalize-name', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: productName })
      });
      
      const data = await response.json();
      if (data.success) {
        return data.normalized;
      }
    } catch (error) {
      console.error('Ghost normalize name error:', error);
    }
    return productName;
  }
  
  /**
   * Tam broşür temizliği
   */
  async fullCleanBrochure(brochureData) {
    this.addMessage('🧹 Tam temizlik başlatılıyor...');
    
    try {
      const response = await fetch('/api/ghost/full-clean-brochure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brochure: brochureData })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.addMessage(data.message, ['Değişiklikleri gör', 'Geri al']);
        return data;
      } else {
        this.addMessage('Temizlik işlemi başarısız oldu.');
      }
    } catch (error) {
      console.error('Ghost full clean error:', error);
      this.addMessage('Bir hata oluştu.');
    }
    return null;
  }
  
  /**
   * Import doğrulama
   */
  async validateImportData(products) {
    try {
      const response = await fetch('/api/ghost/validate-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ products })
      });
      
      const data = await response.json();
      
      if (data.success && data.validation) {
        const validation = data.validation;
        
        // Samimi mesajları göster
        if (validation.suggestions && validation.suggestions.length > 0) {
          validation.suggestions.forEach(suggestion => {
            this.showTip(suggestion.message);
          });
        }
        
        return validation;
      }
    } catch (error) {
      console.error('Ghost validate import error:', error);
    }
    return null;
  }
  
  // ============= AUTO BROCHURE =============
  
  async createAutoBrochurePlan(products, settings = {}) {
    try {
      const response = await fetch('/api/ghost/create-auto-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ products, settings })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.addMessage(
          `Otomatik broşür planı oluşturuldu! ${data.plan.total_steps} adım, tahmini süre: ${data.plan.estimated_time}`,
          ['Başlat', 'Planı görüntüle']
        );
        return data.plan;
      }
    } catch (error) {
      console.error('Ghost auto plan error:', error);
      this.addMessage('Plan oluşturulurken bir hata oluştu.');
    }
    
    return null;
  }
  
  async optimizeBrochure() {
    if (!this.currentBrochureId) {
      this.addMessage('Önce bir broşür açın.');
      return;
    }
    
    this.addMessage('Broşürünüz optimize ediliyor...');
    
    try {
      const response = await fetch('/api/ghost/optimize-brochure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brochure_id: this.currentBrochureId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.addMessage(
          `✨ ${data.message}! Puan: ${data.before_score} → ${data.after_score}`,
          ['Değişiklikleri gör']
        );
        
        // Refresh editor
        if (window.editor && typeof window.editor.refresh === 'function') {
          window.editor.refresh();
        }
      }
    } catch (error) {
      console.error('Ghost optimize error:', error);
      this.addMessage('Optimizasyon sırasında bir hata oluştu.');
    }
  }
}

// Ghost bubble animation styles (inject once)
const ghostStyles = document.createElement('style');
ghostStyles.textContent = `
  @keyframes ghostBubbleFadeIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
  }
  
  .ghost-warning-bubble {
    animation: ghostBubbleFadeIn 0.2s ease !important;
  }
  
  .ghost-bubble-icon {
    font-size: 24px;
    line-height: 1;
  }
  
  .ghost-bubble-content {
    flex: 1;
  }
  
  .ghost-bubble-type {
    display: block;
    font-weight: 600;
    margin-bottom: 4px;
    color: #ffb347;
  }
  
  .ghost-bubble-content p {
    margin: 0 0 6px 0;
  }
  
  .ghost-bubble-content small {
    color: #90ee90;
    display: block;
  }
  
  .ghost-highlighted {
    transition: box-shadow 0.3s ease, border 0.3s ease !important;
    animation: ghostHighlightPulse 2s infinite !important;
  }
  
  @keyframes ghostHighlightPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
  }
`;
document.head.appendChild(ghostStyles);

// Initialize Ghost Assistant
let ghost = null;

function shouldInitializeGhost() {
  if (typeof window === 'undefined') return false;
  // Explicit opt-in: only run when __enableGhostAssistant set true
  return window.__enableGhostAssistant === true;
}

document.addEventListener('DOMContentLoaded', () => {
  if (!shouldInitializeGhost()) {
    console.info('Ghost Assistant disabled (set window.__enableGhostAssistant = true to enable).');
    return;
  }
  // Only initialize on pages with editor
  if (document.querySelector('#main-screen') || document.querySelector('.editor-wrapper')) {
    ghost = new GhostAssistant();
    window.ghost = ghost;
  }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GhostAssistant;
}

