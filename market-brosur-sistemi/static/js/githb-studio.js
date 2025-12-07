/**
 * Gıthb Test Studio - Gerçek Depo + AI Entegrasyonu
 * Yeni özellikler: caption, backgroundPrompt, logoPlacement, Analysis Modal, Style Picker
 */

// ============= GLOBAL STATE =============
let allProducts = [];
let masterTemplate = null;
let lastAnalysisResult = null;
let designStyles = [];
let selectedStyleId = null;

const studioState = {
  pages: [{ id: "page-1", objectsMeta: [], styleProfileId: null, backgroundColor: "#ffffff" }],
  currentPageIndex: 0,
  selectedObjectMeta: null
};

let fabricCanvas = null;

// ============= INITIALIZATION =============
window.addEventListener("DOMContentLoaded", () => {
  loadDepotProducts();
  loadDesignStyles();
  initCanvas();
  initPageButtons();
  initButtons();
  renderTemplatePreview();
});

// ============= TASARIM STİLLERİNİ YÜKLE =============
async function loadDesignStyles() {
  try {
    const response = await fetch('/static/templates/examples/styles.json');
    const data = await response.json();
    designStyles = data.styles || [];
    console.log('Tasarım stilleri yüklendi:', designStyles.length);
  } catch (error) {
    console.error('Stil yükleme hatası:', error);
    designStyles = [];
  }
}

// ============= DEPO ÜRÜNLERİNİ YÜKLE =============
async function loadDepotProducts() {
  const container = document.getElementById("product-list");
  const depotStatus = document.getElementById("depot-status");
  const productCount = document.getElementById("product-count");
  
  container.innerHTML = `
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <p>Depo ürünleri yükleniyor...</p>
    </div>
  `;
  
  try {
    let response = await fetch('/api/admin/all-products');
    let data = await response.json();
    
    if (data.success && data.products && data.products.length > 0) {
      allProducts = data.products.map(p => ({
        id: p.barcode || p.id,
        barcode: p.barcode,
        name: p.product_name || p.name || p.barcode,
        price: parseFloat(p.discount_price) || parseFloat(p.normal_price) || 0,
        oldPrice: parseFloat(p.normal_price) || 0,
        image_url: p.image_url || '/static/placeholder.png',
        product_group: p.product_group || 'Genel',
        sector: p.sector || 'supermarket',
        caption: getCaption(p)
      }));
      
      depotStatus.textContent = 'Admin Deposu';
      depotStatus.style.color = '#22c55e';
    } else {
      response = await fetch('/api/products');
      data = await response.json();
      
      if (data.success && data.products && data.products.length > 0) {
        allProducts = data.products.map(p => ({
          id: p.barcode || p.id,
          barcode: p.barcode,
          name: p.name || p.product_name || p.barcode,
          price: parseFloat(p.discount_price) || parseFloat(p.normal_price) || 0,
          oldPrice: parseFloat(p.normal_price) || 0,
          image_url: p.image_url || '/static/placeholder.png',
          product_group: p.product_group || 'Genel',
          sector: p.sector || 'supermarket',
          caption: getCaption(p)
        }));
        
        depotStatus.textContent = 'Müşteri Deposu';
        depotStatus.style.color = '#3b82f6';
      }
    }
    
    productCount.textContent = allProducts.length;
    renderProductList();
    
  } catch (error) {
    console.error('Depo yükleme hatası:', error);
    depotStatus.textContent = 'Hata!';
    depotStatus.style.color = '#ef4444';
    container.innerHTML = `
      <div class="loading-container" style="color:#ef4444;">
        <p>❌ Ürünler yüklenemedi</p>
        <p style="font-size:10px;margin-top:5px;">${error.message}</p>
      </div>
    `;
  }
}

// ============= CAPTION HESAPLA =============
function getCaption(product) {
  const normal = parseFloat(product.normal_price) || 0;
  const discount = parseFloat(product.discount_price) || 0;
  
  if (normal > 0 && discount > 0) {
    const percent = ((normal - discount) / normal) * 100;
    if (percent >= 30) return 'Süper Fırsat';
    if (percent >= 20) return 'İndirim';
    if (percent >= 10) return 'Kampanya';
  }
  
  const captions = ['Yeni', 'Popüler', 'Önerilen', 'Fırsat'];
  return captions[Math.floor(Math.random() * captions.length)];
}

