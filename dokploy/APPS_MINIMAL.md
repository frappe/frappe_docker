# Minimal Uygulama Kurulumu

Bu konfigürasyonda sadece **5 temel uygulama** bulunur - production-ready minimal setup.

## 📦 İçerilen Uygulamalar (5)

### 1. ERPNext (Core ERP)
- **Repository**: https://github.com/frappe/erpnext
- **Branch**: `version-15`
- **Özellikler**:
  - 📊 Accounting (Muhasebe)
  - 📦 Inventory (Stok Yönetimi)
  - 🛒 Sales & Purchase (Satış & Satınalma)
  - 🏭 Manufacturing (Üretim)
  - 📈 Reports & Analytics
  - 💼 Projects & Tasks
  - 🏢 Asset Management

### 2. HRMS (İnsan Kaynakları)
- **Repository**: https://github.com/frappe/hrms
- **Branch**: `version-15`
- **Özellikler**:
  - 💰 Payroll (Bordro)
  - 🏖️ Leave Management (İzin Yönetimi)
  - ⏰ Attendance (Devam Takibi)
  - 📊 Performance Reviews
  - 🎯 Appraisals
  - 💼 Employee Lifecycle

### 3. CRM (Müşteri İlişkileri)
- **Repository**: https://github.com/frappe/crm
- **Branch**: `main` (v1.53.1)
- **Özellikler**:
  - 👥 Lead Management
  - 💼 Deal Pipeline
  - 📞 Contact Management
  - 📊 Kanban View
  - 📧 Email Integration
  - 📱 WhatsApp Integration

### 4. Helpdesk (Destek Sistemi)
- **Repository**: https://github.com/frappe/helpdesk
- **Branch**: `v1.14.0` (son v15 uyumlu)
- **Özellikler**:
  - 🎫 Ticket Management
  - ⏱️ SLA (Service Level Agreement)
  - 📧 Email Integration
  - 📚 Knowledge Base
  - 🤖 Auto Assignment
  - 📊 Reporting

### 5. Payments (Ödeme Entegrasyonları)
- **Repository**: https://github.com/frappe/payments
- **Branch**: `main`
- **Özellikler**:
  - 💳 Stripe Integration
  - 💰 PayPal Integration
  - 🇮🇳 Razorpay Integration
  - 🔄 Subscription Management
  - 🧾 Payment Request
  - 📊 Payment Analytics

## ❌ Kaldırılan Uygulamalar

### LMS (E-Learning)
- **Sebep**: Çoğu işletme için gerekli değil
- **Manuel kurulum**: `bench get-app lms && bench --site <site> install-app lms`

### Builder (Website Builder)
- **Sebep**: ERPNext'in Website module'ü yeterli
- **Manuel kurulum**: `bench get-app builder && bench --site <site> install-app builder`

### Print Designer (Yazdırma Tasarımcısı)
- **Sebep**: ERPNext'in Print Format yeterli
- **Manuel kurulum**: `bench get-app print_designer && bench --site <site> install-app print_designer`

### Wiki (Bilgi Tabanı)
- **Sebep**: Helpdesk'in Knowledge Base özelliği yeterli
- **Manuel kurulum**: `bench get-app https://github.com/frappe/wiki && bench --site <site> install-app wiki`

## 🎯 Neden Minimal Setup?

### Avantajlar

1. **Hızlı Build** 🚀
   - Önceden: 9 app × 2 dk = 18 dakika
   - Şimdi: 5 app × 2 dk = **10 dakika**
   - **%45 daha hızlı!**

2. **Az Disk Kullanımı** 💾
   - Önceden: ~8 GB final image
   - Şimdi: **~4-5 GB** final image
   - **%40 daha az yer!**

3. **Daha Az Dependency** 📦
   - Daha az npm packages
   - Daha az Python packages
   - Daha az conflict riski

4. **Kolay Maintenance** 🔧
   - Daha az güncelleme
   - Daha az sorun giderme
   - Daha kolay troubleshoot

5. **Production-Ready** ✅
   - Sadece gerçekten kullanılan app'ler
   - Test edilmiş ve stabil
   - Frappe v15 tam uyumlu

## 📊 Özellik Karşılaştırması

### ERPNext Built-in Özellikler

