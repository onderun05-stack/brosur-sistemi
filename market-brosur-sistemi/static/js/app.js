let canvas;
let currentPage = 0;
let pages = [{ products: [], title: '1. Sayfa', locked: false }];
let allProducts = [];
let parkingProducts = [];
let currentUser = null;

// Sync with index.html's fabricCanvas
function syncCanvas() {
  if (typeof fabricCanvas !== 'undefined' && fabricCanvas) {
    canvas = fabricCanvas;
    console.log('✅ Canvas senkronize edildi (fabricCanvas kullanılıyor)');
    return true;
  }
  return false;
}
let currentFont = 'Arial';
let currentColor = '#667eea';
let pinnedProducts = new Set();
let savedPages = {};

// New variables for enhanced features
let undoStack = [];
let redoStack = [];
let currentZoom = 1.0;
let gridSnapEnabled = true;
let gridSize = 20;
let showRulers = false;
let editorPrefs = {};
let themePresets = {
    'Professional': { font: 'Georgia, serif', textColor: '#333', priceColor: '#c41e3a', accent: '#1e3a8a' },
    'Colorful': { font: 'Verdana, sans-serif', textColor: '#2563eb', priceColor: '#dc2626', accent: '#f59e0b' },
    'Minimal': { font: 'Arial, sans-serif', textColor: '#000', priceColor: '#666', accent: '#000' },
    'Modern': { font: '-apple-system, BlinkMacSystemFont, sans-serif', textColor: '#1f2937', priceColor: '#ef4444', accent: '#6366f1' }
};

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkSessionOnLoad();
});

async function checkSessionOnLoad() {
  try {
    const response = await fetch('/api/check-session');
    const data = await response.json();
    if (data.success && data.user) {
      currentUser = data.user;
      showMainScreen();
      let stagedProducts = null;
      const stagedPayload = sessionStorage.getItem('approvedCanvasPayload');
      if (stagedPayload) {
        try {
          stagedProducts = JSON.parse(stagedPayload);
        } catch (error) {
          console.warn('Staged canvas payload parse error:', error);
        }
        sessionStorage.removeItem('approvedCanvasPayload');
        sessionStorage.removeItem('approvedPageSummary');
      }
      if (stagedProducts && Array.isArray(stagedProducts) && stagedProducts.length > 0) {
        allProducts = stagedProducts;
        console.log('🎨 Canvas payload alındı:', allProducts.length, 'ürün');
      } else {
        await loadProducts();
      }
      initializeCanvas();
      renderProducts();
      
      // Ürünleri direkt Canvas'a yerleştir (sayfa 1'den itibaren liste sırasına göre)
      // Canvas'ın tamamen hazır olmasını bekle
      setTimeout(() => {
        // Canvas'ı tekrar senkronize et
        syncCanvas();
        
        if (!canvas) {
          console.error('❌ Canvas hala hazır değil!');
          return;
        }
        
        console.log('🎯 Canvas hazır, ürünler yerleştiriliyor...');
        autoPlaceProductsOnCanvas();
      }, 1000);
    }
  } catch (error) {
    console.log('No session');
  }
}

function setupEventListeners() {
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('file-input').addEventListener('change', handleFileUpload);
  document.getElementById('download-template-btn').addEventListener('click', downloadTemplate);
  document.getElementById('add-page-btn').addEventListener('click', addNewPage);
  document.getElementById('auto-btn').addEventListener('click', generateAutoBrochure);
  document.getElementById('pdf-btn').addEventListener('click', downloadPDF);
  document.getElementById('instagram-btn').addEventListener('click', downloadInstagram);
  document.getElementById('apply-page-btn').addEventListener('click', () => applyStyle(false));
  document.getElementById('apply-all-btn').addEventListener('click', () => applyStyle(true));
  document.getElementById('font-select').addEventListener('change', (e) => {
    currentFont = e.target.value;
  });
  document.getElementById('color-picker').addEventListener('change', (e) => {
    currentColor = e.target.value;
  });
  document.getElementById('close-modal-btn').addEventListener('click', () => {
    document.getElementById('image-modal').classList.add('hidden');
  });
  document.getElementById('close-slogan-modal-btn').addEventListener('click', () => {
    document.getElementById('slogan-modal').classList.add('hidden');
  });
  
  // New AI and template event listeners
  const aiGenerateBtn = document.getElementById('ai-generate-btn');
  if (aiGenerateBtn) {
    aiGenerateBtn.addEventListener('click', generateAIBrochure);
  }
  
  const companyLogoInput = document.getElementById('company-logo-input');
  if (companyLogoInput) {
    companyLogoInput.addEventListener('change', handleLogoUpload);
  }
  
  const templateInput = document.getElementById('template-input');
  if (templateInput) {
    templateInput.addEventListener('change', handleTemplateUpload);
  }
  
  const closeTemplateModalBtn = document.getElementById('close-template-modal-btn');
  if (closeTemplateModalBtn) {
    closeTemplateModalBtn.addEventListener('click', () => {
      document.getElementById('template-modal').classList.add('hidden');
    });
  }
  
  const applyTemplateBtn = document.getElementById('apply-template-btn');
  if (applyTemplateBtn) {
    applyTemplateBtn.addEventListener('click', applySelectedTemplate);
  }
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey) {
      if (e.key === 'p') {
        e.preventDefault();
        handleProductCommand();
      } else if (e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      } else if ((e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
      } else if (e.key === 'g') {
        e.preventDefault();
        gridSnapEnabled = !gridSnapEnabled;
        showNotification(`Grid snap ${gridSnapEnabled ? 'enabled' : 'disabled'}`);
      }
    }
  });
  
  // Add theme preset event listeners
  setupThemeControls();
  setupAlignmentControls();
  setupZoomControls();
}

