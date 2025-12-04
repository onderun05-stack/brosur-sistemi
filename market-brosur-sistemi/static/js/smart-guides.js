/**
 * Smart Guides for Brochure Editor
 * 
 * Provides visual alignment guides when dragging elements.
 * Uses PNG image boundaries as product box boundaries.
 */

class SmartGuides {
    constructor(options = {}) {
        this.enabled = true;
        this.snapThreshold = 10; // pixels
        this.guideColor = '#6366f1';
        this.guideOpacity = 0.8;
        this.showDistance = true;
        
        this.container = null;
        this.guidesContainer = null;
        this.activeElement = null;
        this.guides = [];
        
        this.init(options);
        
        console.log('✅ Smart guides initialized');
    }
    
    /**
     * Initialize smart guides
     */
    init(options) {
        Object.assign(this, options);
        
        // Create guides container
        this.guidesContainer = document.createElement('div');
        this.guidesContainer.className = 'smart-guides-container';
        this.guidesContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        `;
        
        // Bind drag events
        this.bindEvents();
    }
    
    /**
     * Set the container element
     */
    setContainer(element) {
        this.container = element;
        
        // Add guides container
        if (this.container) {
            this.container.style.position = 'relative';
            this.container.appendChild(this.guidesContainer);
        }
    }
    
    /**
     * Bind drag events
     */
    bindEvents() {
        document.addEventListener('dragstart', (e) => this.onDragStart(e));
        document.addEventListener('drag', (e) => this.onDrag(e));
        document.addEventListener('dragend', (e) => this.onDragEnd(e));
        
        // For touch/mouse drag
        document.addEventListener('mousedown', (e) => {
            const draggable = e.target.closest('[draggable="true"], .draggable, .product-box');
            if (draggable) {
                this.onDragStart({ target: draggable });
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.activeElement) {
                this.onDrag(e);
            }
        });
        
        document.addEventListener('mouseup', (e) => {
            if (this.activeElement) {
                this.onDragEnd(e);
            }
        });
    }
    
    /**
     * Handle drag start
     */
    onDragStart(e) {
        if (!this.enabled || !this.container) return;
        
        this.activeElement = e.target.closest('.product-box, .product-item, [data-product-id]');
        
        if (!this.activeElement) return;
        
        // Collect other elements for alignment
        this.collectAlignmentTargets();
    }
    
    /**
     * Handle drag
     */
    onDrag(e) {
        if (!this.enabled || !this.activeElement) return;
        
        const rect = this.activeElement.getBoundingClientRect();
        const containerRect = this.container.getBoundingClientRect();
        
        // Calculate relative position
        const elementBounds = {
            left: rect.left - containerRect.left,
            top: rect.top - containerRect.top,
            right: rect.right - containerRect.left,
            bottom: rect.bottom - containerRect.top,
            centerX: (rect.left + rect.right) / 2 - containerRect.left,
            centerY: (rect.top + rect.bottom) / 2 - containerRect.top,
            width: rect.width,
            height: rect.height
        };
        
        // Find alignments
        const alignments = this.findAlignments(elementBounds);
        
        // Draw guides
        this.drawGuides(alignments);
        
        // Snap if close enough
        this.applySnapping(alignments);
    }
    
    /**
     * Handle drag end
     */
    onDragEnd(e) {
        this.activeElement = null;
        this.clearGuides();
    }
    
    /**
     * Collect other elements to align with
     */
    collectAlignmentTargets() {
        this.alignmentTargets = [];
        
        const elements = this.container.querySelectorAll('.product-box, .product-item, [data-product-id]');
        const containerRect = this.container.getBoundingClientRect();
        
        elements.forEach(el => {
            if (el === this.activeElement) return;
            
            const rect = el.getBoundingClientRect();
            
            this.alignmentTargets.push({
                element: el,
                left: rect.left - containerRect.left,
                top: rect.top - containerRect.top,
                right: rect.right - containerRect.left,
                bottom: rect.bottom - containerRect.top,
                centerX: (rect.left + rect.right) / 2 - containerRect.left,
                centerY: (rect.top + rect.bottom) / 2 - containerRect.top
            });
        });
        
        // Add container boundaries and center
        const width = containerRect.width;
        const height = containerRect.height;
        
        this.containerGuides = {
            left: 0,
            right: width,
            top: 0,
            bottom: height,
            centerX: width / 2,
            centerY: height / 2
        };
    }
    
    /**
     * Find alignments with other elements
     */
    findAlignments(elementBounds) {
        const alignments = {
            horizontal: [],
            vertical: []
        };
        
        // Check container guides
        this.checkAlignment(elementBounds, this.containerGuides, alignments, 'container');
        
        // Check other elements
        this.alignmentTargets.forEach((target, index) => {
            this.checkAlignment(elementBounds, target, alignments, `element-${index}`);
        });
        
        return alignments;
    }
    
    /**
     * Check alignment between two elements
     */
    checkAlignment(source, target, alignments, targetId) {
        const threshold = this.snapThreshold;
        
        // Horizontal alignments (Y axis)
        const horizontalChecks = [
            { source: 'top', target: 'top', label: 'Üst kenar' },
            { source: 'top', target: 'bottom', label: 'Üst-Alt' },
            { source: 'bottom', target: 'top', label: 'Alt-Üst' },
            { source: 'bottom', target: 'bottom', label: 'Alt kenar' },
            { source: 'centerY', target: 'centerY', label: 'Dikey orta' }
        ];
        
        horizontalChecks.forEach(check => {
            const diff = Math.abs(source[check.source] - target[check.target]);
            if (diff < threshold) {
                alignments.horizontal.push({
                    y: target[check.target],
                    sourceY: source[check.source],
                    diff,
                    targetId,
                    label: check.label
                });
            }
        });
        
        // Vertical alignments (X axis)
        const verticalChecks = [
            { source: 'left', target: 'left', label: 'Sol kenar' },
            { source: 'left', target: 'right', label: 'Sol-Sağ' },
            { source: 'right', target: 'left', label: 'Sağ-Sol' },
            { source: 'right', target: 'right', label: 'Sağ kenar' },
            { source: 'centerX', target: 'centerX', label: 'Yatay orta' }
        ];
        
        verticalChecks.forEach(check => {
            const diff = Math.abs(source[check.source] - target[check.target]);
            if (diff < threshold) {
                alignments.vertical.push({
                    x: target[check.target],
                    sourceX: source[check.source],
                    diff,
                    targetId,
                    label: check.label
                });
            }
        });
        
        return alignments;
    }
    
    /**
     * Draw alignment guides
     */
    drawGuides(alignments) {
        this.clearGuides();
        
        // Draw horizontal guides
        alignments.horizontal.forEach(align => {
            const guide = this.createHorizontalGuide(align.y);
            this.guidesContainer.appendChild(guide);
            this.guides.push(guide);
            
            if (this.showDistance && align.diff > 0) {
                const label = this.createDistanceLabel(
                    this.container.offsetWidth / 2,
                    align.y - 15,
                    `${Math.round(align.diff)}px`
                );
                this.guidesContainer.appendChild(label);
                this.guides.push(label);
            }
        });
        
        // Draw vertical guides
        alignments.vertical.forEach(align => {
            const guide = this.createVerticalGuide(align.x);
            this.guidesContainer.appendChild(guide);
            this.guides.push(guide);
            
            if (this.showDistance && align.diff > 0) {
                const label = this.createDistanceLabel(
                    align.x + 5,
                    this.container.offsetHeight / 2,
                    `${Math.round(align.diff)}px`
                );
                this.guidesContainer.appendChild(label);
                this.guides.push(label);
            }
        });
    }
    
    /**
     * Create horizontal guide line
     */
    createHorizontalGuide(y) {
        const guide = document.createElement('div');
        guide.className = 'smart-guide smart-guide-horizontal';
        guide.style.cssText = `
            position: absolute;
            left: 0;
            right: 0;
            top: ${y}px;
            height: 1px;
            background: ${this.guideColor};
            opacity: ${this.guideOpacity};
            box-shadow: 0 0 4px ${this.guideColor};
        `;
        return guide;
    }
    
    /**
     * Create vertical guide line
     */
    createVerticalGuide(x) {
        const guide = document.createElement('div');
        guide.className = 'smart-guide smart-guide-vertical';
        guide.style.cssText = `
            position: absolute;
            top: 0;
            bottom: 0;
            left: ${x}px;
            width: 1px;
            background: ${this.guideColor};
            opacity: ${this.guideOpacity};
            box-shadow: 0 0 4px ${this.guideColor};
        `;
        return guide;
    }
    
    /**
     * Create distance label
     */
    createDistanceLabel(x, y, text) {
        const label = document.createElement('div');
        label.className = 'smart-guide-label';
        label.textContent = text;
        label.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            padding: 2px 6px;
            background: ${this.guideColor};
            color: white;
            font-size: 10px;
            border-radius: 3px;
            white-space: nowrap;
        `;
        return label;
    }
    
