const AdminUsers = {
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
    users: [],
    
    init() {
        console.log('Admin Users module initialized');
        this.bindEvents();
        this.loadUsers();
    },
    
    bindEvents() {
        const searchInput = document.getElementById('user-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.filterUsers(), 300));
        }
        
        const roleFilter = document.getElementById('role-filter');
        if (roleFilter) {
            roleFilter.addEventListener('change', () => this.filterUsers());
        }
        
        const addBtn = document.getElementById('add-user-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showModal());
        }
        
        const closeModal = document.getElementById('close-modal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.hideModal());
        }
        
        const cancelBtn = document.getElementById('cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideModal());
        }
        
        const userForm = document.getElementById('user-form');
        if (userForm) {
            userForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        const prevBtn = document.getElementById('prev-page');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.prevPage());
        }
        
        const nextBtn = document.getElementById('next-page');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextPage());
        }
        
        const modal = document.getElementById('user-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal();
            });
        }
    },
    
    async loadUsers() {
        try {
            const response = await fetch('/api/admin/users');
            const data = await response.json();
            
            if (data.success) {
                this.users = data.users || [];
                this.renderUsers(this.users);
            } else {
                this.showError('Kullanıcılar yüklenemedi: ' + (data.error || 'Bilinmeyen hata'));
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Kullanıcılar yüklenirken hata oluştu');
        }
    },
    
    filterUsers() {
        const searchTerm = document.getElementById('user-search')?.value.toLowerCase() || '';
        const roleFilter = document.getElementById('role-filter')?.value || '';
        
        let filtered = this.users.filter(user => {
            const matchesSearch = !searchTerm || 
                (user.name && user.name.toLowerCase().includes(searchTerm)) ||
                (user.email && user.email.toLowerCase().includes(searchTerm));
            const matchesRole = !roleFilter || user.role === roleFilter;
            return matchesSearch && matchesRole;
        });
        
        this.renderUsers(filtered);
    },
    
    renderUsers(users) {
        const tbody = document.getElementById('users-tbody');
        if (!tbody) return;
        
        if (!users || users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="padding: 3rem; text-align: center; color: rgba(255,255,255,0.5);">
                        Kullanıcı bulunamadı
                    </td>
                </tr>
            `;
            return;
        }
        
        const sectorNames = {
            'supermarket': 'Süpermarket',
            'giyim': 'Giyim',
            'teknoloji': 'Teknoloji & Elektronik',
            'kozmetik': 'Kozmetik & Bakım',
            'evyasam': 'Ev & Yaşam',
            'elsanatlari': 'El Yapımı & El Sanatları',
            'restoran': 'Restoran & Kafe',
            'diger': 'Diğer'
        };
        
        tbody.innerHTML = users.map(user => `
            <tr data-user-id="${user.id}">
                <td>${user.id || '-'}</td>
                <td>${this.escapeHtml(user.name || 'İsimsiz')}</td>
                <td>${this.escapeHtml(user.email || '-')}</td>
                <td>
                    <span class="role-badge role-${user.role || 'customer'}">
                        ${user.role === 'admin' ? 'Admin' : 'Müşteri'}
                    </span>
                </td>
                <td>${sectorNames[user.sector] || user.sector || '-'}</td>
                <td style="text-align: center;">
                    <span style="color: #4caf50; font-weight: 600;">${user.credits || 0}</span>
                </td>
                <td style="text-align: center; color: rgba(255,255,255,0.6);">
                    ${user.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}
                </td>
                <td style="text-align: center;">
                    <button class="action-btn edit-btn" onclick="AdminUsers.editUser(${user.id})" title="Düzenle">✏️</button>
                    <button class="action-btn credit-btn" onclick="AdminUsers.addCredit(${user.id})" title="Kredi Ekle">💳</button>
                    <button class="action-btn delete-btn" onclick="AdminUsers.deleteUser(${user.id})" title="Sil">🗑️</button>
                </td>
            </tr>
        `).join('');
    },
    
    showModal(user = null) {
        const modal = document.getElementById('user-modal');
        const title = document.getElementById('modal-title');
        const form = document.getElementById('user-form');
        
        if (!modal || !form) return;
        
        form.reset();
        document.getElementById('user-id').value = '';
        
        if (user) {
            title.textContent = 'Kullanıcı Düzenle';
            document.getElementById('user-id').value = user.id;
            document.getElementById('user-name').value = user.name || '';
            document.getElementById('user-email').value = user.email || '';
            document.getElementById('user-role').value = user.role || 'customer';
            document.getElementById('user-sector').value = user.sector || 'supermarket';
            document.getElementById('user-credits').value = user.credits || 0;
        } else {
            title.textContent = 'Yeni Kullanıcı';
        }
        
        modal.style.display = 'flex';
    },
    
    hideModal() {
        const modal = document.getElementById('user-modal');
        if (modal) modal.style.display = 'none';
    },
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const userId = document.getElementById('user-id').value;
        const userData = {
            name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            password: document.getElementById('user-password').value,
            role: document.getElementById('user-role').value,
            sector: document.getElementById('user-sector').value,
            credits: parseInt(document.getElementById('user-credits').value) || 0
        };
        
        if (!userData.password) delete userData.password;
        
        try {
            const url = userId ? `/api/admin/users/${userId}` : '/api/admin/users';
            const method = userId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideModal();
                this.loadUsers();
                this.showNotification(userId ? 'Kullanıcı güncellendi' : 'Kullanıcı oluşturuldu', 'success');
            } else {
                this.showNotification('Hata: ' + (data.error || 'Bilinmeyen hata'), 'error');
            }
        } catch (error) {
            console.error('Error saving user:', error);
            this.showNotification('Kullanıcı kaydedilemedi', 'error');
        }
    },
    
    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            this.showModal(user);
        }
    },
    
    async addCredit(userId) {
        const amount = prompt('Eklenecek kredi miktarı:');
        if (amount === null) return;
        
        const credits = parseInt(amount);
        if (isNaN(credits) || credits <= 0) {
            this.showNotification('Geçerli bir miktar girin', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/users/${userId}/credits`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: credits })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadUsers();
                this.showNotification(`${credits} kredi eklendi`, 'success');
            } else {
                this.showNotification('Hata: ' + (data.error || 'Bilinmeyen hata'), 'error');
            }
        } catch (error) {
            console.error('Error adding credits:', error);
            this.showNotification('Kredi eklenemedi', 'error');
        }
    },
    
    async deleteUser(userId) {
        if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
        
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadUsers();
                this.showNotification('Kullanıcı silindi', 'success');
            } else {
                this.showNotification('Hata: ' + (data.error || 'Bilinmeyen hata'), 'error');
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showNotification('Kullanıcı silinemedi', 'error');
        }
    },
    
    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadUsers();
        }
    },
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadUsers();
        }
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    showNotification(message, type = 'info') {
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            alert(message);
        }
    },
    
    showError(message) {
        const tbody = document.getElementById('users-tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="padding: 3rem; text-align: center; color: #f44336;">
                        ${message}
                    </td>
                </tr>
            `;
        }
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminUsers;
}