function handleProductCommand() {
  const cmd = prompt('Komut girin (ör: büyüt, 2. sayfaya at, fontunu değiştir, slogansıyla birlikte):');
  if (!cmd) return;
  
  const selected = canvas.getActiveObject();
  if (!selected) {
    alert('Önce bir ürün seçin');
    return;
  }
  
  if (cmd.includes('büyüt')) {
    selected.set({ scaleX: selected.scaleX * 1.2, scaleY: selected.scaleY * 1.2 });
  } else if (cmd.match(/\d+\.\s*sayfa/)) {
    const pageNum = parseInt(cmd.match(/\d+/)[0]) - 1;
    if (pageNum >= 0 && pageNum < pages.length) {
      pages[currentPage].products = pages[currentPage].products.filter(p => p !== selected.data);
      pages[pageNum].products.push(selected.data);
      updateCanvas();
    }
  } else if (cmd.includes('parka')) {
    parkingProducts.push(selected.data);
    pages[currentPage].products = pages[currentPage].products.filter(p => p !== selected.data);
  }
  canvas.renderAll();
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    if (response.ok && data.success) {
      currentUser = data.user;
      // Redirect to dashboard after successful login
      window.location.href = '/dashboard';
    } else {
      alert(data.message || 'Giriş başarısız');
      console.error('Login error:', data);
    }
  } catch (error) {
    alert('Giriş hatası: ' + error.message);
    console.error('Login exception:', error);
  }
}

function handleLogout() {
  fetch('/api/logout', { method: 'POST' });
  document.getElementById('main-screen').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  currentUser = null;
}

function downloadTemplate() {
  const link = document.createElement('a');
  link.href = '/api/template';
  link.download = 'urun-sablon.xlsx';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function initializeCanvas() {
  const A4_WIDTH = 595;
  const A4_HEIGHT = 842;

  // Önce index.html'deki fabricCanvas'ı kullanmayı dene
  if (syncCanvas()) {
    console.log('✅ Mevcut fabricCanvas kullanılıyor');
    return; // Zaten initialize edilmiş
  }

  canvas = new fabric.Canvas('brochure-canvas', {
    width: A4_WIDTH,
    height: A4_HEIGHT,
    backgroundColor: '#ffffff',
    preserveObjectStacking: true
  });
  
  // Global olarak da erişilebilir yap
  window.fabricCanvas = canvas;

  // Enhanced object moving with grid snap
  canvas.on('object:moving', (e) => {
    const obj = e.target;
    if (gridSnapEnabled && gridSize > 0) {
      obj.set({
        left: Math.round(obj.left / gridSize) * gridSize,
        top: Math.round(obj.top / gridSize) * gridSize
      });
    }
    saveUndoState();
  });

  // Enhanced object scaling with auto-shift
  canvas.on('object:scaling', (e) => {
    const obj = e.target;
    
    // Skip auto-shift if object is pinned
    if (pinnedProducts.has(obj.id)) return;
    
    const scaledWidth = obj.width * obj.scaleX;
    const scaledHeight = obj.height * obj.scaleY;
    
    // Auto-shift other unpinned objects
    const others = canvas.getObjects().filter(o => o !== obj && !pinnedProducts.has(o.id));
    
    others.forEach(other => {
      if (obj.intersectsWithObject(other)) {
        // Calculate push direction
        const objCenter = obj.getCenterPoint();
        const otherCenter = other.getCenterPoint();
        
        const dx = otherCenter.x - objCenter.x;
        const dy = otherCenter.y - objCenter.y;
        
        // Push other object away
        const pushDistance = 30;
        const angle = Math.atan2(dy, dx);
        
        other.set({
          left: other.left + Math.cos(angle) * pushDistance,
          top: other.top + Math.sin(angle) * pushDistance
        });
        
        // Check if object needs to move to next page
        if (other.left + other.width * other.scaleX > A4_WIDTH || 
            other.top + other.height * other.scaleY > A4_HEIGHT) {
          moveProductToNextPage(other);
        }
      }
    });
    
    canvas.renderAll();
    saveUndoState();
  });

  // Add modified event for undo/redo
  canvas.on('object:modified', () => {
    saveUndoState();
  });

  // Double click to pin/unpin product
  canvas.on('mouse:dblclick', (e) => {
    if (e.target) {
      togglePinProduct(e.target);
    }
  });

  // Add zoom controls
  canvas.on('mouse:wheel', (opt) => {
    if (opt.e.ctrlKey) {
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** delta;
      if (zoom > 2) zoom = 2;
      if (zoom < 0.5) zoom = 0.5;
      canvas.setZoom(zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
      currentZoom = zoom;
    }
  });

  const canvasWrapper = document.querySelector('.canvas-wrapper');
  canvasWrapper.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  });

  canvasWrapper.addEventListener('drop', (e) => {
    e.preventDefault();
    const productData = e.dataTransfer.getData('productData');
    if (productData) {
      const product = JSON.parse(productData);
      const canvasElement = document.getElementById('brochure-canvas');
      const rect = canvasElement.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      addProductToCanvas(product, x, y);
    }
  });
  
  setupRulers();
}

async function loadProducts() {
  try {
    const response = await fetch('/api/products');
    const data = await response.json();
    if (data.success) {
      allProducts = data.products;
      renderProducts();
    }
  } catch (error) {
    console.error('Ürünler yüklenemedi:', error);
  }
}

