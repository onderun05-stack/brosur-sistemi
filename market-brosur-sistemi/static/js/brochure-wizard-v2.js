/*********************************************************
 * AEU Broşür Sihirbazı + Mini Stüdyo (Fabric.js 5.3.0)
 *********************************************************/

// GLOBAL: Fabric canvas - step 3'te başlatılacak
let fabricCanvas = null;

// --- STATE ---

const brochureWizardState = {
    step: 1,
    mode: null,              // 'manual' | 'auto'
    allProducts: [],         // Tüm ürünler (30 vs)
    perPageLimit: 12,        // Sayfa başı max ürün (auto kullanılabilir)
    currentPageIndex: 0,
    pages: [],               // [{ products: [id...], layout: 'grid', aiLayout: false }, ...]
    tempSelection: new Set(),// aktif sayfa için seçilen ürün id'leri
    zoom: 1
};

// Dışarıdan çağıracağın giriş fonksiyonu
function initBrochureWizard(products, options = {}) {
    brochureWizardState.allProducts = products || [];
    brochureWizardState.perPageLimit = options.perPageLimit || 12;
    brochureWizardState.step = 1;
    brochureWizardState.mode = null;
    brochureWizardState.pages = [];
    brochureWizardState.currentPageIndex = 0;
    brochureWizardState.tempSelection = new Set();

    const root = document.getElementById('brochure-wizard-root');
    if (!root) {
        console.error('brochure-wizard-root bulunamadı');
        return;
    }
    renderBrochureWizard(root);
}

// --- RENDER ROOT ---

function renderBrochureWizard(root) {
    const s = brochureWizardState;
    console.log('🎨 Wizard rendering to:', root.id, '| Step:', s.step, '| Products:', s.allProducts.length);
    
    root.innerHTML = `
        <div class="bw-container" style="min-height: 400px; border: 2px solid #8b5cf6;">
            <div class="bw-steps">
                <div class="bw-step ${s.step===1?'active':''}">1. Mod Seç</div>
                <div class="bw-step ${s.step===2?'active':''}">2. Ürün Seç</div>
                <div class="bw-step ${s.step===3?'active':''}">3. Sayfa Tasarım</div>
                <div class="bw-step ${s.step===4?'active':''}">4. Önizleme & Çıktı</div>
            </div>
            ${renderWizardStep()}
        </div>
    `;
}

// --- STEP SWITCH ---

function renderWizardStep() {
    const s = brochureWizardState;
    if (s.step === 1) return renderStep1ModeSelect();
    if (s.step === 2) return renderStep2ProductSelect();
    if (s.step === 3) return renderStep3Studio();
    if (s.step === 4) return renderStep4Preview();
    return '';
}

/*********************
 * STEP 1 – Mod Seç
 *********************/
function renderStep1ModeSelect() {
    const total = brochureWizardState.allProducts.length;
    return `
        <div class="bw-main">
            <div class="bw-panel">
                <h3>Broşürü kim hazırlasın?</h3>
                <p style="font-size:12px; opacity:.8; margin-bottom:10px;">
                    Sistemde <strong>${total}</strong> ürün var. İster sen tasarla, ister AEU AI yerleşimi yapsın.
                </p>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <button class="bw-btn bw-btn-primary" onclick="bwSetMode('auto')">
                        🤖 AEU AI Otomatik Tasarlasın
                    </button>
                    <button class="bw-btn bw-btn-ghost" onclick="bwSetMode('manual')">
                        ✋ Ben tasarlayacağım (sürükle-bırak stüdyo)
                    </button>
                </div>
            </div>
            <div class="bw-panel">
                <h3>Akış Özeti</h3>
                <ul style="font-size:11px; opacity:.9; padding-left:16px;">
                    <li>Ürünleri sayfa sayfa seçeceksin</li>
                    <li>İstersen AI otomatik sayfa tasarımı yapacak</li>
                    <li>Sayfayı Fabric.js stüdyoda sürükle-bırak düzenleyeceksin</li>
                    <li>Sonunda PDF / PNG alacaksın</li>
                </ul>
            </div>
        </div>
    `;
}

