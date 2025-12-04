/**
 * Settings Panel - Glassmorphism UI
 * AEU Yazılım Broşür Sistemi
 * 
 * Sekmeli ayarlar paneli: firma, logo, sosyal, yemek çeki, kredi, şablonlar, broşürler
 */

class SettingsPanel {
  constructor() {
    this.isOpen = false;
    this.currentTab = 'company';
    this.settings = {};
    this.init();
  }
  
  init() {
    this.createUI();
    this.bindEvents();
  }
  
  createUI() {
    const modal = document.createElement('div');
    modal.className = 'settings-modal';
    modal.id = 'settings-modal';
    modal.innerHTML = `
      <div class="settings-panel glass-card">
        <div class="settings-header">
          <h2>⚙️ Ayarlar</h2>
          <button class="settings-close" onclick="settingsPanel.close()">×</button>
        </div>
        
        <div class="settings-body">
          <!-- Tabs Navigation -->
          <div class="settings-tabs">
            <button class="settings-tab active" data-tab="company" onclick="settingsPanel.switchTab('company')">
              <span class="settings-tab-icon">🏢</span>
              <span class="settings-tab-text">Firma</span>
            </button>
            <button class="settings-tab" data-tab="logo" onclick="settingsPanel.switchTab('logo')">
              <span class="settings-tab-icon">🖼️</span>
              <span class="settings-tab-text">Logo</span>
            </button>
            <button class="settings-tab" data-tab="social" onclick="settingsPanel.switchTab('social')">
              <span class="settings-tab-icon">📱</span>
              <span class="settings-tab-text">Sosyal</span>
            </button>
            <button class="settings-tab" data-tab="mealcards" onclick="settingsPanel.switchTab('mealcards')">
              <span class="settings-tab-icon">💳</span>
              <span class="settings-tab-text">Yemek Çeki</span>
            </button>
            <button class="settings-tab" data-tab="credits" onclick="settingsPanel.switchTab('credits')">
              <span class="settings-tab-icon">💰</span>
              <span class="settings-tab-text">Kredi</span>
            </button>
            <button class="settings-tab" data-tab="templates" onclick="settingsPanel.switchTab('templates')">
              <span class="settings-tab-icon">📄</span>
              <span class="settings-tab-text">Şablonlar</span>
            </button>
            <button class="settings-tab" data-tab="brochures" onclick="settingsPanel.switchTab('brochures')">
              <span class="settings-tab-icon">📚</span>
              <span class="settings-tab-text">Broşürler</span>
            </button>
            <button class="settings-tab" data-tab="theme" onclick="settingsPanel.switchTab('theme')">
              <span class="settings-tab-icon">🎨</span>
              <span class="settings-tab-text">Tema</span>
            </button>
          </div>
          
          <!-- Tab Contents -->
          <div class="settings-content">
            <!-- Company Tab -->
            <div class="settings-section active" id="tab-company">
              <h3>Firma Bilgileri</h3>
              <div class="settings-row">
                <div class="settings-group">
                  <label>Firma Adı</label>
                  <input type="text" class="glass-input" id="setting-company-name" placeholder="Firma adınız">
                </div>
                <div class="settings-group">
                  <label>Sektör</label>
                  <select class="glass-input" id="setting-sector">
                    <option value="supermarket">Süpermarket</option>
                    <option value="giyim">Giyim</option>
                    <option value="teknoloji">Teknoloji & Elektronik</option>
                    <option value="kozmetik">Kozmetik & Bakım</option>
                    <option value="evyasam">Ev & Yaşam</option>
                    <option value="elsanatlari">El Yapımı & El Sanatları</option>
                    <option value="restoran">Restoran & Kafe</option>
                    <option value="diger">Diğer</option>
                  </select>
                </div>
              </div>
              <div class="settings-row">
                <div class="settings-group">
                  <label>Telefon</label>
                  <input type="tel" class="glass-input" id="setting-phone" placeholder="0555 555 55 55">
                </div>
                <div class="settings-group">
                  <label>Adres</label>
                  <input type="text" class="glass-input" id="setting-address" placeholder="İşletme adresi">
                </div>
              </div>
              <div class="settings-group">
                <label>Slogan</label>
                <input type="text" class="glass-input" id="setting-slogan" placeholder="Firma sloganınız">
              </div>
            </div>
            
            <!-- Logo Tab -->
            <div class="settings-section" id="tab-logo">
              <h3>Logo Ayarları</h3>
              <div class="settings-group">
                <label>Firma Logosu</label>
                <div class="logo-upload-area">
                  <div class="logo-preview" id="logo-preview">
                    <span>Logo Yükle</span>
                  </div>
                  <input type="file" id="logo-upload" accept="image/*" style="display: none;" onchange="settingsPanel.handleLogoUpload(event)">
                  <button class="glass-btn" onclick="document.getElementById('logo-upload').click()">
                    📁 Logo Seç
                  </button>
                </div>
              </div>
              <div class="settings-row">
                <div class="settings-group">
                  <label>Logo Konumu</label>
                  <select class="glass-input" id="setting-logo-position">
                    <option value="top-left">Sol Üst</option>
                    <option value="top-right">Sağ Üst</option>
                    <option value="bottom-left">Sol Alt</option>
                    <option value="bottom-right">Sağ Alt</option>
                  </select>
                </div>
                <div class="settings-group">
                  <label>Logo Boyutu</label>
                  <input type="range" class="glass-input" id="setting-logo-size" min="50" max="200" value="100">
                  <span id="logo-size-value">100px</span>
                </div>
              </div>
            </div>
            
            <!-- Social Tab -->
            <div class="settings-section" id="tab-social">
              <h3>Sosyal Medya</h3>
              <div class="settings-group">
                <label>📸 Instagram</label>
                <input type="text" class="glass-input" id="setting-instagram" placeholder="@kullaniciadi">
              </div>
              <div class="settings-group">
                <label>📘 Facebook</label>
                <input type="text" class="glass-input" id="setting-facebook" placeholder="facebook.com/sayfa">
              </div>
              <div class="settings-group">
                <label>🐦 Twitter/X</label>
                <input type="text" class="glass-input" id="setting-twitter" placeholder="@kullaniciadi">
              </div>
              <div class="settings-group">
                <label>📺 YouTube</label>
                <input type="text" class="glass-input" id="setting-youtube" placeholder="youtube.com/kanal">
              </div>
              <div class="settings-group">
                <label>🌐 Website</label>
                <input type="text" class="glass-input" id="setting-website" placeholder="www.siteadresi.com">
              </div>
            </div>
            
            <!-- Meal Cards Tab -->
            <div class="settings-section" id="tab-mealcards">
              <h3>Yemek Kartı Anlaşmaları</h3>
              <p style="margin-bottom: 20px; color: var(--text); font-size: 14px;">
                Kabul ettiğiniz yemek kartlarını seçin. Seçilenler broşürde otomatik görünecek.
              </p>
              <div class="meal-cards-grid">
                <label class="meal-card-option">
                  <input type="checkbox" id="mc-sodexo" onchange="settingsPanel.updateMealCards()">
                  <span class="meal-card-label">🔵 Sodexo</span>
                </label>
                <label class="meal-card-option">
                  <input type="checkbox" id="mc-multinet" onchange="settingsPanel.updateMealCards()">
                  <span class="meal-card-label">🟢 Multinet</span>
                </label>
                <label class="meal-card-option">
                  <input type="checkbox" id="mc-setcard" onchange="settingsPanel.updateMealCards()">
                  <span class="meal-card-label">🟡 Setcard</span>
                </label>
                <label class="meal-card-option">
                  <input type="checkbox" id="mc-ticket" onchange="settingsPanel.updateMealCards()">
                  <span class="meal-card-label">🔴 Ticket</span>
                </label>
                <label class="meal-card-option">
                  <input type="checkbox" id="mc-metropol" onchange="settingsPanel.updateMealCards()">
                  <span class="meal-card-label">🟣 Metropol</span>
                </label>
              </div>
            </div>
            
            <!-- Credits Tab -->
            <div class="settings-section" id="tab-credits">
              <h3>Kredi Bilgisi</h3>
              <div class="credit-display glass-card">
                <div class="credit-icon">💎</div>
                <div class="credit-info">
                  <span class="credit-amount" id="credit-amount">0</span>
                  <span class="credit-label">Kredi</span>
                </div>
              </div>
              <div class="credit-usage">
                <h4>Kredi Kullanımı</h4>
                <ul>
                  <li>📄 PDF Çıktı: <strong>5 kredi</strong></li>
                  <li>🖼️ PNG/JPEG Çıktı: <strong>3 kredi</strong></li>
                  <li>🤖 AI Slogan: <strong>2 kredi</strong></li>
                  <li>🎨 AI Tema: <strong>3 kredi</strong></li>
                  <li>📦 Şablon Kaydet: <strong>1 kredi</strong></li>
                </ul>
              </div>
              <button class="glass-btn glass-btn-primary" onclick="settingsPanel.openCreditPurchase()" style="width: 100%; margin-top: 20px;">
                💳 Kredi Satın Al
              </button>
            </div>
            
            <!-- Templates Tab -->
            <div class="settings-section" id="tab-templates">
              <h3>Şablonlarım</h3>
              <div class="templates-grid" id="templates-grid">
                <div class="template-placeholder">
                  <span>Henüz kayıtlı şablon yok</span>
                </div>
              </div>
            </div>
            
            <!-- Brochures Tab -->
            <div class="settings-section" id="tab-brochures">
              <h3>Broşürlerim</h3>
              <div class="brochures-list" id="brochures-list">
                <div class="brochure-placeholder">
                  <span>Henüz kayıtlı broşür yok</span>
                </div>
              </div>
            </div>
            
            <!-- Theme Tab -->
            <div class="settings-section" id="tab-theme">
              <h3>Tema Ayarları</h3>
              <div class="settings-group">
                <label>Tema Modu</label>
                <div class="theme-toggle">
                  <button class="theme-toggle-btn active" id="theme-light" onclick="settingsPanel.setTheme('light')">☀️</button>
                  <button class="theme-toggle-btn" id="theme-dark" onclick="settingsPanel.setTheme('dark')">🌙</button>
                </div>
              </div>
              <div class="settings-group">
                <label>Dil</label>
                <select class="glass-input" id="setting-language">
                  <option value="tr">🇹🇷 Türkçe</option>
                  <option value="en">🇬🇧 English</option>
                </select>
              </div>
            </div>
          </div>
        </div>
        
        <div class="settings-footer" style="padding: 20px 30px; border-top: 1px solid var(--glass-border); display: flex; justify-content: flex-end; gap: 12px;">
          <button class="glass-btn" onclick="settingsPanel.close()">İptal</button>
          <button class="glass-btn glass-btn-primary" onclick="settingsPanel.save()">💾 Kaydet</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add custom styles for settings-specific elements
    const style = document.createElement('style');
    style.textContent = `
      .logo-upload-area {
        display: flex;
        align-items: center;
        gap: 20px;
      }
      
      .logo-preview {
        width: 120px;
        height: 120px;
        border: 2px dashed var(--glass-border);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.03);
        overflow: hidden;
      }
      