function renderProducts() {
  const productsList = document.getElementById('products-list');
  productsList.innerHTML = '';
  document.getElementById('products-count').textContent = allProducts.length;

  allProducts.forEach((product, index) => {
    const discountPercent = Math.round(((product.normal_price - product.discount_price) / product.normal_price) * 100);

    const productItem = document.createElement('div');
    productItem.className = 'product-item' + (!product.image_url ? ' no-image' : '');
    productItem.draggable = true;
    productItem.innerHTML = `
      <div class="product-name">${product.name}</div>
      <div class="product-prices">
        <span class="old-price">${product.normal_price.toFixed(2)} ₺</span>
        <span class="new-price">${product.discount_price.toFixed(2)} ₺</span>
      </div>
      <div style="margin-top: 5px;">
        <span class="discount-badge">%${discountPercent} İNDİRİM</span>
      </div>
      ${!product.image_url ? '<button class="find-image-btn" onclick="findImage(' + index + ')">🔍 Resim Bul</button>' : ''}
    `;

    productItem.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('productData', JSON.stringify(product));
      e.dataTransfer.effectAllowed = 'copy';
    });

    productItem.addEventListener('click', () => {
      if (product.image_url) {
        addProductToCanvas(product);
      }
    });

    productsList.appendChild(productItem);
  });
}

// Helper Functions for Enhanced Features
function saveUndoState() {
  const state = JSON.stringify(canvas.toJSON(['id', 'productData']));
  undoStack.push(state);
  if (undoStack.length > 50) undoStack.shift();
  redoStack = [];
}

function undo() {
  if (undoStack.length > 1) {
    redoStack.push(undoStack.pop());
    const state = undoStack[undoStack.length - 1];
    canvas.loadFromJSON(state, () => {
      canvas.renderAll();
    });
  }
}

function redo() {
  if (redoStack.length > 0) {
    const state = redoStack.pop();
    undoStack.push(state);
    canvas.loadFromJSON(state, () => {
      canvas.renderAll();
    });
  }
}

function togglePinProduct(obj) {
  const id = obj.id || obj.productData?.id || Math.random().toString(36);
  obj.id = id;
  
  if (pinnedProducts.has(id)) {
    pinnedProducts.delete(id);
    obj.set({
      borderColor: 'rgba(0, 169, 255, 0.9)',
      cornerColor: 'rgba(0, 169, 255, 0.9)'
    });
    showNotification('Product unpinned');
  } else {
    pinnedProducts.add(id);
    obj.set({
      borderColor: '#ff6b6b',
      cornerColor: '#ff6b6b'
    });
    showNotification('Product pinned - will not auto-move');
  }
  canvas.renderAll();
}

function moveProductToNextPage(obj) {
  const nextPageIndex = currentPage + 1;
  
  if (nextPageIndex >= pages.length) {
    pages.push({ products: [], title: `${nextPageIndex + 1}. Sayfa` });
    renderPageTabs();
  }
  
  pages[currentPage].products = pages[currentPage].products.filter(p => p !== obj.productData?.id);
  pages[nextPageIndex].products.push(obj.productData?.id);
  
  canvas.remove(obj);
  showNotification(`Product moved to page ${nextPageIndex + 1} due to overflow`);
}

function setupRulers() {
  if (!showRulers) return;
  
  // Add ruler lines for guidance
  const rulerLines = [];
  
  // Vertical center line
  const vLine = new fabric.Line([canvas.width / 2, 0, canvas.width / 2, canvas.height], {
    stroke: '#ddd',
    strokeWidth: 1,
    selectable: false,
    evented: false,
    strokeDashArray: [5, 5]
  });
  
  // Horizontal center line
  const hLine = new fabric.Line([0, canvas.height / 2, canvas.width, canvas.height / 2], {
    stroke: '#ddd',
    strokeWidth: 1,
    selectable: false,
    evented: false,
    strokeDashArray: [5, 5]
  });
  
  canvas.add(vLine, hLine);
}

function alignObjects(alignment) {
  const activeObjects = canvas.getActiveObjects();
  if (activeObjects.length < 2) return;
  
  switch(alignment) {
    case 'left':
      const minLeft = Math.min(...activeObjects.map(o => o.left));
      activeObjects.forEach(obj => obj.set({ left: minLeft }));
      break;
    case 'center':
      const centerX = canvas.width / 2;
      activeObjects.forEach(obj => {
        obj.set({ left: centerX - (obj.width * obj.scaleX) / 2 });
      });
      break;
    case 'right':
      const maxRight = Math.max(...activeObjects.map(o => o.left + o.width * o.scaleX));
      activeObjects.forEach(obj => {
        obj.set({ left: maxRight - obj.width * obj.scaleX });
      });
      break;
    case 'distribute':
      if (activeObjects.length < 3) return;
      activeObjects.sort((a, b) => a.left - b.left);
      const first = activeObjects[0];
      const last = activeObjects[activeObjects.length - 1];
      const spacing = (last.left - first.left) / (activeObjects.length - 1);
      activeObjects.forEach((obj, i) => {
        if (i !== 0 && i !== activeObjects.length - 1) {
          obj.set({ left: first.left + spacing * i });
        }
      });
      break;
  }
  canvas.renderAll();
  saveUndoState();
}

function setZoom(level) {
  canvas.setZoom(level);
  currentZoom = level;
  canvas.setWidth(595 * level);
  canvas.setHeight(842 * level);
  canvas.renderAll();
}

function showNotification(message) {
  const notif = document.createElement('div');
  notif.className = 'notification';
  notif.textContent = message;
  notif.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #667eea;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 3000);
}

