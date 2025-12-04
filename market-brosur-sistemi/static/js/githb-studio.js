/**
 * Gıthb Test 2 Studio - Gerçek Depo + AI Entegrasyonu
 * Bu dosya ana sisteme dokunmadan sadece test amaçlı çalışır.
 */

// ============= GLOBAL STATE =============
let allProducts = [];  // Gerçek depo ürünleri
let masterTemplate = null;

const studioState = {
  pages: [{ id: "page-1", objectsMeta: [], styleProfileId: null }],
  currentPageIndex: 0,
  selectedObjectMeta: null
};

let fabricCanvas = null;

// ============= INITIALIZATION =============
window.addEventListener("DOMContentLoaded", () => {
  loadDepotProducts();
  initCanvas();
  initPageButtons();
  initButtons();
});

// ============= DEPO ÜRÜNLERİNİ YÜKLE =============
async function loadDepotProducts() {
  const container = document.getElementById("product-list");
  const depotStatus = document.getElementById("depot-status");
  const productCount = document.getElementById("product-count");
  
  container.innerHTML = `
    <div style="text-align:center;padding:20px;">
      <div class="loading-spinner"></div>
      <p style="color:#9ca3af;margin-top:10px;font-size:11px;">Depo ürünleri yükleniyor...</p>
    </div>
  `;
  
  try {
    // Önce admin ürünlerini dene
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
        sector: p.sector || 'supermarket'
      }));
      
      depotStatus.textContent = 'Admin Deposu';
      depotStatus.style.color = '#22c55e';
    } else {
      // Müşteri ürünlerini dene
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
          sector: p.sector || 'supermarket'
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
      <div style="text-align:center;padding:20px;color:#ef4444;">
        <p>❌ Ürünler yüklenemedi</p>
        <p style="font-size:10px;margin-top:5px;">${error.message}</p>
      </div>
    `;
  }
}

// ============= ÜRÜN LİSTESİ RENDER =============
function renderProductList() {
  const container = document.getElementById("product-list");
  
  if (allProducts.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:20px;color:#9ca3af;">
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
      <div style="display:flex;gap:8px;align-items:center;">
        <img src="${p.image_url}" alt="${p.name}" onerror="this.src='/static/placeholder.png'">
        <div style="flex:1;min-width:0;">
          <div class="product-name">${p.name}</div>
          <div style="display:flex;gap:6px;align-items:center;">
            <span class="product-price">${formatPrice(p.price)}</span>
            ${p.oldPrice > p.price ? `<span class="product-old-price">${formatPrice(p.oldPrice)}</span>` : ''}
          </div>
          <div style="font-size:9px;color:#6b7280;">${p.product_group}</div>
        </div>
      </div>
      <button class="btn-ghost" style="margin-top:6px;width:100%;font-size:11px;">Canvas'a ekle</button>
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
    btn.style.padding = "3px 8px";
    btn.style.fontSize = "11px";
    btn.style.borderRadius = "999px";
    btn.style.border = "1px solid";
    btn.style.cursor = "pointer";
    
    if (idx === studioState.currentPageIndex) {
      btn.style.borderColor = "#818cf8";
      btn.style.background = "#6366f1";
      btn.style.color = "#ffffff";
    } else {
      btn.style.borderColor = "#4b5563";
      btn.style.background = "transparent";
      btn.style.color = "#e5e7eb";
      btn.onmouseenter = () => btn.style.background = "#111827";
      btn.onmouseleave = () => btn.style.background = "transparent";
    }
    btn.onclick = () => switchPage(idx);
    container.appendChild(btn);
  });

  document.getElementById("btn-add-page").onclick = () => {
    studioState.pages.push({
      id: `page-${studioState.pages.length + 1}`,
      objectsMeta: [],
      styleProfileId: null
    });
    studioState.currentPageIndex = studioState.pages.length - 1;
    initPageButtons();
    redrawCanvasFromState();
  };
}

// ============= BUTON OLAYLARI =============
function initButtons() {
  // AI Layout - OpenAI
  document.getElementById("btn-ai-layout-page").onclick = () => callAiLayout({ scope: "page" });
  document.getElementById("btn-ai-layout-selection").onclick = () => callAiLayout({ scope: "selection" });
  
  // KIE.ai Arka Plan
  document.getElementById("btn-ai-soften-bg").onclick = () => callKieBackground();
  
  // Kanvası temizle
  document.getElementById("btn-clear-canvas").onclick = () => {
    if (confirm('Kanvastaki tüm öğeler silinecek. Devam edilsin mi?')) {
      fabricCanvas.clear();
      fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));
      getCurrentPage().objectsMeta = [];
      showToast('Kanvas temizlendi', 'success');
    }
  };

  // PNG indir
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

  // Ana tema kaydet
  document.getElementById("btn-save-template").onclick = () => {
    masterTemplate = exportMasterTemplateFromCurrentPage();
    renderTemplatePreview();
    showToast('Bu sayfa ana tema olarak kaydedildi (demo)', 'success');
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

    // Ürün meta verilerini sakla
    group.productMeta = {
      productId: product.id,
      barcode: product.barcode,
      product_group: product.product_group,
      price: product.price,
      oldPrice: product.oldPrice,
      userEdited: false,
      lockScale: false,
      lockPosition: false
    };

    group.on("mousedblclick", () => {
      showToast(`${product.name} - Büyük önizleme açılabilir`, 'success');
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
  fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));
  
  const page = getCurrentPage();
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

// ============= AI LAYOUT (OpenAI) =============
async function callAiLayout({ scope }) {
  const page = getCurrentPage();
  syncObjectsMetaFromCanvas();

  if (page.objectsMeta.length === 0) {
    showToast('Önce kanvasa ürün ekleyin', 'error');
    return;
  }

  showToast('AI analiz yapıyor...', 'success');

  // Kanvastaki ürünleri topla
  const productsForAi = page.objectsMeta.map(meta => {
    const product = allProducts.find(p => p.id === meta.productId);
    return {
      name: product ? product.name : meta.productId,
      normal_price: product ? product.oldPrice : 0,
      discount_price: product ? product.price : 0,
      product_group: meta.product_group || 'Genel',
      barcode: meta.barcode
    };
  });

  try {
    const response = await fetch('/api/desinger/layout-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products: productsForAi, scope })
    });
    
    const data = await response.json();
    
    if (data.success) {
      let message = '📊 AI Analiz Sonucu:\n\n';
      if (data.analysis) {
        message += `Ürün: ${data.analysis.product_count || 0}\n`;
        if (data.analysis.categories) {
          message += `Kategoriler: ${data.analysis.categories.map(c => c.name).join(', ')}\n`;
        }
      }
      if (data.suggestion && data.suggestion.slogan) {
        message += `\n💡 Slogan: ${data.suggestion.slogan}`;
      }
      if (data.suggestion && data.suggestion.greeting) {
        message += `\n\n${data.suggestion.greeting}`;
      }
      
      alert(message);
      showToast('AI analizi tamamlandı', 'success');
    } else {
      showToast(data.error || 'AI hatası', 'error');
    }
  } catch (e) {
    console.error('AI Layout hatası:', e);
    showToast('Sunucu hatası: ' + e.message, 'error');
  }
}

// ============= DALL-E ARKA PLAN (Kırmızı Market Tarzı) =============
async function callKieBackground() {
  // Tema seçimi için popup göster
  const themes = [
    { id: 'market', name: '🏪 Genel Market (Yeşil/Krem)', desc: 'Profesyonel market broşürü' },
    { id: 'tea', name: '🍵 Çay Kampanyası', desc: 'Yeşil çay tarlası arka planı' },
    { id: 'discount', name: '🔥 Süper İndirim', desc: 'Kırmızı/Sarı patlama efekti' },
    { id: 'fresh', name: '🥬 Manav/Taze Ürünler', desc: 'Yeşil taze sebze teması' },
    { id: 'butcher', name: '🥩 Kasap/Et Ürünleri', desc: 'Bordo/Ahşap premium tema' }
  ];
  
  const themeOptions = themes.map(t => `${t.id}: ${t.name}`).join('\n');
  const selectedTheme = prompt(
    `🎨 Arka Plan Teması Seç:\n\n${themes.map((t, i) => `${i+1}. ${t.name}\n   ${t.desc}`).join('\n\n')}\n\nNumara gir (1-5):`,
    '1'
  );
  
  if (!selectedTheme) return;
  
  const themeIndex = parseInt(selectedTheme) - 1;
  const theme = themes[themeIndex] ? themes[themeIndex].id : 'market';
  
  showToast(`🎨 "${themes[themeIndex]?.name || 'Market'}" arka planı oluşturuluyor... (30-60 sn)`, 'success');

  try {
    const response = await fetch('/api/desinger/kie-background', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ purpose: theme })
    });
    
    const data = await response.json();
    
    if (data.success && data.image_url) {
      fabric.Image.fromURL(data.image_url, bgImg => {
        fabricCanvas.setBackgroundImage(bgImg, fabricCanvas.renderAll.bind(fabricCanvas), {
          scaleX: fabricCanvas.width / bgImg.width,
          scaleY: fabricCanvas.height / bgImg.height
        });
        showToast('✅ Profesyonel arka plan uygulandı!', 'success');
      }, { crossOrigin: 'Anonymous' });
    } else {
      showToast(data.error || 'Arka plan hatası', 'error');
    }
  } catch (e) {
    console.error('Background hatası:', e);
    showToast('Sunucu hatası: ' + e.message, 'error');
  }
}

// ============= ANA TEMA =============
function exportMasterTemplateFromCurrentPage() {
  return {
    id: "template-" + Date.now(),
    name: "Ana Tema " + new Date().toLocaleDateString("tr-TR"),
    canvasSize: { width: 595, height: 842 },
    contentRegions: [{ id: "content-main", x: 0, y: 140, width: 595, height: 620 }],
    styleProfile: { primaryColor: "#6366f1", secondaryColor: "#ec4899" }
  };
}

function renderTemplatePreview() {
  const div = document.getElementById("template-preview");
  if (!masterTemplate) {
    div.textContent = "Henüz ana tema kaydedilmedi.";
    return;
  }
  const r = masterTemplate.contentRegions[0];
  div.innerHTML = `
    <div><b>Ad:</b> ${masterTemplate.name}</div>
    <div><b>İç Bölge:</b> x=${r.x}, y=${r.y}, w=${r.width}, h=${r.height}</div>
    <div><b>Renkler:</b> ${masterTemplate.styleProfile.primaryColor}, ${masterTemplate.styleProfile.secondaryColor}</div>
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
    <div>lockScale: ${meta.lockScale ? "evet" : "hayır"}</div>
    <div>lockPosition: ${meta.lockPosition ? "evet" : "hayır"}</div>
  `;
}

// ============= YARDIMCI FONKSİYONLAR =============
function formatPrice(v) {
  const n = Number(v) || 0;
  return n.toFixed(2).replace(".", ",") + " TL";
}

function showToast(message, type = 'success') {
  // Önceki toast varsa kaldır
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


