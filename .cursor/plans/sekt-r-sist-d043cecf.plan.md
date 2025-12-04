<!-- d043cecf-9197-4138-b5e6-6a7b325335b7 8d50840d-1848-4791-a4bf-9a015a896087 -->
# Web Arama Yapısı Güncelleme

## Yeni Sorgu Ağacı (Sadece Web Arama Kısmı)

```
4. Web Arama
   │
   ├── 1. E-Ticaret Siteleri (Site-Specific Scraping)
   │      ├── asyasanalmarket.com
   │      ├── eonbir.com.tr
   │      ├── marketkarsilastir.com
   │      ├── aykanlarkapida.com
   │      ├── evkiba.com
   │      ├── migros.com.tr
   │      ├── a101.com.tr
   │      └── sokmarket.com.tr
   │
   ├── 2. Google Image Search
   ├── 3. Yandex Image Search
   ├── 4. DuckDuckGo
   └── 5. Bing
   
   + %90 Eşleşme Filtresi
```

## Yapılacaklar

### 1. E-Ticaret Scraping Fonksiyonları

Her site için barkod bazlı ürün çekme:

- Site URL yapısını analiz et
- Resim, isim, fiyat selector'ları belirle
- Cache mekanizması ekle

### 2. Yandex Search Ekle

`search_with_yandex()` fonksiyonu

### 3. Arama Sıralamasını Güncelle

`search_product_by_name()` fonksiyonunu yeni sıralamaya göre düzenle

### 4. %90 Eşleşme Filtresi

Relevance score < 90 olanları filtrele

## E-Ticaret Site Listesi

| Site | URL | Öncelik |

|------|-----|---------|

| Asya Anal Market | asyasanalmarket.com | 1 |

| Eonbir | eonbir.com.tr | 1 |

| Market Karşılaştır | marketkarsilastir.com | 1 |

| Aykanlar Kapıda | aykanlarkapida.com | 1 |

| Evkiba | evkiba.com | 1 |

| Migros | migros.com.tr | 1 |

| A101 | a101.com.tr | 1 |

| ŞOK | sokmarket.com.tr | 1 |

## Dosya

[`services/external_api.py`](market-brosur-sistemi/services/external_api.py)

### To-dos

- [ ] constants.py - 8 sektör + alt gruplar + API mapping
- [ ] database.py - SECTORS referansını constants'tan al
- [ ] login.html - Kayıt formu 8 sektör dropdown
- [ ] admin_users.html - Admin sektör dropdown
- [ ] Sektör kullanan diğer dosyaları kontrol et
- [ ] Yandex Image Search fonksiyonu ekle
- [ ] Arama sıralaması: Google → Yandex → DuckDuckGo → Bing
- [ ] %90 eşleşme filtresi ekle