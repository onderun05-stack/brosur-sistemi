// Multi-Page Brochure Editor with Full Features
class BrochureEditor {
    constructor() {
        this.canvases = {};
        this.currentPage = 1;
        this.totalPages = 1;
        this.products = [];
        this.parkingArea = [];
        this.pageSettings = {};
        this.undoStacks = {};
        this.redoStacks = {};
        this.pinnedProducts = new Set();
        this.lockedPages = new Set();
        this.currentTheme = 'Modern';
        this.gridSnapEnabled = true;
        this.gridSize = 20;
        this.isDraggingTopark = false;
        
        // Initialize
        this.init();
    }
    
    init() {
        this.createPage(1);
        this.setupEventListeners();
        this.setupParkingArea();
        this.loadPreferences();
    }
    
    createPage(pageNum) {
        // Create canvas container if doesn't exist
        if (!document.getElementById(`canvas-page-${pageNum}`)) {
            const canvasContainer = document.createElement('div');
            canvasContainer.id = `canvas-container-${pageNum}`;
            canvasContainer.className = 'canvas-page';
            canvasContainer.style.display = pageNum === 1 ? 'block' : 'none';
            canvasContainer.innerHTML = `<canvas id="canvas-page-${pageNum}"></canvas>`;
            document.getElementById('canvas-area').appendChild(canvasContainer);
        }
        
        // Initialize Fabric.js canvas
        const canvas = new fabric.Canvas(`canvas-page-${pageNum}`, {
            width: 800,
            height: 600,
            backgroundColor: 'white',
            preserveObjectStacking: true
        });
        
        // Setup canvas events
        this.setupCanvasEvents(canvas, pageNum);
        
        // Store canvas
        this.canvases[pageNum] = canvas;
        
        // Initialize page settings
        this.pageSettings[pageNum] = {
            title: `Sayfa ${pageNum}`,
            locked: false,
            theme: 'Modern',
            font: 'Arial',
            textColor: '#333333',
            priceColor: '#e74c3c',
            accentColor: '#667eea',
            products: []
        };
        
        // Initialize undo/redo stacks
        this.undoStacks[pageNum] = [];
        this.redoStacks[pageNum] = [];
        
        // Add page tab
        this.addPageTab(pageNum);
        
        return canvas;
    }
    
    setupCanvasEvents(canvas, pageNum) {
        // Object modified
        canvas.on('object:modified', (e) => {
            this.saveState(pageNum);
            this.updateProductPosition(e.target, pageNum);
        });
        
        // Object removed (send to parking)
        canvas.on('object:removed', (e) => {
            if (!this.isDraggingTopark && e.target && e.target.productData) {
                this.sendToParkingArea(e.target.productData);
            }
        });
        
        // Drop from parking area
        canvas.on('drop', (e) => {
            const draggedData = e.e.dataTransfer.getData('product');
            if (draggedData) {
                const product = JSON.parse(draggedData);
                const pointer = canvas.getPointer(e.e);
                this.addProductToCanvas(product, pageNum, pointer.x, pointer.y);
                this.removeFromParking(product.id);
            }
        });
        
        // Drag over
        canvas.on('dragover', (e) => {
            e.e.preventDefault();
        });
        
        // Selection
        canvas.on('selection:created', (e) => {
            this.showProductOptions(e.selected[0]);
        });
        
        // Double click for quick edit
        canvas.on('mouse:dblclick', (e) => {
            if (e.target && e.target.type === 'group') {
                this.editProductDetails(e.target);
            }
        });
        
        // Grid snapping
        canvas.on('object:moving', (e) => {
            if (this.gridSnapEnabled) {
                const obj = e.target;
                obj.set({
                    left: Math.round(obj.left / this.gridSize) * this.gridSize,
                    top: Math.round(obj.top / this.gridSize) * this.gridSize
                });
            }
        });
    }
    
    setupParkingArea() {
        const parkingDiv = document.createElement('div');
        parkingDiv.id = 'parking-area';
        parkingDiv.className = 'parking-area';
        parkingDiv.innerHTML = `
            <div class="parking-header">
                <h3>🅿️ Park Alanı</h3>
                <span class="parking-count">0 ürün</span>
            </div>
            <div class="parking-products" id="parking-products"></div>
            <div class="parking-actions">
                <button onclick="editor.autoDistributeParking()">Otomatik Dağıt</button>
                <button onclick="editor.clearParking()">Tümünü Sil</button>
            </div>
        `;
        document.body.appendChild(parkingDiv);
        
        // Make parking area droppable
        const parkingProducts = document.getElementById('parking-products');
        parkingProducts.addEventListener('dragover', (e) => {
            e.preventDefault();
            parkingProducts.classList.add('drag-over');
        });
        
        parkingProducts.addEventListener('dragleave', () => {
            parkingProducts.classList.remove('drag-over');
        });
        
        parkingProducts.addEventListener('drop', (e) => {
            e.preventDefault();
            parkingProducts.classList.remove('drag-over');
            
            const productData = e.dataTransfer.getData('product');
            if (productData) {
                const product = JSON.parse(productData);
                this.sendToParkingArea(product);
                
                // Remove from canvas
                const canvas = this.canvases[this.currentPage];
                const objects = canvas.getObjects();
                objects.forEach(obj => {
                    if (obj.productData && obj.productData.id === product.id) {
                        canvas.remove(obj);
                    }
                });
            }
        });
    }
    
