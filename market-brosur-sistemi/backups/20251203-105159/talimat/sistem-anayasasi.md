YOL: E:\cursos\cursor-proje\market-brosur-sistemi\talimat\sistem-anayasasi.md

## Sistem Anayasası – v1 (1. Aşama Odaklı)

Bu dosya, sistemin genel işleyiş kurallarını ve özellikle **Onayla & Aktar – 1. Aşama** sürecini tanımlar.  
Her yeni geliştirmede bu dosya güncellenir, sonraki çalışmalarda son versiyon referans alınır.

---

## 1. Temel Kavramlar

### 1.1. Kaynak Tipleri

- **Depo ürünü (`source_type = depo`)**
  - Kendi depo / stok sisteminden gelen, zaten kayıtlı ürün.
  - Ana veri kaynağı depo veritabanıdır.

- **Dış kaynak ürünü (`source_type = external`)**
  - Excel, web tarama, CAMGOZ, API vb. dış kaynaklardan gelen ürün.
  - Bu ürünler sistem içinde yeni kayıt açılabilir veya mevcut kaydı güncelleyebilir.

### 1.2. Zorunlu Alanlar (Sadece External İçin)

Aşağıdaki alanlar **sadece external ürünler için zorunludur**:

- **İsim**: `product_name`
- **Resim**: `image_url`
- **İndirim / kampanya fiyatı**: `discount_price` (veya kampanya fiyatı kolonu)

Bu alanlardan **herhangi biri eksikse**, 1. Aşama Onayla & Aktar süreci **tamamen iptal edilir**.

---

## 2. Onayla & Aktar – 1. Aşama Genel İlkeleri

1. **Amaç**:
   - External ürünlerde:
     - Zorunlu alanları kontrol etmek (isim + resim + indirim fiyatı),
     - Hepsi tamamsa AI ile **grup atamak**,
     - Son halini **DB’ye yazmak** ve **Canvas’a aktarmak**.
   - Depo ürünlerinde:
     - İkinci kayıt açmamak,
     - Gerekirse sadece **güncelleme talebi** oluşturmak,
     - Canvas’a depo verisi + sayfa bilgisi ile gitmek.

2. **Bu aşamada yapılmayanlar**:
   - Metin güzelleştirme (isim/açıklama zenginleştirme),
   - Resim iyileştirme / varyant üretimi,
   - Ek kampanya metni / slogan üretimi.

Bu işlemler **2. Aşama (Kalite İyileştirme)** kapsamındadır, şu an devrede değildir.

---

## 3. Depodan Gelen Ürün Kuralları (`source_type = depo`)

### 3.1. Kayıt Yönetimi

- Depodan gelen ürünler için:
  - **Yeni ürün kaydı açılmaz** (ikinci kayıt oluşturulmaz).
  - Sistem, o ürün için **tek bir ana depo kaydı** olduğunu varsayar.
  - Onayla & Aktar süreci, bu kaydın üstüne ek bilgi (sayfa, yerleşim vb.) koyar.

### 3.2. Veri Kaynağı

- Ürünle ilgili temel bilgiler (isim, resim, kategori/grup vb.):
  - Mümkün olduğunca **depo veritabanındaki karttan** okunur.
- Canvas’a giderken:
  - Ürünün ana verisi **depodan çekilen data** + sayfa/dizilim bilgisi ile oluşturulur.

### 3.3. Liste Üzerinde Değişiklik → Güncelleme Talebi

- Eğer kullanıcı liste ekranında bir **depo ürünü** üzerinde:
  - İsim,
  - Fiyat,
  - Grup / kategori,
  - vb. alanları değiştirirse;
- Bu değişiklik:
  - **“Depo ürünü için güncelleme talebi”** olarak işaretlenir.
  - Talep mevcut kuralınıza göre **admin onay kuyruğuna** düşer.
  - Admin:
    - **Onaylarsa** → depo kaydı yeni değerlerle güncellenir.
    - **Reddediyorsa** → depo kaydı olduğu gibi kalır.
