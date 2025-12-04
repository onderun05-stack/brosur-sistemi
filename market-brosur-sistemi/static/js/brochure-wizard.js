/**
 * Broşür Master - Neomodern AI-Powered Brochure Creator
 * AEU Yazılım Market Broşür Sistemi
 * 
 * Ultra-minimalist, 2-button wizard design inspired by Stripe & Linear
 * Powered by OpenAI + Kie.ai
 */

// ============= STATE =============

const wizardState = {
    mode: null, // 'quick' veya 'custom'
    step: 'home', // 'home', 'quick-preview', 'custom-chat', 'generating', 'complete'
    products: [],
    aiSuggestion: null,
    generatedBrochure: null,
    chatHistory: []
};

// ============= DESIGN TOKENS =============

const COLORS = {
    bg: '#1C1C1E',
    cardBg: '#2C2C2E',
    accent1: '#BB86FC', // Purple
    accent2: '#03DAC5', // Teal
    text: '#EAEAEA',
    textMuted: '#8E8E93',
    success: '#30D158',
    border: 'rgba(255, 255, 255, 0.1)'
};

// ============= OPEN / CLOSE =============

function openBrochureWizard() {
    console.log('🚀 Broşür Master açılıyor...');
    
    // Reset state
    wizardState.mode = null;
    wizardState.step = 'home';
    wizardState.products = getProductsForWizard();
    wizardState.chatHistory = [];
    
    // Create or show modal
    let modal = document.getElementById('brochure-wizard-modal');
    if (!modal) {
        modal = createWizardModal();
        document.body.appendChild(modal);
    }
    
    // Render home screen
    renderHomeScreen();
    
    // Show with animation
    modal.style.display = 'flex';
    requestAnimationFrame(() => {
        modal.style.opacity = '1';
        modal.querySelector('.wizard-container').style.transform = 'scale(1)';
    });
    
    document.body.style.overflow = 'hidden';
}

