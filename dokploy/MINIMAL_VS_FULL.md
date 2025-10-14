# Minimal vs Full Setup Karşılaştırması

## 📊 Setup Karşılaştırması

| Özellik | Minimal (5 Apps) | Full (9 Apps) |
|---------|-----------------|---------------|
| **Build Süresi** | 15-20 dakika ⚡ | 30-40 dakika |
| **Disk Kullanımı** | 4-5 GB 💾 | 8 GB |
| **Memory Kullanımı** | ~2 GB | ~4 GB |
| **Complexity** | Basit ✅ | Kompleks |
| **Maintenance** | Kolay | Zor |

## 📦 Uygulama Karşılaştırması

### Minimal Setup (Mevcut)

```
✅ ERPNext    - ERP Core
✅ HRMS       - HR Management
✅ CRM        - Customer Relations
✅ Helpdesk   - Customer Support
✅ Payments   - Payment Gateways
```

**Toplam**: 5 App

### Full Setup

```
✅ ERPNext         - ERP Core
✅ HRMS            - HR Management
✅ CRM             - Customer Relations
✅ Helpdesk        - Customer Support
✅ Payments        - Payment Gateways
➕ LMS             - E-Learning
➕ Builder         - Website Builder
➕ Print Designer  - Custom Prints
➕ Wiki            - Knowledge Base
```

**Toplam**: 9 App

## 🎯 Hangi Setup Size Uygun?

### Minimal Setup İçin İdeal (Önerilen)

✅ **Küçük-Orta İşletmeler**
- ERP + HR + CRM ihtiyacı var
- Basit başlamak istiyorlar
- Hızlı deployment gerekli

✅ **E-Ticaret**
- Ürün/stok yönetimi
- Müşteri takibi
- Ödeme entegrasyonu
- Destek sistemi

✅ **Hizmet Şirketleri**
- Proje yönetimi
- HR takibi
- Müşteri CRM
- Ticket sistemi

✅ **Yeni Başlayanlar**
- Frappe'ye yeni başlayanlar
- Test/POC aşamasında
- Sonra eklemek isteyenler

### Full Setup İçin İdeal

✅ **Eğitim Kurumları**
- LMS gerekli
- Online kurslar
- Öğrenci yönetimi

✅ **Ajanslar/Danışmanlık**
- Builder (müşteri siteleri)
- Wiki (dokümantasyon)
- Custom print formats

✅ **Büyük Organizasyonlar**
- Tüm özellikleri kullanacaklar
- Disk/memory sınırlaması yok
- Kompleksliği yönetebilirler

## 💾 Kaynak Kullanımı

### Disk Kullanımı

```
Minimal Setup:
├─ Base image: 1.5 GB
├─ ERPNext: 1.0 GB
├─ HRMS: 0.5 GB
├─ CRM: 0.8 GB
├─ Helpdesk: 0.7 GB
└─ Payments: 0.5 GB
TOPLAM: ~5 GB

Full Setup:
├─ Minimal: 5 GB
├─ LMS: 1.2 GB
├─ Builder: 0.8 GB
├─ Print Designer: 0.6 GB
└─ Wiki: 0.4 GB
TOPLAM: ~8 GB
```

### Memory Kullanımı (Runtime)

```
Minimal Setup:
├─ Backend: 800 MB
├─ Frontend: 200 MB
├─ Workers: 600 MB
├─ Database: 400 MB
└─ Redis: 200 MB
TOPLAM: ~2.2 GB

Full Setup:
├─ Backend: 1.5 GB (daha fazla app)
├─ Frontend: 300 MB
├─ Workers: 1 GB
├─ Database: 600 MB
└─ Redis: 300 MB
TOPLAM: ~3.7 GB
```

## ⏱️ Build Süresi Analizi

### Minimal Setup (5 apps)

```
1. ERPNext: 3 dakika
2. HRMS: 2 dakika
3. CRM: 2 dakika
4. Helpdesk: 1.5 dakika
5. Payments: 1 dakika
6. Cleanup: 0.5 dakika
TOPLAM: ~10 dakika
```

### Full Setup (9 apps)

```
1-5: Minimal apps: 10 dakika
6. LMS: 3 dakika
7. Builder: 2.5 dakika
8. Print Designer: 2 dakika
9. Wiki: 1.5 dakika
10. Cleanup: 1 dakika
TOPLAM: ~20 dakika
```

## 🔄 Migration (Minimal ↔ Full)

### Minimal'e Geçiş (Full'den)

```bash
# Backup alın
bench --site <site> backup --with-files

# Kullanmadığınız app'leri kaldırın
bench --site <site> uninstall-app lms
bench --site <site> uninstall-app builder
bench --site <site> uninstall-app print_designer
bench --site <site> uninstall-app wiki

# Apps klasöründen silin
cd apps
rm -rf lms builder print_designer wiki

# Restart
bench restart
```

### Full'e Geçiş (Minimal'den)

```bash
# Uygulamaları ekleyin (yukarıdaki manuel kurulum bölümüne bakın)
bench get-app lms
bench get-app builder
bench get-app print_designer
bench get-app wiki

# Build edin
bench build

# Site'a kurun
bench --site <site> install-app lms
bench --site <site> install-app builder
bench --site <site> install-app print_designer
bench --site <site> install-app wiki

# Restart
bench restart
```

## 📈 Sistem Gereksinimleri

### Minimal Setup

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 15 GB

**Önerilen**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 30 GB SSD

### Full Setup

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 25 GB

**Önerilen**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 50 GB SSD

## 🎓 Öneri

### Çoğu Kullanıcı İçin: **Minimal Setup** ✨

**Sebep**:
1. Hızlı başlayın
2. İhtiyaç oldukça ekleyin
3. Kaynakları verimli kullanın
4. Bakımı kolay

### Özel İhtiyaçlar: **Full Setup**

Sadece şu durumlarda:
- LMS kesinlikle gerekli
- Çok sayıda website oluşturulacak
- Kompleks print formatları var
- Geniş wiki/dokümantasyon gerekli

## 📝 Özet

**Minimal Setup = Önerilen! ⭐**

- ✅ 5 core app
- ✅ Hızlı ve verimli
- ✅ Production-ready
- ✅ İhtiyaca göre genişleyebilir

---

**Son Güncelleme**: 2025-10-13  
**Önerilen**: Minimal Setup  
**Toplam App**: 5