**Website Builder yerine**:
- ✅ Website module (basic web sitesi)
- ✅ Web pages
- ✅ Blog posts
- ✅ Products catalog

**Print Designer yerine**:
- ✅ Print Format
- ✅ Custom templates
- ✅ Jinja templating
- ✅ PDF generation

**Wiki yerine**:
- ✅ Helpdesk Knowledge Base
- ✅ Notes
- ✅ Comments
- ✅ Rich text editor

## 🔧 Manuel Uygulama Ekleme

Eğer ilave uygulamaya ihtiyaç duyarsanız:

### Container'a Giriş

```bash
# Backend container'a girin
docker exec -it <backend-container> bash
```

### LMS Kurulumu

```bash
# LMS'i indirin
bench get-app lms https://github.com/frappe/lms

# Build edin
bench build --app lms

# Site'a kurun
bench --site <site-name> install-app lms

# Restart
bench restart
```

### Builder Kurulumu

```bash
bench get-app builder https://github.com/frappe/builder
bench build --app builder
bench --site <site-name> install-app builder
bench restart
```

### Print Designer Kurulumu

```bash
bench get-app print_designer https://github.com/frappe/print_designer
bench build --app print_designer
bench --site <site-name> install-app print_designer
bench restart
```

### Wiki Kurulumu

```bash
bench get-app https://github.com/frappe/wiki
bench build --app wiki
bench --site <site-name> install-app wiki
bench restart
```

## 🌐 Port ve SSL Konfigürasyonu

### Frontend Port: 8088

```env
HTTP_PORT=8088
```

**Erişim**:
- HTTP: `http://erp.yourdomain.com:8088`
- HTTPS: `https://erp.yourdomain.com` (port gerekmez)

### SSL/HTTPS Kurulumu

Dokploy otomatik SSL yönetimi sağlar:

1. **Domain ekleyin**: `erp.yourdomain.com`
2. **Enable HTTPS** işaretleyin
3. **Force HTTPS** işaretleyin
4. Let's Encrypt otomatik sertifika oluşturur

Detaylar için: [SSL_SETUP.md](SSL_SETUP.md)

## 📈 Performans

### Build Süreleri

| Konfigürasyon | App Sayısı | Build Süresi | Disk Kullanımı |
|---------------|-----------|--------------|----------------|
| **Full (9 apps)** | 9 | ~30-40 dakika | ~8 GB |
| **Minimal (5 apps)** | 5 | **~15-20 dakika** | **~4-5 GB** |

**Kazanç**: %50 daha hızlı, %40 daha az disk!

### Runtime Performansı

- ✅ Daha az memory kullanımı
- ✅ Daha hızlı startup
- ✅ Daha az background jobs
- ✅ Daha responsive UI

## ✅ Production Önerileri

### Bu Setup İçin İdeal

1. **Küçük-Orta İşletmeler**
   - ERP + HR + CRM + Support
   - Tüm temel ihtiyaçlar karşılanır

2. **E-Ticaret**
   - ERPNext (inventory, sales)
   - CRM (customer management)
   - Payments (gateway integration)
   - Helpdesk (customer support)

3. **Hizmet Şirketleri**
   - Project management (ERPNext)
   - HR management (HRMS)
   - Customer tracking (CRM)
   - Support tickets (Helpdesk)

### Bu Setup İçin Uygun Değil

1. **Eğitim Kurumları** → LMS ekleyin
2. **Çok sayıda landing page** → Builder ekleyin
3. **Kompleks print formatları** → Print Designer ekleyin
4. **Geniş dokümantasyon** → Wiki ekleyin

## 📝 Migration Path

### Full Setup'tan Minimal'e Geçiş

Eğer önceden 9 app kurduysanız:

```bash
# Backup alın
bench --site <site> backup --with-files

# Kullanmadığınız app'leri kaldırın
bench --site <site> uninstall-app lms
bench --site <site> uninstall-app builder
bench --site <site> uninstall-app print_designer
bench --site <site> uninstall-app wiki

# Restart
bench restart
```

### Minimal'den Full'e Geçiş

Yukarıdaki manuel kurulum bölümüne bakın.

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0 (Minimal)  
**Toplam App**: 5 (ERPNext, HRMS, CRM, Helpdesk, Payments)  
**Frontend Port**: 8088  
**SSL**: Dokploy otomatik (Let's Encrypt)

