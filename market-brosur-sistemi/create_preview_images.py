"""
Örnek stil önizleme görselleri oluştur
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Klasör oluştur
output_dir = "static/templates/examples"
os.makedirs(output_dir, exist_ok=True)

# Stil tanımları
styles = {
    "classic_red": {
        "bg": "#FFFFFF",
        "header": "#E63946",
        "accent": "#2A9D8F",
        "text": "Klasik Market"
    },
    "modern_blue": {
        "bg": "#48CAE4",
        "header": "#FFD60A",
        "accent": "#06D6A0",
        "text": "Modern Mavi"
    },
    "grid_clean": {
        "bg": "#F5F5DC",
        "header": "#FF6B35",
        "accent": "#004E89",
        "text": "Temiz Grid"
    },
    "garden_green": {
        "bg": "#2D6A4F",
        "header": "#FFD60A",
        "accent": "#87CEEB",
        "text": "Bahçe Temalı"
    },
    "premium_dark": {
        "bg": "#370617",
        "header": "#FFD60A",
        "accent": "#9D0208",
        "text": "Premium/Kasap"
    },
    "fresh_produce": {
        "bg": "#E9F5E9",
        "header": "#06D6A0",
        "accent": "#FF6B35",
        "text": "Manav/Taze"
    }
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

for style_id, colors in styles.items():
    # 300x400 önizleme görseli
    img = Image.new('RGB', (300, 400), hex_to_rgb(colors["bg"]))
    draw = ImageDraw.Draw(img)
    
    # Header bandı
    draw.rectangle([0, 0, 300, 50], fill=hex_to_rgb(colors["header"]))
    
    # Alt bant
    draw.rectangle([0, 370, 300, 400], fill=hex_to_rgb(colors["accent"]))
    
    # Orta alan - ürün grid simülasyonu
    for row in range(3):
        for col in range(2):
            x = 30 + col * 130
            y = 70 + row * 100
            # Ürün kutusu
            draw.rectangle([x, y, x+110, y+80], outline=hex_to_rgb(colors["header"]), width=2)
    
    # Kaydet
    filepath = os.path.join(output_dir, f"{style_id}.jpg")
    img.save(filepath, "JPEG", quality=90)
    print(f"✅ {filepath} oluşturuldu")

print("\n✅ Tüm önizleme görselleri oluşturuldu!")

