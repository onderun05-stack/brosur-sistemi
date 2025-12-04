YOL: E:\cursos\cursor-proje\market-brosur-sistemi\talimat\sistem-anayasasi.md

## Sistem Anayasası – v2.1 (Tek Kopya + Kişisel İsim)

Bu dosya, sistemin genel işleyiş kurallarını tanımlar.
Her yeni geliştirmede bu dosya güncellenir, sonraki çalışmalarda son versiyon referans alınır.

---

## 📋 VERSİYON GEÇMİŞİ

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| v1.0 | 2025-12-02 | Onayla & Aktar 1. Aşama netleştirildi |
| v2.0 | 2025-12-03 | Kaydet butonu + Broşüre Aktar + Yeni depo akışı |
| v2.1 | 2025-12-03 | TEK KOPYA kuralı + Kişisel isim + Arama hiyerarşisi düzeltmesi |

---

## 1. Temel Kavramlar

### 1.1. Kaynak Tipleri

- **Depo ürünü (`source_type = depo`)**
  - Kendi depo / stok sisteminden gelen, zaten kayıtlı ürün.
  - Ana veri kaynağı depo veritabanıdır.

- **Dış kaynak ürünü (`source_type = external`)**
  - Excel, web tarama, CAMGOZ, API vb. dış kaynaklardan gelen ürün.
  - Bu ürünler sistem içinde yeni kayıt açılabilir veya mevcut kaydı güncelleyebilir.

### 1.2. Onay Durumları (`approval_status`)

- **pending**: Yeni kaydedilmiş, admin onayı bekliyor (ama müşteri kendi kullanabilir!)
- **approved**: Admin tarafından onaylanmış, tüm müşteriler erişebilir
- **rejected**: Admin tarafından reddedilmiş, müşteri deposunda kalır

### 1.3. Zorunlu Alanlar (External İçin)

- **İsim**: `product_name`
- **Resim**: `image_url`
- **İndirim fiyatı**: `discount_price` (> 0)

### 1.4. ⭐ RESİM VE İSİM KURALLARI (YENİ)

| Veri Tipi | Kaynak | Açıklama |
|-----------|--------|----------|
| **Resim** | Admin Deposu | TEK KOPYA - herkes aynı resmi kullanır |
| **Master İsim** | Admin Deposu | Admin'in standartlaştırdığı resmi isim |
| **Kişisel İsim** | Müşteri DB | Müşterinin yöresel/özel ismi |

**Örnek Senaryo:**
1. Müşteri A → Barkod X için "Mısır Yağı" yazar → Kaydeder
2. Admin → Onaylar → "Ayçiçek Mısır Yağı" olarak düzeltir → Admin deposuna TAŞIR
3. Müşteri A → Kendi DB'sinde "Mısır Yağı" kalır → Hep bunu görür
4. Müşteri B → Barkod X sorgular → "Ayçiçek Mısır Yağı" + resim alır

---

## 2. DEPO YAPISI VE AKIŞI

### 2.1. Klasör Hiyerarşisi

```
static/uploads/
│
├── admin/                          ← GENEL DEPO (tüm müşteriler erişir)
│   └── {sector}/{group}/{barcode}/product.png
│   ⚠️ SİSTEMDE TEK KOPYA BURADA!
│
└── customers/                      ← MÜŞTERİ DEPOLARI (geçici)
    └── {user_id}/
        └── {sector}/{group}/{barcode}/product.png
        (Admin onayından SONRA burası TEMİZLENİR!)
```

### 2.2. ⭐ YENİ DEPO AKIŞI (v2.1)

```
┌─────────────────────────────────────────────────────────────┐
│  MÜŞTERİ "KAYDET" BUTONUNA BASAR                           │
│  ↓                                                          │
│  1. Ürün MÜŞTERİ DEPOSUNA kaydedilir (GEÇİCİ)              │
│     → customers/{user_id}/{sector}/{group}/{barcode}/       │
│     → MÜŞTERİ HEMEN KULLANABİLİR!                          │
│                                                             │
│  2. AYNI ZAMANDA admin onay kuyruğuna düşer                 │
│     → approval_status = 'pending'                           │
│     → Müşteri yine de kullanabilir                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ADMİN ONAYLARSA:                                           │
│  ────────────────                                           │
│  1. Müşteri deposundan TAŞINIR (kopyalanmaz!)              │
│  2. ADMİN DEPOSUNA kaydedilir                               │
│     → admin/{sector}/{group}/{barcode}/                     │
│  3. Müşteri deposundaki kopya SİLİNİR                      │
│  4. SİSTEMDE TEK KOPYA KALIR (admin deposunda)             │
│  5. Artık TÜM MÜŞTERİLER erişebilir!                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ADMİN REDDEDERSE:                                          │
│  ────────────────                                           │
│  1. Ürün müşteri deposunda KALIR                           │
│  2. Admin deposuna TAŞINMAZ                                 │
│  3. approval_status = 'rejected'                            │
│  4. Müşteri ürünü kullanamaz                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3. ⚠️ TEK KOPYA KURALI

**SİSTEMDE BİR ÜRÜN 2 ADET OLAMAZ!**

| Durum | Müşteri Deposu | Admin Deposu | Aktif Kopya |
|-------|----------------|--------------|-------------|
| **Pending** | ✅ VAR | ❌ YOK | Müşteri deposunda |
| **Approved** | ❌ SİLİNDİ | ✅ VAR | Admin deposunda |
| **Rejected** | ✅ KALDI | ❌ YOK | Müşteri deposunda (kullanılamaz) |

---

## 3. BUTONLAR VE İŞLEVLERİ

### 3.1. 💾 KAYDET Butonu

**Amaç**: Listedeki ürünleri işle, kategorile ve müşteri deposuna kaydet.

**Akış**:
```
Kaydet butonuna bas
      ↓
