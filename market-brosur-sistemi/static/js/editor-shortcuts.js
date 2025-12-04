/**
 * Keyboard Shortcuts for Brochure Editor
 * 
 * Provides professional keyboard shortcuts for common operations.
 */

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
        this.selectedProducts = new Set();
        this.clipboard = null;
        this.gridVisible = true;
        
        this.registerDefaultShortcuts();
        this.bindEvents();
        
        console.log('✅ Keyboard shortcuts initialized');
    }
    
    /**
     * Register default shortcuts
     */
    registerDefaultShortcuts() {
        // Save
        this.register('ctrl+s', () => this.save(), 'Kaydet');
        
        // Undo/Redo (handled by undo-redo.js but registered here for help display)
        this.register('ctrl+z', () => {
            if (window.actionHistory) window.actionHistory.triggerUndo();
        }, 'Geri Al');
        
        this.register('ctrl+y', () => {
            if (window.actionHistory) window.actionHistory.triggerRedo();
        }, 'Yinele');
        
        this.register('ctrl+shift+z', () => {
            if (window.actionHistory) window.actionHistory.triggerRedo();
        }, 'Yinele');
        
        // Copy/Paste
        this.register('ctrl+c', () => this.copy(), 'Kopyala');
        this.register('ctrl+v', () => this.paste(), 'Yapıştır');
        this.register('ctrl+x', () => this.cut(), 'Kes');
        
        // Selection
        this.register('ctrl+a', () => this.selectAll(), 'Tümünü Seç');
        this.register('escape', () => this.deselectAll(), 'Seçimi Kaldır');
        this.register('delete', () => this.deleteSelected(), 'Sil');
        this.register('backspace', () => this.deleteSelected(), 'Sil');
        
        // Grid
        this.register('ctrl+g', () => this.toggleGrid(), 'Grid Göster/Gizle');
        
        // Page lock
        this.register('ctrl+l', () => this.togglePageLock(), 'Sayfa Kilitle');
        
        // Export
        this.register('ctrl+e', () => this.export(), 'Dışa Aktar');
        
        // Zoom
        this.register('ctrl+=', () => this.zoomIn(), 'Yakınlaştır');
        this.register('ctrl+-', () => this.zoomOut(), 'Uzaklaştır');
        this.register('ctrl+0', () => this.zoomReset(), 'Zoom Sıfırla');
        
        // Navigation
        this.register('pageup', () => this.previousPage(), 'Önceki Sayfa');
        this.register('pagedown', () => this.nextPage(), 'Sonraki Sayfa');
        
        // Help
        this.register('f1', () => this.showHelp(), 'Yardım');
        this.register('ctrl+/', () => this.showHelp(), 'Kısayolları Göster');
    }
    
    /**
     * Register a keyboard shortcut
     */
    register(keys, callback, description = '') {
        this.shortcuts.set(keys.toLowerCase(), {
            callback,
            description,
            keys
        });
    }
    
    /**
     * Unregister a shortcut
     */
    unregister(keys) {
        this.shortcuts.delete(keys.toLowerCase());
    }
    
    /**
     * Bind keyboard events
     */
    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;
            
            // Don't trigger shortcuts when typing in inputs
            if (this.isInputFocused()) return;
            
            const key = this.getKeyString(e);
            const shortcut = this.shortcuts.get(key);
            
            if (shortcut) {
                e.preventDefault();
                shortcut.callback(e);
            }
        });
        
        // Multi-select with click
        document.addEventListener('click', (e) => {
            const productBox = e.target.closest('.product-box, .product-item, [data-product-id]');
            
            if (productBox) {
                const productId = productBox.dataset.productId;
                
                if (e.ctrlKey) {
                    // CTRL+Click: Toggle selection
                    this.toggleSelection(productId, productBox);
                } else if (e.shiftKey) {
                    // SHIFT+Click: Range selection
                    this.rangeSelect(productId, productBox);
                } else {
                    // Normal click: Single selection
                    this.singleSelect(productId, productBox);
                }
            }
        });
    }
    
    /**
     * Check if an input element is focused
     */
    isInputFocused() {
        const active = document.activeElement;
        return active && (
            active.tagName === 'INPUT' ||
            active.tagName === 'TEXTAREA' ||
            active.tagName === 'SELECT' ||
            active.isContentEditable
        );
    }
    
    /**
     * Get key string from event
     */
    getKeyString(e) {
        const parts = [];
        
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');
        
        let key = e.key.toLowerCase();
        
        // Normalize key names
        if (key === ' ') key = 'space';
        if (key === '+') key = '=';
        
        if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
            parts.push(key);
        }
        
        return parts.join('+');
    }
    
    // ============= ACTIONS =============
    
    save() {
        console.log('💾 Saving...');
        
        // Call save function if exists
        if (typeof window.saveCurrentBrochure === 'function') {
            window.saveCurrentBrochure();
        } else if (typeof saveBrochure === 'function') {
            saveBrochure();
        }
        
        this.showNotification('Kaydedildi', 'success');
    }
    
    copy() {
        if (this.selectedProducts.size === 0) {
            this.showNotification('Kopyalanacak ürün seçilmedi', 'warning');
            return;
        }
        
        this.clipboard = Array.from(this.selectedProducts);
        this.clipboardAction = 'copy';
        this.showNotification(`${this.clipboard.length} ürün kopyalandı`, 'info');
    }
    
    cut() {
        if (this.selectedProducts.size === 0) {
            this.showNotification('Kesilecek ürün seçilmedi', 'warning');
            return;
        }
        
        this.clipboard = Array.from(this.selectedProducts);
        this.clipboardAction = 'cut';
        this.showNotification(`${this.clipboard.length} ürün kesildi`, 'info');
    }
    
    paste() {
        if (!this.clipboard || this.clipboard.length === 0) {
            this.showNotification('Yapıştırılacak ürün yok', 'warning');
            return;
        }
        
        // Call paste function if exists
        if (typeof window.pasteProducts === 'function') {
            window.pasteProducts(this.clipboard, this.clipboardAction);
        }
        
        // Clear clipboard if it was a cut
        if (this.clipboardAction === 'cut') {
            this.clipboard = null;
        }
        
        this.showNotification('Yapıştırıldı', 'success');
    }
    
    selectAll() {
        const products = document.querySelectorAll('.product-box, .product-item, [data-product-id]');
        
        products.forEach(product => {
            const id = product.dataset.productId;
            if (id) {
                this.selectedProducts.add(id);
                product.classList.add('selected');
            }
        });
        
        this.updateSelectionUI();
        this.showNotification(`${this.selectedProducts.size} ürün seçildi`, 'info');
    }
    
    deselectAll() {
        document.querySelectorAll('.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        this.selectedProducts.clear();
        this.updateSelectionUI();
    }
    
    deleteSelected() {
        if (this.selectedProducts.size === 0) {
            return;
        }
        
        const count = this.selectedProducts.size;
        
        // Call delete function if exists
        if (typeof window.deleteProducts === 'function') {
            window.deleteProducts(Array.from(this.selectedProducts));
        }
        
        this.deselectAll();
        this.showNotification(`${count} ürün silindi`, 'info');
    }
    
    toggleSelection(productId, element) {
        if (this.selectedProducts.has(productId)) {
            this.selectedProducts.delete(productId);
            element.classList.remove('selected');
        } else {
            this.selectedProducts.add(productId);
            element.classList.add('selected');
        }
        
        this.updateSelectionUI();
    }
    
    singleSelect(productId, element) {
        this.deselectAll();
        
        this.selectedProducts.add(productId);
        element.classList.add('selected');
        
        this.updateSelectionUI();
    }
    
    rangeSelect(productId, element) {
        // Simplified range select - select all between last and current
        const products = Array.from(document.querySelectorAll('.product-box, .product-item, [data-product-id]'));
        const currentIndex = products.indexOf(element);
        
        if (this.lastSelectedIndex !== undefined) {
            const start = Math.min(this.lastSelectedIndex, currentIndex);
            const end = Math.max(this.lastSelectedIndex, currentIndex);
            
            for (let i = start; i <= end; i++) {
                const product = products[i];
                const id = product.dataset.productId;
                if (id) {
                    this.selectedProducts.add(id);
                    product.classList.add('selected');
                }
            }
        }
        
        this.lastSelectedIndex = currentIndex;
        this.updateSelectionUI();
    }
    
    updateSelectionUI() {
        // Update selection count display
        const countEl = document.getElementById('selection-count');
        if (countEl) {
            countEl.textContent = this.selectedProducts.size > 0 
                ? `${this.selectedProducts.size} seçili` 
                : '';
        }
        
        // Dispatch event
        document.dispatchEvent(new CustomEvent('selectionChange', {
            detail: {
                count: this.selectedProducts.size,
                ids: Array.from(this.selectedProducts)
            }
        }));
    }
    
    toggleGrid() {
        this.gridVisible = !this.gridVisible;
        
        const canvas = document.getElementById('brochure-canvas');
        if (canvas) {
            canvas.classList.toggle('show-grid', this.gridVisible);
        }
        
        this.showNotification(this.gridVisible ? 'Grid gösteriliyor' : 'Grid gizlendi', 'info');
    }
    
    togglePageLock() {
        if (typeof window.toggleCurrentPageLock === 'function') {
            window.toggleCurrentPageLock();
        }
        this.showNotification('Sayfa kilidi değiştirildi', 'info');
    }
    
    export() {
        if (typeof window.openExportDialog === 'function') {
            window.openExportDialog();
        } else {
            this.showNotification('Dışa aktarma açılıyor...', 'info');
        }
    }
    
    zoomIn() {
        if (typeof window.zoomCanvas === 'function') {
            window.zoomCanvas(1.1);
        }
    }
    
    zoomOut() {
        if (typeof window.zoomCanvas === 'function') {
            window.zoomCanvas(0.9);
        }
    }
    
    zoomReset() {
        if (typeof window.zoomCanvas === 'function') {
            window.zoomCanvas(1, true);
        }
    }
    
    previousPage() {
        if (typeof window.goToPreviousPage === 'function') {
            window.goToPreviousPage();
        }
    }
    
    nextPage() {
        if (typeof window.goToNextPage === 'function') {
            window.goToNextPage();
        }
    }
    
    showHelp() {
        let helpHTML = `
            <div class="shortcuts-help">
                <h3>⌨️ Klavye Kısayolları</h3>
                <table>
                    <tbody>
        `;
        
        this.shortcuts.forEach((shortcut, keys) => {
            const keyDisplay = keys.replace('ctrl', 'CTRL').replace('shift', 'SHIFT').replace('alt', 'ALT').replace('+', ' + ').toUpperCase();
            helpHTML += `
                <tr>
                    <td><kbd>${keyDisplay}</kbd></td>
                    <td>${shortcut.description}</td>
                </tr>
            `;
        });
        
        helpHTML += `
                    </tbody>
                </table>
                <h4>🖱️ Fare İşlemleri</h4>
                <ul>
                    <li><strong>CTRL + Click:</strong> Çoklu seçim</li>
                    <li><strong>SHIFT + Click:</strong> Aralık seçimi</li>
                    <li><strong>Sürükle & Bırak:</strong> Ürünü taşı</li>
                </ul>
            </div>
        `;
        
        // Show in modal or panel
        if (typeof window.showModal === 'function') {
            window.showModal('Klavye Kısayolları', helpHTML);
        } else {
            // Fallback: alert
            alert('Klavye Kısayolları:\n\n' + 
                Array.from(this.shortcuts.entries())
                    .map(([k, v]) => `${k.toUpperCase()}: ${v.description}`)
                    .join('\n'));
        }
    }
    
    showNotification(message, type = 'info') {
        // Use global notification if available
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }
        
        console.log(`[${type}] ${message}`);
    }
    
    // Enable/disable shortcuts
    enable() { this.enabled = true; }
    disable() { this.enabled = false; }
}

// Global instance
window.keyboardShortcuts = new KeyboardShortcuts();

// CSS for shortcuts
const shortcutStyle = document.createElement('style');
shortcutStyle.textContent = `
    .product-box.selected,
    .product-item.selected,
    [data-product-id].selected {
        outline: 3px solid #6366f1 !important;
        outline-offset: 2px;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.3) !important;
    }
    
    .show-grid {
        background-image: 
            linear-gradient(rgba(99, 102, 241, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.1) 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    .shortcuts-help {
        max-height: 70vh;
        overflow-y: auto;
    }
    
    .shortcuts-help table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
    }
    
    .shortcuts-help td {
        padding: 8px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .shortcuts-help kbd {
        background: rgba(99, 102, 241, 0.2);
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .shortcuts-help h3, .shortcuts-help h4 {
        margin: 16px 0 8px;
        color: #a78bfa;
    }
    
    .shortcuts-help ul {
        padding-left: 20px;
    }
    
    .shortcuts-help li {
        margin: 8px 0;
    }
`;
document.head.appendChild(shortcutStyle);

console.log('📦 Keyboard shortcuts module loaded');