function addProductToCanvas(product, x = null, y = null) {
  if (!canvas) {
    console.error('❌ Canvas henüz hazır değil!');
    return;
  }
  
  const normalPrice = parseFloat(product.normal_price) || 0;
  const discountPrice = parseFloat(product.discount_price) || 0;
  const discountPercent = normalPrice > 0 ? Math.round(((normalPrice - discountPrice) / normalPrice) * 100) : 0;

  // Get current theme preferences
  const theme = savedPages[currentPage]?.theme || {
    fontFamily: currentFont,
    productNameFontSize: 18,
    priceFontSize: 24,
    oldPriceFontSize: 14,
    textColor: '#333',
    priceColor: '#e74c3c',
    accentColor: currentColor
  };

  let posX = x !== null ? x : Math.random() * (canvas.width - 250) + 50;
  let posY = y !== null ? y : Math.random() * (canvas.height - 350) + 50;

  posX = Math.max(10, Math.min(posX, canvas.width - 200));
  posY = Math.max(10, Math.min(posY, canvas.height - 280));

  const imageUrl = product.image_url || 'https://via.placeholder.com/200';
  
  console.log('🖼️ Resim yükleniyor:', imageUrl);

  fabric.Image.fromURL(imageUrl, (img) => {
    if (!img) {
      console.error('❌ Resim yüklenemedi:', imageUrl);
      return;
    }
    img.scaleToWidth(150);
    img.scaleToHeight(150);

    const productName = new fabric.Text(product.name, {
      fontSize: theme.productNameFontSize,
      fontWeight: 'bold',
      fontFamily: theme.fontFamily,
      fill: theme.textColor,
      top: 160
    });

    const oldPrice = new fabric.Text(normalPrice.toFixed(2) + ' ₺', {
      fontSize: theme.oldPriceFontSize,
      fontFamily: theme.fontFamily,
      fill: '#999',
      textDecoration: 'line-through',
      top: 160
    });

    const newPrice = new fabric.Text(discountPrice.toFixed(2) + ' ₺', {
      fontSize: theme.priceFontSize,
      fontWeight: 'bold',
      fontFamily: theme.fontFamily,
      fill: theme.priceColor,
      top: 205
    });

    const discountBadge = new fabric.Rect({
      width: 80,
      height: 30,
      fill: theme.accentColor,
      rx: 5,
      ry: 5,
      top: -10,
      left: 70
    });

    const discountText = new fabric.Text(`%${discountPercent}`, {
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: theme.fontFamily,
      fill: '#ffffff',
      top: -3,
      left: 85
    });

    const pinIndicator = new fabric.Circle({
      radius: 8,
      fill: '#ff6b6b',
      top: -20,
      left: -20,
      visible: false,
      selectable: false
    });

    const sloganBtn = new fabric.Rect({
      width: 150,
      height: 25,
      fill: '#f5576c',
      rx: 5,
      ry: 5,
      top: 235,
      opacity: 0.9
    });

    const sloganBtnText = new fabric.Text('🤖 AI Slogan', {
      fontSize: 12,
      fontFamily: theme.fontFamily,
      fill: '#ffffff',
      top: 240,
      left: 40
    });

    const finalGroup = new fabric.Group(
      [img, productName, oldPrice, newPrice, discountBadge, discountText, pinIndicator, sloganBtn, sloganBtnText],
      {
        left: posX,
        top: posY,
        selectable: true,
        hasControls: true,
        lockRotation: false,
        cornerStyle: 'circle',
        cornerSize: 12,
        transparentCorners: false,
        cornerColor: '#667eea',
        borderColor: '#667eea',
        productData: product,
        id: product.id || Math.random().toString(36)
      }
    );

    finalGroup.on('mousedown', (e) => {
      if (e.target && e.target.top > 230) {
        getSloganSuggestions(product);
      }
    });

    canvas.add(finalGroup);
    canvas.renderAll();

    pages[currentPage].products.push(product.id);
    saveUndoState();
  }, { crossOrigin: 'anonymous' });
}

async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/upload-products', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (data.success) {
      if (data.redirect) {
        // Pre-approval'a yönlendir
        sessionStorage.setItem('preApprovalProducts', JSON.stringify(data.products || []));
        window.location.href = data.redirect;
      } else {
        // Fallback: Eski davranış
        alert(data.message);
        await loadProducts();
        autoPlaceProductsOnCanvas();
      }
    } else {
      alert(data.message || data.error);
    }
  } catch (error) {
    alert('Dosya yükleme hatası: ' + error.message);
  }
}

function autoPlaceProductsOnCanvas() {
  if (!canvas) {
    console.warn('Canvas not initialized yet.');
    return;
  }
  
  console.log('🔄 autoPlaceProductsOnCanvas başladı, ürün sayısı:', allProducts.length);
  
  // Canvas'ı temizle
  canvas.clear();
  canvas.backgroundColor = '#ffffff';
  
  // Ürünleri sayfa numarasına göre sırala (varsayılan: 1)
  const sortedProducts = [...allProducts].sort((a, b) => {
    const pageA = a.page_no || 1;
    const pageB = b.page_no || 1;
    return pageA - pageB;
  });
  
  // Her ürünü Canvas'a yerleştir
  sortedProducts.forEach((product, index) => {
    const col = index % 3;
    const row = Math.floor(index / 3);
    const x = col * 200 + 100;
    const y = row * 250 + 80;
    
    console.log(`📦 Ürün ${index + 1}: ${product.name} -> (${x}, ${y})`);
    addProductToCanvas(product, x, y);
  });
  
  // Canvas'ı yenile
  canvas.renderAll();
  console.log('✅ Canvas render edildi');
}

async function findImage(productIndex) {
  const product = allProducts[productIndex];

  try {
    const response = await fetch('/api/find-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: product.name,
        barcode: product.barcode || ''
      })
    });

    const data = await response.json();
    if (data.success) {
      if (data.stage === 'ai_search' && data.images && data.images.length > 0) {
        showImageModal(data.images, product);
      } else if (data.image_url) {
        // Existing image found, update product
        product.image_url = data.image_url;
        alert('Resim bulundu ve ürüne eklendi!');
        loadProducts();
      }
    } else {
      alert('Resim önerisi alınamadı: ' + (data.error || 'Bilinmeyen hata'));
    }
  } catch (error) {
    alert('Resim arama hatası: ' + error.message);
  }
}

