# 🛒 Market Broşür Sistemi

**AEU Yazılım** tarafından geliştirilen, Türk marketleri için profesyonel broşür oluşturma platformu.

## 🎯 Proje Hakkında

Market Broşür Sistemi, marketlerin tanıtım broşürlerini hızlı ve profesyonel bir şekilde oluşturmasını sağlayan SaaS platformudur.

**Manuel süreç:** 8 saat tasarımcı çalışması  
**Otomatik süreç:** 15 dakikada broşür hazır ✨

## ✨ Özellikler

### 🎨 Canvas Editör
- Multi-page A4 broşür desteği (595x842px)
- Drag & Drop ile ürün yerleştirme
- Fabric.js ile gelişmiş manipülasyon
- PNG ve PDF export

### 📊 Ürün Yönetimi
- Excel (.xlsx) ile toplu ürün yükleme
- CSV dosya desteği
- Barkod bazlı otomatik eşleştirme
- 3-tier image bank sistemi
- Admin onay workflow'u

### 👥 Kullanıcı Sistemi
- Admin ve müşteri rolleri
- Kredi tabanlı sistem
- User-specific data isolation
- Session-based authentication

### 🎨 Modern UI/UX
- Glassmorphism dark purple tema (Dashboard)
- Cream-white wavy tema (Canvas)
- Responsive design
- Windows Explorer-style navigation

### 🔐 Güvenlik
- SQLite veritabanı
- Path traversal protection
- Admin-only access control
- Robust validation

### 🤖 AI Integration
- OpenAI API entegrasyonu
- AI görsel önerme
- AI slogan üretme
- Otomatik broşür tasarımı

## 🛠️ Teknoloji Stack

### Backend
- **Flask** - Python web framework
- **SQLite3** - Veritabanı
- **openpyxl** - Excel parsing
- **Pillow** - Image processing
- **ReportLab** - PDF generation
- **OpenAI** - AI entegrasyonu

### Frontend
- **Fabric.js v5.3.0** - Canvas manipulation
- **Interact.js** - Drag & drop
- **SheetJS** - Excel export
- **Vanilla JavaScript** - No framework
- **HTML5/CSS3** - Modern UI

## 📁 Proje Yapısı

```
market-brosur-sistemi/
├── app.py                      # Ana Flask uygulaması
├── database.py                 # Database management
├── ai_service.py              # OpenAI entegrasyonu
├── image_processor.py         # Görsel işleme modülü
├── services/
│   └── excel_io.py            # Excel parsing service
├── templates/
│   ├── index.html             # Dashboard
│   ├── admin_dashboard.html   # Admin panel
│   ├── pre_approval.html      # Ürün onay ekranı
│   ├── editor.html            # Broşür editörü
│   ├── login.html             # Giriş sayfası
│   ├── home.html              # Ana sayfa
│   ├── musteri_form.html      # Müşteri formu
│   └── partials/              # AJAX partial templates
├── static/
│   ├── css/                   # Stylesheet dosyaları
│   ├── js/                    # JavaScript modülleri
│   ├── uploads/               # Ürün görselleri
│   └── moduller/              # Standalone modüller
├── data/                      # JSON data files
├── attached_assets/           # Şablon dosyalar
├── requirements.txt           # Python bağımlılıkları
└── pyproject.toml             # Proje yapılandırması
```

## 🚀 Kurulum

### 1. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 2. Çevresel Değişkenler (Opsiyonel)

```bash
# OpenAI API (AI özellikleri için)
OPENAI_API_KEY=sk-...

# Session secret (varsayılan otomatik üretilir)
SESSION_SECRET=your-secret-key

# CAMGOZ Barkod API (opsiyonel)
CAMGOZ_API_KEY=your-api-key
```

### 3. Uygulamayı Başlat

```bash
python app.py
```

Uygulama `http://0.0.0.0:5000` adresinde çalışacaktır.

## 📖 Kullanım

### Varsayılan Admin Girişi
- **Email:** admin@brosur.com
- **Şifre:** admin123

### Admin Workflow
1. Admin panel → Ürün yönetimi
2. Excel ile toplu yükleme veya manuel entry
3. Ürün onaylama
4. Müşterilere kredi atama

### Müşteri Workflow
1. Dashboard → Yeni broşür
2. Ürün yükleme (Excel/CSV/manuel)
3. Canvas editör ile tasarım
4. PNG/PDF export

## 📊 Veritabanı Şeması

### SQLite3 (brosur.db)
```sql
-- Kullanıcılar
users (
  id INTEGER PRIMARY KEY,
  email TEXT UNIQUE,
  password TEXT,
  name TEXT,
  role TEXT,
  sector TEXT,
  credits REAL,
  created_at TIMESTAMP
)

-- Ürünler
products (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  barcode TEXT,
  name TEXT,
  normal_price REAL,
  discount_price REAL,
  image_url TEXT,
  product_group TEXT
)
```

## 🎨 Tasarım Sistemi

### Dashboard Theme (Glassmorphism)
- Gradient: `#667eea` → `#764ba2`
- Blur effects & transparency
- Purple-blue color scheme

### Canvas Theme (Cream-White)
- Warm gradients: `#fdf5e6`, `#faebd7`, `#ffe4c4`
- Tan borders
- Wavy patterns

## 📄 Lisans

Bu proje **AEU Yazılım** tarafından geliştirilmiştir.

---

**Son Güncelleme:** 30 Kasım 2025  
**Versiyon:** 1.0.0  
**Durum:** ✅ Aktif