      .logo-preview img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
      }
      
      .meal-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 12px;
      }
      
      .meal-card-option {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 10px;
        cursor: pointer;
        transition: all var(--transition-normal);
      }
      
      .meal-card-option:hover {
        background: var(--glass-primary-light);
      }
      
      .meal-card-option input:checked + .meal-card-label {
        font-weight: 700;
        color: var(--primary);
      }
      
      .credit-display {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 30px;
        margin-bottom: 20px;
      }
      
      .credit-icon {
        font-size: 48px;
      }
      
      .credit-amount {
        font-size: 48px;
        font-weight: 700;
        color: var(--primary);
        display: block;
      }
      
      .credit-label {
        font-size: 16px;
        color: var(--text);
      }
      
      .credit-usage {
        padding: 20px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 12px;
      }
      
      .credit-usage h4 {
        margin-bottom: 12px;
        color: var(--dark);
      }
      
      .credit-usage ul {
        list-style: none;
      }
      
      .credit-usage li {
        padding: 8px 0;
        border-bottom: 1px solid var(--glass-border);
        display: flex;
        justify-content: space-between;
      }
      
      .templates-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
      }
      
      .template-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 12px;
        cursor: pointer;
        transition: all var(--transition-normal);
      }
      
      .template-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      }
      
      .template-card img {
        width: 100%;
        height: 120px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
      }
      
      .template-placeholder, .brochure-placeholder {
        padding: 40px;
        text-align: center;
        color: var(--text);
        opacity: 0.6;
      }
      
      .brochures-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .brochure-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 12px;
        transition: all var(--transition-normal);
      }
      
      .brochure-item:hover {
        background: var(--glass-primary-light);
      }
      
      .brochure-item-info {
        flex: 1;
      }
      
      .brochure-item-title {
        font-weight: 600;
        color: var(--dark);
      }
      
      .brochure-item-date {
        font-size: 12px;
        color: var(--text);
      }
    `;
    document.head.appendChild(style);
  }
  
  bindEvents() {
    // Logo size slider
    const logoSize = document.getElementById('setting-logo-size');
    if (logoSize) {
      logoSize.addEventListener('input', (e) => {
        document.getElementById('logo-size-value').textContent = e.target.value + 'px';
      });
    }
    
    // Close on outside click
    const modal = document.getElementById('settings-modal');
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        this.close();
      }
    });
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }
  
  // ============= PANEL CONTROL =============
  
  open() {
    this.isOpen = true;
    document.getElementById('settings-modal').classList.add('active');
    this.loadSettings();
  }
  
  close() {
    this.isOpen = false;
    document.getElementById('settings-modal').classList.remove('active');
  }
  
  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  // ============= TAB MANAGEMENT =============
  
  switchTab(tabName) {
    this.currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.settings-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update content sections
    document.querySelectorAll('.settings-section').forEach(section => {
      section.classList.toggle('active', section.id === `tab-${tabName}`);
    });
  }
  
  // ============= SETTINGS LOAD/SAVE =============
  
  async loadSettings() {
    try {
      const response = await fetch('/api/get_settings');
      const data = await response.json();
      
      if (data.success) {
        this.settings = data.settings || {};
        this.populateForm();
      }
    } catch (error) {
      console.error('Settings load error:', error);
    }
    
    // Load templates
    this.loadTemplates();
    
    // Load brochures
    this.loadBrochures();
    
    // Load credits
    this.loadCredits();
  }
  
  populateForm() {
    const s = this.settings;
    
    // Company
    if (s.company_name) document.getElementById('setting-company-name').value = s.company_name;
    if (s.sector) document.getElementById('setting-sector').value = s.sector;
    if (s.phone) document.getElementById('setting-phone').value = s.phone;
    if (s.address) document.getElementById('setting-address').value = s.address;
    if (s.slogan) document.getElementById('setting-slogan').value = s.slogan;
    
    // Logo
    if (s.logo_url) {
      const preview = document.getElementById('logo-preview');
      preview.innerHTML = `<img src="${s.logo_url}" alt="Logo">`;
    }
    if (s.logo_position) document.getElementById('setting-logo-position').value = s.logo_position;
    if (s.logo_size) {
      document.getElementById('setting-logo-size').value = s.logo_size;
      document.getElementById('logo-size-value').textContent = s.logo_size + 'px';
    }
    
    // Social
    if (s.instagram) document.getElementById('setting-instagram').value = s.instagram;
    if (s.facebook) document.getElementById('setting-facebook').value = s.facebook;
    if (s.twitter) document.getElementById('setting-twitter').value = s.twitter;
    if (s.youtube) document.getElementById('setting-youtube').value = s.youtube;
    if (s.website) document.getElementById('setting-website').value = s.website;
    
    // Meal cards
    if (s.meal_cards) {
      s.meal_cards.forEach(card => {
        const checkbox = document.getElementById(`mc-${card}`);
        if (checkbox) checkbox.checked = true;
      });
    }
    
    // Theme
    if (s.theme === 'dark') {
      document.getElementById('theme-dark').classList.add('active');
      document.getElementById('theme-light').classList.remove('active');
    }
    
    if (s.language) document.getElementById('setting-language').value = s.language;
  }
  
  async save() {
    const settings = {
      // Company
      company_name: document.getElementById('setting-company-name').value,
      sector: document.getElementById('setting-sector').value,
      phone: document.getElementById('setting-phone').value,
      address: document.getElementById('setting-address').value,
      slogan: document.getElementById('setting-slogan').value,
      
      // Logo
      logo_position: document.getElementById('setting-logo-position').value,
      logo_size: parseInt(document.getElementById('setting-logo-size').value),
      
      // Social
      instagram: document.getElementById('setting-instagram').value,
      facebook: document.getElementById('setting-facebook').value,
      twitter: document.getElementById('setting-twitter').value,
      youtube: document.getElementById('setting-youtube').value,
      website: document.getElementById('setting-website').value,
      
      // Meal cards
      meal_cards: this.getSelectedMealCards(),
      
      // Theme
      theme: document.getElementById('theme-dark').classList.contains('active') ? 'dark' : 'light',
      language: document.getElementById('setting-language').value
    };
    
    try {
      const response = await fetch('/api/save_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.settings = settings;
        
        // Save company info to localStorage for quick access
        const companyInfo = {
          name: settings.company_name,
          phone: settings.phone,
          address: settings.address,
          slogan: settings.slogan,
          logo: this.settings.logo_url,
          instagram: settings.instagram,
          facebook: settings.facebook,
          twitter: settings.twitter,
          youtube: settings.youtube,
          website: settings.website,
          mealCards: settings.meal_cards
        };
        localStorage.setItem('companyInfo', JSON.stringify(companyInfo));
        
        if (this.settings.logo_url) {
          localStorage.setItem('companyLogo', this.settings.logo_url);
        }
        
        this.close();
        
        // Show success notification
        if (window.showNotification) {
          window.showNotification('✅ Ayarlar kaydedildi!', 'success');
        }
      } else {
        alert('Ayarlar kaydedilemedi: ' + (data.error || 'Bilinmeyen hata'));
      }
    } catch (error) {
      console.error('Settings save error:', error);
      alert('Ayarlar kaydedilirken hata oluştu');
    }
  }
  
  // ============= HELPERS =============
  
  handleLogoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById('logo-preview');
      preview.innerHTML = `<img src="${e.target.result}" alt="Logo">`;
      
      // Upload to server
      this.uploadLogo(file);
    };
    reader.readAsDataURL(file);
  }
  
  async uploadLogo(file) {
    const formData = new FormData();
    formData.append('logo', file);
    
    try {
      const response = await fetch('/api/upload-logo', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.settings.logo_url = data.logo_url;
        
        // Save to localStorage for wizard and other components
        localStorage.setItem('companyLogo', data.logo_url);
        
        // Update wizard if open
        const wizardLogo = document.querySelector('.wizard-logo, .wizard-logo-initials');
        if (wizardLogo) {
          wizardLogo.outerHTML = `<img src="${data.logo_url}" alt="Logo" class="wizard-logo">`;
        }
        
        if (window.showNotification) {
          window.showNotification('✅ Logo başarıyla yüklendi!', 'success');
        }
      } else {
        alert('Logo yüklenemedi: ' + (data.error || 'Bilinmeyen hata'));
      }
    } catch (error) {
      console.error('Logo upload error:', error);
      alert('Logo yüklenirken hata oluştu');
    }
  }
  
  getSelectedMealCards() {
    const cards = [];
    ['sodexo', 'multinet', 'setcard', 'ticket', 'metropol'].forEach(card => {
      if (document.getElementById(`mc-${card}`).checked) {
        cards.push(card);
      }
    });
    return cards;
  }
  
  updateMealCards() {
    this.settings.meal_cards = this.getSelectedMealCards();
  }
  
  setTheme(theme) {
    document.getElementById('theme-light').classList.toggle('active', theme === 'light');
    document.getElementById('theme-dark').classList.toggle('active', theme === 'dark');
    
    // Apply theme
    document.documentElement.setAttribute('data-theme', theme);
  }
  
  async loadTemplates() {
    try {
      const response = await fetch('/api/brochure/templates');
      const data = await response.json();
      
      if (data.success && data.templates.length > 0) {
        const grid = document.getElementById('templates-grid');
        grid.innerHTML = data.templates.map(t => `
          <div class="template-card" onclick="settingsPanel.loadTemplate('${t.id}')">
            <img src="${t.preview_url || '/static/images/template-placeholder.png'}" alt="${t.name}">
            <div class="template-name">${t.name}</div>
          </div>
        `).join('');
      }
    } catch (error) {
      console.error('Templates load error:', error);
    }
  }
  
  async loadBrochures() {
    try {
      const response = await fetch('/api/brochure/list');
      const data = await response.json();
      
      if (data.success && data.brochures.length > 0) {
        const list = document.getElementById('brochures-list');
        list.innerHTML = data.brochures.map(b => `
          <div class="brochure-item" onclick="settingsPanel.openBrochure('${b.id}')">
            <span>📄</span>
            <div class="brochure-item-info">
              <div class="brochure-item-title">${b.name}</div>
              <div class="brochure-item-date">${new Date(b.updated_at).toLocaleDateString('tr-TR')}</div>
            </div>
            <button class="glass-btn" onclick="event.stopPropagation(); settingsPanel.deleteBrochure('${b.id}')">🗑️</button>
          </div>
        `).join('');
      }
    } catch (error) {
      console.error('Brochures load error:', error);
    }
  }
  
  async loadCredits() {
    try {
      const response = await fetch('/api/user/credits');
      const data = await response.json();
      
      if (data.success) {
        document.getElementById('credit-amount').textContent = data.credits || 0;
      }
    } catch (error) {
      console.error('Credits load error:', error);
    }
  }
  
  loadTemplate(templateId) {
    if (window.editor && typeof window.editor.loadTemplate === 'function') {
      window.editor.loadTemplate(templateId);
      this.close();
    }
  }
  
  openBrochure(brochureId) {
    if (window.editor && typeof window.editor.loadBrochure === 'function') {
      window.editor.loadBrochure(brochureId);
      this.close();
    }
  }
  
  async deleteBrochure(brochureId) {
    if (!confirm('Bu broşürü silmek istediğinize emin misiniz?')) return;
    
    try {
      const response = await fetch(`/api/brochure/${brochureId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.loadBrochures();
      }
    } catch (error) {
      console.error('Brochure delete error:', error);
    }
  }
  
  openCreditPurchase() {
    // TODO: Open credit purchase modal
    alert('Ödeme sistemi yakında aktif olacak!');
  }
}

// Initialize Settings Panel
let settingsPanel = null;

document.addEventListener('DOMContentLoaded', () => {
  settingsPanel = new SettingsPanel();
  window.settingsPanel = settingsPanel;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SettingsPanel;
}