- Bu süreçte müşteri:
  - Ürünü kullanmaya devam edebilir, stok/ürün kartı admin kararıyla netleşir.

### 3.4. AI Gruplama

- Depodan gelen ürünlerde:
  - **AI gruplama kesinlikle çalıştırılmaz.**
  - Grup/kategori depo tarafında nasıl tutuluyorsa, o şekilde ele alınır.

---

## 4. Dış Kaynaktan Gelen Ürün Kuralları (`source_type = external`)

### 4.1. Zorunlu Alan Kontrolü

- Sadece external ürünler kontrol edilir.
- Her external ürün için:
  - İsim var mı?
  - Resim (image_url) var mı?
  - İndirim / kampanya fiyatı dolu mu ve > 0 mı?

### 4.2. Hata Durumu (Eksik Alan Varsa)

- **Tek bir external üründe bile** bu alanlardan biri eksikse:

  - Tüm 1. Aşama Onayla & Aktar işlemi **iptal edilir**:
    - **DB’ye hiçbir ürün yazılmaz** (depo + external dahil).
    - **Canvas’a hiçbir ürün gönderilmez**.

  - Kullanıcıya gösterilecek mesaj:
    - **“❌ Resimsiz / isimsiz / indirim fiyatsız ürün var. Tüm ürünlere isim, resim ve indirim fiyatı ekleyin, sonra tekrar deneyin.”**

  - Backend, hangi ürünlerde hangi eksik(ler) olduğunu teknik olarak döner.
  - Frontend, listede bu ürünleri vurgular (renk, ikon vb.).

### 4.3. Başarılı Durum (Tüm External Ürünler Temiz)

- Tüm external ürünler için:
  - İsim, resim, indirim fiyatı tamamsa;
- Devam eden adımlar:
  1. **Dağıtım / sayfa kuralı** uygulanır (Bkz. Bölüm 5).
  2. Her external ürün için **AI gruplama** yapılır (Bkz. Bölüm 6).
  3. DB’de:
     - Ürün yoksa → yeni kayıt açılır.
     - Ürün varsa → ilgili alanlar (özellikle `product_group`) güncellenir.
  4. Canvas’a, bu güncellenmiş verilerle aktarım yapılır.

---

## 5. Dağıtım / Sayfa Kuralları

### 5.1. Durum A – Hiç Sayfa / Dağıtım Seçilmemişse

- Ürün listesindeki `page_no` (veya benzeri sayfa alanı) tamamen boşsa:
  - Sistem, **liste sırasına göre otomatik sayfa dizilimi** yapar.

- İşleyiş:
  - Ürünler, frontend’de hangi sıradaysa o sıra korunur.
  - Sistem, mevcut **sayfa kapasitesi** kuralına göre:
    - Önce 1. sayfayı doldurur,
    - Sonra 2. sayfayı, 3. sayfayı… doldurur.

### 5.2. Durum B – Kısmen Sayfa Seçilmiş, Kısmen Boş

- Bazı ürünlerin sayfası seçilmiş, bazılarınınki boşsa:
  - Kullanıcıya şu soru gösterilir:
    - **“X üründe sayfa seçilmemiş. Sayfayı otomatik atayayım mı, yoksa geri dönüp sen mi seçersin?”**

- Kullanıcı cevabına göre:
  - **Otomatik derse**:
    - Sadece **sayfası boş olan ürünler** için:
      - Liste sırasına göre uygun sayfalara otomatik yerleştirilir.
  - **Geri dön derse**:
    - İşlem iptal edilir, kullanıcı liste ekranında kalır.

---

## 6. AI Gruplama Kuralları (Sadece 1. Aşama Kapsamı)

### 6.1. Gruplama Yalnızca External Ürünler İçin

- AI gruplama:
  - **Sadece external ürünler** için devrededir.
  - Depo ürünlerinde AI gruplama **yapılmaz**.

### 6.2. Sektöre Göre Grup Listeleri (Whitelist)

