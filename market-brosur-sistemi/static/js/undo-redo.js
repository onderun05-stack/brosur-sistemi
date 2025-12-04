/**
 * Undo/Redo System for Brochure Editor
 * 
 * Provides state management with undo/redo functionality.
 * Supports CTRL+Z (undo) and CTRL+Y/CTRL+SHIFT+Z (redo)
 */

class ActionHistory {
    constructor(maxHistory = 50) {
        this.undoStack = [];
        this.redoStack = [];
        this.maxHistory = maxHistory;
        this.isUndoing = false;
        this.isRedoing = false;
        this.lastSavedIndex = -1;
        
        // Bind keyboard shortcuts
        this.bindKeyboardShortcuts();
        
        console.log('✅ Undo/Redo system initialized');
    }
    
    /**
     * Push a new state to the history
     * @param {Object} state - The state to save
     * @param {string} actionName - Name of the action for display
     */
    push(state, actionName = 'Değişiklik') {
        if (this.isUndoing || this.isRedoing) return;
        
        // Deep clone the state
        const stateCopy = JSON.parse(JSON.stringify(state));
        
        this.undoStack.push({
            state: stateCopy,
            action: actionName,
            timestamp: Date.now()
        });
        
        // Clear redo stack on new action
        this.redoStack = [];
        
        // Limit history size
        if (this.undoStack.length > this.maxHistory) {
            this.undoStack.shift();
        }
        
        this.updateUI();
        
        console.log(`📝 Action saved: ${actionName} (${this.undoStack.length} in history)`);
    }
    
    /**
     * Undo last action
     * @returns {Object|null} Previous state or null if nothing to undo
     */
    undo() {
        if (this.undoStack.length <= 1) {
            this.showNotification('Geri alınacak işlem yok', 'warning');
            return null;
        }
        
        this.isUndoing = true;
        
        // Move current state to redo stack
        const current = this.undoStack.pop();
        this.redoStack.push(current);
        
        // Get previous state
        const previous = this.undoStack[this.undoStack.length - 1];
        
        this.isUndoing = false;
        this.updateUI();
        
        this.showNotification(`Geri alındı: ${current.action}`, 'info');
        console.log(`↩️ Undo: ${current.action}`);
        
        return previous.state;
    }
    
    /**
     * Redo last undone action
     * @returns {Object|null} Next state or null if nothing to redo
     */
    redo() {
        if (this.redoStack.length === 0) {
            this.showNotification('Yinelenecek işlem yok', 'warning');
            return null;
        }
        
        this.isRedoing = true;
        
        // Move state back to undo stack
        const next = this.redoStack.pop();
        this.undoStack.push(next);
        
        this.isRedoing = false;
        this.updateUI();
        
        this.showNotification(`Yinelendi: ${next.action}`, 'info');
        console.log(`↪️ Redo: ${next.action}`);
        
        return next.state;
    }
    
    /**
     * Check if undo is available
     */
    canUndo() {
        return this.undoStack.length > 1;
    }
    
    /**
     * Check if redo is available
     */
    canRedo() {
        return this.redoStack.length > 0;
    }
    
    /**
     * Get current state without modifying stacks
     */
    getCurrentState() {
        if (this.undoStack.length === 0) return null;
        return this.undoStack[this.undoStack.length - 1].state;
    }
    
    /**
     * Clear all history
     */
    clear() {
        this.undoStack = [];
        this.redoStack = [];
        this.lastSavedIndex = -1;
        this.updateUI();
        console.log('🗑️ History cleared');
    }
    
    /**
     * Mark current state as saved
     */
    markSaved() {
        this.lastSavedIndex = this.undoStack.length - 1;
        this.updateUI();
    }
    
    /**
     * Check if there are unsaved changes
     */
    hasUnsavedChanges() {
        return this.undoStack.length - 1 !== this.lastSavedIndex;
    }
    
    /**
     * Bind keyboard shortcuts
     */
    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // CTRL+Z - Undo
            if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.triggerUndo();
            }
            
            // CTRL+Y or CTRL+SHIFT+Z - Redo
            if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'z')) {
                e.preventDefault();
                this.triggerRedo();
            }
        });
    }
    
    /**
     * Trigger undo with callback
     */
    triggerUndo() {
        const state = this.undo();
        if (state && typeof window.onHistoryUndo === 'function') {
            window.onHistoryUndo(state);
        }
    }
    
    /**
     * Trigger redo with callback
     */
    triggerRedo() {
        const state = this.redo();
        if (state && typeof window.onHistoryRedo === 'function') {
            window.onHistoryRedo(state);
        }
    }
    
    /**
     * Update UI elements (buttons, indicators)
     */
    updateUI() {
        // Update undo button
        const undoBtn = document.getElementById('undo-btn');
        if (undoBtn) {
            undoBtn.disabled = !this.canUndo();
            undoBtn.title = this.canUndo() 
                ? `Geri Al (CTRL+Z) - ${this.undoStack.length - 1} işlem`
                : 'Geri alınacak işlem yok';
        }
        
        // Update redo button
        const redoBtn = document.getElementById('redo-btn');
        if (redoBtn) {
            redoBtn.disabled = !this.canRedo();
            redoBtn.title = this.canRedo()
                ? `Yinele (CTRL+Y) - ${this.redoStack.length} işlem`
                : 'Yinelenecek işlem yok';
        }
        
        // Update save indicator
        const saveIndicator = document.getElementById('save-indicator');
        if (saveIndicator) {
            saveIndicator.style.display = this.hasUnsavedChanges() ? 'inline' : 'none';
        }
        
        // Dispatch custom event
        document.dispatchEvent(new CustomEvent('historyUpdate', {
            detail: {
                canUndo: this.canUndo(),
                canRedo: this.canRedo(),
                undoCount: this.undoStack.length - 1,
                redoCount: this.redoStack.length,
                hasUnsavedChanges: this.hasUnsavedChanges()
            }
        }));
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }
        
        // Fallback: create simple notification
        const notification = document.createElement('div');
        notification.className = `undo-notification undo-notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 24px;
            padding: 12px 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
    
    /**
     * Get history summary
     */
    getHistorySummary() {
        return {
            undoCount: this.undoStack.length - 1,
            redoCount: this.redoStack.length,
            canUndo: this.canUndo(),
            canRedo: this.canRedo(),
            hasUnsavedChanges: this.hasUnsavedChanges(),
            actions: this.undoStack.slice(-10).map(item => ({
                action: item.action,
                timestamp: item.timestamp
            }))
        };
    }
}

// Global instance
window.actionHistory = new ActionHistory(50);

// Callback functions (to be implemented by editor)
window.onHistoryUndo = null;
window.onHistoryRedo = null;

// CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100px); opacity: 0; }
    }
    
    .undo-notification-info {
        border-left: 4px solid #3b82f6;
    }
    .undo-notification-warning {
        border-left: 4px solid #f59e0b;
    }
    .undo-notification-success {
        border-left: 4px solid #10b981;
    }
    .undo-notification-error {
        border-left: 4px solid #ef4444;
    }
`;
document.head.appendChild(style);

console.log('📦 Undo/Redo module loaded');