function showImageModal(images, product) {
  const modal = document.getElementById('image-modal');
  const suggestions = document.getElementById('image-suggestions');
  suggestions.innerHTML = '';

  images.forEach(img => {
    const imgDiv = document.createElement('div');
    imgDiv.className = 'image-option';
    imgDiv.innerHTML = `<img src="${img.url}" alt="${img.term}"><p>${img.term}</p>`;
    imgDiv.onclick = () => selectImage(img.url, product);
    suggestions.appendChild(imgDiv);
  });

  modal.classList.remove('hidden');
}

async function selectImage(imageUrl, product) {
  try {
    const response = await fetch('/api/add-pending-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        barcode: product.barcode || '',
        product_name: product.name,
        image_url: imageUrl
      })
    });

    const data = await response.json();
    if (data.success) {
      alert('Resim admin onayına gönderildi! Onaylandıktan sonra kullanılabilir olacak.');
      document.getElementById('image-modal').classList.add('hidden');
      // Update product locally for preview
      product.image_url = imageUrl;
      loadProducts();
    }
  } catch (error) {
    alert('Resim seçme hatası: ' + error.message);
  }
}

async function getSloganSuggestions(product) {
  try {
    const response = await fetch('/api/generate-slogan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: product.name,
        normal_price: product.normal_price,
        discount_price: product.discount_price
      })
    });

    const data = await response.json();
    if (data.success && data.slogans.length > 0) {
      showSloganModal(data.slogans, product);
    } else {
      alert('Slogan önerisi alınamadı: ' + (data.error || 'OpenAI API key gerekli'));
    }
  } catch (error) {
    alert('Slogan alma hatası: ' + error.message);
  }
}

function showSloganModal(slogans, product) {
  const modal = document.getElementById('slogan-modal');
  const suggestions = document.getElementById('slogan-suggestions');
  suggestions.innerHTML = '';

  slogans.forEach(slogan => {
    const sloganDiv = document.createElement('div');
    sloganDiv.className = 'slogan-option';
    sloganDiv.textContent = slogan;
    sloganDiv.onclick = () => {
      // Add slogan to product on canvas
      const activeObject = canvas.getActiveObject();
      if (activeObject && activeObject.productData) {
        const sloganText = new fabric.Text(slogan, {
          fontSize: 12,
          fontFamily: currentFont,
          fill: '#666',
          top: activeObject.height - 20,
          left: 0,
          width: 150,
          textAlign: 'center'
        });
        activeObject.addWithUpdate(sloganText);
        canvas.renderAll();
      }
      navigator.clipboard.writeText(slogan);
      alert('Slogan ürüne eklendi ve panoya kopyalandı: ' + slogan);
      modal.classList.add('hidden');
    };
    suggestions.appendChild(sloganDiv);
  });

  modal.classList.remove('hidden');
}

function addNewPage() {
  pages.push({ products: [], title: `${pages.length + 1}. Sayfa` });
  renderPageTabs();
  switchPage(pages.length - 1);
}

function renderPageTabs() {
  const tabsContainer = document.getElementById('pages-tabs');
  tabsContainer.innerHTML = '';

  pages.forEach((page, index) => {
    const tab = document.createElement('button');
    tab.className = 'page-tab' + (index === currentPage ? ' active' : '');
    tab.textContent = page.title;
    tab.dataset.page = index;
    tab.onclick = () => switchPage(index);
    tabsContainer.appendChild(tab);
  });
}

function switchPage(pageIndex) {
  currentPage = pageIndex;
  canvas.clear();
  canvas.backgroundColor = '#ffffff';
  renderPageTabs();
}

function applyStyle(applyToAll) {
  if (applyToAll) {
    alert('Font ve renk tüm sayfalara uygulandı! (Gelecek sürümde aktif)');
  } else {
    alert('Font ve renk bu sayfaya uygulandı! (Gelecek sürümde aktif)');
  }
}

async function generateAutoBrochure() {
  if (allProducts.length === 0) {
    alert('Önce ürün yüklemelisiniz!');
    return;
  }

  try {
    // Add index to each product for tracking
    const productsWithIndex = allProducts.map((p, i) => ({ ...p, index: i }));
    
    const response = await fetch('/api/auto-layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products: productsWithIndex })
    });

    const data = await response.json();
    if (data.success && data.pages && data.pages.length > 0) {
      // Clear existing pages and create new ones based on AI layout
      pages = [];
      canvas.clear();
      
      data.pages.forEach((page, pageIndex) => {
        pages.push({
          products: page.product_indices || [],
          title: page.title || `Sayfa ${pageIndex + 1}`
        });
      });
      
      // Switch to first page and render products
      currentPage = 0;
      renderPageTabs();
      
      // Add products to first page canvas
      if (pages[0].products.length > 0) {
        pages[0].products.forEach((productIndex, i) => {
          if (productIndex < allProducts.length) {
            const product = allProducts[productIndex];
            const x = (i % 3) * 200 + 50;
            const y = Math.floor(i / 3) * 280 + 50;
            setTimeout(() => addProductToCanvas(product, x, y), i * 100);
          }
        });
      }
      
      alert(`AI otomatik broşür oluşturdu! ${data.pages.length} sayfa hazırlandı. İlk sayfa en yüksek indirimli ürünlerle başlıyor!`);
    } else {
      alert('Otomatik broşür oluşturulamadı: ' + (data.error || 'OpenAI API key gerekli'));
    }
  } catch (error) {
    alert('Hata: ' + error.message);
  }
}

function downloadPDF() {
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4'
  });

  const dataUrl = canvas.toDataURL({ format: 'png', multiplier: 2 });
  pdf.addImage(dataUrl, 'PNG', 0, 0, 595, 842);

  if (pages.length > 1) {
    for (let i = 1; i < pages.length; i++) {
      pdf.addPage();
    }
  }

  pdf.save('market-brosuru.pdf');
}

