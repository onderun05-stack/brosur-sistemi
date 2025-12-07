// studio.js - client-side uygulama (ESM)
const demoCompanyProfile = {
  id: "firma-001",
  name: "Kırmızı Market",
  logoUrl: "", // örnek: "https://..."
  primaryColor: "#e11d48",
  secondaryColor: "#f97316",
  address: "Örnek Cad. No: 10 / İstanbul",
  socials: { instagram: "@kirmizimarket", web: "www.kirmizimarket.com" },
  foodCards: ["Sodexo", "Multinet", "Ticket"]
};

const demoProducts = [
  { id:"p1", name:"Çaykur Tiryaki Çay 1000 g", price:22.95, oldPrice:28.9, image_url:"https://via.placeholder.com/200x260?text=Caykur+Tiryaki", caption:"Yeni" },
  { id:"p2", name:"Çaykur Altınbaş Çay 500 g", price:13.95, oldPrice:18.9, image_url:"https://via.placeholder.com/180x220?text=Altinbas", caption:"Popüler" },
  { id:"p3", name:"Tirebolu 42 1000 g", price:17.95, oldPrice:23.9, image_url:"https://via.placeholder.com/220x180?text=Tirebolu+42", caption:"Indirim" },
  { id:"p4", name:"Nescafe 3'ü 1 Arada 20'li", price:10.95, oldPrice:14.9, image_url:"https://via.placeholder.com/180x220?text=Nescafe", caption:"Kampanya" },
  { id:"p5", name:"Nesquik 6'lı Süt", price:5.95, oldPrice:7.95, image_url:"https://via.placeholder.com/200x200?text=Nesquik", caption:"Süper Fırsat" }
];

let masterTemplate = null;

const studioState = {
  pages:[{ id:"page-1", objectsMeta:[], styleProfileId:null }],
  currentPageIndex:0,
  selectedObjectMeta:null
};

let fabricCanvas = null;

// Init
window.addEventListener("DOMContentLoaded", () => {
  initCompanyPanel();
  initProductList();
  initCanvas();
  initPageButtons();
  initButtons();
  renderTemplatePreview();
});

function initCompanyPanel(){
  document.getElementById("company-name").textContent = demoCompanyProfile.name;
  const panel = document.getElementById("company-panel");
  panel.innerHTML = `
    <div><b>Adres:</b> ${demoCompanyProfile.address}</div>
    <div><b>Web:</b> ${demoCompanyProfile.socials.web}</div>
    <div><b>Instagram:</b> ${demoCompanyProfile.socials.instagram}</div>
    <div><b>Yemek Kartları:</b> ${demoCompanyProfile.foodCards.join(", ")}</div>
  `;
}

function initProductList(){
  const container = document.getElementById("product-list");
  container.innerHTML = "";
  demoProducts.forEach(p=>{
    const div = document.createElement("div");
    div.className = "product-card";
    div.innerHTML = `
      <div class="row">
        <div class="product-thumb"><img src="${p.image_url}" alt="${p.name}" /></div>
        <div style="flex:1;">
          <div style="font-weight:700;">${p.name}</div>
          <div style="color:#22c55e;font-weight:700;margin-top:6px;">${formatPrice(p.price)}</div>
        </div>
      </div>
      <div style="display:flex;gap:6px;">
        <button class="btn btn-ghost add-btn">Canvas'a ekle</button>
        <button class="btn btn-ghost detail-btn">Detay</button>
      </div>
    `;
    div.querySelector(".add-btn").onclick = ()=>addProductToCanvas(p);
    container.appendChild(div);
  });
}

function initCanvas(){
  fabricCanvas = new fabric.Canvas("brochure-canvas", {
    backgroundColor: "#ffffff",
    preserveObjectStacking: true,
    selection: true
  });
  fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));

  fabricCanvas.on("selection:created", updateSelectedObjectPanel);
  fabricCanvas.on("selection:updated", updateSelectedObjectPanel);
  fabricCanvas.on("selection:cleared", ()=>{ studioState.selectedObjectMeta = null; renderSelectedProductPanel(); });
}

