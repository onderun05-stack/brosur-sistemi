/**
 * Broşür Mini Stüdyo - Wizard içinde hızlı düzenleme
 */

const studioState = {
    template: null,
    products: [],
    selectedProduct: null,
    colors: {},
    slogan: '',
    badges: {},
    zoom: 1
};

// Stüdyo başlat
function initStudio(template, products, campaign = null) {
    studioState.template = template;
    studioState.products = products;
    studioState.colors = { ...template.colors };
    
    // Kampanya varsa onun değerlerini kullan
    if (campaign) {
        studioState.slogan = campaign.slogan || 'İNDİRİM FIRSATLARI!';
        studioState.colors.primary = campaign.color || template.colors.primary;
        studioState.campaign = campaign;
    } else if (typeof wizardState !== 'undefined' && wizardState.selectedCampaign) {
        studioState.slogan = wizardState.selectedCampaign.slogan || 'İNDİRİM FIRSATLARI!';
        studioState.colors.primary = wizardState.selectedCampaign.color || template.colors.primary;
        studioState.campaign = wizardState.selectedCampaign;
    } else {
        studioState.slogan = 'İNDİRİM FIRSATLARI!';
    }
    
    injectStudioCSS();
}

// CSS inject
function injectStudioCSS() {
    if (document.getElementById('studio-css')) return;
    const style = document.createElement('style');
    style.id = 'studio-css';
    style.textContent = `
        .studio-container { display:grid; grid-template-columns:220px 1fr 180px; gap:12px; height:450px; background:#0a0a0f; border-radius:12px; padding:12px; }
        .studio-panel { background:rgba(255,255,255,0.05); border-radius:10px; padding:10px; overflow-y:auto; }
        .studio-panel h4 { color:#fff; font-size:13px; margin:0 0 10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px; }
        .studio-product { display:flex; gap:8px; padding:8px; background:rgba(255,255,255,0.08); border-radius:6px; margin-bottom:6px; cursor:grab; }
        .studio-product:hover { background:rgba(255,255,255,0.12); }
        .studio-product img { width:36px; height:36px; object-fit:contain; background:#fff; border-radius:4px; }
        .studio-product-name { color:#fff; font-size:11px; }
        .studio-product-price { color:#10b981; font-size:11px; font-weight:600; }
        .studio-canvas { background:#fff; border-radius:10px; position:relative; overflow:hidden; }
        .studio-preview { min-width:380px; min-height:450px; margin:15px; box-shadow:0 4px 16px rgba(0,0,0,0.2); }
        .studio-zoom { position:absolute; bottom:10px; right:10px; display:flex; gap:6px; }
        .studio-zoom button { width:28px; height:28px; background:rgba(0,0,0,0.7); color:#fff; border:none; border-radius:5px; cursor:pointer; }
        .studio-input { width:100%; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); border-radius:5px; padding:7px 9px; color:#fff; font-size:12px; margin-bottom:6px; }
        .studio-colors { display:flex; gap:5px; flex-wrap:wrap; }
        .studio-color { width:26px; height:26px; border-radius:5px; cursor:pointer; border:2px solid transparent; }
        .studio-color:hover, .studio-color.active { border-color:#fff; transform:scale(1.1); }
        .studio-btn { width:100%; padding:9px; border:none; border-radius:7px; font-size:12px; font-weight:600; cursor:pointer; margin-bottom:6px; }
        .studio-btn.primary { background:linear-gradient(135deg,#8b5cf6,#a855f7); color:#fff; }
        .studio-btn.secondary { background:rgba(255,255,255,0.1); color:#fff; }
        .brochure-header { padding:15px; display:flex; justify-content:space-between; align-items:center; }
        .brochure-grid { display:grid; padding:12px; gap:8px; }
        .brochure-card { background:#fff; border:1px solid #eee; border-radius:6px; padding:8px; text-align:center; position:relative; }
        .brochure-card img { width:100%; height:70px; object-fit:contain; }
        .brochure-card-name { font-size:11px; font-weight:600; margin:4px 0 2px; }
        .brochure-card-price { font-size:14px; font-weight:bold; }
        .brochure-badge { position:absolute; top:-4px; right:-4px; padding:3px 6px; font-size:9px; font-weight:bold; border-radius:3px; }
    `;
    document.head.appendChild(style);
}

