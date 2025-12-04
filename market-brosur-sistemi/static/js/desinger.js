// Desınger Test Sayfası
// Gerçek depo ürünleriyle çalışan basit Fabric.js stüdyosu

let desingerCanvas = null;
let desingerProducts = [];

document.addEventListener('DOMContentLoaded', () => {
  if (typeof fabric === 'undefined') {
    console.error('Fabric.js yüklenemedi');
    return;
  }

  desingerCanvas = new fabric.Canvas('brochure-canvas', {
    backgroundColor: '#ffffff',
  });

  setupDragDrop();
  loadDepotProducts();
  setupButtons();
});

function setupDragDrop() {
  const canvasArea = document.getElementById('canvas-area');
  if (!canvasArea) return;

  canvasArea.addEventListener('dragover', (e) => e.preventDefault());
  canvasArea.addEventListener('drop', (e) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData('text/plain');
    if (!raw) return;
    try {
      const data = JSON.parse(raw);
      addProductToCanvas(data);
    } catch (err) {
      console.error('Drop parse error:', err);
    }
  });
}

async function loadDepotProducts() {
  const statusEl = document.getElementById('product-list-status');
  const bodyEl = document.getElementById('product-list-body');
  if (!bodyEl) return;

  if (statusEl) {
    statusEl.textContent = 'Depodaki ürünler yükleniyor...';
  }

  try {
    const resp = await fetch('/api/admin/all-products');
    const data = await resp.json();

    if (!data.success) {
      throw new Error(data.error || 'Ürünler alınamadı');
    }

    const rawProducts = data.products || [];
    desingerProducts = rawProducts.map((p) => {
      const normal = parseFloat(p.normal_price) || 0;
      const discount = parseFloat(p.discount_price) || 0;
      return {
        id: p.barcode,
        name: p.product_name || p.name || p.barcode,
        normal_price: normal,
        discount_price: discount || normal,
        image_url: p.image_url || '/static/placeholder.png',
        barcode: p.barcode,
        product_group: p.product_group || 'Genel',
      };
    });

    renderProductList();

    if (statusEl) {
      statusEl.textContent = `${desingerProducts.length} ürün yüklendi. Sürükleyip kanvasa bırakabilirsiniz.`;
    }
  } catch (error) {
    console.error('Depot load error:', error);
    if (statusEl) {
      statusEl.textContent =
        'Ürünler yüklenemedi. Giriş yaptığınızdan ve admin olduğunuzdan emin olun.';
      statusEl.style.color = '#b91c1c';
    }
  }
}

function renderProductList() {
  const bodyEl = document.getElementById('product-list-body');
  if (!bodyEl) return;
  bodyEl.innerHTML = '';

  desingerProducts.forEach((p) => {
    const el = document.createElement('div');
    el.className = 'product';
    el.draggable = true;

    const priceValue = p.discount_price || p.normal_price || 0;
    const priceLabel = priceValue
      ? priceValue.toFixed(2).replace('.', ',') + ' ₺'
      : '';

    el.dataset.name = p.name;
    el.dataset.normalPrice = p.normal_price || 0;
    el.dataset.discountPrice = p.discount_price || 0;
    el.dataset.img = p.image_url;
    el.dataset.barcode = p.barcode;
    el.dataset.group = p.product_group || 'Genel';
    el.dataset.priceLabel = priceLabel;

    el.innerHTML = `
      <div class="product-name">${p.name}</div>
      <div class="product-meta">
        <span class="product-price">${priceLabel}</span>
        <span class="product-group">${p.product_group || ''}</span>
      </div>
    `;

    el.addEventListener('dragstart', (e) => {
      const payload = {
        name: el.dataset.name,
        normal_price: parseFloat(el.dataset.normalPrice) || 0,
        discount_price: parseFloat(el.dataset.discountPrice) || 0,
        price_label: el.dataset.priceLabel,
        image_url: el.dataset.img,
        barcode: el.dataset.barcode,
        product_group: el.dataset.group,
      };
      e.dataTransfer.setData('text/plain', JSON.stringify(payload));
    });

    bodyEl.appendChild(el);
  });
}

function addProductToCanvas(product) {
  if (!desingerCanvas) return;

  const imgUrl = product.image_url || product.image || product.img;
  const priceText = product.price_label || formatPrice(product.discount_price || product.normal_price);

  fabric.Image.fromURL(
    imgUrl,
    (img) => {
      img.scaleToWidth(120);
      img.left = 80;
      img.top = 80;
      img.set({
        originX: 'left',
        originY: 'top',
      });
      img.data = {
        type: 'product',
        name: product.name,
        barcode: product.barcode,
        product_group: product.product_group || 'Genel',
        normal_price: product.normal_price || 0,
        discount_price: product.discount_price || 0,
        price_label: priceText,
      };

      desingerCanvas.add(img);

      const label = new fabric.Textbox(`${product.name}\n${priceText}`, {
        top: img.top + img.getScaledHeight() + 8,
        left: img.left,
        fontSize: 16,
        fill: '#111827',
        fontFamily: 'Segoe UI',
      });
      label.data = {
        type: 'product-label',
        barcode: product.barcode,
      };

      desingerCanvas.add(label);
      desingerCanvas.setActiveObject(img);
      desingerCanvas.renderAll();
    },
    {
      crossOrigin: 'anonymous',
    }
  );
}