function downloadInstagram() {
  const zip = { files: [] };

  const square = new fabric.Canvas(null, {
    width: 1080,
    height: 1080,
    backgroundColor: '#ffffff'
  });

  const originalObjects = canvas.getObjects();
  const scale = 1080 / canvas.width;

  originalObjects.forEach(obj => {
    const cloned = fabric.util.object.clone(obj);
    cloned.scaleX *= scale;
    cloned.scaleY *= scale;
    cloned.left *= scale;
    cloned.top *= scale;
    square.add(cloned);
  });

  square.renderAll();

  const link = document.createElement('a');
  link.download = 'instagram-kare-1080x1080.png';
  link.href = square.toDataURL({ format: 'png', multiplier: 2 });
  link.click();

  alert('Instagram kare formatı indirildi! Reels formatı için geliştirilme aşamasında.');
}

// Enhanced Control Functions
function setupThemeControls() {
  // Create theme selector if not exists
  let themeContainer = document.getElementById('theme-container');
  if (!themeContainer) {
    const toolbar = document.querySelector('.editor-toolbar');
    if (!toolbar) return;
    
    themeContainer = document.createElement('div');
    themeContainer.id = 'theme-container';
    themeContainer.className = 'theme-controls';
    themeContainer.innerHTML = `
      <label>Theme:</label>
      <select id="theme-preset">
        <option value="custom">Custom</option>
        <option value="Professional">Professional</option>
        <option value="Colorful">Colorful</option>
        <option value="Minimal">Minimal</option>
        <option value="Modern">Modern</option>
      </select>
      <input type="number" id="name-font-size" placeholder="Name Size" value="18" min="8" max="48">
      <input type="number" id="price-font-size" placeholder="Price Size" value="24" min="8" max="48">
      <input type="color" id="text-color-picker" value="#333333">
      <input type="color" id="price-color-picker" value="#e74c3c">
      <button id="apply-theme-page">Apply to Page</button>
      <button id="apply-theme-all">Apply to All</button>
    `;
    toolbar.appendChild(themeContainer);
  }
  
  // Add event listeners
  document.getElementById('theme-preset')?.addEventListener('change', (e) => {
    const preset = themePresets[e.target.value];
    if (preset) {
      document.getElementById('font-select').value = preset.font;
      document.getElementById('text-color-picker').value = preset.textColor;
      document.getElementById('price-color-picker').value = preset.priceColor;
      document.getElementById('color-picker').value = preset.accent;
      currentFont = preset.font;
      currentColor = preset.accent;
    }
  });
  
  document.getElementById('apply-theme-page')?.addEventListener('click', () => {
    applyThemeToPage(currentPage);
  });
  
  document.getElementById('apply-theme-all')?.addEventListener('click', () => {
    for (let i = 0; i < pages.length; i++) {
      applyThemeToPage(i);
    }
    showNotification('Theme applied to all pages');
  });
}

function applyThemeToPage(pageIndex) {
  const theme = {
    fontFamily: document.getElementById('font-select')?.value || currentFont,
    productNameFontSize: parseInt(document.getElementById('name-font-size')?.value || 18),
    priceFontSize: parseInt(document.getElementById('price-font-size')?.value || 24),
    oldPriceFontSize: 14,
    textColor: document.getElementById('text-color-picker')?.value || '#333',
    priceColor: document.getElementById('price-color-picker')?.value || '#e74c3c',
    accentColor: document.getElementById('color-picker')?.value || currentColor
  };
  
  savedPages[pageIndex] = savedPages[pageIndex] || {};
  savedPages[pageIndex].theme = theme;
  
  // Update existing products on canvas if current page
  if (pageIndex === currentPage) {
    canvas.getObjects().forEach(obj => {
      if (obj.productData) {
        updateProductStyle(obj, theme);
      }
    });
    canvas.renderAll();
  }
  
  // Save to database
  saveThemePreference(theme, pageIndex === currentPage, pageIndex);
}

function updateProductStyle(obj, theme) {
  const items = obj.getObjects();
  items.forEach(item => {
    if (item.type === 'text') {
      item.set({
        fontFamily: theme.fontFamily,
        fill: item.text.includes('₺') ? theme.priceColor : theme.textColor
      });
      if (item.text === obj.productData?.name) {
        item.set({ fontSize: theme.productNameFontSize });
      }
    } else if (item.type === 'rect' && item.fill !== '#f5576c') {
      item.set({ fill: theme.accentColor });
    }
  });
  obj.dirty = true;
}

function setupAlignmentControls() {
  let alignContainer = document.getElementById('align-container');
  if (!alignContainer) {
    const toolbar = document.querySelector('.editor-toolbar');
    if (!toolbar) return;
    
    alignContainer = document.createElement('div');
    alignContainer.id = 'align-container';
    alignContainer.className = 'align-controls';
    alignContainer.innerHTML = `
      <button id="align-left" title="Align Left">⬅</button>
      <button id="align-center" title="Align Center">⬌</button>
      <button id="align-right" title="Align Right">➡</button>
      <button id="align-distribute" title="Distribute">↔</button>
      <button id="toggle-grid" title="Toggle Grid">⚏</button>
      <button id="toggle-rulers" title="Toggle Rulers">📏</button>
    `;
    toolbar.appendChild(alignContainer);
  }
  
  document.getElementById('align-left')?.addEventListener('click', () => alignObjects('left'));
  document.getElementById('align-center')?.addEventListener('click', () => alignObjects('center'));
  document.getElementById('align-right')?.addEventListener('click', () => alignObjects('right'));
  document.getElementById('align-distribute')?.addEventListener('click', () => alignObjects('distribute'));
  
  document.getElementById('toggle-grid')?.addEventListener('click', () => {
    gridSnapEnabled = !gridSnapEnabled;
    document.getElementById('toggle-grid').classList.toggle('active');
    showNotification(`Grid snap ${gridSnapEnabled ? 'enabled' : 'disabled'}`);
  });
  
  document.getElementById('toggle-rulers')?.addEventListener('click', () => {
    showRulers = !showRulers;
    document.getElementById('toggle-rulers').classList.toggle('active');
    canvas.clear();
    initializeCanvas();
    showNotification(`Rulers ${showRulers ? 'enabled' : 'disabled'}`);
  });
}