function closeBrochureWizard() {
    const modal = document.getElementById('brochure-wizard-modal');
    if (modal) {
        modal.style.opacity = '0';
        modal.querySelector('.wizard-container').style.transform = 'scale(0.95)';
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
    document.body.style.overflow = '';
}

// ============= CREATE MODAL =============

function createWizardModal() {
    const modal = document.createElement('div');
    modal.id = 'brochure-wizard-modal';
    modal.className = 'wizard-modal-overlay';
    modal.innerHTML = `
        <style>
            .wizard-modal-overlay {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(20px);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
                padding: 20px;
            }
            
            .wizard-container {
                background: ${COLORS.bg};
                border-radius: 24px;
                width: 100%;
                max-width: 560px;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 25px 100px rgba(0, 0, 0, 0.5), 
                            0 0 0 1px ${COLORS.border},
                            0 0 80px rgba(187, 134, 252, 0.15);
                transform: scale(0.95);
                transition: transform 0.3s ease;
            }
            
            .wizard-header {
                padding: 20px 24px;
                border-bottom: 1px solid ${COLORS.border};
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .wizard-header-left {
                display: flex;
                align-items: center;
                gap: 14px;
            }
            
            .wizard-logo {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                object-fit: contain;
                background: ${COLORS.cardBg};
                padding: 6px;
                border: 2px solid ${COLORS.border};
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 20px ${COLORS.accent1}20;
                transition: transform 0.2s ease;
            }
            
            .wizard-logo:hover {
                transform: scale(1.05);
            }
            
            .wizard-logo-placeholder {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                background: linear-gradient(135deg, ${COLORS.accent1}30, ${COLORS.accent2}30);
                border: 2px solid ${COLORS.border};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }
            
            .wizard-logo-initials {
                width: 56px;
                height: 56px;
                border-radius: 12px;
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                font-weight: 700;
                color: ${COLORS.bg};
                letter-spacing: -0.5px;
                box-shadow: 0 4px 16px ${COLORS.accent1}50;
                transition: transform 0.2s ease;
            }
            
            .wizard-logo-initials:hover {
                transform: scale(1.05);
            }
            
            .wizard-title {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .wizard-title h2 {
                color: ${COLORS.text};
                font-size: 18px;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.3px;
            }
            
            .wizard-badge {
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                color: ${COLORS.bg};
                font-size: 10px;
                font-weight: 700;
                padding: 4px 8px;
                border-radius: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .wizard-close {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                color: ${COLORS.textMuted};
                width: 32px;
                height: 32px;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                transition: all 0.2s;
            }
            
            .wizard-close:hover {
                background: rgba(255, 255, 255, 0.1);
                color: ${COLORS.text};
            }
            
            .wizard-content {
                padding: 32px 24px;
                min-height: 300px;
            }
            
            /* Home Screen */
            .wizard-home {
                text-align: center;
            }
            
            .wizard-orb {
                width: 100px;
                height: 100px;
                margin: 0 auto 32px;
                background: linear-gradient(135deg, ${COLORS.accent1}40, ${COLORS.accent2}40);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                animation: orbFloat 4s ease-in-out infinite;
            }
            
            .wizard-orb::before {
                content: '';
                position: absolute;
                inset: -4px;
                border-radius: 50%;
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                opacity: 0.3;
                filter: blur(15px);
                animation: orbGlow 3s ease-in-out infinite;
            }
            
            .wizard-orb span {
                font-size: 48px;
                position: relative;
                z-index: 1;
            }
            
            @keyframes orbFloat {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-8px); }
            }
            
            @keyframes orbGlow {
                0%, 100% { opacity: 0.3; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.1); }
            }
            
            .wizard-greeting {
                color: ${COLORS.text};
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 8px 0;
                letter-spacing: -0.5px;
            }
            
            .wizard-subtext {
                color: ${COLORS.textMuted};
                font-size: 15px;
                margin: 0 0 40px 0;
            }
            
            .wizard-buttons {
                display: flex;
                gap: 16px;
            }
            
            .wizard-btn {
                flex: 1;
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                border-radius: 16px;
                padding: 24px 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: left;
            }
            
            .wizard-btn:hover {
                transform: translateY(-4px);
                border-color: transparent;
            }
            
            .wizard-btn.btn-quick:hover {
                background: linear-gradient(135deg, ${COLORS.accent1}20, ${COLORS.accent1}10);
                box-shadow: 0 8px 32px ${COLORS.accent1}30, 0 0 0 1px ${COLORS.accent1}50;
            }
            
            .wizard-btn.btn-custom:hover {
                background: linear-gradient(135deg, ${COLORS.accent2}20, ${COLORS.accent2}10);
                box-shadow: 0 8px 32px ${COLORS.accent2}30, 0 0 0 1px ${COLORS.accent2}50;
            }
            
            .wizard-btn-icon {
                font-size: 32px;
                margin-bottom: 12px;
            }
            
            .wizard-btn-title {
                color: ${COLORS.text};
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 4px 0;
            }
            
            .wizard-btn-subtitle {
                color: ${COLORS.textMuted};
                font-size: 13px;
                margin: 0;
            }
            
            /* Quick Preview Screen */
            .wizard-preview {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .preview-header {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .preview-back {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                color: ${COLORS.textMuted};
                width: 36px;
                height: 36px;
                border-radius: 10px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            
            .preview-back:hover {
                background: rgba(255, 255, 255, 0.1);
                color: ${COLORS.text};
            }
            
            .preview-title {
                color: ${COLORS.text};
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }
            
            .preview-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
            }
            
            .stat-card {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                border-radius: 12px;
                padding: 16px;
                text-align: center;
            }
            
            .stat-value {
                color: ${COLORS.accent1};
                font-size: 24px;
                font-weight: 700;
                margin: 0;
            }
            
            .stat-label {
                color: ${COLORS.textMuted};
                font-size: 12px;
                margin: 4px 0 0 0;
            }
            
            .preview-mock {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                border-radius: 16px;
                padding: 20px;
                aspect-ratio: 4/3;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            
            .preview-mock::before {
                content: '';
                position: absolute;
                inset: 0;
                background: linear-gradient(135deg, ${COLORS.accent1}10, ${COLORS.accent2}10);
            }
            
            .preview-mock-text {
                color: ${COLORS.textMuted};
                font-size: 14px;
                text-align: center;
                position: relative;
                z-index: 1;
            }
            
            .preview-actions {
                display: flex;
                gap: 12px;
            }
            
            .action-btn {
                flex: 1;
                padding: 14px 20px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
            }
            
            .action-btn.primary {
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                color: ${COLORS.bg};
            }
            
            .action-btn.primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px ${COLORS.accent1}40;
            }
            
            .action-btn.secondary {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                color: ${COLORS.text};
            }
            
            .action-btn.secondary:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            /* Chat Screen */
            .wizard-chat {
                display: flex;
                flex-direction: column;
                height: 400px;
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding-right: 8px;
                margin-bottom: 16px;
            }
            
            .chat-message {
                margin-bottom: 16px;
                animation: messageIn 0.3s ease;
            }
            
            @keyframes messageIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .chat-message.ai {
                display: flex;
                gap: 12px;
            }
            
            .chat-avatar {
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .chat-avatar span {
                font-size: 18px;
            }
            
            .chat-bubble {
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                border-radius: 12px;
                padding: 14px 16px;
                color: ${COLORS.text};
                font-size: 14px;
                line-height: 1.5;
                max-width: 85%;
            }
            
            .chat-message.user .chat-bubble {
                background: linear-gradient(135deg, ${COLORS.accent1}30, ${COLORS.accent2}30);
                margin-left: auto;
            }
            
            .chat-input-area {
                display: flex;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                background: ${COLORS.cardBg};
                border: 1px solid ${COLORS.border};
                border-radius: 12px;
                padding: 14px 16px;
                color: ${COLORS.text};
                font-size: 14px;
                outline: none;
                transition: all 0.2s;
            }
            
            .chat-input:focus {
                border-color: ${COLORS.accent1};
                box-shadow: 0 0 0 3px ${COLORS.accent1}20;
            }
            
            .chat-input::placeholder {
                color: ${COLORS.textMuted};
            }
            
            .chat-send {
                background: linear-gradient(135deg, ${COLORS.accent1}, ${COLORS.accent2});
                border: none;
                color: ${COLORS.bg};
                width: 48px;
                height: 48px;
                border-radius: 12px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                transition: all 0.2s;
            }
            
            .chat-send:hover {
                transform: scale(1.05);
            }
            
            /* Generating Screen */
            .wizard-generating {
                text-align: center;
                padding: 40px 0;
            }
            
            .generating-spinner {
                width: 80px;
                height: 80px;
                margin: 0 auto 24px;
                position: relative;
            }
            
            .generating-spinner::before,
            .generating-spinner::after {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: 50%;
                border: 3px solid transparent;
            }
            
            .generating-spinner::before {
                border-top-color: ${COLORS.accent1};
                animation: spin 1s linear infinite;
            }
            
            .generating-spinner::after {
                inset: 8px;
                border-top-color: ${COLORS.accent2};
                animation: spin 1.5s linear infinite reverse;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            @keyframes bounce {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-8px); }
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background: ${COLORS.accent1};
                border-radius: 50%;
                display: inline-block;
            }
            
            .generating-text {
                color: ${COLORS.text};
                font-size: 18px;
                font-weight: 600;
                margin: 0 0 8px 0;
            }
            
            .generating-subtext {
                color: ${COLORS.textMuted};
                font-size: 14px;
                margin: 0;
            }
            
            /* Complete Screen */
            .wizard-complete {
                text-align: center;
            }
            
            .complete-icon {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, ${COLORS.success}20, ${COLORS.accent2}20);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
            }
            
            .complete-icon span {
                font-size: 40px;
            }
            
            .complete-title {
                color: ${COLORS.text};
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 8px 0;
            }
            
            .complete-subtitle {
                color: ${COLORS.textMuted};
                font-size: 15px;
                margin: 0 0 32px 0;
            }
            
            .complete-actions {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            /* No Products Warning */
            .no-products {
                background: rgba(255, 179, 64, 0.1);
                border: 1px solid rgba(255, 179, 64, 0.3);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 20px;
            }
            
            .no-products-title {
                color: #FFB340;
                font-size: 14px;
                font-weight: 600;
                margin: 0 0 4px 0;
            }
            
            .no-products-text {
                color: ${COLORS.textMuted};
                font-size: 13px;
                margin: 0;
            }
        </style>
        
        <div class="wizard-container">
            <div class="wizard-header">
                <div class="wizard-header-left">
                    ${getCompanyLogoHTML()}
                    <div class="wizard-title">
                        <h2>Broşür Master</h2>
                        <span class="wizard-badge">AI</span>
                    </div>
                </div>
                <button class="wizard-close" onclick="closeBrochureWizard()">×</button>
            </div>
            <div class="wizard-content" id="wizard-content">
                <!-- Content rendered dynamically -->
            </div>
        </div>
    `;
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeBrochureWizard();
    });
    
    return modal;
}

