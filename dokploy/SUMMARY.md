# Frappe ERPNext - Dokploy Paketi Özeti

## 📦 Paket İçeriği

Frappe ERPNext ve 3 ek uygulama ile production-ready deployment paketi.

### İçerilen Uygulamalar

| Uygulama | Açıklama | Branch/Tag |
|----------|----------|-----------|
| **ERPNext** | ERP Core (Accounting, Inventory, Sales) | version-15 |
| **CRM** | Müşteri İlişkileri Yönetimi | main (v1.53.1) |
| **Helpdesk** | Destek Sistemi (Ticket, SLA) | v1.14.0 |
| **Payments** | Ödeme Entegrasyonları | main |

**Toplam**: 4 Uygulama

## 🎯 Özellikler

- ⚡ Hızlı deployment (10-15 dakika)
- 💾 Az disk kullanımı (3-4 GB)
- 🔒 Otomatik SSL (Let's Encrypt)
- 🚀 Production-ready konfigürasyon
- 📱 Port 8080 (standard)

## 🏗️ Mimari

```
Browser (HTTPS:443)
    ↓
Dokploy Proxy (SSL)
    ↓
Frontend (Port 8080)
    ↓
Backend (Port 8000)
    ↓
MariaDB + Redis
```

## 📊 Performans

- **Build Süresi**: 10-15 dakika
- **Memory**: 2 GB
- **Disk**: 3-4 GB
- **CPU**: 2+ cores

## 🔧 Konfigürasyon

### Environment Variables

```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=your_password
DB_PASSWORD=db_password
HTTP_PORT=8080
```

### SSL

- Dokploy otomatik Let's Encrypt
- HTTPS force redirect
- Auto renewal

## 📚 Dokümantasyon

- [README](README.md) - Genel bilgi
- [QUICKSTART](QUICKSTART.md) - Hızlı başlangıç
- [SSL_SETUP](SSL_SETUP.md) - SSL konfigürasyonu
- [ENV_VARIABLES](ENV_VARIABLES.md) - Environment variables

---

**Apps**: 4  
**Port**: 8088  
**SSL**: Auto  
**Build**: 10-15 min