// ============= ÜRÜN LİSTESİ RENDER =============
function renderProductList() {
  const container = document.getElementById("product-list");
  
  if (allProducts.length === 0) {
    container.innerHTML = `
      <div class="loading-container">
        <p>⚠️ Depoda ürün bulunamadı</p>
        <p style="font-size:10px;margin-top:5px;">Admin panelinden ürün ekleyin.</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = "";
  
  allProducts.forEach(p => {
    const div = document.createElement("div");
    div.className = "product-card";
    div.innerHTML = `
      <div class="row">
        <div class="product-thumb">
          <img src="${p.image_url}" alt="${p.name}" onerror="this.src='/static/placeholder.png'">
        </div>
        <div style="flex:1;min-width:0;">
          <div class="product-name">${p.name}</div>
          <div style="display:flex;gap:6px;align-items:center;margin-top:4px;">
            <span class="product-price">${formatPrice(p.price)}</span>
            ${p.oldPrice > p.price ? `<span class="product-old-price">${formatPrice(p.oldPrice)}</span>` : ''}
          </div>
          <div style="display:flex;gap:6px;align-items:center;margin-top:4px;">
            ${p.caption ? `<span class="product-caption">${p.caption}</span>` : ''}
            <span class="product-group">${p.product_group}</span>
          </div>
        </div>
      </div>
      <button class="btn btn-ghost" style="width:100%;font-size:11px;margin-top:4px;">Canvas'a ekle</button>
    `;
    div.querySelector("button").onclick = () => addProductToCanvas(p);
    container.appendChild(div);
  });
}

// ============= CANVAS BAŞLAT =============
function initCanvas() {
  fabricCanvas = new fabric.Canvas("brochure-canvas", {
    backgroundColor: "#ffffff",
    selection: true,
    preserveObjectStacking: true
  });
  fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));

  fabricCanvas.on("selection:created", updateSelectedObjectPanel);
  fabricCanvas.on("selection:updated", updateSelectedObjectPanel);
  fabricCanvas.on("selection:cleared", () => {
    studioState.selectedObjectMeta = null;
    renderSelectedProductPanel();
  });
}

// ============= SAYFA BUTONLARI =============
function initPageButtons() {
  const container = document.getElementById("page-buttons");
  container.innerHTML = "";
  
  studioState.pages.forEach((page, idx) => {
    const btn = document.createElement("button");
    btn.textContent = `Sayfa ${idx + 1}`;
    btn.className = idx === studioState.currentPageIndex ? 'active' : '';
    btn.onclick = () => switchPage(idx);
    container.appendChild(btn);
  });

  document.getElementById("btn-add-page").onclick = () => {
    studioState.pages.push({
      id: `page-${studioState.pages.length + 1}`,
      objectsMeta: [],
      styleProfileId: null,
      backgroundColor: "#ffffff"
    });
    studioState.currentPageIndex = studioState.pages.length - 1;
    initPageButtons();
    redrawCanvasFromState();
    showToast('Yeni sayfa eklendi', 'success');
  };
}

// ============= BUTON OLAYLARI =============
function initButtons() {
  document.getElementById("btn-ai-layout-page").onclick = () => callAiLayout({ scope: "page" });
  document.getElementById("btn-ai-layout-selection").onclick = () => callAiLayout({ scope: "selection" });
  document.getElementById("btn-ai-soften-bg").onclick = () => openStylePicker();
  
  document.getElementById("btn-clear-canvas").onclick = () => {
    if (confirm('Kanvastaki tüm öğeler silinecek. Devam edilsin mi?')) {
      fabricCanvas.clear();
      fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));
      getCurrentPage().objectsMeta = [];
      showToast('Kanvas temizlendi', 'success');
    }
  };

  document.getElementById("btn-download-png").onclick = () => {
    if (!fabricCanvas) return;
    const dataUrl = fabricCanvas.toDataURL({ format: "png", multiplier: 2 });
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `brosur_sayfa_${studioState.currentPageIndex + 1}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('PNG indirildi', 'success');
  };

  document.getElementById("btn-save-template").onclick = () => {
    masterTemplate = exportMasterTemplateFromCurrentPage();
    renderTemplatePreview();
    showToast('Bu sayfa ana tema olarak kaydedildi', 'success');
  };
}

