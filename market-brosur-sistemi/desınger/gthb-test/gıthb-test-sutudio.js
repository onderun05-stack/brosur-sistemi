// Demo firma ve ürün verisi
const demoCompanyProfile = {
  id: "firma-001",
  name: "Kırmızı Market",
  logoUrl: "",
  primaryColor: "#e11d48",
  secondaryColor: "#f97316",
  address: "Örnek Cad. No: 10 / İstanbul",
  socials: { instagram: "@kirmizimarket", web: "www.kirmizimarket.com" },
  foodCards: ["Sodexo", "Multinet", "Ticket"]
};

const demoProducts = [
  { id:"p1", name:"Çaykur Tiryaki Çay 1000 g", price:22.95, oldPrice:28.9, image_url:"https://via.placeholder.com/200x260?text=Caykur+Tiryaki" },
  { id:"p2", name:"Çaykur Altınbaş Çay 500 g", price:13.95, oldPrice:18.9, image_url:"https://via.placeholder.com/180x220?text=Altinbas" },
  { id:"p3", name:"Tirebolu 42 1000 g", price:17.95, oldPrice:23.9, image_url:"https://via.placeholder.com/220x180?text=Tirebolu+42" },
  { id:"p4", name:"Nescafe 3'ü 1 Arada 20'li", price:10.95, oldPrice:14.9, image_url:"https://via.placeholder.com/180x220?text=Nescafe" },
  { id:"p5", name:"Nesquik 6'lı Süt", price:5.95, oldPrice:7.95, image_url:"https://via.placeholder.com/200x200?text=Nesquik" }
];

let masterTemplate = null;

const studioState = {
  pages:[{ id:"page-1", objectsMeta:[], styleProfileId:null }],
  currentPageIndex:0,
  selectedObjectMeta:null
};

let fabricCanvas = null;

window.addEventListener("DOMContentLoaded", () => {
  initCompanyPanel();
  initProductList();
  initCanvas();
  initPageButtons();
  initButtons();
});

function initCompanyPanel() {
  document.getElementById("company-name").textContent = demoCompanyProfile.name;
  const panel = document.getElementById("company-panel");
  panel.innerHTML = `
    <div><b>Adres:</b> ${demoCompanyProfile.address}</div>
    <div><b>Web:</b> ${demoCompanyProfile.socials.web}</div>
    <div><b>Instagram:</b> ${demoCompanyProfile.socials.instagram}</div>
    <div><b>Yemek Kartları:</b> ${demoCompanyProfile.foodCards.join(", ")}</div>
  `;
}

function initProductList() {
  const container = document.getElementById("product-list");
  container.innerHTML = "";
  demoProducts.forEach(p=>{
    const div = document.createElement("div");
    div.style.border = "1px solid #1f2937";
    div.style.borderRadius = "6px";
    div.style.padding = "6px";
    div.style.background = "#030712";
    div.innerHTML = `
      <div style="display:flex;gap:8px;align-items:center;">
        <div style="width:40px;height:40px;background:#1f2937;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#9ca3af;">IMG</div>
        <div style="flex:1;">
          <div style="font-size:11px;font-weight:600;">${p.name}</div>
          <div style="font-size:11px;color:#22c55e;font-weight:700;">${formatPrice(p.price)}</div>
        </div>
      </div>
      <button class="btn-ghost" style="margin-top:4px;width:100%;font-size:11px;">Canvas'a ekle</button>
    `;
    div.querySelector("button").onclick = ()=>addProductToCanvas(p);
    container.appendChild(div);
  });
}

function initCanvas() {
  fabricCanvas = new fabric.Canvas("brochure-canvas", {
    backgroundColor:"#ffffff",
    selection:true,
    preserveObjectStacking:true
  });
  fabricCanvas.setBackgroundColor("#ffffff", fabricCanvas.renderAll.bind(fabricCanvas));

  fabricCanvas.on("selection:created", updateSelectedObjectPanel);
  fabricCanvas.on("selection:updated", updateSelectedObjectPanel);
  fabricCanvas.on("selection:cleared", ()=>{studioState.selectedObjectMeta=null;renderSelectedProductPanel();});
}