// Stüdyo render
function renderStudio(container) {
    if (!studioState.template) return;
    const t = studioState.template;
    
    container.innerHTML = `
        <div class="studio-container">
            <div class="studio-panel">
                <h4>📦 Ürünler (${studioState.products.length})</h4>
                ${studioState.products.map((p, i) => `
                    <div class="studio-product" data-idx="${i}">
                        <img src="${p.image_url || '/static/placeholder.png'}">
                        <div>
                            <div class="studio-product-name">${p.name}</div>
                            <div class="studio-product-price">${formatStudioPrice(p.discount_price)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="studio-canvas">
                <div class="studio-preview" id="studio-preview">
                    ${renderStudioBrochure()}
                </div>
                <div class="studio-zoom">
                    <button onclick="studioZoom(-0.1)">−</button>
                    <button onclick="studioZoom(0.1)">+</button>
                </div>
            </div>
            <div class="studio-panel">
                <h4>✏️ Slogan</h4>
                <input class="studio-input" value="${studioState.slogan}" onchange="updateStudioSlogan(this.value)">
                <h4>🎨 Renk</h4>
                <div class="studio-colors">
                    ${['#e53935','#43a047','#1976d2','#ff9800','#8e24aa','#2d3436'].map(c => 
                        `<div class="studio-color${c===studioState.colors.primary?' active':''}" style="background:${c}" onclick="setStudioColor('${c}')"></div>`
                    ).join('')}
                </div>
                <h4 style="margin-top:12px">📐 Şablon</h4>
                <select class="studio-input" onchange="setStudioTemplate(this.value)">
                    ${Object.values(BROCHURE_TEMPLATES || {}).map(tm => 
                        `<option value="${tm.id}"${tm.id===t.id?' selected':''}>${tm.name}</option>`
                    ).join('')}
                </select>
                <button class="studio-btn primary" onclick="finishStudio()">✨ Oluştur</button>
                <button class="studio-btn secondary" onclick="previewStudioFull()">👁️ Önizle</button>
            </div>
        </div>
    `;
}

function renderStudioBrochure() {
    const t = studioState.template;
    const c = studioState.colors;
    return `
        <div class="brochure-header" style="background:${c.primary}">
            <img src="/static/aeu_logo.png" style="height:40px">
            <div style="color:#fff;font-size:18px;font-weight:bold;flex:1;text-align:center">${studioState.slogan}</div>
            <div style="color:#fff;font-size:12px">${new Date().toLocaleDateString('tr-TR')}</div>
        </div>
        <div class="brochure-grid" style="grid-template-columns:repeat(${t.layout?.grid?.columns||3},1fr);background:${c.background||'#fff'}">
            ${studioState.products.slice(0,12).map((p,i) => `
                <div class="brochure-card">
                    ${studioState.badges[i] ? `<div class="brochure-badge" style="background:${BADGE_STYLES?.[studioState.badges[i]]?.backgroundColor||'#e53935'};color:#fff">${BADGE_STYLES?.[studioState.badges[i]]?.text||''}</div>` : ''}
                    <img src="${p.image_url||'/static/placeholder.png'}">
                    <div class="brochure-card-name">${p.name}</div>
                    ${p.normal_price>p.discount_price?`<div style="font-size:10px;color:#999;text-decoration:line-through">${formatStudioPrice(p.normal_price)}</div>`:''}
                    <div class="brochure-card-price" style="color:${c.priceNew||c.primary}">${formatStudioPrice(p.discount_price)}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function formatStudioPrice(p) { return p ? p.toFixed(2).replace('.',',')+' ₺' : '0,00 ₺'; }
function updateStudioSlogan(v) { studioState.slogan=v; refreshStudioPreview(); }
function setStudioColor(c) { studioState.colors.primary=c; document.querySelectorAll('.studio-color').forEach(el=>el.classList.toggle('active',el.style.background===c)); refreshStudioPreview(); }
function setStudioTemplate(id) { if(BROCHURE_TEMPLATES?.[id]) { studioState.template=BROCHURE_TEMPLATES[id]; studioState.colors={...studioState.template.colors}; renderStudio(document.querySelector('.studio-container')?.parentNode); } }
function studioZoom(d) { studioState.zoom=Math.max(0.5,Math.min(1.5,studioState.zoom+d)); document.getElementById('studio-preview').style.transform=`scale(${studioState.zoom})`; }
function refreshStudioPreview() { document.getElementById('studio-preview').innerHTML=renderStudioBrochure(); }
function finishStudio() { if(typeof wizardApplyStudioChanges==='function') wizardApplyStudioChanges(studioState); }
function previewStudioFull() { document.getElementById('studio-preview')?.requestFullscreen?.(); }

window.initStudio = initStudio;
window.renderStudio = renderStudio;
window.studioState = studioState;
console.log('🎨 Mini Stüdyo yüklendi');

