/**
 * Profesyonel Broşür Şablonları
 * Kırmızı Market tarzı hazır tasarımlar
 */

// ============= ŞABLON VERİLERİ =============

const BROCHURE_TEMPLATES = {
    
    // 1. Klasik Market Şablonu (Kırmızı Market tarzı)
    'classic-market': {
        id: 'classic-market',
        name: 'Klasik Market',
        description: 'Kırmızı Market tarzı profesyonel tasarım',
        preview: '/static/templates/classic-market-preview.png',
        colors: {
            primary: '#e53935',      // Kırmızı
            secondary: '#43a047',    // Yeşil
            accent: '#fdd835',       // Sarı
            background: '#ffffff',
            text: '#333333',
            priceOld: '#999999',
            priceNew: '#e53935'
        },
        layout: {
            header: {
                height: 120,
                logoPosition: 'left',
                sloganPosition: 'center',
                datePosition: 'right',
                backgroundColor: '#e53935',
                textColor: '#ffffff'
            },
            grid: {
                columns: 3,
                rows: 4,
                gap: 10,
                padding: 15
            },
            productCard: {
                style: 'classic',
                showOldPrice: true,
                showDiscount: true,
                showBadge: true,
                imageSize: 'medium'
            }
        },
        badges: ['sok-fiyat', 'kaliteli', 'yeni'],
        fonts: {
            header: 'Arial Black',
            product: 'Arial',
            price: 'Arial Black'
        }
    },
    
    // 2. Modern Minimal Şablon
    'modern-minimal': {
        id: 'modern-minimal',
        name: 'Modern Minimal',
        description: 'Temiz ve modern tasarım',
        preview: '/static/templates/modern-minimal-preview.png',
        colors: {
            primary: '#2d3436',
            secondary: '#0984e3',
            accent: '#00b894',
            background: '#f8f9fa',
            text: '#2d3436',
            priceOld: '#b2bec3',
            priceNew: '#0984e3'
        },
        layout: {
            header: {
                height: 80,
                logoPosition: 'left',
                sloganPosition: 'center',
                datePosition: 'right',
                backgroundColor: '#2d3436',
                textColor: '#ffffff'
            },
            grid: {
                columns: 4,
                rows: 3,
                gap: 15,
                padding: 20
            },
            productCard: {
                style: 'minimal',
                showOldPrice: true,
                showDiscount: true,
                showBadge: false,
                imageSize: 'large'
            }
        },
        badges: ['indirim'],
        fonts: {
            header: 'Montserrat',
            product: 'Open Sans',
            price: 'Montserrat'
        }
    },
    
    // 3. Ramazan/Bayram Şablonu
    'bayram-special': {
        id: 'bayram-special',
        name: 'Bayram Özel',
        description: 'Ramazan ve bayramlar için özel tasarım',
        preview: '/static/templates/bayram-special-preview.png',
        colors: {
            primary: '#1a5f2a',       // Koyu yeşil
            secondary: '#c9a227',     // Altın
            accent: '#8b0000',        // Bordo
            background: '#fffef5',    // Krem
            text: '#1a5f2a',
            priceOld: '#999999',
            priceNew: '#8b0000'
        },
        layout: {
            header: {
                height: 140,
                logoPosition: 'left',
                sloganPosition: 'center',
                datePosition: 'right',
                backgroundColor: 'linear-gradient(135deg, #1a5f2a 0%, #2d8f4e 100%)',
                textColor: '#c9a227',
                showMoon: true,
                showStars: true
            },
            grid: {
                columns: 3,
                rows: 4,
                gap: 12,
                padding: 15
            },
            productCard: {
                style: 'elegant',
                showOldPrice: true,
                showDiscount: true,
                showBadge: true,
                imageSize: 'medium',
                borderStyle: 'gold'
            }
        },
        badges: ['bayram-firsati', 'ozel'],
        fonts: {
            header: 'Georgia',
            product: 'Georgia',
            price: 'Arial Black'
        }
    },
    
    // 4. Manav/Sebze-Meyve Şablonu
    'fresh-produce': {
        id: 'fresh-produce',
        name: 'Taze Ürünler',
        description: 'Manav ve sebze-meyve için doğal tasarım',
        preview: '/static/templates/fresh-produce-preview.png',
        colors: {
            primary: '#2e7d32',
            secondary: '#81c784',
            accent: '#ff9800',
            background: '#f1f8e9',
            text: '#1b5e20',
            priceOld: '#757575',
            priceNew: '#2e7d32'
        },
        layout: {
            header: {
                height: 100,
                logoPosition: 'left',
                sloganPosition: 'center',
                datePosition: 'right',
                backgroundColor: '#2e7d32',
                textColor: '#ffffff',
                showLeaves: true
            },
            grid: {
                columns: 3,
                rows: 4,
                gap: 10,
                padding: 15
            },
            productCard: {
                style: 'natural',
                showOldPrice: true,
                showDiscount: true,
                showBadge: true,
                imageSize: 'large',
                showWeight: true
            }
        },
        badges: ['taze', 'gunluk', 'organik'],
        fonts: {
            header: 'Verdana',
            product: 'Verdana',
            price: 'Arial Black'
        }
    },
    
    // 5. Kasap Şablonu
    'butcher-premium': {
        id: 'butcher-premium',
        name: 'Premium Kasap',
        description: 'Kasap ve et ürünleri için kaliteli tasarım',
        preview: '/static/templates/butcher-premium-preview.png',
        colors: {
            primary: '#8b0000',
            secondary: '#2d2d2d',
            accent: '#c9a227',
            background: '#1a1a1a',
            text: '#ffffff',
            priceOld: '#888888',
            priceNew: '#c9a227'
        },
        layout: {
            header: {
                height: 100,
                logoPosition: 'left',
                sloganPosition: 'center',
                datePosition: 'right',
                backgroundColor: '#8b0000',
                textColor: '#ffffff'
            },
            grid: {
                columns: 2,
                rows: 3,
                gap: 15,
                padding: 20
            },
            productCard: {
                style: 'premium',
                showOldPrice: true,
                showDiscount: true,
                showBadge: true,
                imageSize: 'xlarge',
                showWeight: true
            }
        },
        badges: ['kaliteli', 'gunluk-kesim', 'helal'],
        fonts: {
            header: 'Georgia',
            product: 'Georgia',
            price: 'Arial Black'
        }
    },
    
    // 6. İş İlanı Şablonu
    'job-posting': {
        id: 'job-posting',
        name: 'İş İlanı',
        description: 'Profesyonel eleman arama broşürü',
        preview: '/static/templates/job-posting-preview.png',
        colors: {
            primary: '#1565c0',
            secondary: '#42a5f5',
            accent: '#ff9800',
            background: '#ffffff',
            text: '#333333',
            highlight: '#1565c0'
        },
        layout: {
            header: {
                height: 150,
                logoPosition: 'center',
                sloganPosition: 'below',
                datePosition: 'none',
                backgroundColor: '#1565c0',
                textColor: '#ffffff'
            },
            content: {
                style: 'job-listing',
                sections: ['pozisyon', 'gereksinimler', 'sunulanlar', 'iletisim']
            }
        },
        badges: [],
        fonts: {
            header: 'Arial Black',
            content: 'Arial',
            highlight: 'Arial Black'
        }
    }
};