function initPageButtons() {
  const container = document.getElementById("page-buttons");
  container.innerHTML = "";
  studioState.pages.forEach((page,idx)=>{
    const btn = document.createElement("button");
    btn.textContent = `Sayfa ${idx+1}`;
    btn.style.padding = "3px 8px";
    btn.style.fontSize = "11px";
    btn.style.borderRadius = "999px";
    btn.style.border = "1px solid";
    if(idx===studioState.currentPageIndex){
      btn.style.borderColor="#818cf8";
      btn.style.background="#6366f1";
      btn.style.color="#ffffff";
    }else{
      btn.style.borderColor="#4b5563";
      btn.style.color="#e5e7eb";
      btn.onmouseenter = ()=>btn.style.background="#111827";
      btn.onmouseleave = ()=>btn.style.background="transparent";
    }
    btn.onclick = ()=>switchPage(idx);
    container.appendChild(btn);
  });

  document.getElementById("btn-add-page").onclick = ()=>{
    studioState.pages.push({id:`page-${studioState.pages.length+1}`,objectsMeta:[],styleProfileId:null});
    studioState.currentPageIndex = studioState.pages.length-1;
    initPageButtons();
    redrawCanvasFromState();
  };
}

function initButtons() {
  document.getElementById("btn-ai-layout-page").onclick = ()=>callAiLayout({scope:"page"});
  document.getElementById("btn-ai-layout-selection").onclick = ()=>callAiLayout({scope:"selection"});
  document.getElementById("btn-ai-soften-bg").onclick = ()=>callAiLayout({scope:"background"});

  document.getElementById("btn-download-png").onclick = ()=>{
    if(!fabricCanvas) return;
    const dataUrl = fabricCanvas.toDataURL({format:"png",multiplier:2});
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = "brosur_sayfa.png";
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

// ÜRÜNÜ CANVAS'A EKLE
function addProductToCanvas(product) {
  const page = getCurrentPage();
  const baseX = 60 + page.objectsMeta.length*30;
  const baseY = 160 + page.objectsMeta.length*20;

  fabric.Image.fromURL(product.image_url || "https://via.placeholder.com/200x200?text=IMG", img=>{
    img.scaleToWidth(140);
    const h = img.getScaledHeight();

    img.set({left:10,top:10,originX:"left",originY:"top",selectable:false});

    const nameText = new fabric.Textbox(product.name,{
      left:10,top:10+h+6,width:160,fontSize:13,fontWeight:"bold",textAlign:"center",fill:"#111827",selectable:false
    });
    const priceText = new fabric.Textbox(formatPrice(product.price),{
      left:10,top:10+h+28,width:160,fontSize:18,fontWeight:"bold",textAlign:"center",fill:"#dc2626",selectable:false
    });

    const group = new fabric.Group([img,nameText,priceText],{
      left:baseX,top:baseY,hasControls:true,borderColor:"#6366f1",cornerColor:"#6366f1",cornerStyle:"circle",padding:6
    });

    group.productMeta = {productId:product.id,userEdited:false,lockScale:false,lockPosition:false};

    group.on("mousedblclick",()=>alert(product.name+" – büyük önizleme burada açılabilir."));
    group.on("modified",()=>{group.productMeta.userEdited=true;syncObjectsMetaFromCanvas();});

    fabricCanvas.add(group);
    fabricCanvas.setActiveObject(group);
    fabricCanvas.renderAll();
    syncObjectsMetaFromCanvas();
  },{crossOrigin:"Anonymous"});
}

// STATE <-> CANVAS
function getCurrentPage(){return studioState.pages[studioState.currentPageIndex];}

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
      productId:obj.productMeta.productId,
      left:obj.left,
      top:obj.top,
      scaleX:obj.scaleX,
      scaleY:obj.scaleY,
      userEdited:obj.productMeta.userEdited,
      lockScale:obj.productMeta.lockScale,
      lockPosition:obj.productMeta.lockPosition
    });
  });
}