// ============= RENDER SCREENS =============

function renderHomeScreen() {
    const content = document.getElementById('wizard-content');
    const productCount = wizardState.products.length;
    const canvasCount = getCanvasProductCount();
    const listCount = (window.allProducts || []).length;
    
    // Canvas'ta ürün varsa onu göster, yoksa liste sayısını göster
    const displayCount = canvasCount > 0 ? canvasCount : productCount;
    const sourceText = canvasCount > 0 ? `Canvas'ta ${canvasCount} ürün` : 
                       productCount > 0 ? `Listede ${productCount} ürün` : '';
    
    content.innerHTML = `
        <div class="wizard-home">
            <div class="wizard-orb">
                <span>✨</span>
            </div>
            <h3 class="wizard-greeting">Ne yapmak istersin?</h3>
            <p class="wizard-subtext">AI destekli broşür oluşturucuya hoş geldin</p>
            
            ${displayCount === 0 ? `
                <div class="no-products">
                    <p class="no-products-title">⚠️ Canvas boş</p>
                    <p class="no-products-text">Hızlı broşür için önce ürünleri canvas'a sürükle</p>
                </div>
            ` : `
                <div class="products-info" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px; margin-bottom: 20px; text-align: center;">
                    <p style="color: #10b981; font-size: 14px; font-weight: 600; margin: 0;">✅ ${sourceText}</p>
                </div>
            `}
            
            <div class="wizard-buttons">
                <button class="wizard-btn btn-quick" onclick="startQuickMode()" ${displayCount === 0 ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                    <div class="wizard-btn-icon">🚀</div>
                    <p class="wizard-btn-title">Hızlı Broşür</p>
                    <p class="wizard-btn-subtitle">${displayCount > 0 ? `${displayCount} ürün hazır` : 'Önce canvas\'a ürün ekle'}</p>
                </button>
                <button class="wizard-btn btn-custom" onclick="startCustomMode()">
                    <div class="wizard-btn-icon">🤖</div>
                    <p class="wizard-btn-title">Özel İstek</p>
                    <p class="wizard-btn-subtitle">AI ile konuş</p>
                </button>
            </div>
        </div>
    `;
}