┌─────────────────────────────────────┐
│  AŞAMA 1: Resim İşleme              │
│  ─────────────────────────────      │
│  1. Resmi indir                     │
│  2. rembg ile arka planı kaldır     │
│  3. 1024x1024 resize                │
│  4. PNG olarak kaydet               │
│  5. Orijinallik: %95-100            │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│  AŞAMA 2: Kategorileme + Kayıt      │
│  ─────────────────────────────      │
│  1. OpenAI Vision: resim + isim     │
│  2. Sektör whitelist'inden grup seç │
│  3. MÜŞTERİ DEPOSUNA kaydet         │
│     → customers/{user_id}/...       │
│  4. DB: approval_status = 'pending' │
│  5. Müşteri HEMEN kullanabilir!     │
└─────────────────────────────────────┘
      ↓
Admin Onay Bekle (paralel süreç)
```

**Kurallar**:
- Ürünler `customers/{user_id}/` klasörüne DİREKT kaydedilir
- Yeni ürünler `approval_status = 'pending'` ile kaydedilir
- Müşteri kendi ürününü HEMEN kullanabilir (onay beklemeden)
- Admin onayı genel depoya TAŞIMA için gerekli (kopyalama değil!)
- Depo ürünlerinde güncelleme yoksa Aşama 1 atlanır

---

### 3.2. 🎨 BROŞÜRE AKTAR Butonu

**Amaç**: Kayıtlı ürünleri Canvas'a gönder.

**Veri Kaynakları**:
- **Resim, Grup** → DB'den (admin veya müşteri deposu)
- **İsim** → Müşteri DB'den (kişisel isim)
- **Eski Fiyat, İndirimli Fiyat** → Ön onay listesinden

**Akış**:
```
Broşüre Aktar butonuna bas
      ↓
┌─────────────────────────────────────┐
│  1. Listedeki her barkodu DB'de ara │
│  2. Kayıtlı değilse → HATA          │
│     "Önce Kaydet butonuna bas!"     │
│  3. Rejected ise → HATA             │
│     "Admin tarafından reddedildi"   │
│  4. Pending/Approved ise → DEVAM    │
│     (Kendi ürünü pending olsa bile  │
│      kullanabilir!)                 │
└─────────────────────────────────────┘
      ↓
Canvas Payload Oluştur → SessionStorage → Dashboard
```

**Kurallar**:
- Kayıtlı olmayan ürün Canvas'a gidemez
- Reddedilen ürün Canvas'a gidemez
- **Pending ürün kullanılabilir** (kendi deposundan)
- Fiyatlar listeden, resim depodan, isim müşteri DB'den gelir

---

## 4. CANVAS AKTARIM SİSTEMİ

### 4.1. SessionStorage Mekanizması

```javascript
// Pre-approval'dan:
sessionStorage.setItem('approvedCanvasPayload', JSON.stringify(products));

// Dashboard'da:
const payload = sessionStorage.getItem('approvedCanvasPayload');
placeProductsOnCanvas(JSON.parse(payload));
```

### 4.2. Ürün Kartı Yapısı

```
┌────────────────────┐
│ Ürün Adı           │  ← Müşteri DB'den (kişisel isim)
├────────────────────┤
│                    │
│   [ÜRÜN RESMİ]     │  ← Admin deposundan (tek kopya)
│                    │
├────────────────────┤
│ 1̶0̶0̶.̶0̶0̶ ̶₺̶            │  ← Listeden (normal_price)
│ 79.90 ₺            │  ← Listeden (discount_price)
├────────────────────┤
│      [%20]         │  ← Hesaplanır
└────────────────────┘
```

---

## 5. SEKTÖR VE GRUP YAPISI

### 5.1. Ana Sektörler

| Sektör | Kod |
|--------|-----|
| Süpermarket | supermarket |
| Giyim | giyim |
| Teknoloji | teknoloji |
| Kozmetik | kozmetik |
| Ev & Yaşam | ev_yasam |
| El Sanatları | el_sanatlari |
| Restoran | restoran |
| Diğer | diger |

### 5.2. Alt Gruplar (Whitelist)

```
Süpermarket:
  Gıda, İçecek, Et & Tavuk, Meyve & Sebze, Temizlik, 
  Kişisel Bakım, Atıştırmalık, Dondurulmuş, Şarküteri, Genel

