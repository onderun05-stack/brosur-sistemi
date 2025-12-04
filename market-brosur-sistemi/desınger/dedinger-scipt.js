const canvas = new fabric.Canvas('brochure-canvas');

// Drag & Drop ürünleri ekleme
const products = document.querySelectorAll('.product');
products.forEach(el => {
  el.addEventListener('dragstart', e => {
    e.dataTransfer.setData('text/plain', JSON.stringify({
      name: el.dataset.name,
      price: el.dataset.price,
      image: el.dataset.img
    }));
  });
});

const canvasArea = document.getElementById('canvas-area');
canvasArea.addEventListener('dragover', e => e.preventDefault());
canvasArea.addEventListener('drop', e => {
  e.preventDefault();
  const data = JSON.parse(e.dataTransfer.getData('text/plain'));
  addProductToCanvas(data);
});

function addProductToCanvas(product) {
  fabric.Image.fromURL(product.image, img => {
    img.scaleToWidth(100);
    img.left = 100;
    img.top = 100;
    canvas.add(img);

    const text = new fabric.Text(`${product.name} - ${product.price} TL`, {
      top: img.top + img.height + 10,
      left: img.left,
      fontSize: 16,
      fill: '#000'
    });
    canvas.add(text);
  });
}

// OpenAI düzenleme stub (gerçek API çağrısı entegre edilecek)
document.getElementById('ai-layout').onclick = () => {
  alert('OpenAI ile düzenleme yapılacak (bağlantı entegre edilecek)');
};

document.getElementById('ai-style').onclick = () => {
  alert('Yazı tipi + zemin önerileri gelecek (OpenAI entegre edilecek)');
};

document.getElementById('export').onclick = () => {
  const dataUrl = canvas.toDataURL({ format: 'png' });
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = 'brosur.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};
