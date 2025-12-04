let currentSection = 'products';
let currentSector = 'all';

document.addEventListener('DOMContentLoaded', function() {
    toggleFolder(document.querySelector('.folder-item'), 'products-folder');
    loadSection('products');
    selectSector('all', document.querySelector('[data-sector="all"]'));
});

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function toggleFolder(element, folderId) {
    const folder = document.getElementById(folderId);
    const icon = element.querySelector('.folder-icon');
    
    if (folder.classList.contains('expanded')) {
        folder.classList.remove('expanded');
        icon.textContent = '\u{1F4C1}';
        icon.classList.remove('open');
    } else {
        folder.classList.add('expanded');
        icon.textContent = '\u{1F4C2}';
        icon.classList.add('open');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadSection(section) {
    const contentArea = document.getElementById('content-area');
    currentSection = section;
    
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`[data-section="${section}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    contentArea.innerHTML = '<div class="loading"><div class="loading-spinner"></div><span>Yukleniyor...</span></div>';
    
    try {
        const response = await fetch(`/admin/partial/${section}`);
        if (response.ok) {
            const html = await response.text();
            contentArea.innerHTML = html;
            
            if (section === 'products') {
                initProductsSection();
            } else if (section === 'pending') {
                loadPendingProducts();
            } else if (section === 'customers') {
                loadCustomers();
            } else if (section === 'settings') {
                initSettingsSection();
            } else if (section === 'users') {
                await loadUsersModule();
            }
        } else {
            contentArea.innerHTML = '<div class="empty-state"><div class="icon">&#9888;</div><h3>Hata</h3><p>Icerik yuklenemedi</p></div>';
        }
    } catch (error) {
        contentArea.innerHTML = `<div class="empty-state"><div class="icon">&#9888;</div><h3>Baglanti Hatasi</h3><p>${error.message}</p></div>`;
    }
}

function selectSector(sector, element) {
    document.querySelectorAll('.sector-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    
    currentSector = sector;
    
    if (currentSection === 'products') {
        const titles = {
            'all': 'Tüm Ürünler',
            'supermarket': 'Süpermarket',
            'giyim': 'Giyim',
            'teknoloji': 'Teknoloji & Elektronik',
            'kozmetik': 'Kozmetik & Bakım',
            'evyasam': 'Ev & Yaşam',
            'elsanatlari': 'El Yapımı & El Sanatları',
            'restoran': 'Restoran & Kafe',
            'diger': 'Diğer'
        };
        
        const titleEl = document.getElementById('current-view-title');
        if (titleEl) titleEl.textContent = titles[sector] || 'Urunler';
        
        loadProducts();
    }
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 4000);
}

// ========== SÜTUN BOYUTLANDIRMA ==========
function initResize(e, resizer) {
    e.preventDefault();
    e.stopPropagation();
    
    const th = resizer.parentElement;
    const table = th.closest('table');
    const startX = e.pageX;
    const startWidth = th.offsetWidth;
    
    // Add visual feedback
    resizer.classList.add('resizing');
    if (table) table.classList.add('resizing-col');
    document.body.style.cursor = 'col-resize';
    
    function doResize(e) {
        const diff = e.pageX - startX;
        const newWidth = startWidth + diff;
        
        // Minimum width based on column type
        const minWidth = th.classList.contains('col-name') ? 150 : 
                        th.classList.contains('col-barcode') ? 100 : 
                        th.classList.contains('col-thumb') ? 50 : 60;
        
        if (newWidth >= minWidth) {
            th.style.width = newWidth + 'px';
            th.style.minWidth = newWidth + 'px';
        }
    }
    
    function stopResize() {
        resizer.classList.remove('resizing');
        if (table) table.classList.remove('resizing-col');
        document.body.style.cursor = '';
        document.removeEventListener('mousemove', doResize);
        document.removeEventListener('mouseup', stopResize);
        
        // Save column widths to localStorage
        saveColumnWidths();
    }
    
    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
}

// ========== SATIR BOYUTLANDIRMA ==========
function initRowResize(e, resizer) {
    e.preventDefault();
    e.stopPropagation();
    
    const td = resizer.parentElement;
    const tr = td.parentElement;
    const table = tr.closest('table');
    const startY = e.pageY;
    const startHeight = tr.offsetHeight;
    
    // Add visual feedback
    resizer.classList.add('resizing');
    if (table) table.classList.add('resizing-row');
    document.body.style.cursor = 'row-resize';
    
    function doResize(e) {
        const diff = e.pageY - startY;
        const newHeight = startHeight + diff;
        
        // Excel tarzı satır yüksekliği: min 8px, max 30px
        const minHeight = 8;
        const maxHeight = 30;
        
        if (newHeight >= minHeight && newHeight <= maxHeight) {
            tr.style.height = newHeight + 'px';
            // Apply to all cells in row
            tr.querySelectorAll('td').forEach(cell => {
                cell.style.height = newHeight + 'px';
            });
        }
    }
    
    function stopResize() {
        resizer.classList.remove('resizing');
        if (table) table.classList.remove('resizing-row');
        document.body.style.cursor = '';
        document.removeEventListener('mousemove', doResize);
        document.removeEventListener('mouseup', stopResize);
        
        // Save row heights to localStorage
        saveRowHeights();
    }
    
    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
}

// Save row heights to localStorage
function saveRowHeights() {
    const table = document.getElementById('product-table');
    if (!table) return;
    
    const heights = {};
    table.querySelectorAll('tbody tr').forEach((tr, index) => {
        if (tr.style.height) {
            heights[index] = tr.style.height;
        }
    });
    
    localStorage.setItem('adminProductRowHeights', JSON.stringify(heights));
}

// Load row heights from localStorage
function loadRowHeights() {
    const table = document.getElementById('product-table');
    if (!table) return;
    
    try {
        const heights = JSON.parse(localStorage.getItem('adminProductRowHeights') || '{}');
        table.querySelectorAll('tbody tr').forEach((tr, index) => {
            if (heights[index]) {
                tr.style.height = heights[index];
                tr.querySelectorAll('td').forEach(cell => {
                    cell.style.height = heights[index];
                });
            }
        });
    } catch (e) {
        console.error('Error loading row heights:', e);
    }
}

// Save column widths to localStorage
function saveColumnWidths() {
    const table = document.getElementById('product-table');
    if (!table) return;
    
    const widths = {};
    table.querySelectorAll('thead th').forEach((th, index) => {
        if (th.style.width) {
            widths[index] = th.style.width;
        }
    });
    
    localStorage.setItem('adminProductColumnWidths', JSON.stringify(widths));
}

// Load column widths from localStorage
function loadColumnWidths() {
    const table = document.getElementById('product-table');
    if (!table) return;
    
    try {
        const widths = JSON.parse(localStorage.getItem('adminProductColumnWidths') || '{}');
        table.querySelectorAll('thead tr:first-child th').forEach((th, index) => {
            if (widths[index]) {
                th.style.width = widths[index];
                th.style.minWidth = widths[index];
            }
        });
    } catch (e) {
        console.error('Error loading column widths:', e);
    }
}

// Double-click to auto-fit column width
function autoFitColumn(e, resizer) {
    e.preventDefault();
    const th = resizer.parentElement;
    const table = th.closest('table');
    const columnIndex = Array.from(th.parentElement.children).indexOf(th);
    
    // Find max content width in this column
    let maxWidth = 80;
    table.querySelectorAll('tbody tr').forEach(row => {
        const cell = row.children[columnIndex];
        if (cell) {
            const content = cell.querySelector('span, img, button') || cell;
            maxWidth = Math.max(maxWidth, content.scrollWidth + 20);
        }
    });
    
    th.style.width = Math.min(maxWidth, 400) + 'px';
    th.style.minWidth = th.style.width;
    saveColumnWidths();
}

async function loadUsersModule() {
    return new Promise((resolve) => {
        if (typeof AdminUsers !== 'undefined') {
            AdminUsers.init();
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = '/static/js/admin/admin_users.js';
        script.onload = () => {
            if (typeof AdminUsers !== 'undefined') {
                AdminUsers.init();
            }
            resolve();
        };
        script.onerror = () => {
            console.error('Admin Users script yuklenemedi');
            resolve();
        };
        document.head.appendChild(script);
    });
}
