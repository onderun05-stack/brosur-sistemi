function initSettingsSection() {
    loadAIPricing();
    loadUsers();
    loadGeneralSettings();
}

function switchSettingsTab(tabName, element) {
    document.querySelectorAll('.settings-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.settings-panel').forEach(panel => panel.classList.remove('active'));
    
    element.classList.add('active');
    const panel = document.getElementById(`panel-${tabName}`);
    if (panel) panel.classList.add('active');
}

async function loadAIPricing() {
    try {
        const response = await fetch('/api/admin/settings/ai-pricing');
        const data = await response.json();
        
        if (data.success && data.settings) {
            document.getElementById('price-gpt4o').value = data.settings.gpt4o_price || 10;
            document.getElementById('price-gpt4o-mini').value = data.settings.gpt4o_mini_price || 2;
            document.getElementById('price-dalle3').value = data.settings.dalle3_price || 50;
            document.getElementById('default-credits').value = data.settings.default_credits || 100;
        }
    } catch (error) {
        console.error('AI pricing load error:', error);
    }
}

async function saveAIPricing() {
    const settings = {
        gpt4o_price: parseInt(document.getElementById('price-gpt4o').value) || 10,
        gpt4o_mini_price: parseInt(document.getElementById('price-gpt4o-mini').value) || 2,
        dalle3_price: parseInt(document.getElementById('price-dalle3').value) || 50,
        default_credits: parseInt(document.getElementById('default-credits').value) || 100
    };
    
    try {
        const response = await fetch('/api/admin/settings/ai-pricing', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('AI fiyatlandirma kaydedildi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

async function loadUsers() {
    const tbody = document.getElementById('users-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">Yukleniyor...</td></tr>';
    
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        if (data.success && data.users) {
            if (data.users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;">Kullanici bulunamadi</td></tr>';
            } else {
                let html = '';
                data.users.forEach((user, index) => {
                    const roleClass = user.role === 'admin' ? 'color:#dc3545;font-weight:600;' : '';
                    html += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${escapeHtml(user.username)}</td>
                            <td>${escapeHtml(user.email)}</td>
                            <td style="${roleClass}">${user.role}</td>
                            <td>${user.credits || 0}</td>
                            <td>
                                <button class="btn-edit" onclick="openAddCreditModal(${user.id}, '${escapeHtml(user.username)}', ${user.credits || 0})">Kredi</button>
                                <button class="btn-edit" onclick="toggleUserRole(${user.id}, '${user.role}')" style="margin-left:5px;">Rol</button>
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            }
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:#dc3545;">Hata: ${error.message}</td></tr>`;
    }
}

function openAddCreditModal(userId, username, currentCredits) {
    const amount = prompt(`${username} icin eklenecek kredi miktari:\n(Mevcut: ${currentCredits} kredi)`);
    if (amount !== null && !isNaN(amount)) {
        addCreditsToUser(userId, parseInt(amount));
    }
}

async function addCreditsToUser(userId, amount) {
    try {
        const response = await fetch('/api/admin/users/add-credits', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, amount: amount})
        });
        
        const result = await response.json();
        if (result.success) {
            loadUsers();
            showNotification(`${amount} kredi eklendi`, 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

async function toggleUserRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    
    if (!confirm(`Kullanici rolu "${newRole}" olarak degistirilsin mi?`)) return;
    
    try {
        const response = await fetch('/api/admin/users/update-role', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, role: newRole})
        });
        
        const result = await response.json();
        if (result.success) {
            loadUsers();
            showNotification('Kullanici rolu guncellendi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

async function loadGeneralSettings() {
    try {
        const response = await fetch('/api/admin/settings/general');
        const data = await response.json();
        
        if (data.success && data.settings) {
            document.getElementById('site-title').value = data.settings.site_title || 'AEU Yazilim Brosur Sistemi';
            document.getElementById('company-name').value = data.settings.company_name || 'AEU Yazilim';
            document.getElementById('primary-color').value = data.settings.primary_color || '#667eea';
            document.getElementById('secondary-color').value = data.settings.secondary_color || '#764ba2';
            
            // Logo yükle
            if (data.settings.logo_url) {
                const preview = document.getElementById('logo-preview');
                const placeholder = document.getElementById('logo-placeholder');
                if (preview) {
                    preview.src = data.settings.logo_url;
                    preview.style.display = 'block';
                    if (placeholder) placeholder.style.display = 'none';
                }
            }
        }
    } catch (error) {
        console.error('General settings load error:', error);
    }
}

async function saveGeneralSettings() {
    const settings = {
        site_title: document.getElementById('site-title').value,
        company_name: document.getElementById('company-name').value,
        primary_color: document.getElementById('primary-color').value,
        secondary_color: document.getElementById('secondary-color').value
    };
    
    try {
        const response = await fetch('/api/admin/settings/general', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('Genel ayarlar kaydedildi', 'success');
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Baglanti hatasi: ' + error.message, 'error');
    }
}

// Logo yükleme fonksiyonu
async function uploadLogo() {
    const fileInput = document.getElementById('logo-upload');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showNotification('Lütfen bir logo dosyası seçin', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Dosya tipi kontrolü
    if (!file.type.startsWith('image/')) {
        showNotification('Lütfen bir resim dosyası seçin', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('logo', file);
    
    try {
        const response = await fetch('/api/admin/upload-logo', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('Logo başarıyla yüklendi!', 'success');
            // Preview güncelle
            const preview = document.getElementById('logo-preview');
            const placeholder = document.getElementById('logo-placeholder');
            if (preview) {
                preview.src = result.logo_url + '?t=' + Date.now();
                preview.style.display = 'block';
                if (placeholder) placeholder.style.display = 'none';
            }
        } else {
            showNotification('Hata: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Bağlantı hatası: ' + error.message, 'error');
    }
}

// Logo seçildiğinde preview göster
function handleLogoSelect(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('logo-preview');
            const placeholder = document.getElementById('logo-placeholder');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
                if (placeholder) placeholder.style.display = 'none';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

async function loadCustomers() {
    const tbody = document.getElementById('customers-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6"><div class="loading"><div class="loading-spinner"></div><span>Yukleniyor...</span></div></td></tr>';
    
    try {
        const response = await fetch('/api/admin/customers');
        const data = await response.json();
        
        if (data.success && data.customers) {
            const countEl = document.getElementById('customer-count');
            if (countEl) countEl.textContent = `${data.customers.length} musteri`;
            
            if (data.customers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="icon">&#128101;</div><h3>Musteri Bulunamadi</h3></div></td></tr>';
            } else {
                let html = '';
                data.customers.forEach((c, index) => {
                    html += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${escapeHtml(c.username)}</td>
                            <td>${escapeHtml(c.email)}</td>
                            <td>${c.credits || 0}</td>
                            <td>${c.created_at || '-'}</td>
                            <td>
                                <button class="btn-edit" onclick="viewCustomerProducts(${c.id})">Urunler</button>
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

function viewCustomerProducts(customerId) {
    showNotification('Musteri urunleri goruntuleme yakinda eklenecek', 'info');
}