function setupZoomControls() {
  let zoomContainer = document.getElementById('zoom-container');
  if (!zoomContainer) {
    const toolbar = document.querySelector('.editor-toolbar');
    if (!toolbar) return;
    
    zoomContainer = document.createElement('div');
    zoomContainer.id = 'zoom-container';
    zoomContainer.className = 'zoom-controls';
    zoomContainer.innerHTML = `
      <button id="zoom-50">50%</button>
      <button id="zoom-75">75%</button>
      <button id="zoom-100" class="active">100%</button>
      <button id="zoom-125">125%</button>
      <button id="zoom-150">150%</button>
    `;
    toolbar.appendChild(zoomContainer);
  }
  
  const zoomButtons = {
    'zoom-50': 0.5,
    'zoom-75': 0.75,
    'zoom-100': 1.0,
    'zoom-125': 1.25,
    'zoom-150': 1.5
  };
  
  Object.entries(zoomButtons).forEach(([id, level]) => {
    document.getElementById(id)?.addEventListener('click', () => {
      document.querySelectorAll('.zoom-controls button').forEach(btn => btn.classList.remove('active'));
      document.getElementById(id).classList.add('active');
      setZoom(level);
    });
  });
}

async function saveThemePreference(theme, pageSpecific, pageNumber) {
  try {
    await fetch('/api/theme-preference', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        theme_data: theme,
        page_specific: pageSpecific,
        page_number: pageNumber
      })
    });
  } catch (error) {
    console.error('Error saving theme preference:', error);
  }
}

async function loadEditorPreferences() {
  try {
    const response = await fetch('/api/editor-preferences');
    const data = await response.json();
    if (data.success) {
      editorPrefs = data.preferences;
      gridSnapEnabled = editorPrefs.grid_snap_enabled;
      gridSize = editorPrefs.grid_size;
      currentZoom = editorPrefs.zoom_level;
      showRulers = editorPrefs.show_rulers;
    }
  } catch (error) {
    console.error('Error loading editor preferences:', error);
  }
}

// New functions for AI brochure generation and templates
let uploadedLogoFile = null;
let selectedTemplateUrl = null;

function handleLogoUpload(e) {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    uploadedLogoFile = file;
    const reader = new FileReader();
    reader.onload = function(event) {
      const previewDiv = document.getElementById('logo-preview');
      if (previewDiv) {
        previewDiv.innerHTML = `<img src="${event.target.result}" style="max-width: 100%; max-height: 60px; object-fit: contain;">`;
      }
    };
    reader.readAsDataURL(file);
  }
}

function handleTemplateUpload(e) {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    // Show template modal with options
    document.getElementById('template-modal').classList.remove('hidden');
    document.getElementById('template-modal').classList.add('show');
    
    // Store file temporarily
    window.templateFile = file;
  }
}

async function applySelectedTemplate() {
  if (!window.templateFile) return;
  
  const option = document.querySelector('input[name="template-option"]:checked').value;
  const applyToAll = option === 'all-pages';
  
  // Upload template
  const formData = new FormData();
  formData.append('file', window.templateFile);
  formData.append('apply_to_all', applyToAll);
  formData.append('page_number', currentPage);
  
  try {
    const response = await fetch('/api/upload-template', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    if (data.success) {
      selectedTemplateUrl = data.image_url;
      
      // Apply template to canvas as background
      if (canvas) {
        fabric.Image.fromURL(selectedTemplateUrl, (img) => {
          // Scale image to fit canvas
          const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
          img.scale(scale);
          img.set({
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          });
          
          // Add to canvas as background
          canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas));
        });
      }
      
      // Close modal
      document.getElementById('template-modal').classList.add('hidden');
      document.getElementById('template-modal').classList.remove('show');
      
      showNotification('✅ Şablon başarıyla uygulandı!');
    } else {
      alert('Şablon yüklenirken hata: ' + data.error);
    }
  } catch (error) {
    alert('Şablon yükleme hatası: ' + error.message);
  }
  
  window.templateFile = null;
}