Giyim:
  Giyim, Ayakkabı, Aksesuar, Genel

Teknoloji:
  Telefon, Bilgisayar & Tablet, TV & Ses, Beyaz Eşya, 
  Küçük Ev Aletleri, Oyun, Genel

Kozmetik:
  Parfüm, Kişisel Bakım, Genel

Ev & Yaşam:
  Mobilya, Dekorasyon, Bahçe, Genel

El Sanatları:
  Takı, Tekstil, Seramik, Ahşap, Genel

Restoran:
  Yemek, İçecek, Tatlı, Aperatif, Genel

Diğer:
  Genel
```

### 5.3. AI Gruplama Kuralları

- AI'ye sektör + whitelist gönderilir
- AI sadece whitelist'ten bir grup seçer
- Kararsız kalırsa → "Genel" grubuna atanır
- OpenAI Vision: resim + isim analizi yapılır

---

## 6. ADMIN ONAY AKIŞI

### 6.1. Onay Bekleyenler

- `approval_status = 'pending'` olan ürünler
- Admin panelinde "Onay Bekleyenler" sekmesinde görünür
- Müşteri bu arada ürünü kullanmaya devam eder!

### 6.2. ⭐ Onay Sonrası (v2.1 - TEK KOPYA)

1. Resim müşteri deposundan admin deposuna **TAŞINIR** (kopyalanmaz!)
2. Müşteri deposundaki kopya **SİLİNİR**
3. Sistemde **TEK KOPYA** kalır (admin deposunda)
4. Admin ürün ismini düzeltebilir (master isim)
5. Tüm müşteriler admin deposundan erişebilir

### 6.3. Red Sonrası

- Ürün reddedilir, müşteri kullanamaz
- Resim müşteri deposunda KALIR (admin deposuna taşınmaz)
- `approval_status = 'rejected'`

---

## 7. ⭐ BARKOD ARAMA HİYERARŞİSİ (v2.1 - DÜZELTİLDİ)

```
Barkod Sorgula
      ↓
┌─────────────────────────────────────┐
│ 1. ÖNCE ADMİN DEPOSU                │
│    ↓ Varsa → İsim + Resim al        │
│    ↓ CAMGOZ SORGUSU YAPILMAZ!       │
└─────────────────────────────────────┘
      ↓ (admin deposunda yoksa)
┌─────────────────────────────────────┐
│ 2. MÜŞTERİ DEPOSU                   │
│    (Sadece kendi pending ürünleri)  │
└─────────────────────────────────────┘
      ↓ (hiçbir depoda yoksa)
┌─────────────────────────────────────┐
│ 3. CAMGOZ API                       │
│    (Sadece depoda yoksa sorgulanır!)│
└─────────────────────────────────────┘
      ↓ (CAMGOZ'da yoksa)
┌─────────────────────────────────────┐
│ 4. Google Custom Search             │
│    (Sadece resim için)              │
└─────────────────────────────────────┘
```

**ÖNEMLİ:** Admin deposunda varsa CAMGOZ sorgusu YAPILMAZ!

---

## 8. TEKNİK DETAYLAR

### 8.1. Kullanılan Servisler

| Servis | Amaç |
|--------|------|
| rembg | Arka plan kaldırma |
| OpenAI GPT-4o Vision | Kategorileme |
| Fabric.js | Canvas işlemleri |
| Flask | Backend API |
| SQLite | Veritabanı |

### 8.2. API Endpoints

| Endpoint | Metod | Amaç |
|----------|-------|------|
| `/api/products/save` | POST | Kaydet butonu |
| `/api/products/transfer-to-canvas` | POST | Broşüre Aktar |
| `/api/admin/pending-approvals` | GET | Onay bekleyenler |
| `/api/admin/approve-product` | POST | Ürün onayla (admin deposuna TAŞI) |

---

## 9. GELECEKTEKİ GELİŞTİRMELER

### 9.1. AI Entegrasyonu (Planlanan)

- **Kimi AI**: Metin işleme, slogan üretimi
- **OpenAI DALL-E**: Arka plan üretimi
- **Hibrit Kullanım**: İşleme göre AI seçimi

### 9.2. 2. Aşama Özellikleri (Planlanan)

- Metin güzelleştirme
- Resim varyantları
- Kampanya sloganları
- Otomatik layout önerileri

---

## 10. NOTLAR

- Bu dosya sistemin **canlı anayasası**dır
- Her değişiklik versiyon numarası ile kaydedilir
- Yeni sohbetlerde önce bu dosya referans alınır
- `app.js` dosyası kullanılmıyor, tüm Canvas mantığı `index.html` içinde
- **v2.1 ÖNEMLİ:** Sistemde bir ürün 2 adet olamaz - tek kopya kuralı!