function bwSetMode(mode) {
    brochureWizardState.mode = mode;
    brochureWizardState.step = 2;
    brochureWizardState.currentPageIndex = 0;
    brochureWizardState.tempSelection = new Set();
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
}

/*************************
 * STEP 2 – Ürün Seçimi
 *************************/
function renderStep2ProductSelect() {
    const s = brochureWizardState;
    const products = s.allProducts;
    const selectedCount = s.tempSelection.size;
    const limit = s.perPageLimit;

    return `
        <div class="bw-main">
            <div class="bw-panel">
                <h3>Sayfa ${s.pages.length + 1} için ürün seç</h3>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; margin-bottom:6px;">
                    <div>Toplam ürün: <strong>${products.length}</strong></div>
                    <div>Bu sayfa: <strong>${selectedCount}/${limit}</strong></div>
                </div>
                <div class="bw-product-grid">
                    ${products.map(p => renderProductCard(p)).join('')}
                </div>
            </div>
            <div class="bw-panel">
                <h3>İpucu & Hızlı Ayar</h3>
                <p style="font-size:11px; opacity:.85;">
                    Sayfa başına ideal ürün sayısı: 8–12 arası. <br/>
                    Son sayfada 2–3 ürün kalmasın diye AI arkada sana dağıtım önerecek.
                </p>
                <div style="margin-top:8px; display:flex; gap:6px; flex-wrap:wrap;">
                    <button class="bw-btn bw-btn-ghost" onclick="bwQuickSelect(8)">8 ürün seç</button>
                    <button class="bw-btn bw-btn-ghost" onclick="bwQuickSelect(10)">10 ürün seç</button>
                    <button class="bw-btn bw-btn-ghost" onclick="bwQuickSelect(${s.perPageLimit})">Maks (${s.perPageLimit})</button>
                </div>
                <div style="height:1px; background:rgba(148,163,184,0.4); margin:10px 0;"></div>
                <p style="font-size:11px; opacity:.8;">
                    Ürünün üzerine geldiğinde küçük büyütme, tıklayınca 4K önizleme ekleyebilirsin (şu an kod tarafında hazır hook var).
                </p>
            </div>
        </div>
        <div class="bw-footer">
            <div>
                <button class="bw-btn bw-btn-ghost" onclick="bwPrevStep()" ${brochureWizardState.step===1?'disabled':''}>← Geri</button>
            </div>
            <div style="display:flex; gap:6px;">
                <button class="bw-btn bw-btn-ghost" onclick="bwClearSelection()">Seçimi temizle</button>
                <button class="bw-btn bw-btn-primary" onclick="bwConfirmPageSelection()" ${selectedCount===0?'disabled':''}>
                    Sayfayı oluştur →
                </button>
            </div>
        </div>
    `;
}

function renderProductCard(p) {
    const s = brochureWizardState;
    const selected = s.tempSelection.has(p.id);
    return `
        <div class="bw-product-card ${selected?'selected':''}" onclick="bwToggleProduct('${p.id}')">
            <img src="${p.image_url || '/static/placeholder.png'}" alt="">
            <div style="font-size:11px; margin-top:4px; max-height:30px; overflow:hidden;">${p.name}</div>
            <div style="font-size:11px; margin-top:2px; color:#22c55e; font-weight:600;">
                ${formatPriceTry(p.discount_price)}
            </div>
        </div>
    `;
}

function bwToggleProduct(id) {
    const set = brochureWizardState.tempSelection;
    if (set.has(id)) set.delete(id);
    else set.add(id);
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
}

function bwQuickSelect(n) {
    const s = brochureWizardState;
    s.tempSelection = new Set();
    s.allProducts.slice(0, n).forEach(p => s.tempSelection.add(p.id));
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
}

function bwClearSelection() {
    brochureWizardState.tempSelection = new Set();
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
}