// ============= GÜNLÜK & ÖZEL KAMPANYALAR =============

const CAMPAIGN_TYPES = {
    // Haftanın Günleri
    'pazartesi': {
        id: 'pazartesi',
        name: 'Pazartesi İndirimi',
        slogan: 'PAZARTESE ÖZEL FIRSATLAR!',
        icon: '🌙',
        color: '#3f51b5',
        gradient: 'linear-gradient(135deg, #3f51b5 0%, #5c6bc0 100%)',
        description: 'Haftaya indirimle başla!'
    },
    'sali': {
        id: 'sali',
        name: 'Salı İndirimi',
        slogan: 'SALI ÇARŞISI!',
        icon: '🔥',
        color: '#f44336',
        gradient: 'linear-gradient(135deg, #f44336 0%, #ef5350 100%)',
        description: 'Salı günü fırsatları'
    },
    'carsamba': {
        id: 'carsamba',
        name: 'Çarşamba Özel',
        slogan: 'ÇARŞAMBAYA ÖZEL!',
        icon: '⭐',
        color: '#ff9800',
        gradient: 'linear-gradient(135deg, #ff9800 0%, #ffb74d 100%)',
        description: 'Haftanın ortası indirimi'
    },
    'persembe': {
        id: 'persembe',
        name: 'Perşembe Şenliği',
        slogan: 'PERŞEMBE ŞENLİĞİ!',
        icon: '🎉',
        color: '#9c27b0',
        gradient: 'linear-gradient(135deg, #9c27b0 0%, #ba68c8 100%)',
        description: 'Perşembe günü özel fırsatlar'
    },
    'cuma': {
        id: 'cuma',
        name: 'Cuma Fırsatları',
        slogan: 'CUMA FIRSATLARI!',
        icon: '🕌',
        color: '#4caf50',
        gradient: 'linear-gradient(135deg, #4caf50 0%, #81c784 100%)',
        description: 'Cuma günü özel'
    },
    'cumartesi': {
        id: 'cumartesi',
        name: 'Cumartesi Çılgınlığı',
        slogan: 'CUMARTESİ ÇILGINLIĞI!',
        icon: '🛒',
        color: '#e91e63',
        gradient: 'linear-gradient(135deg, #e91e63 0%, #f48fb1 100%)',
        description: 'Hafta sonu alışverişi'
    },
    'pazar': {
        id: 'pazar',
        name: 'Pazar Pazarı',
        slogan: 'PAZAR PAZARI!',
        icon: '☀️',
        color: '#ff5722',
        gradient: 'linear-gradient(135deg, #ff5722 0%, #ff8a65 100%)',
        description: 'Pazar günü indirimleri'
    },
    
    // Özel Günler
    'acilis': {
        id: 'acilis',
        name: 'Açılışa Özel',
        slogan: 'BÜYÜK AÇILIŞ!',
        icon: '🎊',
        color: '#ffd700',
        gradient: 'linear-gradient(135deg, #ffd700 0%, #ffeb3b 100%)',
        description: 'Yeni mağaza açılışı',
        badges: ['acilis-ozel', 'hediye']
    },
    'yildonumu': {
        id: 'yildonumu',
        name: 'Yıldönümü',
        slogan: 'X. YIL ŞENLİĞİ!',
        icon: '🎂',
        color: '#673ab7',
        gradient: 'linear-gradient(135deg, #673ab7 0%, #9575cd 100%)',
        description: 'Kuruluş yıldönümü kutlaması'
    },
    'tasfiye': {
        id: 'tasfiye',
        name: 'Tasfiye',
        slogan: 'BÜYÜK TASFİYE!',
        icon: '📦',
        color: '#795548',
        gradient: 'linear-gradient(135deg, #795548 0%, #a1887f 100%)',
        description: 'Stok eritme kampanyası'
    },
    'sezon-sonu': {
        id: 'sezon-sonu',
        name: 'Sezon Sonu',
        slogan: 'SEZON SONU İNDİRİMLERİ!',
        icon: '🍂',
        color: '#ff7043',
        gradient: 'linear-gradient(135deg, #ff7043 0%, #ffab91 100%)',
        description: 'Sezon sonu fırsatları'
    },
    'hafta-sonu': {
        id: 'hafta-sonu',
        name: 'Hafta Sonu Özel',
        slogan: 'HAFTA SONU FIRSATLARI!',
        icon: '🌟',
        color: '#00bcd4',
        gradient: 'linear-gradient(135deg, #00bcd4 0%, #4dd0e1 100%)',
        description: 'Cumartesi-Pazar indirimleri'
    },
    'ogrenci': {
        id: 'ogrenci',
        name: 'Öğrenci İndirimi',
        slogan: 'ÖĞRENCİYE ÖZEL!',
        icon: '📚',
        color: '#2196f3',
        gradient: 'linear-gradient(135deg, #2196f3 0%, #64b5f6 100%)',
        description: 'Öğrencilere özel fırsatlar'
    },
    'emekli': {
        id: 'emekli',
        name: 'Emekli İndirimi',
        slogan: 'EMEKLİYE ÖZEL!',
        icon: '👴',
        color: '#607d8b',
        gradient: 'linear-gradient(135deg, #607d8b 0%, #90a4ae 100%)',
        description: 'Emeklilere özel kampanya'
    },
    'anne-gunu': {
        id: 'anne-gunu',
        name: 'Anneler Günü',
        slogan: 'ANNELER GÜNÜ\'NE ÖZEL!',
        icon: '💐',
        color: '#e91e63',
        gradient: 'linear-gradient(135deg, #e91e63 0%, #f48fb1 100%)',
        description: 'Anneler günü kampanyası'
    },
    'baba-gunu': {
        id: 'baba-gunu',
        name: 'Babalar Günü',
        slogan: 'BABALAR GÜNÜ\'NE ÖZEL!',
        icon: '👔',
        color: '#3f51b5',
        gradient: 'linear-gradient(135deg, #3f51b5 0%, #7986cb 100%)',
        description: 'Babalar günü kampanyası'
    },
    'sevgililer': {
        id: 'sevgililer',
        name: 'Sevgililer Günü',
        slogan: '14 ŞUBAT\'A ÖZEL!',
        icon: '❤️',
        color: '#d32f2f',
        gradient: 'linear-gradient(135deg, #d32f2f 0%, #ef5350 100%)',
        description: 'Sevgililer günü fırsatları'
    },
    'yilbasi': {
        id: 'yilbasi',
        name: 'Yılbaşı',
        slogan: 'YENİ YIL FIRSATLARI!',
        icon: '🎄',
        color: '#c62828',
        gradient: 'linear-gradient(135deg, #1b5e20 0%, #c62828 100%)',
        description: 'Yılbaşı indirimleri'
    },
    '23-nisan': {
        id: '23-nisan',
        name: '23 Nisan',
        slogan: '23 NİSAN COŞKUSU!',
        icon: '🇹🇷',
        color: '#d32f2f',
        gradient: 'linear-gradient(135deg, #d32f2f 0%, #ef5350 100%)',
        description: '23 Nisan özel kampanya'
    },
    '19-mayis': {
        id: '19-mayis',
        name: '19 Mayıs',
        slogan: '19 MAYIS FIRSATLARI!',
        icon: '🇹🇷',
        color: '#d32f2f',
        gradient: 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)',
        description: '19 Mayıs kampanyası'
    },
    '29-ekim': {
        id: '29-ekim',
        name: '29 Ekim',
        slogan: 'CUMHURİYET BAYRAMI!',
        icon: '🇹🇷',
        color: '#d32f2f',
        gradient: 'linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%)',
        description: 'Cumhuriyet Bayramı indirimleri'
    }
};

