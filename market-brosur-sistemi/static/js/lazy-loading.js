/**
 * Lazy Loading Module
 * 
 * Provides lazy loading for images using Intersection Observer.
 * Only loads images when they enter the viewport.
 */

class LazyLoader {
    constructor(options = {}) {
        this.rootMargin = options.rootMargin || '50px';
        this.threshold = options.threshold || 0.1;
        this.loadedClass = options.loadedClass || 'lazy-loaded';
        this.errorClass = options.errorClass || 'lazy-error';
        this.placeholder = options.placeholder || '/static/images/placeholder.png';
        this.observer = null;
        
        this.init();
        
        console.log('✅ Lazy loading initialized');
    }
    
    /**
     * Initialize the lazy loader
     */
    init() {
        // Check for IntersectionObserver support
        if (!('IntersectionObserver' in window)) {
            console.warn('IntersectionObserver not supported, loading all images');
            this.loadAllImages();
            return;
        }
        
        // Create observer
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            {
                rootMargin: this.rootMargin,
                threshold: this.threshold
            }
        );
        
        // Observe existing lazy images
        this.observeImages();
        
        // Set up mutation observer for dynamically added images
        this.setupMutationObserver();
    }
    
    /**
     * Handle intersection events
     */
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                this.loadImage(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }
    
    /**
     * Load an image
     */
    loadImage(img) {
        const src = img.dataset.src || img.dataset.lazySrc;
        const srcset = img.dataset.srcset;
        
        if (!src) return;
        
        // Create a temporary image to preload
        const tempImg = new Image();
        
        tempImg.onload = () => {
            img.src = src;
            if (srcset) img.srcset = srcset;
            
            img.classList.add(this.loadedClass);
            img.classList.remove('lazy');
            
            // Remove data attributes
            delete img.dataset.src;
            delete img.dataset.lazySrc;
            delete img.dataset.srcset;
            
            // Dispatch loaded event
            img.dispatchEvent(new CustomEvent('lazyloaded'));
        };
        
        tempImg.onerror = () => {
            img.classList.add(this.errorClass);
            
            // Set fallback placeholder
            if (this.placeholder) {
                img.src = this.placeholder;
            }
            
            // Dispatch error event
            img.dispatchEvent(new CustomEvent('lazyerror'));
        };
        
        tempImg.src = src;
    }
    
    /**
     * Observe all lazy images
     */
    observeImages() {
        const images = document.querySelectorAll('img.lazy, img[data-src], img[data-lazy-src]');
        
        images.forEach(img => {
            if (!img.classList.contains(this.loadedClass)) {
                this.observer.observe(img);
            }
        });
        
        console.log(`Observing ${images.length} lazy images`);
    }
    
    /**
     * Set up mutation observer for dynamic content
     */
    setupMutationObserver() {
        const mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // Check if the node itself is a lazy image
                        if (this.isLazyImage(node)) {
                            this.observer.observe(node);
                        }
                        
                        // Check for lazy images inside the node
                        const lazyImages = node.querySelectorAll?.('img.lazy, img[data-src], img[data-lazy-src]');
                        lazyImages?.forEach(img => {
                            if (!img.classList.contains(this.loadedClass)) {
                                this.observer.observe(img);
                            }
                        });
                    }
                });
            });
        });
        
        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Check if element is a lazy image
     */
    isLazyImage(element) {
        return element.tagName === 'IMG' && (
            element.classList.contains('lazy') ||
            element.dataset.src ||
            element.dataset.lazySrc
        );
    }
    
    /**
     * Fallback: Load all images immediately
     */
    loadAllImages() {
        const images = document.querySelectorAll('img.lazy, img[data-src], img[data-lazy-src]');
        images.forEach(img => this.loadImage(img));
    }
    
    /**
     * Manually trigger loading of specific image
     */
    load(img) {
        if (this.observer) {
            this.observer.unobserve(img);
        }
        this.loadImage(img);
    }
    
    /**
     * Refresh - re-observe all lazy images
     */
    refresh() {
        this.observeImages();
    }
    
    /**
     * Destroy the lazy loader
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// ============= PRODUCT LIST LAZY LOADER =============

class ProductListLazyLoader {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        this.batchSize = options.batchSize || 20;
        this.products = [];
        this.loadedCount = 0;
        this.loading = false;
        this.hasMore = true;
        
        if (this.container) {
            this.init();
        }
    }
    
    /**
     * Initialize the product list lazy loader
     */
    init() {
        // Create sentinel element for infinite scroll
        this.sentinel = document.createElement('div');
        this.sentinel.className = 'product-sentinel';
        this.sentinel.style.height = '1px';
        this.container.appendChild(this.sentinel);
        
        // Create intersection observer for infinite scroll
        this.scrollObserver = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !this.loading && this.hasMore) {
                    this.loadNextBatch();
                }
            },
            { rootMargin: '200px' }
        );
        
        this.scrollObserver.observe(this.sentinel);
        
        console.log('✅ Product list lazy loader initialized');
    }
    
    /**
     * Set products data
     */
    setProducts(products) {
        this.products = products;
        this.loadedCount = 0;
        this.hasMore = true;
        
        // Clear container except sentinel
        const children = Array.from(this.container.children);
        children.forEach(child => {
            if (child !== this.sentinel) {
                child.remove();
            }
        });
        
        // Load first batch
        this.loadNextBatch();
    }
    
    /**
     * Load next batch of products
     */
    loadNextBatch() {
        if (this.loading || !this.hasMore) return;
        
        this.loading = true;
        this.showLoading();
        
        // Get next batch
        const start = this.loadedCount;
        const end = Math.min(start + this.batchSize, this.products.length);
        const batch = this.products.slice(start, end);
        
        // Render products
        batch.forEach((product, index) => {
            const element = this.renderProduct(product, start + index);
            this.container.insertBefore(element, this.sentinel);
        });
        
        this.loadedCount = end;
        this.hasMore = end < this.products.length;
        
        this.hideLoading();
        this.loading = false;
        
        // Dispatch event
        this.container.dispatchEvent(new CustomEvent('batchLoaded', {
            detail: {
                loaded: this.loadedCount,
                total: this.products.length,
                hasMore: this.hasMore
            }
        }));
    }
    
    /**
     * Render a single product (override this for custom rendering)
     */
    renderProduct(product, index) {
        const div = document.createElement('div');
        div.className = 'product-item';
        div.dataset.productId = product.id || product.barcode;
        div.dataset.index = index;
        
        div.innerHTML = `
            <img class="lazy" 
                 data-src="${product.image_url || '/static/images/placeholder.png'}" 
                 src="/static/images/placeholder.png"
                 alt="${product.name || ''}">
            <div class="product-info">
                <h4>${product.name || 'Ürün'}</h4>
                <p class="product-price">${this.formatPrice(product.price)}</p>
            </div>
        `;
        
        // Initialize lazy loading for the image
        if (window.lazyLoader) {
            const img = div.querySelector('img.lazy');
            if (img) {
                window.lazyLoader.observer?.observe(img);
            }
        }
        
        return div;
    }
    
    /**
     * Format price
     */
    formatPrice(price) {
        if (price === null || price === undefined) return '';
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY'
        }).format(price);
    }
    
    /**
     * Show loading indicator
     */
    showLoading() {
        if (!this.loadingEl) {
            this.loadingEl = document.createElement('div');
            this.loadingEl.className = 'products-loading';
            this.loadingEl.innerHTML = `
                <div class="loading-spinner"></div>
                <span>Yükleniyor...</span>
            `;
        }
        this.container.insertBefore(this.loadingEl, this.sentinel);
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        this.loadingEl?.remove();
    }
    
    /**
     * Destroy
     */
    destroy() {
        this.scrollObserver?.disconnect();
        this.sentinel?.remove();
    }
}

// ============= GLOBAL INSTANCES =============

// Initialize global lazy loader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.lazyLoader = new LazyLoader();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LazyLoader, ProductListLazyLoader };
}

// CSS for lazy loading
const lazyStyle = document.createElement('style');
lazyStyle.textContent = `
    img.lazy {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    img.lazy-loaded {
        opacity: 1;
    }
    
    img.lazy-error {
        opacity: 0.5;
        filter: grayscale(1);
    }
    
    .products-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 20px;
        color: rgba(255, 255, 255, 0.7);
    }
    
    .loading-spinner {
        width: 24px;
        height: 24px;
        border: 3px solid rgba(255, 255, 255, 0.2);
        border-top-color: #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(lazyStyle);

console.log('📦 Lazy loading module loaded');