function renderQuickPreview() {
    const content = document.getElementById('wizard-content');
    const products = wizardState.products;
    
    // Calculate stats
    const totalProducts = products.length;
    const avgDiscount = calculateAverageDiscount(products);
    const categories = [...new Set(products.map(p => p.product_group || 'Genel'))].length;
    
    // Bugünün kampanyası
    const todayCampaign = typeof getTodayCampaign === 'function' ? getTodayCampaign() : null;
    
    content.innerHTML = `
        <div class="wizard-preview">
            <div class="preview-header">
                <button class="preview-back" onclick="renderHomeScreen()">←</button>
                <h3 class="preview-title">Hızlı Broşür</h3>
            </div>
            
            <div class="preview-stats">
                <div class="stat-card">
                    <p class="stat-value">${totalProducts}</p>
                    <p class="stat-label">Ürün</p>
                </div>
                <div class="stat-card">
                    <p class="stat-value" style="color: ${COLORS.accent2}">%${avgDiscount}</p>
                    <p class="stat-label">Ort. İndirim</p>
                </div>
                <div class="stat-card">
                    <p class="stat-value" style="color: ${COLORS.success}">${categories}</p>
                    <p class="stat-label">Kategori</p>
                </div>
            </div>
            
            ${todayCampaign ? `
                <div style="text-align: center; margin: 16px 0;">
                    <p style="color: ${COLORS.textMuted}; font-size: 12px; margin-bottom: 8px;">Bugüne özel öneri:</p>
                    <button class="campaign-suggestion" onclick="selectCampaign('${todayCampaign.id}')" 
                            style="background: ${todayCampaign.gradient}; border: none; padding: 12px 24px; border-radius: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">
                        <span style="font-size: 24px;">${todayCampaign.icon}</span>
                        <span style="color: white; font-weight: 600;">${todayCampaign.name}</span>
                    </button>
                </div>
            ` : ''}
            
            <div style="text-align: center; margin: 12px 0;">
                <button onclick="renderCampaignSelection()" style="background: none; border: 1px solid ${COLORS.border}; color: ${COLORS.textMuted}; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 13px;">
                    📅 Tüm kampanyalar
                </button>
            </div>
            
            <div class="preview-actions">
                <button class="action-btn secondary" onclick="renderHomeScreen()">Geri</button>
                <button class="action-btn primary" onclick="generateQuickBrochure()">
                    ✨ Oluştur
                </button>
            </div>
        </div>
    `;
}

// ============= KAMPANYA SEÇİMİ =============

