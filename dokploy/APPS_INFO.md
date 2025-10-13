# Frappe Apps Bilgileri

Bu dokümanda, Dokploy image'inde kullanılan Frappe uygulamaları ve branch bilgileri açıklanır.

## 📦 İçerilen Uygulamalar

### 1. ERPNext
- **Repository**: https://github.com/frappe/erpnext
- **Branch**: `version-15`
- **Açıklama**: Tam özellikli açık kaynak ERP sistemi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅

### 2. CRM
- **Repository**: https://github.com/frappe/crm
- **Branch**: `version-15`
- **Açıklama**: Modern müşteri ilişkileri yönetimi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅
- **Not**: Main branch'ten version-15'e geçildi (uyumluluk için)

### 3. LMS (Learning Management System)
- **Repository**: https://github.com/frappe/lms
- **Branch**: `version-15`
- **Açıklama**: Öğrenme yönetim sistemi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅
- **Not**: Main branch'ten version-15'e geçildi (uyumluluk için)

### 4. Builder
- **Repository**: https://github.com/frappe/builder
- **Branch**: `main`
- **Açıklama**: Drag & drop web sitesi oluşturucu
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Not**: Main branch Frappe v15 destekliyor

### 5. Print Designer
- **Repository**: https://github.com/frappe/print_designer
- **Branch**: `version-15`
- **Açıklama**: Özel yazdırma şablonu tasarımcısı
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅

### 6. Payments
- **Repository**: https://github.com/frappe/payments
- **Branch**: `version-15`
- **Açıklama**: Ödeme gateway entegrasyonları
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅
- **Not**: Develop branch'ten version-15'e geçildi

### 7. Wiki
- **Repository**: https://github.com/frappe/wiki
- **Branch**: `version-15`
- **Açıklama**: Bilgi tabanı ve dokümantasyon sistemi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅

## ❌ Kaldırılan Uygulamalar

### Twilio Integration
- **Sebep**: Version-15 branch'i yok, master branch uyumsuz
- **Alternatif**: ERPNext'in built-in SMS/telefon özellikleri kullanılabilir
- **Manuel Kurulum**: Gerekirse sonradan `bench get-app` ile eklenebilir

### ERPNext Shipping
- **Sebep**: Version-15 branch'i yok, dependency sorunları
- **Alternatif**: ERPNext'in built-in shipping özellikleri kullanılabilir
- **Manuel Kurulum**: Gerekirse sonradan `bench get-app` ile eklenebilir

## 🔧 Versiyon Uyumluluğu

### Frappe Framework: v15
Tüm uygulamalar Frappe v15 ile test edilmiştir ve uyumludur.

### Branch Stratejisi
- **`version-15`**: Stable, production-ready
- **`main`**: Latest features (v15 uyumlu olanlar)
- **`develop`**: Development branch (kullanılmıyor)

## 📊 Branch Değişiklikleri

| Uygulama | Önceki Branch | Yeni Branch | Sebep |
|----------|---------------|-------------|-------|
| CRM | main | version-15 | Uyumluluk |
| LMS | main | version-15 | Uyumluluk |
| Payments | develop | version-15 | Stabilite |
| Wiki | main | version-15 | Uyumluluk |
| Twilio | master | ❌ Kaldırıldı | Branch yok |
| Shipping | main | ❌ Kaldırıldı | Uyumsuzluk |

## 🚀 Manuel Uygulama Ekleme

Eğer kaldırılan uygulamaları eklemek isterseniz:

### Twilio Integration (Riskli)
```bash
# Container'a girin
docker exec -it <backend-container> bash

# Uygulamayı ekleyin
bench get-app https://github.com/frappe/twilio-integration

# Site'a kurun
bench --site <site-name> install-app twilio_integration

# Restart
bench restart
```

### ERPNext Shipping (Riskli)
```bash
# Container'a girin
docker exec -it <backend-container> bash

# Uygulamayı ekleyin
bench get-app https://github.com/frappe/erpnext-shipping

# Site'a kurun
bench --site <site-name> install-app erpnext_shipping

# Restart
bench restart
```

⚠️ **Uyarı**: Bu uygulamalar Frappe v15 ile test edilmemiştir ve sorunlara yol açabilir.

## ✅ Production Önerileri

### Önerilen Konfigürasyon (Mevcut)
- ✅ ERPNext
- ✅ CRM
- ✅ LMS
- ✅ Builder
- ✅ Print Designer
- ✅ Payments
- ✅ Wiki

Bu 7 uygulama Frappe v15 ile tam uyumlu ve production-ready'dir.

### İsteğe Bağlı Eklemeler
Site kurulduktan sonra manuel olarak ekleyebilirsiniz:
- Twilio Integration (SMS/telefon)
- ERPNext Shipping (kargo)
- Diğer custom apps

## 🔄 Güncelleme

Uygulamaları güncellemek için:

```bash
# Container'a girin
docker exec -it <backend-container> bash

# Tüm uygulamaları güncelle
bench update --reset

# Sadece belirli app
bench update --app crm

# Site'ı migrate et
bench --site <site-name> migrate
```

## 📚 Kaynaklar

- [Frappe Apps](https://github.com/frappe)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)

---

**Son Güncelleme**: 2025-10-13
**Frappe Versiyon**: v15
**Toplam App**: 7

