let allProducts = [];

function initProductsSection() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterProducts, 300));
    }
    
    // Load saved column widths
    if (typeof loadColumnWidths === 'function') {
        loadColumnWidths();
    }
    
    loadProducts();
}

function buildFsImageUrl(product, size = 'thumb') {
    const params = new URLSearchParams({
        path: product.source || 'customer',
        sector: product.sector || 'supermarket',
        barcode: product.barcode || '',
        customer_id: product.customer_id || '',
        size
    });
    return `/admin/get-image?${params.toString()}`;
}

function getProductThumbUrl(product) {
    if ((product.image_handler === 'url' || !product.source) && product.image_url) {
        return product.image_url;
    }
    return buildFsImageUrl(product, 'thumb');
}

function getProductPreviewUrl(product) {
    if ((product.image_handler === 'url' || !product.source) && product.image_url) {
        return product.image_url;
    }
    return buildFsImageUrl(product, 'full');
}

async function loadProducts() {
    const tbody = document.getElementById('products-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = `<tr><td colspan="8"><div class="loading"><div class="loading-spinner"></div><span>Yukleniyor...</span></div></td></tr>`;
    
    try {
        const search = document.getElementById('search-input')?.value || '';
        const sector = (typeof currentSector !== 'undefined' && currentSector !== 'all') ? currentSector : '';
        
        const response = await fetch(`/api/admin/all-products?search=${encodeURIComponent(search)}&sector=${sector}`);
        const data = await response.json();
        
        if (data.success) {
            allProducts = data.products;
            renderProducts(allProducts);
            updateCounts(allProducts);
        } else {
            tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="icon">&#9888;</div><h3>Hata</h3><p>${data.error}</p></div></td></tr>`;
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="icon">&#9888;</div><h3>Baglanti Hatasi</h3><p>${error.message}</p></div></td></tr>`;
    }
}

function renderProducts(products) {
    const tbody = document.getElementById('products-tbody');
    if (!tbody) return;
    
    if (products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="icon">&#128193;</div><h3>Urun Bulunamadi</h3><p>Bu kategoride henuz urun yok</p></div></td></tr>`;
        const statusRight = document.getElementById('status-right');
        if (statusRight) statusRight.textContent = '0 urun';
        return;
    }
    
    let html = '';
    products.forEach(product => {
        const qualityClass = getQualityClass(product.image_quality || 'unknown');
        const qualityTitle = getQualityTitle(product.image_quality || 'unknown');
        const sourceInfo = getSourceInfo(product.image_source || product.source || 'unknown');
        
        // Ürün adı: Eğer boş veya barkod ile aynıysa "İsimsiz" göster
        let displayName = product.product_name || '';
        if (!displayName || displayName === product.barcode) {
            displayName = '(İsimsiz - Düzenle)';
        }
        
        // Satış fiyatı formatla
        const price = product.market_price || product.price || 0;
        const priceDisplay = price > 0 ? `₺${parseFloat(price).toFixed(2)}` : '-';
        
        const thumbUrl = getProductThumbUrl(product) || '/static/placeholder.png';
        const previewUrl = getProductPreviewUrl(product) || '';
        const imageHandler = product.image_handler || (product.image_url ? 'url' : 'fs');
        const safeThumb = escapeHtml(thumbUrl);
        const safeImageUrl = escapeHtml(product.image_url || previewUrl || '');
        const safeSource = escapeHtml(product.source || product.image_source || '');
        const safeSector = escapeHtml(product.sector || '');
        const safeBarcode = escapeHtml(product.barcode || '');
        const safeCustomer = escapeHtml(product.customer_id || '');
        
        const allowEdit = product.allow_edit !== false;
        const editHandler = `openEditModal('${product.barcode}', '${escapeHtml(product.product_name || '')}', '${product.product_group || 'Genel'}', '${product.sector}', '${product.source}', '${product.customer_id || ''}')`;
        const rowClickAttr = allowEdit ? `onclick="${editHandler}"` : '';
        const editButtonHtml = allowEdit 
            ? `<button class="btn-edit" onclick="event.stopPropagation(); ${editHandler}">Düzenle</button>`
            : `<span class="text-muted" style="opacity:0.6;">—</span>`;
        
        html += `
            <tr ${rowClickAttr} data-barcode="${product.barcode}" data-name="${escapeHtml(displayName).toLowerCase()}" data-group="${(product.product_group || 'Genel').toLowerCase()}" data-source="${product.image_source || product.source || ''}" data-price="${price}">
                <td class="col-quality">
                    <span class="quality-indicator ${qualityClass}" title="${qualityTitle}"></span>
                    <div class="row-resizer" onmousedown="initRowResize(event, this)" title="Satır yüksekliğini ayarla"></div>
                </td>
                <td class="col-thumb thumb-cell">
                    <img class="thumb-img" 
                         src="${safeThumb}" 
                         alt="${escapeHtml(displayName)}"
                         data-image-handler="${imageHandler}"
                         data-image-url="${safeImageUrl}"
                         data-source="${safeSource}"
                         data-sector="${safeSector}"
                         data-barcode="${safeBarcode}"
                         data-customer="${safeCustomer}"
                         onerror="this.src='/static/placeholder.png'"
                         onmouseenter="handleThumbHover(event, this)"
                         onmouseleave="hideHoverPreview()"
                         onmousemove="moveHoverPreview(event)">
                </td>
                <td class="col-barcode">${product.barcode}</td>
                <td class="col-name ${!product.product_name || product.product_name === product.barcode ? 'text-warning' : ''}">${escapeHtml(displayName)}</td>
                <td class="col-group">${product.product_group || 'Genel'}</td>
                <td class="col-source">
                    <span class="source-badge ${sourceInfo.class}" title="${sourceInfo.title}">
                        ${sourceInfo.icon} ${sourceInfo.label}
                    </span>
                </td>
                <td class="col-price">${priceDisplay}</td>
                <td class="col-actions">
                    ${editButtonHtml}
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    const statusRight = document.getElementById('status-right');
    if (statusRight) statusRight.textContent = `${products.length} urun`;
}

// Excel-style column filtering
function applyColumnFilters() {
    const barcodeFilter = (document.getElementById('filter-barcode')?.value || '').toLowerCase();
    const nameFilter = (document.getElementById('filter-name')?.value || '').toLowerCase();
    const groupFilter = document.getElementById('filter-group')?.value || '';
    const sourceFilter = document.getElementById('filter-source')?.value || '';
    const priceFilter = document.getElementById('filter-price')?.value || '';
    
    const rows = document.querySelectorAll('#products-tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        if (row.querySelector('.empty-state') || row.querySelector('.loading')) {
            return; // Skip empty/loading rows
        }
        
        const barcode = row.dataset.barcode || '';
        const name = row.dataset.name || '';
        const group = row.dataset.group || '';
        const source = row.dataset.source || '';
        const price = row.dataset.price || '';
        
        let show = true;
        
        if (barcodeFilter && !barcode.toLowerCase().includes(barcodeFilter)) show = false;
        if (nameFilter && !name.includes(nameFilter)) show = false;
        if (groupFilter && !group.includes(groupFilter.toLowerCase())) show = false;
        if (sourceFilter && source !== sourceFilter) show = false;
        if (priceFilter && !price.includes(priceFilter)) show = false;
        
        row.style.display = show ? '' : 'none';
        if (show) visibleCount++;
    });
    
    const statusRight = document.getElementById('status-right');
    if (statusRight) statusRight.textContent = `${visibleCount} urun (filtrelendi)`;
}

// Clear all filters
function clearAllFilters() {
    const filterInputs = document.querySelectorAll('.column-filter');
    filterInputs.forEach(input => {
        if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        } else {
            input.value = '';
        }
    });
    
    // Also clear main search
    const mainSearch = document.getElementById('search-input');
    if (mainSearch) mainSearch.value = '';
    
    // Show all rows
    const rows = document.querySelectorAll('#products-tbody tr');
    rows.forEach(row => row.style.display = '');
    
    const statusRight = document.getElementById('status-right');
    if (statusRight) statusRight.textContent = `${rows.length} urun`;
}

// Get source display info
function getSourceInfo(source) {
    const sources = {
        'customer': { label: 'Müşteri', icon: '👤', class: 'source-customer', title: 'Müşteri tarafından yüklendi' },
        'customer_depot': { label: 'Müşteri Deposu', icon: '📦', class: 'source-customer', title: 'Müşteri deposu kaydı' },
        'admin': { label: 'Admin', icon: '🏢', class: 'source-admin', title: 'Admin tarafından yüklendi' },
        'admin_depot': { label: 'Admin Deposu', icon: '🏢', class: 'source-admin', title: 'Admin deposu kaydı' },
        'google_search': { label: 'Google', icon: '🔍', class: 'source-google', title: 'Google Search ile bulundu' },
        'camgoz': { label: 'CAMGOZ', icon: '📦', class: 'source-camgoz', title: 'CAMGOZ API\'den' },
        'n11': { label: 'N11', icon: '🛒', class: 'source-n11', title: 'N11 API\'den' },
        'trendyol': { label: 'Trendyol', icon: '🛍️', class: 'source-trendyol', title: 'Trendyol API\'den' },
        'manual': { label: 'Manuel', icon: '✏️', class: 'source-manual', title: 'Manuel yükleme' },
        'ai': { label: 'AI', icon: '🤖', class: 'source-ai', title: 'AI tarafından oluşturuldu' },
        'database': { label: 'Veritabanı', icon: '💾', class: 'source-admin', title: 'Veritabanı kaydı' }
    };
    
    return sources[source] || { label: 'Bilinmiyor', icon: '❓', class: 'source-unknown', title: 'Kaynak bilinmiyor' };
}

function getQualityClass(quality) {
    switch(quality) {
        case 'high': return 'quality-high';
        case 'medium': return 'quality-medium';
        case 'low': return 'quality-low';
        default: return 'quality-unknown';
    }
}

function getQualityTitle(quality) {
    switch(quality) {
        case 'high': return 'Yuksek Kalite (1024px+)';
        case 'medium': return 'Orta Kalite (512-1024px)';
        case 'low': return 'Dusuk Kalite (<512px)';
        default: return 'Kalite Bilinmiyor';
    }
}

function updateCounts(products) {
    const counts = {
        'all': 0,
        'supermarket': 0,
        'giyim': 0,
        'teknoloji': 0,
        'kozmetik': 0,
        'evyasam': 0,
        'elsanatlari': 0,
        'restoran': 0,
        'diger': 0
    };
    
    products.forEach(p => {
        counts['all']++;
        if (counts[p.sector] !== undefined) {
            counts[p.sector]++;
        }
    });
    
    Object.keys(counts).forEach(sector => {
        const el = document.getElementById(`count-${sector}`);
        if (el) el.textContent = counts[sector];
    });
}

function filterProducts() {
    const search = document.getElementById('search-input')?.value.toLowerCase() || '';
    
    if (!search) {
        renderProducts(allProducts);
        return;
    }
    
    const filtered = allProducts.filter(p => 
        p.barcode.toLowerCase().includes(search) || 
        p.product_name.toLowerCase().includes(search)
    );
    
    renderProducts(filtered);
}

function handleThumbHover(event, imgEl) {
    const handler = imgEl.dataset.imageHandler || 'fs';
    const directUrl = imgEl.dataset.imageUrl || '';
    let imageUrl = '';
    
    if (handler === 'url' && directUrl) {
        imageUrl = directUrl;
    } else {
        imageUrl = buildFsImageUrl({
            source: imgEl.dataset.source || 'customer',
            sector: imgEl.dataset.sector || 'supermarket',
            barcode: imgEl.dataset.barcode || '',
            customer_id: imgEl.dataset.customer || ''
        }, 'full');
    }
    
    showHoverPreview(event, imageUrl);
}

function showHoverPreview(event, imageUrl) {
    const preview = document.getElementById('hover-preview');
    const previewImg = document.getElementById('hover-preview-img');
    if (!preview || !previewImg) return;
    
    previewImg.src = imageUrl || '/static/placeholder.png';
    preview.classList.add('show');
    moveHoverPreview(event);
}

function hideHoverPreview() {
    const preview = document.getElementById('hover-preview');
    if (preview) preview.classList.remove('show');
}

function moveHoverPreview(event) {
    const preview = document.getElementById('hover-preview');
    if (!preview) return;
    
    const x = event.clientX + 20;
    const y = event.clientY + 20;
    const maxX = window.innerWidth - 320;
    const maxY = window.innerHeight - 320;
    
    preview.style.left = Math.min(x, maxX) + 'px';
    preview.style.top = Math.min(y, maxY) + 'px';
}

// Global function for HTML onchange event
window.updateProductGroupDropdown = async function(sector) {
    const groupSelect = document.getElementById('edit-group');
    if (!groupSelect) {
        console.warn('edit-group element not found');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/product-groups?sector=${sector || 'supermarket'}`);
        const data = await response.json();
        
        if (data.success && data.product_groups) {
            groupSelect.innerHTML = '';
            // İlk seçenek olarak "Seçiniz" ekle
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Seçiniz';
            groupSelect.appendChild(defaultOption);
            // Diğer grupları ekle
            data.product_groups.forEach(group => {
                if (group !== 'Genel') { // Genel'i listeden çıkar (zorunlu alan olduğu için)
                    const option = document.createElement('option');
                    option.value = group;
                    option.textContent = group;
                    groupSelect.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Error loading product groups:', error);
    }
}

async function updateProductGroupDropdown(sector) {
    return window.updateProductGroupDropdown(sector);
}

async function openEditModal(barcode, name, group, sector, source, customerId) {
    // Önce modal'ı aç
    document.getElementById('edit-modal').classList.add('show');
    
    // Modal açıldıktan sonra elementlere eriş
    await new Promise(resolve => setTimeout(resolve, 50)); // DOM'un güncellenmesi için kısa bir bekleme
    
    const barcodeInput = document.getElementById('edit-barcode');
    if (barcodeInput) {
        barcodeInput.value = barcode;
        barcodeInput.readOnly = true;
    }
    
    const nameInput = document.getElementById('edit-name');
    if (nameInput) {
        nameInput.value = name;
    }
    
    const sectorSelect = document.getElementById('edit-sector');
    const selectedSector = sector || 'supermarket';
    if (sectorSelect) {
        sectorSelect.value = selectedSector;
    }
    
    document.getElementById('edit-id').value = JSON.stringify({barcode, sector, source, customerId});
    
    // Update product group dropdown based on sector
    await updateProductGroupDropdown(selectedSector);
    
    const groupSelect = document.getElementById('edit-group');
    if (groupSelect) {
        // Eğer grup varsa ve geçerliyse seç, yoksa boş bırak
        if (group && group !== 'Genel' && group !== '') {
            groupSelect.value = group;
        } else {
            // İlk seçeneği seç (boş veya "Seçiniz")
            if (groupSelect.options.length > 0) {
                groupSelect.value = groupSelect.options[0].value;
            }
        }
    }
    
    const previewImg = document.getElementById('edit-preview-img');
    if (previewImg) {
        previewImg.src = `/admin/get-image?path=${source}&sector=${sector}&barcode=${barcode}&customer_id=${customerId}&size=full`;
        previewImg.style.display = 'block';
    }
    
    const modalTitle = document.querySelector('#edit-modal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Urun Duzenle';
    }
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.remove('show');
}

async function saveProduct() {
    const data = JSON.parse(document.getElementById('edit-id').value);
    const barcode = document.getElementById('edit-barcode').value.trim();
    const name = document.getElementById('edit-name').value.trim();
    const group = document.getElementById('edit-group').value;
    const sector = document.getElementById('edit-sector').value || 'supermarket';
    
    // Validasyon: Barkod zorunlu
    if (!barcode) {
        showNotification('Hata: Barkod gerekli', 'error');
        return;
    }
    
    // Validasyon: Ürün adı zorunlu
    if (!name) {
        showNotification('Hata: Ürün adı gerekli', 'error');
        return;
    }
    
    // Validasyon: Ürün grubu zorunlu (Genel seçilemez)
    if (!group || group === '' || group === 'Genel') {
        showNotification('Hata: Ürün grubu seçilmelidir. Lütfen sektöre uygun bir ürün grubu seçin.', 'error');
        return;
    }
    
    // Validasyon: Sektör zorunlu
    if (!sector) {
        showNotification('Hata: Sektör seçilmelidir', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/update-product', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                barcode: barcode,
                sector: sector,
                source: data.source || 'admin',
                customer_id: data.customerId || '',
                product_name: name,
                product_group: group
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeEditModal();
            loadProducts();
            showNotification('Urun guncellendi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

async function deleteProduct() {
    const data = JSON.parse(document.getElementById('edit-id').value);
    
    if (!data.barcode) {
        showNotification('Silinecek ürün bulunamadı', 'error');
        return;
    }
    
    // Onay iste
    if (!confirm(`"${document.getElementById('edit-name').value || data.barcode}" ürününü silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/delete-product', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                barcode: data.barcode,
                sector: data.sector,
                source: data.source,
                customer_id: data.customerId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeEditModal();
            loadProducts();
            showNotification('Ürün başarıyla silindi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Bağlantı hatası: ' + error.message, 'error');
    }
}

async function openAddProductModal() {
    // Önce modal'ı aç
    document.getElementById('edit-modal').classList.add('show');
    
    // Modal açıldıktan sonra elementlere eriş
    await new Promise(resolve => setTimeout(resolve, 50)); // DOM'un güncellenmesi için kısa bir bekleme
    
    document.getElementById('edit-barcode').value = '';
    document.getElementById('edit-barcode').readOnly = false;
    document.getElementById('edit-name').value = '';
    // currentSector tanımlı değilse varsayılan olarak 'supermarket' kullan
    const sector = typeof currentSector !== 'undefined' ? currentSector : 'supermarket';
    
    const sectorSelect = document.getElementById('edit-sector');
    if (sectorSelect) {
        sectorSelect.value = sector;
    }
    
    document.getElementById('edit-id').value = JSON.stringify({isNew: true, sector: sector});
    
    const previewImg = document.getElementById('edit-preview-img');
    if (previewImg) {
        previewImg.style.display = 'none';
    }
    
    // Update product group dropdown based on sector
    await updateProductGroupDropdown(sector);
    
    const groupSelect = document.getElementById('edit-group');
    if (groupSelect) {
        // İlk seçeneği seç (boş veya "Seçiniz" olabilir)
        if (groupSelect.options.length > 0) {
            groupSelect.value = groupSelect.options[0].value;
        }
    }
    
    const modalTitle = document.querySelector('#edit-modal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Yeni Urun Ekle';
    }
}

async function loadPendingProducts() {
    const tbody = document.getElementById('pending-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = `<tr><td colspan="6"><div class="loading"><div class="loading-spinner"></div><span>Yukleniyor...</span></div></td></tr>`;
    
    try {
        const response = await fetch('/api/admin/pending-approvals');
        const data = await response.json();
        
        if (data.success && data.pending) {
            const badge = document.getElementById('pending-badge');
            if (badge) badge.textContent = data.pending.length;
            
            const countEl = document.getElementById('pending-count');
            if (countEl) countEl.textContent = `${data.pending.length} bekleyen`;
            
            if (data.pending.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">&#9989;</div><h3>Tum Urunler Onaylandi</h3><p>Bekleyen urun yok</p></div></td></tr>`;
            } else {
                let html = '';
                data.pending.forEach(p => {
                    const productName = p.name || p.product_name || '-';
                    const productGroup = p.group || p.product_group || 'Genel';
                    html += `
                        <tr>
                            <td class="col-quality"><span class="quality-indicator quality-unknown"></span></td>
                            <td class="col-thumb thumb-cell">
                                <img class="thumb-img" src="${p.image_url}" alt="${p.barcode}" onerror="this.src='/static/placeholder.png'">
                            </td>
                            <td class="col-barcode">${p.barcode}</td>
                            <td class="col-name">${escapeHtml(productName)}</td>
                            <td class="col-group">${productGroup} (${p.sector})</td>
                            <td class="col-actions" style="width:150px;">
                                <button class="btn-edit" style="background:#d4edda;color:#155724;margin-right:5px;" onclick="approveProduct(${p.id}, '${p.barcode}', '${p.sector}')">Onayla</button>
                                <button class="btn-edit" style="background:#f8d7da;color:#721c24;" onclick="rejectProduct(${p.id}, '${p.barcode}', '${p.sector}')">Reddet</button>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            }
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">&#9888;</div><h3>Hata</h3><p>${error.message}</p></div></td></tr>`;
    }
}

async function approveProduct(id, barcode, sector) {
    try {
        const response = await fetch('/api/admin/approve-product', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id, barcode, sector})
        });
        
        const result = await response.json();
        if (result.success) {
            loadPendingProducts();
            loadProducts(); // Tüm ürünler listesini de yenile
            showNotification('Urun onaylandi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

async function rejectProduct(id, barcode, sector) {
    if (!confirm('Bu urunu reddetmek istediginizden emin misiniz?')) return;
    
    try {
        const response = await fetch('/api/admin/reject-product', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id, barcode, sector})
        });
        
        const result = await response.json();
        if (result.success) {
            loadPendingProducts();
            showNotification('Urun reddedildi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}
