# Frappe Apps Bilgileri

Bu dokümanda, Dokploy image'inde kullanılan Frappe uygulamaları ve branch bilgileri açıklanır.

## 📦 İçerilen Uygulamalar (9 Uygulama)

### 1. ERPNext
- **Repository**: https://github.com/frappe/erpnext
- **Branch**: `version-15`
- **Docker Image**: N/A (source build)
- **Açıklama**: Tam özellikli açık kaynak ERP sistemi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅

### 2. HRMS (Human Resource Management System) 🆕
- **Repository**: https://github.com/frappe/hrms  
- **Branch**: `version-15`
- **Docker Image**: `ghcr.io/frappe/hrms:version-15`
- **Açıklama**: İnsan Kaynakları Yönetim Sistemi
- **Uyumluluk**: Frappe v15 ile tam uyumlu ✅
- **Özellikler**: Bordro, izin yönetimi, devam takibi, performans değerlendirme

### 3. CRM (Customer Relationship Management)
- **Repository**: https://github.com/frappe/crm
- **Branch**: `main` (latest)
- **Docker Image**: `ghcr.io/frappe/crm:latest`
- **Açıklama**: Modern müşteri ilişkileri yönetimi
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Lead tracking, deal management, kanban view

### 4. Helpdesk 🆕
- **Repository**: https://github.com/frappe/helpdesk
- **Branch**: `main` (stable)
- **Docker Image**: `ghcr.io/frappe/helpdesk:stable`
- **Açıklama**: Müşteri destek ve ticket yönetim sistemi
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Ticket management, SLA, email integration, knowledge base

### 5. LMS (Learning Management System)
- **Repository**: https://github.com/frappe/lms
- **Branch**: `main` (stable)
- **Docker Image**: `ghcr.io/frappe/lms:stable`
- **Açıklama**: E-Learning ve öğrenme yönetim sistemi
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Online courses, quizzes, certifications, student management

### 6. Builder
- **Repository**: https://github.com/frappe/builder
- **Branch**: `main` (stable)
- **Docker Image**: `ghcr.io/frappe/builder:stable`
- **Açıklama**: Drag & drop web sitesi oluşturucu
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Visual page builder, responsive design, SEO optimization

### 7. Print Designer
- **Repository**: https://github.com/frappe/print_designer
- **Branch**: `main` (stable)
- **Docker Image**: `ghcr.io/frappe/print_designer:stable`
- **Açıklama**: Özel yazdırma şablonu tasarımcısı
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Custom print formats, drag & drop designer, PDF generation

### 8. Payments
- **Repository**: https://github.com/frappe/payments
- **Branch**: `main`
- **Docker Image**: N/A (install via bench)
- **Açıklama**: Ödeme gateway entegrasyonları
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Stripe, PayPal, Razorpay integration
- **Kurulum**: `bench --site <sitename> install-app payments`

### 9. Wiki
- **Repository**: https://github.com/frappe/wiki
- **Branch**: `main`
- **Docker Image**: N/A (install via bench)
- **Açıklama**: Bilgi tabanı ve dokümantasyon sistemi
- **Uyumluluk**: Frappe v15 ile uyumlu ✅
- **Özellikler**: Wiki pages, version control, markdown support
- **Kurulum**: `bench get-app https://github.com/frappe/wiki`

## ❌ Kaldırılan Uygulamalar

### Twilio Integration
- **Sebep**: Version-15 branch'i yok, uyumluluk sorunları
- **Alternatif**: ERPNext'in built-in SMS/telefon özellikleri
- **Manuel Kurulum**: Gerekirse sonradan eklenebilir (riskli)

### ERPNext Shipping
- **Sebep**: Version-15 branch'i yok, dependency sorunları
- **Alternatif**: ERPNext'in built-in shipping özellikleri
- **Manuel Kurulum**: Gerekirse sonradan eklenebilir (riskli)

## 🔧 Versiyon Uyumluluğu

### Frappe Framework: v15
Tüm uygulamalar Frappe v15 ile test edilmiştir ve uyumludur.

### Branch Stratejisi
- **`version-15`**: Stable, production-ready (ERPNext, HRMS)
- **`main`**: Latest stable features (diğer tüm uygulamalar)

## 📊 Branch Değişiklikleri

| Uygulama | Branch | Docker Image | Durum |
|----------|--------|--------------|-------|
| ERPNext | version-15 | N/A | ✅ Stable |
| HRMS 🆕 | version-15 | ghcr.io/frappe/hrms:version-15 | ✅ Stable |
| CRM | main (latest) | ghcr.io/frappe/crm:latest | ✅ Production |
| Helpdesk 🆕 | main (stable) | ghcr.io/frappe/helpdesk:stable | ✅ Production |
| LMS | main (stable) | ghcr.io/frappe/lms:stable | ✅ Production |
| Builder | main (stable) | ghcr.io/frappe/builder:stable | ✅ Production |
| Print Designer | main (stable) | ghcr.io/frappe/print_designer:stable | ✅ Production |
| Payments | main | N/A | ✅ Production |
| Wiki | main | N/A | ✅ Production |

## ✅ Production Önerileri

### Önerilen Konfigürasyon (Mevcut - 9 Uygulama)
- ✅ **ERPNext** - ERP Core
- ✅ **HRMS** - İnsan Kaynakları 🆕
- ✅ **CRM** - Müşteri İlişkileri
- ✅ **Helpdesk** - Destek Sistemi 🆕
- ✅ **LMS** - E-Learning
- ✅ **Builder** - Web Sitesi
- ✅ **Print Designer** - Yazdırma
- ✅ **Payments** - Ödeme
- ✅ **Wiki** - Bilgi Tabanı

Bu 9 uygulama Frappe v15 ile tam uyumlu ve production-ready'dir.

## 🚀 Docker Image Kullanımı

GitHub Container Registry'de bazı uygulamaların hazır image'ları var:

```bash
# HRMS
docker pull ghcr.io/frappe/hrms:version-15

# CRM
docker pull ghcr.io/frappe/crm:latest

# Helpdesk
docker pull ghcr.io/frappe/helpdesk:stable

# LMS
docker pull ghcr.io/frappe/lms:stable

# Builder
docker pull ghcr.io/frappe/builder:stable

# Print Designer
docker pull ghcr.io/frappe/print_designer:stable
```

**Not**: Bizim Dockerfile source'tan build ediyor, Docker image'ları kullanmıyor.

## 📚 Kaynaklar

- [Frappe Apps](https://github.com/frappe)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)
- [GitHub Container Registry](https://github.com/orgs/frappe/packages)

---

**Son Güncelleme**: 2025-10-13  
**Frappe Versiyon**: v15  
**Toplam App**: 9 (2 yeni: HRMS, Helpdesk)