function renderCampaignSelection() {
    const content = document.getElementById('wizard-content');
    
    const dailyCampaigns = typeof getDailyCampaigns === 'function' ? getDailyCampaigns() : [];
    const specialCampaigns = typeof getSpecialCampaigns === 'function' ? getSpecialCampaigns() : [];
    const holidayCampaigns = typeof getHolidayCampaigns === 'function' ? getHolidayCampaigns() : [];
    
    content.innerHTML = `
        <div class="wizard-campaigns">
            <div class="preview-header">
                <button class="preview-back" onclick="renderQuickPreview()">←</button>
                <h3 class="preview-title">Kampanya Seç</h3>
            </div>
            
            <div class="campaign-section">
                <h4 style="color: ${COLORS.text}; font-size: 14px; margin: 16px 0 12px;">📅 Haftanın Günleri</h4>
                <div class="campaign-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
                    ${dailyCampaigns.map(c => `
                        <button class="campaign-card" onclick="selectCampaign('${c.id}')" 
                                style="background: ${c.gradient}; border: none; padding: 12px 8px; border-radius: 10px; cursor: pointer; text-align: center;">
                            <span style="font-size: 20px; display: block;">${c.icon}</span>
                            <span style="color: white; font-size: 11px; font-weight: 600; display: block; margin-top: 4px;">${c.name.replace(' İndirimi', '').replace(' Özel', '')}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <div class="campaign-section">
                <h4 style="color: ${COLORS.text}; font-size: 14px; margin: 16px 0 12px;">🎉 Özel Kampanyalar</h4>
                <div class="campaign-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                    ${specialCampaigns.map(c => `
                        <button class="campaign-card" onclick="selectCampaign('${c.id}')" 
                                style="background: ${c.gradient}; border: none; padding: 14px 10px; border-radius: 10px; cursor: pointer; text-align: center;">
                            <span style="font-size: 22px; display: block;">${c.icon}</span>
                            <span style="color: white; font-size: 11px; font-weight: 600; display: block; margin-top: 4px;">${c.name}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
            
            <div class="campaign-section">
                <h4 style="color: ${COLORS.text}; font-size: 14px; margin: 16px 0 12px;">🎊 Özel Günler</h4>
                <div class="campaign-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                    ${holidayCampaigns.map(c => `
                        <button class="campaign-card" onclick="selectCampaign('${c.id}')" 
                                style="background: ${c.gradient}; border: none; padding: 14px 10px; border-radius: 10px; cursor: pointer; text-align: center;">
                            <span style="font-size: 22px; display: block;">${c.icon}</span>
                            <span style="color: white; font-size: 11px; font-weight: 600; display: block; margin-top: 4px;">${c.name}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function selectCampaign(campaignId) {
    const campaign = typeof getCampaign === 'function' ? getCampaign(campaignId) : null;
    
    if (campaign) {
        wizardState.selectedCampaign = campaign;
        wizardState.slogan = campaign.slogan;
        wizardState.colors = {
            primary: campaign.color,
            gradient: campaign.gradient
        };
        
        wizardShowNotification(`✅ ${campaign.name} seçildi!`);
        
        // Stüdyoya geç (kampanya bilgileriyle)
        renderGenerating(`${campaign.icon} ${campaign.name} broşürü hazırlanıyor...`);
        setTimeout(() => renderStudioStep(), 1500);
    }
}

function renderCustomChat() {
    const content = document.getElementById('wizard-content');
    
    content.innerHTML = `
        <div class="wizard-chat">
            <div class="preview-header" style="margin-bottom: 16px;">
                <button class="preview-back" onclick="renderHomeScreen()">←</button>
                <h3 class="preview-title">AI ile Konuş</h3>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <!-- Messages rendered here -->
            </div>
            
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chat-input" 
                       placeholder="Ne tür bir broşür istiyorsun?" 
                       onkeypress="if(event.key==='Enter') sendChatMessage()">
                <button class="chat-send" onclick="sendChatMessage()">→</button>
            </div>
        </div>
    `;
    
    // Add initial AI message
    addAIMessage("Merhaba! 👋 Ben AEU AI asistanıyım. Ne tür bir broşür oluşturmak istiyorsun? Örneğin:\n\n• İndirim kampanyası\n• Bayram broşürü\n• İş ilanı\n• Özel duyuru");
}

function renderGenerating(message = 'Broşür hazırlanıyor...') {
    const content = document.getElementById('wizard-content');
    
    content.innerHTML = `
        <div class="wizard-generating">
            <div class="generating-spinner"></div>
            <p class="generating-text">${message}</p>
            <p class="generating-subtext">AI tasarımınızı oluşturuyor</p>
        </div>
    `;
}

function renderComplete() {
    const content = document.getElementById('wizard-content');
    
    // Canvas önizlemesi al
    let previewUrl = '';
    if (typeof fabricCanvas !== 'undefined' && fabricCanvas) {
        try {
            previewUrl = fabricCanvas.toDataURL({
                format: 'jpeg',
                quality: 0.8,
                multiplier: 0.5
            });
        } catch (e) {
            console.log('Canvas preview error:', e);
        }
    }
    
    content.innerHTML = `
        <div class="wizard-complete">
            <div class="complete-icon">
                <span>✅</span>
            </div>
            <h3 class="complete-title">Broşür Hazır!</h3>
            <p class="complete-subtitle">Broşürünüz başarıyla oluşturuldu</p>
            
            ${previewUrl ? `
                <div class="brochure-preview" style="margin: 20px 0; border-radius: 12px; overflow: hidden; border: 2px solid ${COLORS.border}; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                    <img src="${previewUrl}" alt="Broşür Önizleme" style="width: 100%; height: auto; display: block;">
                </div>
            ` : ''}
            
            <div class="complete-actions">
                <button class="action-btn primary" onclick="downloadBrochure()">
                    📥 PDF İndir
                </button>
                <button class="action-btn secondary" onclick="saveBrochure()">
                    💾 Kaydet
                </button>
                <button class="action-btn secondary" onclick="closeBrochureWizard()">
                    ✏️ Düzenle
                </button>
            </div>
        </div>
    `;
}

// Broşürü indir
function downloadBrochure() {
    if (typeof fabricCanvas !== 'undefined' && fabricCanvas) {
        const dataUrl = fabricCanvas.toDataURL({
            format: 'jpeg',
            quality: 1.0
        });
        
        const link = document.createElement('a');
        link.download = `brosur-${Date.now()}.jpg`;
        link.href = dataUrl;
        link.click();
        
        wizardShowNotification('✅ Broşür indirildi!');
    } else {
        wizardShowNotification('❌ Canvas bulunamadı');
    }
}

// ============= MODE HANDLERS =============

function startQuickMode() {
    if (wizardState.products.length === 0) return;
    
    wizardState.mode = 'quick';
    wizardState.step = 'quick-preview';
    renderQuickPreview();
}

function startCustomMode() {
    wizardState.mode = 'custom';
    wizardState.step = 'custom-chat';
    renderCustomChat();
}

// ============= CHAT FUNCTIONS =============

function addAIMessage(text) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageHtml = `
        <div class="chat-message ai">
            <div class="chat-avatar"><span>🤖</span></div>
            <div class="chat-bubble">${text.replace(/\n/g, '<br>')}</div>
        </div>
    `;
    
    messagesDiv.innerHTML += messageHtml;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    wizardState.chatHistory.push({ role: 'assistant', content: text });
}