// ============= ÜRÜNÜ CANVAS'A EKLE =============
function addProductToCanvas(product) {
  const page = getCurrentPage();
  const baseX = 60 + (page.objectsMeta.length % 4) * 150;
  const baseY = 100 + Math.floor(page.objectsMeta.length / 4) * 220;

  fabric.Image.fromURL(product.image_url || "/static/placeholder.png", img => {
    img.scaleToWidth(120);
    const h = img.getScaledHeight();

    img.set({ left: 10, top: 10, originX: "left", originY: "top", selectable: false });

    const nameText = new fabric.Textbox(product.name, {
      left: 10,
      top: 10 + h + 6,
      width: 140,
      fontSize: 11,
      fontWeight: "bold",
      textAlign: "center",
      fill: "#111827",
      selectable: false
    });
    
    const priceText = new fabric.Textbox(formatPrice(product.price), {
      left: 10,
      top: 10 + h + 26,
      width: 140,
      fontSize: 16,
      fontWeight: "bold",
      textAlign: "center",
      fill: "#dc2626",
      selectable: false
    });

    const group = new fabric.Group([img, nameText, priceText], {
      left: baseX,
      top: baseY,
      hasControls: true,
      borderColor: "#6366f1",
      cornerColor: "#6366f1",
      cornerStyle: "circle",
      padding: 6
    });

    group.productMeta = {
      productId: product.id,
      barcode: product.barcode,
      product_group: product.product_group,
      price: product.price,
      oldPrice: product.oldPrice,
      caption: product.caption,
      userEdited: false,
      lockScale: false,
      lockPosition: false
    };

    group.on("mousedblclick", () => {
      showToast(`${product.name} - Büyük önizleme`, 'success');
    });
    
    group.on("modified", () => {
      group.productMeta.userEdited = true;
      syncObjectsMetaFromCanvas();
    });

    fabricCanvas.add(group);
    fabricCanvas.setActiveObject(group);
    fabricCanvas.renderAll();
    syncObjectsMetaFromCanvas();
    
    showToast(`${product.name} eklendi`, 'success');
  }, { crossOrigin: "Anonymous" });
}

// ============= STATE <-> CANVAS =============
function getCurrentPage() {
  return studioState.pages[studioState.currentPageIndex];
}

function switchPage(idx) {
  studioState.currentPageIndex = idx;
  initPageButtons();
  redrawCanvasFromState();
}

function syncObjectsMetaFromCanvas() {
  const page = getCurrentPage();
  page.objectsMeta = [];
  fabricCanvas.getObjects().forEach(obj => {
    if (!obj.productMeta) return;
    page.objectsMeta.push({
      productId: obj.productMeta.productId,
      barcode: obj.productMeta.barcode,
      product_group: obj.productMeta.product_group,
      caption: obj.productMeta.caption,
      left: obj.left,
      top: obj.top,
      scaleX: obj.scaleX,
      scaleY: obj.scaleY,
      userEdited: obj.productMeta.userEdited,
      lockScale: obj.productMeta.lockScale,
      lockPosition: obj.productMeta.lockPosition
    });
  });
}

function redrawCanvasFromState() {
  fabricCanvas.clear();
  const page = getCurrentPage();
  const bgColor = page.backgroundColor || "#ffffff";
  fabricCanvas.setBackgroundColor(bgColor, fabricCanvas.renderAll.bind(fabricCanvas));
  
  page.objectsMeta.forEach(meta => {
    const product = allProducts.find(p => p.id === meta.productId);
    if (!product) return;
    
    fabric.Image.fromURL(product.image_url || "/static/placeholder.png", img => {
      img.scaleToWidth(120 * (meta.scaleX || 1));
      const h = img.getScaledHeight();
      img.set({ left: 10, top: 10, originX: "left", originY: "top", selectable: false });
      
      const nameText = new fabric.Textbox(product.name, {
        left: 10,
        top: 10 + h + 6,
        width: 140,
        fontSize: 11,
        fontWeight: "bold",
        textAlign: "center",
        fill: "#111827",
        selectable: false
      });
      
      const priceText = new fabric.Textbox(formatPrice(product.price), {
        left: 10,
        top: 10 + h + 26,
        width: 140,
        fontSize: 16,
        fontWeight: "bold",
        textAlign: "center",
        fill: "#dc2626",
        selectable: false
      });
      
      const group = new fabric.Group([img, nameText, priceText], {
        left: meta.left,
        top: meta.top,
        scaleX: meta.scaleX || 1,
        scaleY: meta.scaleY || 1,
        hasControls: true,
        borderColor: "#6366f1",
        cornerColor: "#6366f1",
        cornerStyle: "circle",
        padding: 6
      });
      
      group.productMeta = { ...meta };
      group.on("modified", () => {
        group.productMeta.userEdited = true;
        syncObjectsMetaFromCanvas();
      });
      
      fabricCanvas.add(group);
      fabricCanvas.renderAll();
    }, { crossOrigin: "Anonymous" });
  });
}