function redrawCanvasFromState(){
  fabricCanvas.clear();
  fabricCanvas.setBackgroundColor("#ffffff",fabricCanvas.renderAll.bind(fabricCanvas));
  const page = getCurrentPage();
  page.objectsMeta.forEach(meta=>{
    const product = demoProducts.find(p=>p.id===meta.productId);
    if(!product) return;
    fabric.Image.fromURL(product.image_url || "https://via.placeholder.com/200x200?text=IMG",img=>{
      img.scaleToWidth(140*(meta.scaleX||1));
      const h = img.getScaledHeight();
      img.set({left:10,top:10,originX:"left",originY:"top",selectable:false});
      const nameText = new fabric.Textbox(product.name,{
        left:10,top:10+h+6,width:160,fontSize:13,fontWeight:"bold",textAlign:"center",fill:"#111827",selectable:false
      });
      const priceText = new fabric.Textbox(formatPrice(product.price),{
        left:10,top:10+h+28,width:160,fontSize:18,fontWeight:"bold",textAlign:"center",fill:"#dc2626",selectable:false
      });
      const group = new fabric.Group([img,nameText,priceText],{
        left:meta.left,top:meta.top,scaleX:meta.scaleX||1,scaleY:meta.scaleY||1,
        hasControls:true,borderColor:"#6366f1",cornerColor:"#6366f1",cornerStyle:"circle",padding:6
      });
      group.productMeta = {...meta};
      group.on("modified",()=>{group.productMeta.userEdited=true;syncObjectsMetaFromCanvas();});
      fabricCanvas.add(group);
      fabricCanvas.renderAll();
    },{crossOrigin:"Anonymous"});
  });
}

// AI LAYOUT (şimdilik backend'e istek)
async function callAiLayout({scope}){
  const page = getCurrentPage();
  syncObjectsMetaFromCanvas();

  const body = {
    scope,
    companyProfile:demoCompanyProfile,
    masterTemplate,
    page:{id:page.id,canvas:{width:595,height:842},objects:page.objectsMeta},
    products:demoProducts
  };

  try{
    const resp = await fetch("/api/ai/layout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    if(!resp.ok){alert("AI düzenlemesi hatalı");return;}
    const data = await resp.json();
    applyAiLayoutResponse(data);
  }catch(e){
    console.error(e);
    alert("Sunucu hatası");
  }
}

function applyAiLayoutResponse(layout){
  if(!layout || !layout.products) return;
  const page = getCurrentPage();
  const metaById = new Map(page.objectsMeta.map(m=>[m.productId,m]));
  layout.products.forEach(p=>{
    const meta = metaById.get(p.productId);
    if(!meta) return;
    if(!meta.lockPosition && p.position){meta.left=p.position.x;meta.top=p.position.y;}
    if(!meta.lockScale && p.size){
      const base=140;const scale=(p.size.width||base)/base;meta.scaleX=scale;meta.scaleY=scale;
    }
  });
  if(layout.background && layout.background.color){
    fabricCanvas.setBackgroundColor(layout.background.color,fabricCanvas.renderAll.bind(fabricCanvas));
  }
  redrawCanvasFromState();
}

// ANA TEMA
function exportMasterTemplateFromCurrentPage(){
  return {
    id:"template-"+Date.now(),
    ownerCompanyId:demoCompanyProfile.id,
    name:"Ana Tema "+new Date().toLocaleDateString("tr-TR"),
    canvasSize:{width:595,height:842},
    contentRegions:[{id:"content-main",x:0,y:140,width:595,height:620}],
    styleProfile:{primaryColor:demoCompanyProfile.primaryColor,secondaryColor:demoCompanyProfile.secondaryColor}
  };
}
function renderTemplatePreview(){
  const div = document.getElementById("template-preview");
  if(!masterTemplate){div.textContent="Henüz ana tema kaydedilmedi.";return;}
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
  if(!meta){panel.textContent="Henüz ürün seçilmedi.";return;}
  const product = demoProducts.find(p=>p.id===meta.productId);
  panel.innerHTML = `
    <div style="font-weight:600;">${product?product.name:meta.productId}</div>
    <div>lockScale: ${meta.lockScale?"evet":"hayır"}</div>
    <div>lockPosition: ${meta.lockPosition?"evet":"hayır"}</div>
  `;
}

function formatPrice(v){const n=Number(v)||0;return n.toFixed(2).replace(".",",")+" TL";}