function addUserMessage(text) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageHtml = `
        <div class="chat-message user">
            <div class="chat-bubble">${text}</div>
        </div>
    `;
    
    messagesDiv.innerHTML += messageHtml;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    wizardState.chatHistory.push({ role: 'user', content: text });
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    input.value = '';
    addUserMessage(message);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Get context for AI
        const context = {
            purpose: wizardState.mode || 'general',
            products: wizardState.products.slice(0, 10), // Send max 10 products
            companyName: getCompanyName()
        };
        
        // Call real AI endpoint
        const response = await fetch('/api/wizard/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: wizardState.chatHistory,
                context: context
            })
        });
        
        const data = await response.json();
        
        hideTypingIndicator();
        
        if (data.success && data.message) {
            addAIMessage(data.message);
            
            // Show token usage if available
            if (data.tokens_used > 0) {
                console.log(`🤖 AI: ${data.tokens_used} token kullanıldı ($${data.cost_usd})`);
            }
            
            // Check if AI says ready to create
            if (data.message.toLowerCase().includes('oluştur') || 
                data.message.toLowerCase().includes('hazır')) {
                showCreateButton();
            }
        } else {
            addAIMessage("Bir sorun oluştu, tekrar dener misin? 🙏");
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        hideTypingIndicator();
        addAIMessage("Bağlantı sorunu var, tekrar dene! 🔄");
    }
}

function showTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const typingHtml = `
        <div class="chat-message ai typing-indicator" id="typing-indicator">
            <div class="chat-avatar"><span>🤖</span></div>
            <div class="chat-bubble" style="display: flex; gap: 4px; padding: 16px;">
                <span class="typing-dot" style="animation: bounce 1s infinite;"></span>
                <span class="typing-dot" style="animation: bounce 1s infinite 0.2s;"></span>
                <span class="typing-dot" style="animation: bounce 1s infinite 0.4s;"></span>
            </div>
        </div>
    `;
    
    messagesDiv.innerHTML += typingHtml;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function showCreateButton() {
    const chatArea = document.querySelector('.chat-input-area');
    if (!chatArea) return;
    
    // Check if button already exists
    if (document.getElementById('create-from-chat-btn')) return;
    
    const createBtn = document.createElement('button');
    createBtn.id = 'create-from-chat-btn';
    createBtn.className = 'action-btn primary';
    createBtn.style.cssText = 'margin-top: 12px; width: 100%;';
    createBtn.innerHTML = '✨ Broşürü Oluştur';
    createBtn.onclick = () => {
        renderGenerating('AI broşürünüzü tasarlıyor...');
        setTimeout(() => renderComplete(), 2000);
    };
    
    chatArea.parentNode.appendChild(createBtn);
}