function bwConfirmPageSelection() {
    const s = brochureWizardState;
    const ids = Array.from(s.tempSelection);
    s.pages.push({
        products: ids,
        layout: 'grid',
        aiLayout: (s.mode === 'auto')
    });
    s.tempSelection = new Set();
    s.currentPageIndex = s.pages.length - 1;
    s.step = 3;
    
    // Önce HTML'i render et, sonra canvas'ı başlat
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
    
    // DOM güncellendikten sonra canvas'ı başlat
    setTimeout(() => {
        bwRenderCurrentPageOnFabric();
    }, 100);
}

/*************************
 * STEP 3 – Stüdyo (Fabric)
 *************************/
function renderStep3Studio() {
    const s = brochureWizardState;
    const page = s.pages[s.currentPageIndex];
    const totalPages = s.pages.length;

    return `
        <div class="bw-main">
            <div class="bw-panel">
                <h3>Sayfa ${s.currentPageIndex+1} – Stüdyo</h3>
                <div class="studio-toolbar">
                    <div class="studio-toolbar-left">
                        <span class="studio-tag">Mod: ${s.mode==='auto'?'AI Otomatik':'Manuel'}</span>
                        <span class="studio-tag">Bu sayfa ürün: ${page.products.length}</span>
                        <span class="studio-tag">Toplam sayfa: ${totalPages}</span>
                    </div>
                    <div class="studio-toolbar-right">
                        <button class="studio-zoom-btn" onclick="bwZoomFabric(-0.1)">−</button>
                        <button class="studio-zoom-btn" onclick="bwZoomFabric(0.1)">+</button>
                        <button class="bw-btn bw-btn-ghost" style="padding:4px 8px;font-size:11px;" onclick="bwAiAutoLayoutCurrentPage()">
                            🤖 AI Diz
                        </button>
                    </div>
                </div>
                <div class="studio-canvas-frame">
                    <!-- Canvas zaten sayfanın altında duruyor, burada sadece görsel olarak çerçeveledik -->
                    <canvas id="brochure-canvas" width="595" height="842"></canvas>
                </div>
            </div>
            <div class="bw-panel">
                <h3>Sayfa Kontrol & Geçiş</h3>
                <p style="font-size:11px; opacity:.85;">
                    Ürünleri kanvas üzerinde sürükle-bırak yerleştirebilirsin. <br/>
                    Çift tık ile ürünün büyük önizlemesini açacak hook'ları da bağlayabilirsin.
                </p>
                <div style="margin:8px 0; display:flex; gap:6px; flex-wrap:wrap;">
                    ${brochureWizardState.pages.map((p, idx) => `
                        <button class="bw-btn ${idx===brochureWizardState.currentPageIndex?'bw-btn-primary':'bw-btn-ghost'}" 
                            style="padding:5px 9px;font-size:11px;"
                            onclick="bwGotoPage(${idx})">
                            Sayfa ${idx+1}
                        </button>
                    `).join('')}
                </div>
                <div style="height:1px; background:rgba(148,163,184,0.4); margin:8px 0;"></div>
                <button class="bw-btn bw-btn-ghost" onclick="bwAddNewPageFromRemaining()" style="width:100%; margin-bottom:6px;">
                    ➕ Yeni sayfa oluştur (kalan ürünlerden)
                </button>
                <button class="bw-btn bw-btn-primary" onclick="bwGoPreviewStep()" style="width:100%;">
                    ✔ Bu sayfa tamam → Önizleme
                </button>
            </div>
        </div>
        <div class="bw-footer">
            <div>
                <button class="bw-btn bw-btn-ghost" onclick="bwPrevStep()">← Geri</button>
            </div>
            <div></div>
        </div>
    `;
}