// ============= STİL SEÇİCİ MODAL =============
function openStylePicker() {
  selectedStyleId = null;
  renderStyleGrid();
  document.getElementById('style-picker-modal').classList.remove('hidden');
  document.getElementById('btn-apply-style').disabled = true;
}

function closeStylePicker() {
  document.getElementById('style-picker-modal').classList.add('hidden');
}

function renderStyleGrid() {
  const grid = document.getElementById('style-grid');
  
  if (designStyles.length === 0) {
    grid.innerHTML = `<p style="color:var(--muted);text-align:center;grid-column:1/-1;">Tasarım stilleri yüklenemedi.</p>`;
    return;
  }
  
  grid.innerHTML = designStyles.map(style => `
    <div class="style-card" data-style-id="${style.id}" onclick="selectStyle('${style.id}')">
      <div class="style-preview">
        <div class="style-preview-placeholder">
          <div class="style-preview-colors">
            <span style="background:${style.colors.primary}"></span>
            <span style="background:${style.colors.secondary}"></span>
            <span style="background:${style.colors.accent}"></span>
          </div>
          <span style="font-size:10px;">${style.layout === 'grid' ? '▦ Grid' : '◇ Serbest'}</span>
        </div>
      </div>
      <div class="style-name">${style.name}</div>
      <div class="style-desc">${style.description}</div>
      <div class="style-features">
        ${style.features.slice(0, 3).map(f => `<span class="style-feature">${f}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

function selectStyle(styleId) {
  selectedStyleId = styleId;
  
  document.querySelectorAll('.style-card').forEach(card => {
    card.classList.remove('selected');
  });
  
  const selectedCard = document.querySelector(`.style-card[data-style-id="${styleId}"]`);
  if (selectedCard) {
    selectedCard.classList.add('selected');
  }
  
  document.getElementById('btn-apply-style').disabled = false;
}

async function applySelectedStyle() {
  if (!selectedStyleId) {
    showToast('Önce bir stil seçin', 'error');
    return;
  }
  
  const style = designStyles.find(s => s.id === selectedStyleId);
  if (!style) {
    showToast('Stil bulunamadı', 'error');
    return;
  }
  
  closeStylePicker();
  showToast(`"${style.name}" stili için arka plan oluşturuluyor...`, 'success');
  
  try {
    const response = await fetch('/api/desinger/kie-background', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        purpose: style.id,
        backgroundPrompt: style.background_prompt,
        colors: style.colors
      })
    });
    
    const data = await response.json();
    
    if (data.success && data.image_url) {
      fabric.Image.fromURL(data.image_url, bgImg => {
        fabricCanvas.setBackgroundImage(bgImg, fabricCanvas.renderAll.bind(fabricCanvas), {
          scaleX: fabricCanvas.width / bgImg.width,
          scaleY: fabricCanvas.height / bgImg.height
        });
        
        const page = getCurrentPage();
        page.styleProfileId = style.id;
        
        showToast(`✅ "${style.name}" arka planı uygulandı!`, 'success');
      }, { crossOrigin: 'Anonymous' });
    } else {
      // Fallback: Basit renk arka planı
      applyFallbackBackground(style);
    }
  } catch (e) {
    console.error('Stil uygulama hatası:', e);
    applyFallbackBackground(style);
  }
}

function applyFallbackBackground(style) {
  if (!style) return;
  const bgColor = style.colors.background || '#ffffff';
  fabricCanvas.setBackgroundColor(bgColor, fabricCanvas.renderAll.bind(fabricCanvas));
  showToast(`⚠️ Düz renk arka plan uygulandı`, 'success');
}