function getCompanyName() {
    try {
        const companyInfo = JSON.parse(localStorage.getItem('companyInfo') || '{}');
        return companyInfo.name || 'Market';
    } catch (e) {
        return 'Market';
    }
}

// ============= GENERATE FUNCTIONS =============

async function generateQuickBrochure() {
    renderGenerating('AI broşürünüzü tasarlıyor...');
    
    try {
        // Call backend API
        const response = await fetch('/api/wizard/generate-brochure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                purpose: 'discount',
                products: wizardState.products.slice(0, 20),
                companyInfo: JSON.parse(localStorage.getItem('companyInfo') || '{}'),
                logo: localStorage.getItem('companyLogo') || ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            wizardState.generatedBrochure = data.brochure;
        }
        
        // Her durumda stüdyoya geç (düzenleme imkanı ver)
        renderStudioStep();
        
    } catch (error) {
        console.error('Generate error:', error);
        renderStudioStep();
        wizardShowNotification('⚠️ AI şu an meşgul, manuel düzenle');
    }
}

// ============= STUDIO STEP =============

function renderStudioStep() {
    const content = document.getElementById('wizard-content');
    
    // Şablon seç (varsayılan veya AI önerisi)
    const templateId = wizardState.generatedBrochure?.template || 'classic-market';
    const template = (typeof getTemplate === 'function') ? getTemplate(templateId) : null;
    
    if (!template) {
        // Şablon sistemi yüklenemedi, direkt complete'e git
        console.warn('Template system not loaded');
        renderComplete();
        return;
    }
    
    // Stüdyoyu başlat
    initStudio(template, wizardState.products);
    
    content.innerHTML = `
        <div class="studio-step">
            <div class="studio-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <div>
                    <h3 style="color:${COLORS.text};margin:0;font-size:18px;">🎨 Broşür Stüdyosu</h3>
                    <p style="color:${COLORS.textMuted};margin:4px 0 0;font-size:13px;">Şablonu, renkleri ve sloganı düzenle</p>
                </div>
                <div style="display:flex;gap:8px;">
                    <button class="action-btn secondary" onclick="renderHomeScreen()" style="padding:8px 16px;">
                        ← Geri
                    </button>
                </div>
            </div>
            <div id="studio-container"></div>
        </div>
    `;
    
    // Stüdyoyu render et
    const container = document.getElementById('studio-container');
    if (container && typeof renderStudio === 'function') {
        renderStudio(container);
    }
}

// Stüdyodan çağrılır
function wizardApplyStudioChanges(state) {
    // Stüdyo değişikliklerini kaydet
    wizardState.generatedBrochure = {
        ...wizardState.generatedBrochure,
        template: state.template.id,
        colors: state.colors,
        slogan: state.slogan,
        badges: state.badges
    };
    
    // Canvas'a uygula
    applyBrochureToCanvas(state);
    
    // Complete ekranına geç
    renderComplete();
}

function applyBrochureToCanvas(state) {
    if (typeof fabricCanvas === 'undefined' || !fabricCanvas) return;
    
    // Arka plan rengini ayarla
    fabricCanvas.backgroundColor = state.colors.background || '#ffffff';
    
    // Header ekle
    const headerRect = new fabric.Rect({
        left: 0,
        top: 0,
        width: fabricCanvas.width,
        height: 80,
        fill: state.colors.primary,
        selectable: false
    });
    fabricCanvas.add(headerRect);
    
    // Slogan ekle
    const sloganText = new fabric.Text(state.slogan, {
        left: fabricCanvas.width / 2,
        top: 30,
        fontSize: 28,
        fontWeight: 'bold',
        fill: '#ffffff',
        originX: 'center',
        fontFamily: 'Arial Black'
    });
    fabricCanvas.add(sloganText);
    
    fabricCanvas.renderAll();
    wizardShowNotification('✅ Broşür canvas\'a uygulandı!');
}

async function saveBrochure() {
    try {
        // Save to user's brochures
        const brochures = JSON.parse(localStorage.getItem('userBrochures') || '[]');
        brochures.push({
            id: Date.now(),
            name: `Broşür ${new Date().toLocaleDateString('tr-TR')}`,
            data: wizardState.generatedBrochure,
            createdAt: new Date().toISOString()
        });
        localStorage.setItem('userBrochures', JSON.stringify(brochures));
        
        wizardShowNotification('✅ Broşür "Broşürlerim" klasörüne kaydedildi!');
        closeBrochureWizard();
    } catch (error) {
        console.error('Save error:', error);
        wizardShowNotification('❌ Kaydetme hatası');
    }
}