    /**
     * Apply snapping to closest alignment
     */
    applySnapping(alignments) {
        if (!this.activeElement) return;
        
        // Find best horizontal alignment
        const bestH = alignments.horizontal.reduce((best, curr) => 
            !best || curr.diff < best.diff ? curr : best, null);
        
        // Find best vertical alignment
        const bestV = alignments.vertical.reduce((best, curr) =>
            !best || curr.diff < best.diff ? curr : best, null);
        
        // Dispatch snap event
        if (bestH || bestV) {
            document.dispatchEvent(new CustomEvent('smartGuideSnap', {
                detail: {
                    element: this.activeElement,
                    horizontal: bestH,
                    vertical: bestV
                }
            }));
        }
    }
    
    /**
     * Clear all guides
     */
    clearGuides() {
        this.guides.forEach(guide => guide.remove());
        this.guides = [];
    }
    
    /**
     * Enable/disable guides
     */
    enable() { this.enabled = true; }
    disable() { this.enabled = false; }
    toggle() { this.enabled = !this.enabled; }
}

// Global instance (initialized when canvas is ready)
window.smartGuides = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('brochure-canvas') || 
                   document.getElementById('canvas') ||
                   document.querySelector('.canvas-area');
    
    if (canvas) {
        window.smartGuides = new SmartGuides();
        window.smartGuides.setContainer(canvas);
    }
});

console.log('📦 Smart guides module loaded');