function setupButtons() {
  const layoutBtn = document.getElementById('ai-layout');
  const styleBtn = document.getElementById('ai-style');
  const exportBtn = document.getElementById('export');
  const clearBtn = document.getElementById('clear-canvas');

  if (layoutBtn) {
    layoutBtn.addEventListener('click', handleAiLayout);
  }
  if (styleBtn) {
    styleBtn.addEventListener('click', handleKieBackground);
  }
  if (exportBtn) {
    exportBtn.addEventListener('click', exportCanvasPng);
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', clearCanvas);
  }
}

function collectCanvasProducts() {
  if (!desingerCanvas) return [];
  const objs = desingerCanvas.getObjects();
  const products = [];

  objs.forEach((obj) => {
    if (obj.data && obj.data.type === 'product') {
      products.push({
        id: obj.data.barcode || obj.data.name,
        name: obj.data.name,
        barcode: obj.data.barcode,
        product_group: obj.data.product_group,
        normal_price: obj.data.normal_price,
        discount_price: obj.data.discount_price,
      });
    }
  });

  return products;
}

async function handleAiLayout() {
  const products = collectCanvasProducts();
  if (!products.length) {
    alert('Önce kanvasa en az bir ürün yerleştirin.');
    return;
  }

  try {
    const resp = await fetch('/api/desinger/layout-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        products,
        purpose: 'discount',
      }),
    });
    const data = await resp.json();

    if (!data.success) {
      alert('AI düzen önerisi alınamadı: ' + (data.error || 'Bilinmeyen hata'));
      return;
    }

    const slogan = data.result && data.result.slogan;
    const analysis = data.analysis && data.analysis.analysis;

    let msg = 'AI düzen analizi hazır.\n';
    if (analysis) msg += '\nÖzet: ' + analysis;
    if (slogan) msg += '\nÖnerilen slogan: ' + slogan;
    alert(msg);
  } catch (err) {
    console.error('Layout AI error:', err);
    alert('AI düzen servisine ulaşılamadı.');
  }
}

async function handleKieBackground() {
  // Tema seçimi için popup (Kırmızı Market referanslı)
  const themes = [
    { id: 'market', name: '🏪 Genel Market (Yeşil/Krem)', desc: 'Profesyonel market broşürü' },
    { id: 'tea', name: '🍵 Çay Kampanyası', desc: 'Yeşil çay tarlası arka planı' },
    { id: 'discount', name: '🔥 Süper İndirim', desc: 'Kırmızı/Sarı patlama efekti' },
    { id: 'fresh', name: '🥬 Manav/Taze Ürünler', desc: 'Yeşil taze sebze teması' },
    { id: 'butcher', name: '🥩 Kasap/Et Ürünleri', desc: 'Bordo/Ahşap premium tema' }
  ];
  
  const selectedTheme = prompt(
    `🎨 Arka Plan Teması Seç (Kırmızı Market Tarzı):\n\n${themes.map((t, i) => `${i+1}. ${t.name}\n   ${t.desc}`).join('\n\n')}\n\nNumara gir (1-5):`,
    '1'
  );
  
  if (!selectedTheme) return;
  
  const themeIndex = parseInt(selectedTheme) - 1;
  const theme = themes[themeIndex] ? themes[themeIndex].id : 'market';
  
  alert(`🎨 "${themes[themeIndex]?.name || 'Market'}" arka planı oluşturuluyor...\nBu işlem 30-60 saniye sürebilir.`);
  
  try {
    const resp = await fetch('/api/desinger/kie-background', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        purpose: theme,
      }),
    });
    const data = await resp.json();
    if (!data.success || !data.image_url) {
      alert('Arka plan üretilemedi: ' + (data.error || 'Bilinmeyen hata'));
      return;
    }

    if (!desingerCanvas) return;

    desingerCanvas.setBackgroundImage(
      data.image_url,
      () => {
        desingerCanvas.renderAll();
        alert('✅ Profesyonel arka plan uygulandı!');
      },
      {
        originX: 'left',
        originY: 'top',
        crossOrigin: 'anonymous',
      }
    );
  } catch (err) {
    console.error('Background error:', err);
    alert('Sunucu hatası: ' + err.message);
  }
}

function exportCanvasPng() {
  if (!desingerCanvas) return;
  const dataUrl = desingerCanvas.toDataURL({ format: 'png' });
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = 'desinger-test.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function clearCanvas() {
  if (!desingerCanvas) return;
  desingerCanvas.clear();
  desingerCanvas.backgroundColor = '#ffffff';
  desingerCanvas.renderAll();
}

function formatPrice(value) {
  const num = parseFloat(value);
  if (!num) return '';
  return num.toFixed(2).replace('.', ',') + ' ₺';
}