// ============= ROZET VERİLERİ =============

const BADGE_STYLES = {
    // Yeni rozetler
    'acilis-ozel': {
        text: 'AÇILIŞA ÖZEL',
        backgroundColor: '#ffd700',
        textColor: '#000000',
        shape: 'star',
        icon: '🎊'
    },
    'hediye': {
        text: 'HEDİYELİ',
        backgroundColor: '#e91e63',
        textColor: '#ffffff',
        shape: 'badge',
        icon: '🎁'
    },
    'sinirli-stok': {
        text: 'SINIRLI STOK',
        backgroundColor: '#ff5722',
        textColor: '#ffffff',
        shape: 'ribbon',
        icon: '⚡'
    },
    'son-gun': {
        text: 'SON GÜN',
        backgroundColor: '#f44336',
        textColor: '#ffffff',
        shape: 'burst',
        icon: '⏰'
    },
    'gun-firsati': {
        text: 'GÜNÜN FIRSATI',
        backgroundColor: '#ff9800',
        textColor: '#000000',
        shape: 'star',
        icon: '⭐'
    },
    'sok-fiyat': {
        text: 'ŞOK FİYAT',
        backgroundColor: '#e53935',
        textColor: '#ffffff',
        shape: 'burst',
        icon: '💥'
    },
    'kaliteli': {
        text: 'KALİTELİ ÜRÜN',
        backgroundColor: '#43a047',
        textColor: '#ffffff',
        shape: 'ribbon',
        icon: '✓'
    },
    'indirim': {
        text: '%{discount} İNDİRİM',
        backgroundColor: '#ff9800',
        textColor: '#000000',
        shape: 'circle',
        icon: ''
    },
    'yeni': {
        text: 'YENİ',
        backgroundColor: '#2196f3',
        textColor: '#ffffff',
        shape: 'badge',
        icon: '★'
    },
    'taze': {
        text: 'TAZE',
        backgroundColor: '#4caf50',
        textColor: '#ffffff',
        shape: 'leaf',
        icon: '🌿'
    },
    'gunluk': {
        text: 'GÜNLÜK',
        backgroundColor: '#ff5722',
        textColor: '#ffffff',
        shape: 'badge',
        icon: '📅'
    },
    'organik': {
        text: 'ORGANİK',
        backgroundColor: '#8bc34a',
        textColor: '#ffffff',
        shape: 'leaf',
        icon: '🌱'
    },
    'gunluk-kesim': {
        text: 'GÜNLÜK KESİM',
        backgroundColor: '#c62828',
        textColor: '#ffffff',
        shape: 'ribbon',
        icon: '🔪'
    },
    'helal': {
        text: 'HELAL',
        backgroundColor: '#1b5e20',
        textColor: '#ffffff',
        shape: 'badge',
        icon: '☪'
    },
    'bayram-firsati': {
        text: 'BAYRAM FIRSATI',
        backgroundColor: '#c9a227',
        textColor: '#1a5f2a',
        shape: 'star',
        icon: '🌙'
    },
    'ozel': {
        text: 'ÖZEL',
        backgroundColor: '#9c27b0',
        textColor: '#ffffff',
        shape: 'badge',
        icon: '★'
    }
};