- Her sektör için backend’de bir **alt grup whitelist listesi** tanımlanır.
- Tüm listelerde mutlaka **`Genel`** grubu bulunur.

- Örnekler:

  - **Market sektörü**:
    - `Gıda, Temizlik, Kozmetik, İçecek, Et/Şarküteri, Bebek, Ev&Yaşam, Atıştırmalık, Kahvaltılık, Genel`

  - **Giyim sektörü** (örnek):
    - `Üst Giyim, Alt Giyim, Ayakkabı, Aksesuar, Genel`

  - Diğer sektörler için de proje ilerledikçe benzer listeler tanımlanacaktır.

### 6.3. AI’ye Verilen Bilgiler

Her external ürün için AI tarafına iletilen temel bilgiler:

- Ürün adı
- Sektör
- (Opsiyonel) Resim URL’si – sadece ek bağlam olarak

### 6.4. AI’den Beklenen Çıktı

- AI’den istenen:
  - Sadece ilgili sektörün whitelist listesinde bulunan gruplardan **tam olarak bir tanesini** döndürmesidir.

- Örneğin:
  - Sektör = `market` → sadece `Gıda, Temizlik, ... , Genel` içinden bir isim.
  - Sektör = `giyim` → sadece `Üst Giyim, Alt Giyim, Ayakkabı, Aksesuar, Genel` içinden bir isim.

### 6.5. Hata / Kararsızlık Durumu

- AI’den dönen grup ismi:
  - İlgili sektörün whitelist’inde **varsa**:
    - Ürünün `product_group` alanına **aynı şekilde** yazılır.
  - Whitelist’te **yoksa**, boşsa veya geçersiz görünüyorsa:
    - İlgili sektörün **`Genel`** grubuna atanır.

- Eğer bir sektör için henüz özel whitelist tanımlı değilse:
  - Varsayılan olarak **market sektörünün** grup listesi kullanılır.

---

## 7. Onayla & Aktar – 1. Aşama Özet Akış

1. Kullanıcı **Onayla & Aktar** butonuna basar.
2. Sistem ürünleri **kaynağına göre ayırır**:
   - `source_type = depo`
   - `source_type = external`
3. **Zorunlu alan kontrolü**:
   - Sadece external ürünlerde yapılır.
   - Eksik alanı olan **bir tane bile external ürün varsa**:
     - Tüm aktarım iptal edilir,
     - DB’ye ve Canvas’a hiçbir şey gitmez,
     - Kullanıcıya uyarı gösterilir.
4. **Dağıtım / sayfa kuralı** uygulanır:
   - Hiç sayfa seçilmemişse → liste sırasına göre otomatik dizilim,
   - Kısmen boşsa → kullanıcıya “otomatik mi, geri dön mü?” sorusu.
5. **Depo ürünleri** için:
   - Yeni kayıt açılmaz,
   - Değişiklikler **güncelleme talebi** olarak admin onayına gider,
   - Canvas’a depo datası + sayfa/dizilim bilgisi ile gönderilir.
6. **External ürünler** için:
   - AI, sektöre uygun whitelist’ten **tek grup** seçer,
   - `product_group` alanı doldurulur,
   - DB’ye yeni kayıt / güncelleme yapılır,
   - Canvas’a bu nihai veri ile aktarım yapılır.
7. Bu aşamada:
   - **Hiçbir metin/resim güzelleştirme yoktur**,
   - Sadece: **kontrol → gruplama → DB yaz → Canvas’a normal aktar** hattı çalışır.

---

## 8. Versiyonlama ve Güncelleme Notu

- Bu dosya, sistemin **canlı anayasası** olarak kabul edilir.
- Her önemli kural değişikliği sonrasında:
  - İlgili bölüm güncellenir,
  - Versiyon notu (örn. `v1.1 – 2025-12-02 – Onayla & Aktar 1. Aşama netleştirildi`) eklenir.
- Yeni sohbetlerde:
  - Önce bu dosyanın son hali referans alınır,
  - Gerekirse anayasa üzerinde **açık şekilde değişiklik yapılır**, sonra koda yansıtılır.