// ============= AI LAYOUT (OpenAI) =============
async function callAiLayout({ scope }) {
  const page = getCurrentPage();
  syncObjectsMetaFromCanvas();

  if (page.objectsMeta.length === 0) {
    showToast('Önce kanvasa ürün ekleyin', 'error');
    return;
  }

  showToast('AI analiz yapıyor...', 'success');

  const productsForAi = page.objectsMeta.map(meta => {
    const product = allProducts.find(p => p.id === meta.productId);
    return {
      name: product ? product.name : meta.productId,
      normal_price: product ? product.oldPrice : 0,
      discount_price: product ? product.price : 0,
      product_group: meta.product_group || 'Genel',
      barcode: meta.barcode,
      caption: meta.caption
    };
  });

  const styleExamples = designStyles.map(s => ({
    id: s.id,
    name: s.name,
    description: s.description
  }));

  try {
    const response = await fetch('/api/desinger/layout-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        products: productsForAi, 
        scope,
        availableStyles: styleExamples
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      lastAnalysisResult = data;
      showAnalysisModal(data);
    } else {
      showToast(data.error || 'AI hatası', 'error');
    }
  } catch (e) {
    console.error('AI Layout hatası:', e);
    showToast('Sunucu hatası: ' + e.message, 'error');
  }
}

// ============= ANALİZ MODAL =============
function showAnalysisModal(data) {
  const modal = document.getElementById('analysis-modal');
  const body = document.getElementById('analysis-modal-body');
  
  const result = data.result || {};
  
  let layoutHtml = '';
  if (result.layout && result.layout.pages) {
    layoutHtml = result.layout.pages.map((page, idx) => `
      <div class="analysis-page">
        <span class="page-num">${idx + 1}</span>
        <div>
          <strong>${page.title || 'Sayfa ' + (idx + 1)}</strong>
          ${page.products ? `<div style="font-size:10px;color:#9ca3af;">${page.products.join(', ')}</div>` : ''}
        </div>
      </div>
    `).join('');
  }
  
  let colorsHtml = '';
  if (result.color_theme) {
    const theme = result.color_theme;
    colorsHtml = `
      <div class="analysis-colors">
        ${theme.primary ? `<div><div class="color-swatch" style="background:${theme.primary}"></div><div class="color-label">Ana</div></div>` : ''}
        ${theme.secondary ? `<div><div class="color-swatch" style="background:${theme.secondary}"></div><div class="color-label">İkincil</div></div>` : ''}
        ${theme.accent ? `<div><div class="color-swatch" style="background:${theme.accent}"></div><div class="color-label">Vurgu</div></div>` : ''}
      </div>
    `;
  }
  
  let styleHtml = '';
  if (result.recommended_style) {
    const recStyle = designStyles.find(s => s.id === result.recommended_style);
    if (recStyle) {
      styleHtml = `
        <div class="analysis-section">
          <h4>🎨 Önerilen Tasarım Stili</h4>
          <div style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--bg);border-radius:8px;">
            <div class="style-preview-colors">
              <span style="background:${recStyle.colors.primary};width:20px;height:20px;border-radius:4px;"></span>
              <span style="background:${recStyle.colors.secondary};width:20px;height:20px;border-radius:4px;"></span>
            </div>
            <div>
              <strong>${recStyle.name}</strong>
              <div style="font-size:10px;color:#9ca3af;">${recStyle.description}</div>
            </div>
          </div>
        </div>
      `;
    }
  }
  
  body.innerHTML = `
    ${result.greeting ? `<div class="analysis-greeting">${result.greeting}</div>` : ''}
    
    ${result.analysis ? `
      <div class="analysis-section">
        <h4>📊 Analiz</h4>
        <p style="font-size:13px;color:#e5e7eb;">${result.analysis}</p>
      </div>
    ` : ''}
    
    ${result.slogan ? `
      <div class="analysis-section">
        <h4>💡 Önerilen Slogan</h4>
        <div class="analysis-slogan">"${result.slogan}"</div>
      </div>
    ` : ''}
    
    ${styleHtml}
    
    ${layoutHtml ? `
      <div class="analysis-section">
        <h4>📑 Sayfa Düzeni</h4>
        <div class="analysis-layout">${layoutHtml}</div>
      </div>
    ` : ''}
    
    ${colorsHtml ? `
      <div class="analysis-section">
        <h4>🎨 Renk Teması</h4>
        ${colorsHtml}
      </div>
    ` : ''}
    
    ${result.suggestion ? `
      <div class="analysis-section">
        <h4>✨ Öneri</h4>
        <p style="font-size:13px;color:#e5e7eb;">${result.suggestion}</p>
      </div>
    ` : ''}
  `;
  
  modal.classList.remove('hidden');
}