// ============= ŞABLON FONKSİYONLARI =============

function getTemplate(templateId) {
    return BROCHURE_TEMPLATES[templateId] || BROCHURE_TEMPLATES['classic-market'];
}

function getAllTemplates() {
    return Object.values(BROCHURE_TEMPLATES);
}

function getTemplatesByCategory(category) {
    const categoryMap = {
        'market': ['classic-market', 'modern-minimal'],
        'holiday': ['bayram-special'],
        'produce': ['fresh-produce'],
        'meat': ['butcher-premium'],
        'job': ['job-posting']
    };
    
    const ids = categoryMap[category] || Object.keys(BROCHURE_TEMPLATES);
    return ids.map(id => BROCHURE_TEMPLATES[id]).filter(Boolean);
}

function getBadge(badgeId, discount = 0) {
    const badge = BADGE_STYLES[badgeId];
    if (!badge) return null;
    
    return {
        ...badge,
        text: badge.text.replace('{discount}', discount.toString())
    };
}

function renderTemplatePreview(template, container) {
    const html = `
        <div class="template-preview-card" data-template="${template.id}">
            <div class="template-preview-image" style="background: ${template.colors.primary};">
                <div class="template-mini-header" style="background: ${template.colors.primary}; color: ${template.layout.header.textColor};">
                    <span>LOGO</span>
                    <span>${template.name}</span>
                </div>
                <div class="template-mini-grid">
                    ${Array(6).fill('<div class="template-mini-product"></div>').join('')}
                </div>
            </div>
            <div class="template-preview-info">
                <h4>${template.name}</h4>
                <p>${template.description}</p>
            </div>
        </div>
    `;
    
    if (container) {
        container.innerHTML += html;
    }
    return html;
}