// Sayfadaki ürünleri Fabric canvas'a çiz
function bwRenderCurrentPageOnFabric() {
    if (!fabricCanvas && window.fabric) {
        fabricCanvas = new fabric.Canvas('brochure-canvas', {
            backgroundColor: '#ffffff',
            selection: true,
            preserveObjectStacking: true
        });
    }
    if (!fabricCanvas) return;

    const s = brochureWizardState;
    const page = s.pages[s.currentPageIndex];
    const products = s.allProducts.filter(p => page.products.includes(p.id));

    fabricCanvas.clear();
    fabricCanvas.setBackgroundColor('#ffffff', fabricCanvas.renderAll.bind(fabricCanvas));

    // basit grid yerleşimi (AI override edebilir)
    const cols = 3;
    const cellW = 180;
    const cellH = 240;
    const offsetX = 20;
    const offsetY = 20;

    products.forEach((p, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        const x = offsetX + col * cellW;
        const y = offsetY + row * cellH;
        bwAddProductCardToCanvas(p, x, y);
    });

    fabricCanvas.renderAll();
}

function bwAddProductCardToCanvas(product, left, top) {
    fabric.Image.fromURL(product.image_url || '/static/placeholder.png', function(img) {

        img.scaleToWidth(120);

        const nameText = new fabric.Textbox(product.name || '', {
            width: 140,
            fontSize: 13,
            fontWeight: 'bold',
            top: img.height * img.scaleY + 6,
            textAlign: 'center',
            fill: '#111827'
        });

        const oldPriceText = product.normal_price && product.normal_price > product.discount_price
            ? new fabric.Textbox(formatPriceTry(product.normal_price), {
                width: 140,
                fontSize: 11,
                textAlign: 'center',
                fill: '#9ca3af',
                top: img.height * img.scaleY + 24,
                linethrough: true
              })
            : null;

        const newPriceText = new fabric.Textbox(formatPriceTry(product.discount_price), {
            width: 140,
            fontSize: 18,
            fontWeight: 'bold',
            textAlign: 'center',
            fill: '#dc2626',
            top: img.height * img.scaleY + (oldPriceText ? 38 : 28)
        });

        const elements = [img, nameText];
        if (oldPriceText) elements.push(oldPriceText);
        elements.push(newPriceText);

        const group = new fabric.Group(elements, {
            left,
            top,
            selectable: true,
            hasControls: true,
            hasBorders: true,
            borderColor: '#6366f1',
            cornerColor: '#6366f1',
            cornerStyle: 'circle',
            padding: 8
        });

        // Çift tık büyük önizleme hook
        group.on('mousedblclick', () => {
            bwOpenBigPreview(product);
        });

        fabricCanvas.add(group);
    }, { crossOrigin: 'Anonymous' });
}

function bwZoomFabric(delta) {
    if (!fabricCanvas) return;
    brochureWizardState.zoom = Math.max(0.5, Math.min(1.5, brochureWizardState.zoom + delta));
    fabricCanvas.setZoom(brochureWizardState.zoom);
    fabricCanvas.setViewportTransform([brochureWizardState.zoom,0,0,brochureWizardState.zoom,0,0]);
}

function bwGotoPage(idx) {
    brochureWizardState.currentPageIndex = idx;
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
    setTimeout(() => bwRenderCurrentPageOnFabric(), 100);
}

function bwAddNewPageFromRemaining() {
    const s = brochureWizardState;
    const usedIds = new Set(s.pages.flatMap(p => p.products));
    const remaining = s.allProducts.filter(p => !usedIds.has(p.id));

    if (remaining.length === 0) {
        alert('Kalan ürün yok.');
        return;
    }

    const take = Math.min(s.perPageLimit, remaining.length);
    const ids = remaining.slice(0, take).map(p => p.id);

    s.pages.push({
        products: ids,
        layout: 'grid',
        aiLayout: (s.mode === 'auto')
    });
    s.currentPageIndex = s.pages.length - 1;
    s.step = 3;
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
    setTimeout(() => bwRenderCurrentPageOnFabric(), 100);
}