async function generateAIBrochure() {
  // Show loading overlay
  const loadingOverlay = document.getElementById('loading-overlay');
  if (loadingOverlay) {
    loadingOverlay.classList.remove('hidden');
    loadingOverlay.classList.add('show');
  }
  
  // Gather company info from input fields
  const companyInfo = {
    name: document.getElementById('company-name')?.value || '',
    address: document.getElementById('company-address')?.value || '',
    phone: document.getElementById('company-phone')?.value || '',
    email: document.getElementById('company-email')?.value || ''
  };
  
  // Get products
  const products = allProducts.length > 0 ? allProducts : pages[currentPage].products;
  
  if (products.length === 0) {
    if (loadingOverlay) {
      loadingOverlay.classList.add('hidden');
      loadingOverlay.classList.remove('show');
    }
    alert('Lütfen önce ürünleri yükleyin!');
    return;
  }
  
  try {
    // Call AI generation endpoint
    const response = await fetch('/api/generate-complete-brochure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_info: companyInfo,
        products: products.slice(0, 20) // Limit to 20 products for AI
      })
    });
    
    const data = await response.json();
    if (data.success) {
      const brochure = data.brochure;
      
      // Apply theme
      if (brochure.theme) {
        currentColor = brochure.theme.primary_color || '#667eea';
        currentFont = brochure.theme.font || 'Arial';
        
        // Update UI elements
        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) colorPicker.value = currentColor;
        
        const fontSelect = document.getElementById('font-select');
        if (fontSelect) fontSelect.value = currentFont;
      }
      
      // Create pages based on AI suggestions
      if (brochure.pages && brochure.pages.length > 0) {
        pages = [];
        
        brochure.pages.forEach((pageData, index) => {
          // Find matching products
          const pageProducts = [];
          if (pageData.products) {
            pageData.products.forEach(productName => {
              const product = allProducts.find(p => p.name === productName);
              if (product) pageProducts.push(product);
            });
          }
          
          pages.push({
            title: pageData.title || `Sayfa ${index + 1}`,
            products: pageProducts,
            locked: false,
            header: pageData.header,
            footer: pageData.footer
          });
        });
        
        // Update canvas with first page
        currentPage = 0;
        updateCanvas();
        
        // Add header and footer if suggested
        if (pages[0].header && pages[0].header.show) {
          addHeaderToCanvas(pages[0].header.content, companyInfo);
        }
        
        if (pages[0].footer && pages[0].footer.show) {
          addFooterToCanvas(pages[0].footer.content);
        }
        
        // Auto-layout products
        autoLayoutProducts(pages[0].products, brochure.pages[0].layout || 'grid');
      }
      
      // Show suggestions
      if (brochure.suggestions && brochure.suggestions.length > 0) {
        showNotification('💡 Öneriler: ' + brochure.suggestions.join(', '));
      }
      
    } else {
      alert('AI broşür oluşturma hatası: ' + (data.error || 'Bilinmeyen hata'));
    }
    
  } catch (error) {
    alert('AI broşür oluşturma hatası: ' + error.message);
  } finally {
    // Hide loading overlay
    if (loadingOverlay) {
      loadingOverlay.classList.add('hidden');
      loadingOverlay.classList.remove('show');
    }
  }
}

function addHeaderToCanvas(content, companyInfo) {
  if (!canvas) return;
  
  // Add header text
  const headerText = new fabric.Text(content, {
    left: canvas.width / 2,
    top: 30,
    fontSize: 24,
    fontFamily: currentFont,
    fill: currentColor,
    fontWeight: 'bold',
    originX: 'center'
  });
  
  canvas.add(headerText);
  
  // Add company info below header
  if (companyInfo.name) {
    const companyText = new fabric.Text(companyInfo.name, {
      left: canvas.width / 2,
      top: 60,
      fontSize: 18,
      fontFamily: currentFont,
      fill: '#666',
      originX: 'center'
    });
    canvas.add(companyText);
  }
  
  // Add logo if uploaded
  if (uploadedLogoFile) {
    const reader = new FileReader();
    reader.onload = function(e) {
      fabric.Image.fromURL(e.target.result, (img) => {
        img.scale(0.2); // Scale logo
        img.set({
          left: 50,
          top: 20
        });
        canvas.add(img);
      });
    };
    reader.readAsDataURL(uploadedLogoFile);
  }
}

function addFooterToCanvas(content) {
  if (!canvas) return;
  
  const footerText = new fabric.Text(content, {
    left: canvas.width / 2,
    top: canvas.height - 40,
    fontSize: 12,
    fontFamily: currentFont,
    fill: '#999',
    originX: 'center'
  });
  
  canvas.add(footerText);
}

function autoLayoutProducts(products, layoutType = 'grid') {
  if (!canvas || !products || products.length === 0) return;
  
  const startY = 120; // Start below header
  const endY = canvas.height - 60; // End before footer
  
  if (layoutType === 'grid') {
    const cols = 3;
    const rows = Math.ceil(products.length / cols);
    const cellWidth = canvas.width / cols;
    const cellHeight = (endY - startY) / rows;
    
    products.forEach((product, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const x = col * cellWidth + cellWidth / 2;
      const y = startY + row * cellHeight + cellHeight / 2;
      
      addProductToCanvas(product, x, y);
    });
  } else if (layoutType === 'featured') {
    // First product featured large
    if (products[0]) {
      addProductToCanvas(products[0], canvas.width / 2, startY + 100, 1.5);
    }
    
    // Rest in smaller grid
    const remainingProducts = products.slice(1);
    const cols = 4;
    const startGridY = startY + 250;
    const cellWidth = canvas.width / cols;
    
    remainingProducts.forEach((product, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const x = col * cellWidth + cellWidth / 2;
      const y = startGridY + row * 120;
      
      addProductToCanvas(product, x, y, 0.8);
    });
  }
}

function addProductToCanvas(product, x, y, scale = 1.0) {
  if (!canvas) return;
  
  // Create product group
  const group = new fabric.Group([], {
    left: x,
    top: y,
    originX: 'center',
    originY: 'center'
  });
  
  // Add product image if available
  if (product.image_url) {
    fabric.Image.fromURL(product.image_url, (img) => {
      img.scale(0.15 * scale);
      group.addWithUpdate(img);
    });
  }
  
  // Add product name
  const nameText = new fabric.Text(product.name, {
    fontSize: 14 * scale,
    fontFamily: currentFont,
    fill: '#333',
    textAlign: 'center',
    top: 60 * scale
  });
  group.addWithUpdate(nameText);
  
  // Add price
  const priceText = new fabric.Text(`${product.discount_price || product.normal_price}₺`, {
    fontSize: 20 * scale,
    fontFamily: currentFont,
    fill: currentColor,
    fontWeight: 'bold',
    textAlign: 'center',
    top: 80 * scale
  });
  group.addWithUpdate(priceText);
  
  group.data = product;
  canvas.add(group);
}

function showNotification(message, duration = 3000) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: ${currentColor};
    color: white;
    padding: 15px 25px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => document.body.removeChild(notification), 300);
  }, duration);
}