// ============= KAMPANYA FONKSİYONLARI =============

function getCampaign(campaignId) {
    return CAMPAIGN_TYPES[campaignId] || null;
}

function getAllCampaigns() {
    return Object.values(CAMPAIGN_TYPES);
}

function getDailyCampaigns() {
    const days = ['pazartesi', 'sali', 'carsamba', 'persembe', 'cuma', 'cumartesi', 'pazar'];
    return days.map(d => CAMPAIGN_TYPES[d]);
}

function getSpecialCampaigns() {
    const specials = ['acilis', 'yildonumu', 'tasfiye', 'sezon-sonu', 'hafta-sonu', 'ogrenci', 'emekli'];
    return specials.map(s => CAMPAIGN_TYPES[s]);
}

function getHolidayCampaigns() {
    const holidays = ['anne-gunu', 'baba-gunu', 'sevgililer', 'yilbasi', '23-nisan', '19-mayis', '29-ekim'];
    return holidays.map(h => CAMPAIGN_TYPES[h]);
}

function getTodayCampaign() {
    const days = ['pazar', 'pazartesi', 'sali', 'carsamba', 'persembe', 'cuma', 'cumartesi'];
    const today = new Date().getDay();
    return CAMPAIGN_TYPES[days[today]];
}

function renderCampaignSelector(container) {
    const html = `
        <div class="campaign-selector">
            <h4>📅 Günlük Kampanyalar</h4>
            <div class="campaign-grid daily">
                ${getDailyCampaigns().map(c => `
                    <div class="campaign-card" data-campaign="${c.id}" onclick="selectCampaign('${c.id}')" 
                         style="background: ${c.gradient};">
                        <span class="campaign-icon">${c.icon}</span>
                        <span class="campaign-name">${c.name}</span>
                    </div>
                `).join('')}
            </div>
            
            <h4>🎉 Özel Kampanyalar</h4>
            <div class="campaign-grid special">
                ${getSpecialCampaigns().map(c => `
                    <div class="campaign-card" data-campaign="${c.id}" onclick="selectCampaign('${c.id}')"
                         style="background: ${c.gradient};">
                        <span class="campaign-icon">${c.icon}</span>
                        <span class="campaign-name">${c.name}</span>
                    </div>
                `).join('')}
            </div>
            
            <h4>🎊 Özel Günler</h4>
            <div class="campaign-grid holidays">
                ${getHolidayCampaigns().map(c => `
                    <div class="campaign-card" data-campaign="${c.id}" onclick="selectCampaign('${c.id}')"
                         style="background: ${c.gradient};">
                        <span class="campaign-icon">${c.icon}</span>
                        <span class="campaign-name">${c.name}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    if (container) {
        container.innerHTML = html;
    }
    return html;
}

// ============= EXPORTS =============

window.BROCHURE_TEMPLATES = BROCHURE_TEMPLATES;
window.BADGE_STYLES = BADGE_STYLES;
window.CAMPAIGN_TYPES = CAMPAIGN_TYPES;
window.getTemplate = getTemplate;
window.getAllTemplates = getAllTemplates;
window.getTemplatesByCategory = getTemplatesByCategory;
window.getBadge = getBadge;
window.renderTemplatePreview = renderTemplatePreview;
window.getCampaign = getCampaign;
window.getAllCampaigns = getAllCampaigns;
window.getDailyCampaigns = getDailyCampaigns;
window.getSpecialCampaigns = getSpecialCampaigns;
window.getHolidayCampaigns = getHolidayCampaigns;
window.getTodayCampaign = getTodayCampaign;
window.renderCampaignSelector = renderCampaignSelector;

console.log('📋 Broşür şablonları yüklendi:', Object.keys(BROCHURE_TEMPLATES).length, 'şablon,', Object.keys(CAMPAIGN_TYPES).length, 'kampanya');