function initPageButtons(){
  const container = document.getElementById("page-buttons");
  container.innerHTML = "";
  studioState.pages.forEach((page,idx)=>{
    const btn = document.createElement("button");
    btn.textContent = `Sayfa ${idx+1}`;
    btn.onclick = ()=>switchPage(idx);
    if(idx===studioState.currentPageIndex){
      btn.style.background = "#6366f1";
      btn.style.color = "#fff";
      btn.style.borderColor = "#6366f1";
    } else {
      btn.style.borderColor = "#4b5563";
      btn.style.color = "#e5e7eb";
    }
    container.appendChild(btn);
  });

  document.getElementById("btn-add-page").onclick = ()=>{
    studioState.pages.push({ id:`page-${studioState.pages.length+1}`, objectsMeta:[], styleProfileId:null });
    studioState.currentPageIndex = studioState.pages.length-1;
    initPageButtons();
    redrawCanvasFromState();
  };
}

function initButtons(){
  document.getElementById("btn-ai-layout-page").onclick = ()=>callAiLayout({ scope: "page" });
  document.getElementById("btn-ai-layout-selection").onclick = ()=>callAiLayout({ scope: "selection" });
  document.getElementById("btn-ai-soften-bg").onclick = ()=>callAiLayout({ scope: "background" });

  document.getElementById("btn-download-png").onclick = ()=>{
    if(!fabricCanvas) return;
    const url = fabricCanvas.toDataURL({ format:"png", multiplier:2 });
    const a = document.createElement("a");
    a.href = url;
    a.download = "brosur.png";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  document.getElementById("btn-save-template").onclick = ()=>{
    masterTemplate = exportMasterTemplateFromCurrentPage();
    renderTemplatePreview();
    alert("Bu sayfa ana tema olarak kaydedildi (demo).");
  };
}

// Ürün ekleme
function addProductToCanvas(product){
  const page = getCurrentPage();
  const baseX = 60 + page.objectsMeta.length*20;
  const baseY = 160 + page.objectsMeta.length*15;

  fabric.Image.fromURL(product.image_url || "https://via.placeholder.com/200", img=>{
    img.scaleToWidth(140);
    const h = img.getScaledHeight();
    img.set({ left:10, top:10, originX:"left", originY:"top", selectable:false });

    const nameText = new fabric.Textbox(product.name, {
      left:10, top:10+h+6, width:160, fontSize:13, fontWeight:"bold", textAlign:"center", fill:"#111827", selectable:false
    });
    const priceText = new fabric.Textbox(formatPrice(product.price), {
      left:10, top:10+h+28, width:160, fontSize:18, fontWeight:"bold", textAlign:"center", fill:"#dc2626", selectable:false
    });

    const group = new fabric.Group([img, nameText, priceText], {
      left: baseX, top: baseY, hasControls:true, borderColor:"#6366f1", cornerColor:"#6366f1", cornerStyle:"circle", padding:6
    });

    group.productMeta = { productId: product.id, userEdited:false, lockScale:false, lockPosition:false };
    group.on("modified", ()=>{ group.productMeta.userEdited = true; syncObjectsMetaFromCanvas(); });
    group.on("mousedblclick", ()=>alert(product.name + " – büyük önizleme burada açılabilir."));

    fabricCanvas.add(group);
    fabricCanvas.setActiveObject(group);
    fabricCanvas.requestRenderAll();
    syncObjectsMetaFromCanvas();
  }, { crossOrigin: "Anonymous" });
}

function getCurrentPage(){ return studioState.pages[studioState.currentPageIndex]; }

function switchPage(idx){
  studioState.currentPageIndex = idx;
  initPageButtons();
  redrawCanvasFromState();
}

function syncObjectsMetaFromCanvas(){
  const page = getCurrentPage();
  page.objectsMeta = [];
  fabricCanvas.getObjects().forEach(obj=>{
    if(!obj.productMeta) return;
    page.objectsMeta.push({
      productId: obj.productMeta.productId,
      left: Math.round(obj.left),
      top: Math.round(obj.top),
      scaleX: obj.scaleX,
      scaleY: obj.scaleY,
      userEdited: !!obj.productMeta.userEdited,
      lockScale: !!obj.productMeta.lockScale,
      lockPosition: !!obj.productMeta.lockPosition
    });
  });
}

function redrawCanvasFromState(){
  fabricCanvas.clear();
  const page = getCurrentPage();
  const bg = (page.backgroundColor) || "#ffffff";
  fabricCanvas.setBackgroundColor(bg, fabricCanvas.renderAll.bind(fabricCanvas));

  page.objectsMeta.forEach(meta=>{
    const product = demoProducts.find(p=>p.id===meta.productId);
    if(!product) return;
    fabric.Image.fromURL(product.image_url || "https://via.placeholder.com/200", img=>{
      img.scaleToWidth(140 * (meta.scaleX || 1));
      const h = img.getScaledHeight();
      img.set({ left:10, top:10, originX:"left", originY:"top", selectable:false });

      const nameText = new fabric.Textbox(product.name, {
        left:10, top:10+h+6, width:160, fontSize:13, fontWeight:"bold", textAlign:"center", fill:"#111827", selectable:false
      });
      const priceText = new fabric.Textbox(formatPrice(product.price), {
        left:10, top:10+h+28, width:160, fontSize:18, fontWeight:"bold", textAlign:"center", fill:"#dc2626", selectable:false
      });

      const group = new fabric.Group([img, nameText, priceText], {
        left: meta.left || 60, top: meta.top || 160, scaleX: meta.scaleX || 1, scaleY: meta.scaleY || 1,
        hasControls:true, borderColor:"#6366f1", cornerColor:"#6366f1", cornerStyle:"circle", padding:6
      });
      group.productMeta = { ...meta };
      group.on("modified", ()=>{ group.productMeta.userEdited = true; syncObjectsMetaFromCanvas(); });
      fabricCanvas.add(group);
      fabricCanvas.requestRenderAll();
    }, { crossOrigin: "Anonymous" });
  });
}

// AI akışı
async function callAiLayout({ scope }){
  const page = getCurrentPage();
  syncObjectsMetaFromCanvas();

  const body = {
    scope,
    companyProfile: demoCompanyProfile,
    masterTemplate,
    page: { id: page.id, canvas: { width: 595, height: 842 }, objects: page.objectsMeta },
    products: demoProducts
  };

  try {
    const resp = await fetch("/api/ai/layout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if(!resp.ok){ alert("AI düzenlemesi başarısız"); return; }
    const data = await resp.json();
    applyAiLayoutResponse(data);
  } catch(e) {
    console.error(e);
    alert("Sunucu hatası");
  }
}

function applyAiLayoutResponse(layout){
  if(!layout || !layout.products){
    alert("AI'den beklenen formatta cevap gelmedi.");
    console.warn(layout);
    return;
  }

  // Background
  if(layout.background && layout.background.color){
    fabricCanvas.setBackgroundColor(layout.background.color, fabricCanvas.renderAll.bind(fabricCanvas));
  }
  if(layout.background && layout.background.backgroundPrompt){
    console.info("Background prompt for renderer/designer:", layout.background.backgroundPrompt);
  }

  // Template / logo
  if(layout.template){
    document.getElementById("template-name").textContent = layout.template.useMasterTemplate ? "Kayıtlı Ana Tema" : "Otomatik Oluşturulan Tema";
    if(layout.template.logo && layout.template.keepLogo){
      // basit logo yer tutucu
      const logo = layout.template.logo;
      const rect = new fabric.Rect({
        left: logo.x || 20, top: logo.y || 12, width: logo.width || 120, height: logo.height || 36,
        fill: demoCompanyProfile.primaryColor || "#111", rx:6, ry:6, selectable:false, evented:false
      });
      const txt = new fabric.Text(demoCompanyProfile.name, {
        left: (logo.x || 20) + 8, top: (logo.y || 12) + 6, fontSize:12, fill:"#fff", selectable:false, evented:false
      });
      rect.__isLogoPlaceholder = true;
      txt.__isLogoPlaceholder = true;
      // temizle önce
      fabricCanvas.getObjects().filter(o=>o.__isLogoPlaceholder).forEach(o=>fabricCanvas.remove(o));
      fabricCanvas.add(rect);
      fabricCanvas.add(txt);
    }
  }

  // Update objects metadata with AI positions & sizes
  const page = getCurrentPage();
  const metaById = new Map(page.objectsMeta.map(m=>[m.productId,m]));
  layout.products.forEach(p=>{
    const meta = metaById.get(p.productId);
    const scaleX = (p.size && p.size.width) ? (p.size.width / 140) : 1;
    if(!meta){
      page.objectsMeta.push({
        productId: p.productId,
        left: p.position.x || 60,
        top: p.position.y || 160,
        scaleX: scaleX,
        scaleY: scaleX,
        userEdited: false,
        lockScale: false,
        lockPosition: false
      });
    } else {
      if(!meta.lockPosition && p.position){
        meta.left = p.position.x;
        meta.top = p.position.y;
      }
      if(!meta.lockScale && p.size){
        meta.scaleX = scaleX;
        meta.scaleY = scaleX;
      }
    }
  });

  redrawCanvasFromState();

  // Apply suggested font sizes
  fabricCanvas.getObjects().forEach(obj=>{
    if(obj.type === "group" && Array.isArray(obj._objects)){
      const meta = obj.productMeta;
      if(!meta) return;
      const aiProduct = layout.products.find(pp => pp.productId === meta.productId);
      if(!aiProduct) return;
      obj._objects.forEach(child=>{
        if(child.type === "textbox" || child.type === "text"){
          if(child.text && aiProduct.price != null && child.text.includes(formatPrice(aiProduct.price))){
            child.set({ fontSize: aiProduct.priceFontSize || child.fontSize || 16, fill:"#dc2626" });
          } else {
            child.set({ fontSize: aiProduct.nameFontSize || child.fontSize || 12 });
          }
        }
      });
      obj.setCoords();
    }
  });
  fabricCanvas.requestRenderAll();

  if(layout.annotations && layout.annotations.analysis){
    console.log("AI analysis:", layout.annotations.analysis);
  }
}

// Template export/preview
function exportMasterTemplateFromCurrentPage(){
  return {
    id: "template-" + Date.now(),
    ownerCompanyId: demoCompanyProfile.id,
    name: "Ana Tema " + new Date().toLocaleString("tr-TR"),
    canvasSize: { width: 595, height: 842 },
    contentRegions: [{ id: "content-main", x: 0, y: 140, width: 595, height: 620 }],
    styleProfile: { primaryColor: demoCompanyProfile.primaryColor, secondaryColor: demoCompanyProfile.secondaryColor },
    logoPlacement: { x:20, y:12, width:120, height:36 }
  };
}
function renderTemplatePreview(){
  const div = document.getElementById("template-preview");
  if(!masterTemplate){ div.textContent = "Henüz ana tema kaydedilmedi."; return; }
  const r = masterTemplate.contentRegions[0];
  div.innerHTML = `
    <div><b>Ad:</b> ${masterTemplate.name}</div>
    <div><b>İç Bölge:</b> x=${r.x}, y=${r.y}, w=${r.width}, h=${r.height}</div>
    <div><b>Renkler:</b> ${masterTemplate.styleProfile.primaryColor}, ${masterTemplate.styleProfile.secondaryColor}</div>
  `;
}

// Seçili ürün paneli
function updateSelectedObjectPanel(e){
  const obj = e.selected && e.selected[0];
  studioState.selectedObjectMeta = obj && obj.productMeta ? obj.productMeta : null;
  renderSelectedProductPanel();
}
function renderSelectedProductPanel(){
  const panel = document.getElementById("selected-product-panel");
  const meta = studioState.selectedObjectMeta;
  if(!meta){ panel.textContent = "Henüz ürün seçilmedi."; return; }
  const product = demoProducts.find(p => p.id === meta.productId);
  panel.innerHTML = `
    <div style="font-weight:600;">${product ? product.name : meta.productId}</div>
    <div>lockScale: ${meta.lockScale ? "evet" : "hayır"}</div>
    <div>lockPosition: ${meta.lockPosition ? "evet" : "hayır"}</div>
  `;
}

// Helpers
function formatPrice(v){ const n = Number(v) || 0; return n.toFixed(2).replace(".", ",") + " TL"; }
function getCurrentPage(){ return studioState.pages[studioState.currentPageIndex]; }