// AI dizilimi: OpenAI'den layout önerisi al ve uygula
async function bwAiAutoLayoutCurrentPage() {
    const s = brochureWizardState;
    const page = s.pages[s.currentPageIndex];
    const products = s.allProducts.filter(p => page.products.includes(p.id));
    
    if (products.length === 0) {
        alert('Bu sayfada ürün yok!');
        return;
    }
    
    // Loading göster
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ AI düşünüyor...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/wizard/ai-layout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                products: products.map(p => ({
                    id: p.id,
                    name: p.name,
                    price: p.discount_price,
                    hasImage: !!p.image_url
                })),
                canvasWidth: 595,
                canvasHeight: 842,
                mode: s.mode
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.layout) {
            // AI'dan gelen layout'u uygula
            bwApplyAiLayout(data.layout, products);
            console.log('✅ AI layout uygulandı:', data.layout);
            
            // Token bilgisi göster
            if (data.tokens_used) {
                console.log(`🤖 ${data.tokens_used} token kullanıldı ($${data.cost_usd})`);
            }
        } else {
            // Fallback: varsayılan grid
            bwRenderCurrentPageOnFabric();
            alert('AI önerisi alınamadı, varsayılan düzen uygulandı.');
        }
        
    } catch (error) {
        console.error('AI layout error:', error);
        bwRenderCurrentPageOnFabric();
        alert('Bağlantı hatası, varsayılan düzen uygulandı.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// AI'dan gelen layout'u canvas'a uygula
function bwApplyAiLayout(layout, products) {
    if (!fabricCanvas) return;
    
    fabricCanvas.clear();
    fabricCanvas.setBackgroundColor(layout.backgroundColor || '#ffffff', fabricCanvas.renderAll.bind(fabricCanvas));
    
    // Header ekle (AI önerisi varsa)
    if (layout.header) {
        const headerRect = new fabric.Rect({
            left: 0,
            top: 0,
            width: 595,
            height: layout.header.height || 80,
            fill: layout.header.color || '#e53935',
            selectable: false
        });
        fabricCanvas.add(headerRect);
        
        // Slogan
        if (layout.header.slogan) {
            const sloganText = new fabric.Text(layout.header.slogan, {
                left: 297.5,
                top: (layout.header.height || 80) / 2 - 14,
                fontSize: 28,
                fontWeight: 'bold',
                fill: '#ffffff',
                originX: 'center',
                fontFamily: 'Arial Black'
            });
            fabricCanvas.add(sloganText);
        }
    }
    
    // Ürünleri AI pozisyonlarına yerleştir
    if (layout.products && Array.isArray(layout.products)) {
        layout.products.forEach((pos, idx) => {
            const product = products.find(p => p.id === pos.id) || products[idx];
            if (product) {
                bwAddProductCardToCanvas(product, pos.x || 20, pos.y || 100);
            }
        });
    } else {
        // Fallback: grid
        products.forEach((p, idx) => {
            const col = idx % 3;
            const row = Math.floor(idx / 3);
            bwAddProductCardToCanvas(p, 20 + col * 180, 100 + row * 240);
        });
    }
    
    fabricCanvas.renderAll();
}

/*************************
 * STEP 4 – Önizleme + Magnifier
 *************************/
function renderStep4Preview() {
    const s = brochureWizardState;
    const totalPages = s.pages.length;

    // Canvas'ı image’a çevir (şimdilik tek sayfa – currentPageIndex)
    let dataUrl = '';
    try {
        if (fabricCanvas) {
            dataUrl = fabricCanvas.toDataURL({
                format: 'png',
                multiplier: 2
            });
        }
    } catch (e) {
        console.warn('Canvas toDataURL hata:', e);
    }

    return `
        <div class="bw-main">
            <div class="bw-panel">
                <h3>Son Önizleme</h3>
                <div class="magnifier-wrapper" id="magnifier-wrapper">
                    <img src="${dataUrl || '/static/placeholder_brochure.png'}" 
                         class="magnifier-target" id="magnifier-target">
                    <div class="magnifier-lens" id="magnifier-lens">
                        <img src="${dataUrl || '/static/placeholder_brochure.png'}" 
                             class="magnifier-lens-inner" id="magnifier-lens-inner">
                    </div>
                </div>
                <p style="font-size:11px; opacity:.85; margin-top:6px;">
                    Merceği görmek için görselin üzerine gel, detayları net gör. 
                    (Lens aktif js kodu aşağıda bağlı.)
                </p>
            </div>
            <div class="bw-panel">
                <h3>Çıktı & Kaydet</h3>
                <p style="font-size:11px; opacity:.85;">
                    Toplam sayfa: <strong>${totalPages}</strong> <br/>
                    Not: Çoklu sayfa için her sayfayı ayrı canvas’tan toplayıp PDF birleştirme adımı eklenebilir.
                </p>
                <button class="bw-btn bw-btn-primary" style="width:100%; margin-top:8px;" onclick="bwDownloadCurrentAsPng()">
                    📥 Bu sayfayı PNG indir
                </button>
                <button class="bw-btn bw-btn-ghost" style="width:100%; margin-top:6px;" onclick="bwFinishWizard()">
                    ✅ Sihirbazı bitir
                </button>
            </div>
        </div>
        <div class="bw-footer">
            <button class="bw-btn bw-btn-ghost" onclick="bwPrevStep()">← Geri</button>
            <div></div>
        </div>
    `;
}

// Magnifier bağla (step 4 render edildikten sonra çağır)
function bwInitMagnifier() {
    const wrapper = document.getElementById('magnifier-wrapper');
    const target = document.getElementById('magnifier-target');
    const lens = document.getElementById('magnifier-lens');
    const lensInner = document.getElementById('magnifier-lens-inner');
    if (!wrapper || !target || !lens || !lensInner) return;

    const zoom = 2; // büyütme oranı

    wrapper.addEventListener('mousemove', moveLens);
    wrapper.addEventListener('mouseleave', () => { lens.style.display = 'none'; });

    function moveLens(e) {
        const rect = wrapper.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        lens.style.display = 'block';
        const lensSize = lens.offsetWidth || 120;
        const lx = x - lensSize / 2;
        const ly = y - lensSize / 2;
        lens.style.left = lx + 'px';
        lens.style.top = ly + 'px';

        lensInner.style.width = target.offsetWidth * zoom + 'px';
        lensInner.style.height = target.offsetHeight * zoom + 'px';
        lensInner.style.transform = `scale(${zoom}) translate(${-x}px, ${-y}px)`;
    }
}

function bwDownloadCurrentAsPng() {
    if (!fabricCanvas) return;
    const dataUrl = fabricCanvas.toDataURL({
        format: 'png',
        multiplier: 2
    });

    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'aeu_brosur_sayfa.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function bwFinishWizard() {
    alert('Sihirbaz bitti. Buradan sonra istersen boş şablon kaydı, çoklu PDF vs. aşamalarını genişletebiliriz.');
}

/***********************
 * Genel yardımcılar
 ***********************/
function bwPrevStep() {
    brochureWizardState.step = Math.max(1, brochureWizardState.step - 1);
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
    
    if (brochureWizardState.step === 3) {
        setTimeout(() => bwRenderCurrentPageOnFabric(), 100);
    }
    if (brochureWizardState.step === 4) {
        setTimeout(bwInitMagnifier, 100);
    }
}

function bwGoPreviewStep() {
    brochureWizardState.step = 4;
    renderBrochureWizard(document.getElementById('brochure-wizard-root'));
    setTimeout(bwInitMagnifier, 50);
}

function formatPriceTry(p) {
    if (!p && p !== 0) return '0,00 ₺';
    const v = Number(p) || 0;
    return v.toFixed(2).replace('.', ',') + ' ₺';
}

// Büyük ürün önizleme (modal yerine şimdilik alert simülasyon, sen modal ile bağlayabilirsin)
function bwOpenBigPreview(product) {
    // Buraya kendi modal sistemini bağlayabilirsin
    console.log('Büyük önizleme:', product);
    alert(product.name + ' – büyük önizleme hook');
}

// İlk başlatmayı dışarı aç
window.initBrochureWizard = initBrochureWizard;