// ============= HELPERS =============

function getCompanyLogoHTML() {
    // Wizard header'da admin/site logosu gösterilir (tüm müşteriler için aynı)
    // Müşterinin kendi logosu broşüre eklenir, wizard UI'da site logosu görünür
    return `<img src="/static/aeu_logo.png" alt="Site Logo" class="wizard-logo" onerror="this.outerHTML=getCompanyInitials()">`;
}

function getCompanyInitials() {
    let initials = 'AEU'; // Default
    
    try {
        const companyInfo = JSON.parse(localStorage.getItem('companyInfo') || '{}');
        if (companyInfo.name) {
            // Get first 2-3 letters of company name
            const words = companyInfo.name.split(' ').filter(w => w.length > 0);
            if (words.length >= 2) {
                initials = words.slice(0, 2).map(w => w[0].toUpperCase()).join('');
            } else if (words.length === 1) {
                initials = words[0].substring(0, 2).toUpperCase();
            }
        }
    } catch (e) {
        console.log('Company info parse error:', e);
    }
    
    return `<div class="wizard-logo-initials">${initials}</div>`;
}

function getProductsForWizard() {
    // 1. ÖNCE Canvas'taki ürünleri kontrol et (en önemli kaynak)
    if (typeof fabricCanvas !== 'undefined' && fabricCanvas) {
        const canvasObjects = fabricCanvas.getObjects();
        const canvasProducts = canvasObjects
            .filter(obj => obj.productCard || obj.productData)
            .map(obj => obj.productData)
            .filter(data => data); // null olanları filtrele
        
        if (canvasProducts.length > 0) {
            console.log('✅ Wizard: Canvas\'tan ürünler alındı:', canvasProducts.length);
            return canvasProducts;
        }
    }
    
    // 2. Canvas boşsa, ürün listesinden al
    if (window.allProducts && window.allProducts.length > 0) {
        console.log('ℹ️ Wizard: Canvas boş, ürün listesi kullanılıyor:', window.allProducts.length);
        return window.allProducts;
    }
    
    // 3. Fallback: try local allProducts
    if (typeof allProducts !== 'undefined' && allProducts.length > 0) {
        console.log('ℹ️ Wizard: local allProducts kullanılıyor');
        return allProducts;
    }
    
    console.log('⚠️ Wizard: Ürün bulunamadı');
    return [];
}

// Canvas'taki ürün sayısını al (ayrı fonksiyon)
function getCanvasProductCount() {
    if (typeof fabricCanvas !== 'undefined' && fabricCanvas) {
        return fabricCanvas.getObjects().filter(obj => obj.productCard || obj.productData).length;
    }
    return 0;
}

function calculateAverageDiscount(products) {
    if (!products.length) return 0;
    
    let totalDiscount = 0;
    let count = 0;
    
    products.forEach(p => {
        const normal = parseFloat(p.normal_price) || 0;
        const discount = parseFloat(p.discount_price) || 0;
        
        if (normal > 0 && discount > 0 && discount < normal) {
            totalDiscount += ((normal - discount) / normal) * 100;
            count++;
        }
    });
    
    return count > 0 ? Math.round(totalDiscount / count) : 0;
}

function wizardShowNotification(message) {
    // Use the global showNotification from index.html if available
    const globalNotify = window._originalShowNotification || window.showNotification;
    if (globalNotify && typeof globalNotify === 'function' && globalNotify !== wizardShowNotification) {
        globalNotify(message);
    } else {
        // Fallback: create simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 99999;
            animation: slideIn 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// ============= KEYBOARD SHORTCUTS =============

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('brochure-wizard-modal');
        if (modal && modal.style.display !== 'none') {
            closeBrochureWizard();
        }
    }
});

// ============= EXPORTS =============

window.openBrochureWizard = openBrochureWizard;
window.closeBrochureWizard = closeBrochureWizard;
window.startQuickMode = startQuickMode;
window.startCustomMode = startCustomMode;
window.sendChatMessage = sendChatMessage;
window.generateQuickBrochure = generateQuickBrochure;
window.saveBrochure = saveBrochure;
window.downloadBrochure = downloadBrochure;
window.renderHomeScreen = renderHomeScreen;
window.getCanvasProductCount = getCanvasProductCount;

console.log('🚀 Broşür Master yüklendi');