    sendToParkingArea(product) {
        if (!this.parkingArea.find(p => p.id === product.id)) {
            this.parkingArea.push(product);
            this.renderParkingArea();
        }
    }
    
    renderParkingArea() {
        const parkingProducts = document.getElementById('parking-products');
        parkingProducts.innerHTML = '';
        
        this.parkingArea.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'parking-product';
            productCard.draggable = true;
            productCard.innerHTML = `
                <img src="${product.image_url || '/api/placeholder/80/80'}" alt="${product.name}">
                <div class="parking-product-info">
                    <div class="name">${product.name}</div>
                    <div class="price">${product.discount_price}₺</div>
                </div>
                <button class="remove-btn" onclick="editor.removeFromParking('${product.id}')">×</button>
            `;
            
            // Make draggable
            productCard.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('product', JSON.stringify(product));
                e.dataTransfer.effectAllowed = 'move';
            });
            
            parkingProducts.appendChild(productCard);
        });
        
        // Update count
        document.querySelector('.parking-count').textContent = `${this.parkingArea.length} ürün`;
    }
    
    removeFromParking(productId) {
        this.parkingArea = this.parkingArea.filter(p => p.id !== productId);
        this.renderParkingArea();
    }
    
    clearParking() {
        if (confirm('Park alanındaki tüm ürünler silinecek. Emin misiniz?')) {
            this.parkingArea = [];
            this.renderParkingArea();
        }
    }
    
    autoDistributeParking() {
        if (this.parkingArea.length === 0) {
            alert('Park alanında ürün yok');
            return;
        }
        
        const itemsPerPage = 12;
        let currentPageIndex = this.currentPage;
        let itemsOnPage = this.pageSettings[currentPageIndex].products.length;
        
        [...this.parkingArea].forEach(product => {
            if (itemsOnPage >= itemsPerPage) {
                currentPageIndex++;
                if (!this.canvases[currentPageIndex]) {
                    this.createPage(currentPageIndex);
                }
                itemsOnPage = 0;
            }
            
            const x = (itemsOnPage % 4) * 200 + 50;
            const y = Math.floor(itemsOnPage / 4) * 180 + 50;
            
            this.addProductToCanvas(product, currentPageIndex, x, y);
            this.removeFromParking(product.id);
            itemsOnPage++;
        });
        
        alert('Ürünler sayfalara dağıtıldı');
    }
    
    addProductToCanvas(product, pageNum, x = 100, y = 100) {
        const canvas = this.canvases[pageNum];
        if (!canvas) return;
        
        // Ghost Name Normalizer entegrasyonu (Madde 6)
        // Ürün adını normalize et (API'dan temizlenmiş isim al)
        this.normalizeProductName(product).then(normalizedProduct => {
            // Create product group with normalized name
            const group = this.createProductCard(normalizedProduct, x, y);
            
            // Add to canvas
            canvas.add(group);
            canvas.renderAll();
            
            // Add to page products
            if (!this.pageSettings[pageNum].products.find(p => p.id === normalizedProduct.id)) {
                this.pageSettings[pageNum].products.push(normalizedProduct);
            }
            
            // Save state
            this.saveState(pageNum);
            
            // Ghost analizi tetikle
            this.triggerGhostAnalysis(pageNum);
        }).catch(() => {
            // Fallback: Normal ekleme
            const group = this.createProductCard(product, x, y);
            canvas.add(group);
            canvas.renderAll();
            
            if (!this.pageSettings[pageNum].products.find(p => p.id === product.id)) {
                this.pageSettings[pageNum].products.push(product);
            }
            this.saveState(pageNum);
        });
    }
    
    /**
     * Ghost Name Normalizer API çağrısı (Madde 6)
     * Ürün adını normalize eder
     */
    async normalizeProductName(product) {
        if (!product.name || product.name.length <= 26) {
            return product; // Kısa isimler için normalizeye gerek yok
        }
        
        try {
            const response = await fetch('/api/ghost/normalize-name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: product.name })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.normalized) {
                    return {
                        ...product,
                        original_name: product.name,
                        name: data.normalized
                    };
                }
            }
        } catch (error) {
            console.warn('Ghost name normalizer error:', error);
        }
        
        return product;
    }
    
    /**
     * Ghost sayfa analizi tetikle
     */
    async triggerGhostAnalysis(pageNum) {
        try {
            const pageData = this.getPageData(pageNum);
            const response = await fetch('/api/ghost/analyze-page', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pageData)
            });
            
            if (response.ok) {
                const analysis = await response.json();
                if (analysis.success) {
                    // Stil önerilerini uygula
                    this.applyGhostStyleHints(analysis.data, pageNum);
                    
                    // Ürün uyarılarını göster
                    if (analysis.data.product_warnings) {
                        this.showProductWarnings(analysis.data.product_warnings, pageNum);
                    }
                }
            }
        } catch (error) {
            console.warn('Ghost analysis error:', error);
        }
    }
    
    /**
     * Sayfa verisini hazırla
     */
    getPageData(pageNum) {
        const canvas = this.canvases[pageNum];
        const settings = this.pageSettings[pageNum];
        
        return {
            id: pageNum,
            layout: settings.layout || 'grid_4x4',
            locked: settings.locked,
            products: settings.products.map(p => ({
                id: p.id,
                name: p.name,
                price: p.discount_price,
                image_url: p.image_url,
                image_quality: p.image_quality || 'medium',
                position: this.getProductPosition(canvas, p.id)
            })),
            page_size: {
                width: canvas.width,
                height: canvas.height
            }
        };
    }
    
    /**
     * Ürün pozisyonunu al
     */
    getProductPosition(canvas, productId) {
        const obj = canvas.getObjects().find(o => o.productData && o.productData.id === productId);
        if (obj) {
            const bounds = obj.getBoundingRect();
            return {
                x: bounds.left,
                y: bounds.top,
                width: bounds.width,
                height: bounds.height
            };
        }
        return { x: 0, y: 0, width: 150, height: 180 };
    }
    
    createProductCard(product, x, y) {
        // Product image
        const imageObj = new fabric.Image.fromURL(
            product.image_url || '/api/placeholder/150/150',
            (img) => {
                img.set({
                    width: 150,
                    height: 150,
                    originX: 'center',
                    originY: 'center'
                });
            }
        );
        
        // Product name
        const nameText = new fabric.Text(product.name, {
            fontSize: 14,
            fontFamily: this.pageSettings[this.currentPage].font,
            fill: this.pageSettings[this.currentPage].textColor,
            originX: 'center',
            originY: 'top',
            textAlign: 'center'
        });
        
        // Old price (strikethrough)
        const oldPriceText = new fabric.Text(`${product.normal_price}₺`, {
            fontSize: 12,
            fontFamily: this.pageSettings[this.currentPage].font,
            fill: '#999',
            originX: 'center',
            originY: 'top',
            textDecoration: 'line-through'
        });
        
        // Discount price
        const discountPriceText = new fabric.Text(`${product.discount_price}₺`, {
            fontSize: 18,
            fontFamily: this.pageSettings[this.currentPage].font,
            fill: this.pageSettings[this.currentPage].priceColor,
            fontWeight: 'bold',
            originX: 'center',
            originY: 'top'
        });
        
        // Create group
        const group = new fabric.Group([imageObj, nameText, oldPriceText, discountPriceText], {
            left: x,
            top: y,
            hasControls: true,
            hasBorders: true,
            lockRotation: true,
            productData: product
        });
        
        // Position texts
        nameText.top = 80;
        oldPriceText.top = 100;
        discountPriceText.top = 115;
        
        return group;
    }
    
    switchToPage(pageNum) {
        // Hide current page
        const currentContainer = document.getElementById(`canvas-container-${this.currentPage}`);
        if (currentContainer) {
            currentContainer.style.display = 'none';
        }
        
        // Show new page
        let newContainer = document.getElementById(`canvas-container-${pageNum}`);
        if (!newContainer) {
            // Create page if doesn't exist
            this.createPage(pageNum);
            newContainer = document.getElementById(`canvas-container-${pageNum}`);
        }
        newContainer.style.display = 'block';
        
        // Update current page
        this.currentPage = pageNum;
        
        // Update tabs
        this.updatePageTabs();
        
        // Render canvas
        if (this.canvases[pageNum]) {
            this.canvases[pageNum].renderAll();
        }
    }
    
    addPageTab(pageNum) {
        const tabsContainer = document.getElementById('page-tabs');
        const tab = document.createElement('div');
        tab.className = 'page-tab';
        tab.dataset.page = pageNum;
        tab.innerHTML = `
            <span class="tab-title">Sayfa ${pageNum}</span>
            ${this.lockedPages.has(pageNum) ? '<span class="lock-icon">🔒</span>' : ''}
            <button class="close-tab" onclick="editor.removePage(${pageNum})">×</button>
        `;
        
        tab.addEventListener('click', (e) => {
            if (!e.target.classList.contains('close-tab')) {
                this.switchToPage(pageNum);
            }
        });
        
        // Add before the "add page" button
        const addPageBtn = document.getElementById('add-page-btn');
        tabsContainer.insertBefore(tab, addPageBtn);
    }
    
    updatePageTabs() {
        const tabs = document.querySelectorAll('.page-tab');
        tabs.forEach(tab => {
            const pageNum = parseInt(tab.dataset.page);
            if (pageNum === this.currentPage) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }
    
    addNewPage() {
        this.totalPages++;
        this.createPage(this.totalPages);
        this.switchToPage(this.totalPages);
    }
    
    removePage(pageNum) {
        if (this.totalPages === 1) {
            alert('Son sayfa silinemez');
            return;
        }
        
        if (confirm(`Sayfa ${pageNum} silinecek. Emin misiniz?`)) {
            // Move products to parking
            const pageProducts = this.pageSettings[pageNum].products || [];
            pageProducts.forEach(product => {
                this.sendToParkingArea(product);
            });
            
            // Remove canvas
            const container = document.getElementById(`canvas-container-${pageNum}`);
            if (container) {
                container.remove();
            }
            
            // Remove tab
            const tab = document.querySelector(`[data-page="${pageNum}"]`);
            if (tab) {
                tab.remove();
            }
            
            // Clean up
            delete this.canvases[pageNum];
            delete this.pageSettings[pageNum];
            delete this.undoStacks[pageNum];
            delete this.redoStacks[pageNum];
            
            // Switch to first page
            if (this.currentPage === pageNum) {
                this.switchToPage(1);
            }
            
            this.totalPages--;
        }
    }
    
    togglePageLock(pageNum = null) {
        const page = pageNum || this.currentPage;
        const canvas = this.canvases[page];
        
        if (this.lockedPages.has(page)) {
            // Unlock
            this.lockedPages.delete(page);
            this.pageSettings[page].locked = false;
            canvas.selection = true;
            canvas.getObjects().forEach(obj => {
                obj.selectable = true;
                obj.evented = true;
            });
        } else {
            // Lock
            this.lockedPages.add(page);
            this.pageSettings[page].locked = true;
            canvas.selection = false;
            canvas.discardActiveObject();
            canvas.getObjects().forEach(obj => {
                obj.selectable = false;
                obj.evented = false;
            });
        }
        
        canvas.renderAll();
        this.updatePageTabs();
    }
    
    applyThemeToPage(theme, pageNum = null) {
        const page = pageNum || this.currentPage;
        const settings = this.getThemeSettings(theme);
        
        // Update page settings
        Object.assign(this.pageSettings[page], settings);
        
        // Apply to all products on page
        const canvas = this.canvases[page];
        canvas.getObjects().forEach(obj => {
            if (obj.type === 'group') {
                const items = obj.getObjects();
                items.forEach(item => {
                    if (item.type === 'text') {
                        item.set({
                            fontFamily: settings.font,
                            fill: item.text.includes('₺') ? settings.priceColor : settings.textColor
                        });
                    }
                });
            }
        });
        
        canvas.renderAll();
    }
    
    getThemeSettings(theme) {
        const themes = {
            'Modern': {
                font: 'Arial, sans-serif',
                textColor: '#333333',
                priceColor: '#e74c3c',
                accentColor: '#667eea'
            },
            'Classic': {
                font: 'Georgia, serif',
                textColor: '#2c3e50',
                priceColor: '#c0392b',
                accentColor: '#3498db'
            },
            'Fun': {
                font: 'Comic Sans MS, cursive',
                textColor: '#e67e22',
                priceColor: '#e74c3c',
                accentColor: '#f39c12'
            },
            'Minimal': {
                font: 'Helvetica, sans-serif',
                textColor: '#000000',
                priceColor: '#666666',
                accentColor: '#000000'
            }
        };
        
        return themes[theme] || themes['Modern'];
    }
    
    saveState(pageNum) {
        const canvas = this.canvases[pageNum];
        const state = JSON.stringify(canvas.toJSON());
        
        this.undoStacks[pageNum] = this.undoStacks[pageNum] || [];
        this.undoStacks[pageNum].push(state);
        
        // Limit undo stack size
        if (this.undoStacks[pageNum].length > 50) {
            this.undoStacks[pageNum].shift();
        }
        
        // Clear redo stack
        this.redoStacks[pageNum] = [];
    }
    
    undo(pageNum = null) {
        const page = pageNum || this.currentPage;
        const undoStack = this.undoStacks[page];
        const redoStack = this.redoStacks[page];
        
        if (undoStack && undoStack.length > 0) {
            const currentState = JSON.stringify(this.canvases[page].toJSON());
            redoStack.push(currentState);
            
            const previousState = undoStack.pop();
            this.canvases[page].loadFromJSON(previousState, () => {
                this.canvases[page].renderAll();
            });
        }
    }
    
    redo(pageNum = null) {
        const page = pageNum || this.currentPage;
        const undoStack = this.undoStacks[page];
        const redoStack = this.redoStacks[page];
        
        if (redoStack && redoStack.length > 0) {
            const currentState = JSON.stringify(this.canvases[page].toJSON());
            undoStack.push(currentState);
            
            const nextState = redoStack.pop();
            this.canvases[page].loadFromJSON(nextState, () => {
                this.canvases[page].renderAll();
            });
        }
    }
    
    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'z':
                        if (e.shiftKey) {
                            this.redo();
                        } else {
                            this.undo();
                        }
                        e.preventDefault();
                        break;
                    case 'y':
                        this.redo();
                        e.preventDefault();
                        break;
                    case 'l':
                        this.togglePageLock();
                        e.preventDefault();
                        break;
                    case 'g':
                        this.gridSnapEnabled = !this.gridSnapEnabled;
                        e.preventDefault();
                        break;
                    case 's':
                        this.saveProject();
                        e.preventDefault();
                        break;
                }
            } else if (e.key === 'Delete') {
                this.deleteSelected();
            }
        });
    }
    
    deleteSelected() {
        const canvas = this.canvases[this.currentPage];
        const activeObject = canvas.getActiveObject();
        
        if (activeObject) {
            // Send to parking instead of deleting
            if (activeObject.productData) {
                this.sendToParkingArea(activeObject.productData);
            }
            
            canvas.remove(activeObject);
            canvas.renderAll();
        }
    }
    
    showProductOptions(object) {
        if (!object || !object.productData) return;
        
        const product = object.productData;
        const options = document.createElement('div');
        options.className = 'product-options-panel';
        options.innerHTML = `
            <h4>${product.name}</h4>
            <button onclick="editor.enlargeProduct('${product.id}')">Büyüt</button>
            <button onclick="editor.generateSlogan('${product.id}')">Slogan Üret</button>
            <button onclick="editor.pinProduct('${product.id}')">Sabitle</button>
            <button onclick="editor.moveToPage('${product.id}')">Başka Sayfaya Taşı</button>
            <button onclick="editor.deleteProduct('${product.id}')">Parka Gönder</button>
        `;
        
        // Position near selected object
        document.body.appendChild(options);
    }
    
    async generateSlogan(productId) {
        const product = this.findProductById(productId);
        if (!product) return;
        
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
            if (data.success && data.slogans) {
                // Show slogan selection dialog
                this.showSloganDialog(productId, data.slogans);
            }
        } catch (error) {
            console.error('Error generating slogan:', error);
        }
    }
    
    showSloganDialog(productId, slogans) {
        const dialog = document.createElement('div');
        dialog.className = 'slogan-dialog';
        dialog.innerHTML = `
            <h3>Slogan Seçin</h3>
            ${slogans.map((slogan, i) => `
                <div class="slogan-option">
                    <input type="radio" name="slogan" id="slogan-${i}" value="${slogan}">
                    <label for="slogan-${i}">${slogan}</label>
                </div>
            `).join('')}
            <button onclick="editor.applySlogan('${productId}')">Uygula</button>
        `;
        
        document.body.appendChild(dialog);
    }
    
    findProductById(productId) {
        // Search in all pages
        for (const pageNum in this.pageSettings) {
            const product = this.pageSettings[pageNum].products.find(p => p.id === productId);
            if (product) return product;
        }
        
        // Search in parking
        return this.parkingArea.find(p => p.id === productId);
    }
    
    updateProductPosition(object, pageNum) {
        if (!object.productData) return;
        
        const product = object.productData;
        const canvas = this.canvases[pageNum];
        
        // Check for collisions
        const objects = canvas.getObjects();
        objects.forEach(obj => {
            if (obj !== object && obj.productData) {
                if (this.checkCollision(object, obj)) {
                    // Push other product
                    this.pushProduct(obj, object);
                }
            }
        });
    }
    
    checkCollision(obj1, obj2) {
        const bounds1 = obj1.getBoundingRect();
        const bounds2 = obj2.getBoundingRect();
        
        return !(bounds1.left > bounds2.left + bounds2.width ||
                bounds1.left + bounds1.width < bounds2.left ||
                bounds1.top > bounds2.top + bounds2.height ||
                bounds1.top + bounds1.height < bounds2.top);
    }
    
    pushProduct(productToPush, pusher) {
        const pusherBounds = pusher.getBoundingRect();
        const pushBounds = productToPush.getBoundingRect();
        
        // Calculate push direction
        const dx = pushBounds.left + pushBounds.width/2 - (pusherBounds.left + pusherBounds.width/2);
        const dy = pushBounds.top + pushBounds.height/2 - (pusherBounds.top + pusherBounds.height/2);
        
        // Push away
        const pushDistance = 20;
        const angle = Math.atan2(dy, dx);
        
        productToPush.set({
            left: productToPush.left + Math.cos(angle) * pushDistance,
            top: productToPush.top + Math.sin(angle) * pushDistance
        });
        
        productToPush.setCoords();
    }
    
    saveProject() {
        const projectData = {
            pages: {},
            parkingArea: this.parkingArea,
            settings: this.pageSettings
        };
        
        // Save each page
        for (const pageNum in this.canvases) {
            projectData.pages[pageNum] = this.canvases[pageNum].toJSON();
        }
        
        // Save to localStorage or send to server
        localStorage.setItem('brochureProject', JSON.stringify(projectData));
        
        // Also save to server
        this.saveToServer(projectData);
    }
    
    async saveToServer(projectData) {
        try {
            const response = await fetch('/api/save-brochure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
            
            if (response.ok) {
                this.showNotification('Proje kaydedildi');
            }
        } catch (error) {
            console.error('Error saving project:', error);
        }
    }
    
    loadProject(projectData) {
        // Clear existing
        this.clearAll();
        
        // Load pages
        for (const pageNum in projectData.pages) {
            if (!this.canvases[pageNum]) {
                this.createPage(parseInt(pageNum));
            }
            
            this.canvases[pageNum].loadFromJSON(projectData.pages[pageNum], () => {
                this.canvases[pageNum].renderAll();
            });
        }
        
        // Load settings
        this.pageSettings = projectData.settings;
        this.parkingArea = projectData.parkingArea || [];
        this.renderParkingArea();
    }
    
    clearAll() {
        // Remove all pages except first
        for (let i = this.totalPages; i > 1; i--) {
            this.removePage(i);
        }
        
        // Clear first page
        this.canvases[1].clear();
        this.canvases[1].backgroundColor = 'white';
        
        // Clear parking
        this.parkingArea = [];
        this.renderParkingArea();
    }
    
    exportPage(pageNum, format = 'png') {
        const canvas = this.canvases[pageNum];
        
        switch(format) {
            case 'png':
                return canvas.toDataURL('image/png');
            case 'jpeg':
                return canvas.toDataURL('image/jpeg', 0.9);
            case 'pdf':
                return this.exportToPDF(pageNum);
            default:
                return canvas.toDataURL();
        }
    }
    
    async exportAllPages(format = 'pdf') {
        const pages = [];
        
        for (const pageNum in this.canvases) {
            const pageData = await this.exportPage(pageNum, format === 'pdf' ? 'png' : format);
            pages.push({
                pageNum: pageNum,
                data: pageData
            });
        }
        
        if (format === 'pdf') {
            return this.combineToPDF(pages);
        }
        
        return pages;
    }
    
    async exportToPDF(pageNum = null) {
        // This would integrate with a PDF library like jsPDF
        const pages = pageNum ? [pageNum] : Object.keys(this.canvases);
        
        // Placeholder for PDF generation
        const pdfData = {
            pages: pages.map(p => ({
                pageNum: p,
                imageData: this.canvases[p].toDataURL('image/png')
            }))
        };
        
        // Send to server for PDF generation
        try {
            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pdfData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `brochure_${Date.now()}.pdf`;
                a.click();
            }
        } catch (error) {
            console.error('Error generating PDF:', error);
        }
    }
    
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    loadPreferences() {
        // Load user preferences from server
        fetch('/api/editor-preferences')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.preferences) {
                    this.gridSnapEnabled = data.preferences.grid_snap_enabled;
                    this.gridSize = data.preferences.grid_size;
                }
            })
            .catch(error => console.error('Error loading preferences:', error));
    }
    
    // ============= GHOST STYLE HINTS SYSTEM (Madde 2) =============
    
    /**
     * Ghost stil önerilerini canvas'a uygula (Madde 2)
     * 
     * @param {Object} pageAnalysis - Ghost'tan gelen analiz sonuçları
     * @param {number} pageNum - Sayfa numarası
     */
    applyGhostStyleHints(pageAnalysis, pageNum) {
        if (!pageAnalysis || !pageAnalysis.style_hints) return;
        
        const canvas = this.canvases[pageNum];
        const hints = pageAnalysis.style_hints;
        
        // Font ayarlamaları
        if (hints.font_adjustments && hints.font_adjustments.length > 0) {
            hints.font_adjustments.forEach(adjustment => {
                this.applyFontAdjustment(canvas, adjustment);
            });
        }
        
        // Boyut ayarlamaları
        if (hints.size_adjustments && hints.size_adjustments.length > 0) {
            hints.size_adjustments.forEach(adjustment => {
                this.applySizeAdjustment(canvas, adjustment, pageNum);
            });
        }
        
        // Spacing ayarlamaları
        if (hints.spacing_adjustments && hints.spacing_adjustments.length > 0) {
            hints.spacing_adjustments.forEach(adjustment => {
                this.applySpacingAdjustment(canvas, adjustment, pageNum);
            });
        }
        
        canvas.renderAll();
        this.showNotification('👻 Ghost stil önerileri uygulandı', 'info');
    }
    
    /**
     * Font ayarlaması uygula
     */
    applyFontAdjustment(canvas, adjustment) {
        const objects = canvas.getObjects();
        
        objects.forEach(obj => {
            if (obj.productData && obj.productData.id === adjustment.product_id) {
                // Group içindeki text nesnelerini bul
                if (obj.type === 'group') {
                    obj.getObjects().forEach(item => {
                        if (item.type === 'text') {
                            // İsim mi fiyat mı kontrol et
                            const isPrice = item.text && item.text.includes('₺');
                            
                            if (adjustment.target === 'name' && !isPrice) {
                                item.set({ fontSize: adjustment.suggested });
                            } else if (adjustment.target === 'price' && isPrice) {
                                item.set({ fontSize: adjustment.suggested });
                            }
                        }
                    });
                }
            }
        });
    }
    
    /**
     * Boyut ayarlaması uygula
     */
    applySizeAdjustment(canvas, adjustment, pageNum) {
        if (adjustment.target === 'cards') {
            // Tüm kartları ölçekle
            const scaleFactor = adjustment.action === 'increase' 
                ? 1 + (adjustment.percentage / 100)
                : 1 - (adjustment.percentage / 100);
            
            canvas.getObjects().forEach(obj => {
                if (obj.productData) {
                    obj.scale(obj.scaleX * scaleFactor);
                    obj.setCoords();
                }
            });
        } else if (adjustment.target === 'image' && adjustment.product_id) {
            // Tek ürün görseli
            canvas.getObjects().forEach(obj => {
                if (obj.productData && obj.productData.id === adjustment.product_id) {
                    if (obj.type === 'group') {
                        obj.getObjects().forEach(item => {
                            if (item.type === 'image') {
                                const newScale = adjustment.suggested_scale || 0.8;
                                item.scale(newScale);
                            }
                        });
                    }
                }
            });
        }
    }
    
    /**
     * Spacing ayarlaması uygula
     */
    applySpacingAdjustment(canvas, adjustment, pageNum) {
        if (adjustment.target === 'card_margin') {
            const marginChange = adjustment.action === 'increase' 
                ? adjustment.pixels 
                : -adjustment.pixels;
            
            // Kartları yeniden konumlandır
            const objects = canvas.getObjects().filter(o => o.productData);
            const sorted = objects.sort((a, b) => {
                const aPos = a.top * 1000 + a.left;
                const bPos = b.top * 1000 + b.left;
                return aPos - bPos;
            });
            
            let currentX = 50;
            let currentY = 50;
            const cardsPerRow = 4;
            let cardIndex = 0;
            
            sorted.forEach(obj => {
                const bounds = obj.getBoundingRect();
                obj.set({
                    left: currentX,
                    top: currentY
                });
                obj.setCoords();
                
                cardIndex++;
                if (cardIndex % cardsPerRow === 0) {
                    currentX = 50;
                    currentY += bounds.height + marginChange + 20;
                } else {
                    currentX += bounds.width + marginChange + 20;
                }
            });
        }
    }
    
    // ============= SMART DESIGNER MODULE (Madde 5) =============
    
    /**
     * Ghost akıllı düzenleme (Madde 5)
     * Kart boyutu, spacing, image scale, fontSize güncelle
     * 
     * @param {number} pageNum - Sayfa numarası
     * @param {Object} hints - Ghost önerileri
     */
    async smartRearrange(pageNum, hints = null) {
        const canvas = this.canvases[pageNum];
        if (!canvas) return;
        
        // Hint yoksa Ghost'tan al
        if (!hints) {
            try {
                const response = await fetch('/api/ghost/suggest-layout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.getPageData(pageNum))
                });
                
                if (response.ok) {
                    const data = await response.json();
                    hints = data.hints || data.style_hints;
                }
            } catch (error) {
                console.warn('Smart rearrange hint fetch error:', error);
            }
        }
        
        if (!hints) {
            // Default düzenleme
            this.autoArrangePage(pageNum);
            return;
        }
        
        // Stil önerilerini uygula
        this.applyGhostStyleHints({ style_hints: hints }, pageNum);
        
        // Otomatik düzenleme
        this.autoArrangePage(pageNum);
        
        this.saveState(pageNum);
        this.showNotification('👻 Akıllı düzenleme tamamlandı', 'success');
    }
    
    /**
     * Sayfa otomatik düzenleme
     */
    autoArrangePage(pageNum) {
        const canvas = this.canvases[pageNum];
        const objects = canvas.getObjects().filter(o => o.productData);
        
        if (objects.length === 0) return;
        
        // Grid düzeni hesapla
        const canvasWidth = canvas.width;
        const canvasHeight = canvas.height;
        
        const cols = Math.ceil(Math.sqrt(objects.length));
        const rows = Math.ceil(objects.length / cols);
        
        const cellWidth = (canvasWidth - 100) / cols;
        const cellHeight = (canvasHeight - 100) / rows;
        
        objects.forEach((obj, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);
            
            const x = 50 + col * cellWidth + cellWidth / 2;
            const y = 50 + row * cellHeight + cellHeight / 2;
            
            obj.set({
                left: x - obj.width / 2,
                top: y - obj.height / 2
            });
            obj.setCoords();
        });
        
        canvas.renderAll();
    }
    
    // ============= PRODUCT WARNINGS SYSTEM (Madde 3) =============
    
    /**
     * Ürün uyarılarını canvas üzerinde göster (Madde 3)
     * 
     * @param {Array} warnings - Ürün bazlı uyarılar
     * @param {number} pageNum - Sayfa numarası
     */
    showProductWarnings(warnings, pageNum) {
        if (!warnings || warnings.length === 0) return;
        
        const canvas = this.canvases[pageNum];
        
        // Mevcut uyarı efektlerini temizle
        this.clearWarningEffects(canvas);
        
        warnings.forEach(warning => {
            const obj = canvas.getObjects().find(
                o => o.productData && o.productData.id === warning.product_id
            );
            
            if (obj) {
                this.addWarningEffect(obj, warning, canvas);
            }
        });
        
        canvas.renderAll();
    }
    
    /**
     * Uyarı efektlerini temizle
     */
    clearWarningEffects(canvas) {
        canvas.getObjects().forEach(obj => {
            if (obj.isWarningEffect) {
                canvas.remove(obj);
            }
            // Reset shadow
            if (obj.productData) {
                obj.set({ shadow: null });
            }
        });
    }
    
    /**
     * Ürüne uyarı efekti ekle (glow + hover balonu)
     */
    addWarningEffect(productObj, warning, canvas) {
        // Glow efekti
        const glowColor = this.getWarningColor(warning.severity);
        productObj.set({
            shadow: new fabric.Shadow({
                color: glowColor,
                blur: 12,
                offsetX: 0,
                offsetY: 0
            })
        });
        
        // Store warning data for hover
        productObj.warningData = warning;
        
        // Hover event ekle
        productObj.on('mouseover', () => {
            this.showWarningBubble(productObj, warning, canvas);
        });
        
        productObj.on('mouseout', () => {
            this.hideWarningBubble(canvas);
        });
    }
    
    /**
     * Uyarı rengi al
     */
    getWarningColor(severity) {
        const colors = {
            'error': '#ff6565',
            'warning': '#ffb347',
            'info': '#87ceeb',
            'success': '#90ee90'
        };
        return colors[severity] || colors['warning'];
    }
    
    /**
     * Hayalet uyarı balonu göster
     */
    showWarningBubble(productObj, warning, canvas) {
        // Mevcut balonu temizle
        this.hideWarningBubble(canvas);
        
        const bounds = productObj.getBoundingRect();
        
        // Balon arka planı
        const bubble = new fabric.Rect({
            left: bounds.left + bounds.width + 10,
            top: bounds.top,
            width: 200,
            height: 60,
            fill: 'rgba(50, 50, 50, 0.9)',
            rx: 8,
            ry: 8,
            isWarningEffect: true,
            selectable: false,
            evented: false
        });
        
        // Ghost ikonu
        const ghostIcon = new fabric.Text('👻', {
            left: bounds.left + bounds.width + 20,
            top: bounds.top + 8,
            fontSize: 20,
            isWarningEffect: true,
            selectable: false,
            evented: false
        });
        
        // Uyarı mesajı
        const message = new fabric.Text(warning.message, {
            left: bounds.left + bounds.width + 50,
            top: bounds.top + 12,
            fontSize: 11,
            fill: 'white',
            width: 150,
            isWarningEffect: true,
            selectable: false,
            evented: false
        });
        
        canvas.add(bubble, ghostIcon, message);
        canvas.renderAll();
    }
    
    /**
     * Uyarı balonunu gizle
     */
    hideWarningBubble(canvas) {
        canvas.getObjects().forEach(obj => {
            if (obj.isWarningEffect && obj.type !== 'group') {
                canvas.remove(obj);
            }
        });
        canvas.renderAll();
    }
    
    // ============= GHOST API HELPERS =============
    
    /**
     * Ghost tam temizlik çağrısı (Madde 10)
     */
    async ghostFullClean() {
        const brochureData = this.getBrochureData();
        
        try {
            const response = await fetch('/api/ghost/full-clean-brochure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(brochureData)
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Optimize edilmiş broşürü yükle
                    this.loadOptimizedBrochure(result.optimized_brochure);
                    this.showNotification(result.message, 'success');
                }
            }
        } catch (error) {
            console.error('Ghost full clean error:', error);
            this.showNotification('Temizlik işlemi başarısız', 'error');
        }
    }
    
    /**
     * Tüm broşür verisini al
     */
    getBrochureData() {
        const pages = [];
        
        for (const pageNum in this.canvases) {
            pages.push({
                id: parseInt(pageNum),
                ...this.getPageData(pageNum)
            });
        }
        
        return {
            pages: pages,
            parking_area: this.parkingArea
        };
    }
    
    /**
     * Optimize edilmiş broşürü yükle
     */
    loadOptimizedBrochure(brochureData) {
        if (!brochureData || !brochureData.pages) return;
        
        brochureData.pages.forEach(pageData => {
            const pageNum = pageData.id;
            
            if (this.pageSettings[pageNum]) {
                // Ürün isimlerini güncelle
                pageData.products.forEach(optimizedProduct => {
                    const existingProduct = this.pageSettings[pageNum].products.find(
                        p => p.id === optimizedProduct.id
                    );
                    if (existingProduct) {
                        existingProduct.name = optimizedProduct.name;
                        existingProduct.name_font_size = optimizedProduct.name_font_size;
                        existingProduct.price_font_size = optimizedProduct.price_font_size;
                        existingProduct.image_scale = optimizedProduct.image_scale;
                    }
                });
                
                // Canvas'ı yeniden çiz
                this.refreshCanvasProducts(pageNum);
            }
        });
    }
    
    /**
     * Canvas ürünlerini yenile
     */
    refreshCanvasProducts(pageNum) {
        const canvas = this.canvases[pageNum];
        const products = this.pageSettings[pageNum].products;
        
        // Mevcut ürün objelerini güncelle
        canvas.getObjects().forEach(obj => {
            if (obj.productData) {
                const updatedProduct = products.find(p => p.id === obj.productData.id);
                if (updatedProduct) {
                    obj.productData = updatedProduct;
                    
                    // Text nesnelerini güncelle
                    if (obj.type === 'group') {
                        obj.getObjects().forEach(item => {
                            if (item.type === 'text') {
                                if (!item.text.includes('₺')) {
                                    // İsim text'i
                                    item.set({
                                        text: updatedProduct.name,
                                        fontSize: updatedProduct.name_font_size || 14
                                    });
                                } else if (item.text.includes('₺') && !item.textDecoration) {
                                    // Fiyat text'i
                                    item.set({
                                        fontSize: updatedProduct.price_font_size || 18
                                    });
                                }
                            }
                        });
                    }
                }
            }
        });
        
        canvas.renderAll();
    }
}

// Initialize editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.editor = new BrochureEditor();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrochureEditor;
}