function closeAnalysisModal() {
  document.getElementById('analysis-modal').classList.add('hidden');
}

async function applyAnalysisSuggestion() {
  if (!lastAnalysisResult || !lastAnalysisResult.result) {
    showToast('Uygulanacak öneri bulunamadı', 'error');
    return;
  }
  
  const result = lastAnalysisResult.result;
  
  if (result.recommended_style) {
    selectedStyleId = result.recommended_style;
    await applySelectedStyle();
  } else if (result.color_theme && result.color_theme.primary) {
    const page = getCurrentPage();
    page.backgroundColor = result.color_theme.primary + '10';
    fabricCanvas.setBackgroundColor(page.backgroundColor, fabricCanvas.renderAll.bind(fabricCanvas));
  }
  
  closeAnalysisModal();
  showToast('Öneriler uygulandı!', 'success');
}

// ============= ANA TEMA =============
function exportMasterTemplateFromCurrentPage() {
  const style = selectedStyleId ? designStyles.find(s => s.id === selectedStyleId) : null;
  
  return {
    id: "template-" + Date.now(),
    name: "Ana Tema " + new Date().toLocaleDateString("tr-TR"),
    canvasSize: { width: 595, height: 842 },
    contentRegions: [{ id: "content-main", x: 0, y: 140, width: 595, height: 620 }],
    styleProfile: style ? style.colors : { primaryColor: "#6366f1", secondaryColor: "#ec4899" },
    styleId: selectedStyleId,
    logoPlacement: { x: 20, y: 12, width: 120, height: 36 }
  };
}

function renderTemplatePreview() {
  const div = document.getElementById("template-preview");
  if (!masterTemplate) {
    div.textContent = "Henüz ana tema kaydedilmedi.";
    return;
  }
  const logo = masterTemplate.logoPlacement || {};
  const styleName = masterTemplate.styleId ? 
    (designStyles.find(s => s.id === masterTemplate.styleId)?.name || masterTemplate.styleId) : 
    'Özel';
  
  div.innerHTML = `
    <div><b>Ad:</b> ${masterTemplate.name}</div>
    <div><b>Stil:</b> ${styleName}</div>
    <div><b>Logo:</b> x=${logo.x || 20}, y=${logo.y || 12}</div>
  `;
}

// ============= SEÇİLİ ÜRÜN PANELİ =============
function updateSelectedObjectPanel(e) {
  const obj = e.selected && e.selected[0];
  studioState.selectedObjectMeta = obj && obj.productMeta ? obj.productMeta : null;
  renderSelectedProductPanel();
}

function renderSelectedProductPanel() {
  const panel = document.getElementById("selected-product-panel");
  const meta = studioState.selectedObjectMeta;
  if (!meta) {
    panel.textContent = "Henüz ürün seçilmedi.";
    return;
  }
  const product = allProducts.find(p => p.id === meta.productId);
  panel.innerHTML = `
    <div style="font-weight:600;">${product ? product.name : meta.productId}</div>
    <div>Barkod: ${meta.barcode || '-'}</div>
    <div>Grup: ${meta.product_group || '-'}</div>
    ${meta.caption ? `<div>Etiket: <span style="color:#ec4899;">${meta.caption}</span></div>` : ''}
    <div style="margin-top:6px;font-size:10px;color:#6b7280;">
      lockScale: ${meta.lockScale ? "evet" : "hayır"} | 
      lockPosition: ${meta.lockPosition ? "evet" : "hayır"}
    </div>
  `;
}

// ============= YARDIMCI FONKSİYONLAR =============
function formatPrice(v) {
  const n = Number(v) || 0;
  return n.toFixed(2).replace(".", ",") + " TL";
}

function showToast(message, type = 'success') {
  const existingToast = document.querySelector('.toast');
  if (existingToast) existingToast.remove();
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : '❌'}</span>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.remove(), 3000);
}

// Global functions
window.closeAnalysisModal = closeAnalysisModal;
window.applyAnalysisSuggestion = applyAnalysisSuggestion;
window.closeStylePicker = closeStylePicker;
window.selectStyle = selectStyle;
window.applySelectedStyle = applySelectedStyle;
