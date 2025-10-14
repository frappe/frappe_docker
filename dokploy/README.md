# Frappe ERPNext - Dokploy Deployment

Frappe ERPNext'i 4 temel uygulama ile Dokploy'da kolayca deploy edin.

## 📦 İçerilen Uygulamalar

1. **ERPNext** - Tam özellikli ERP (Accounting, Inventory, Sales, Manufacturing)
2. **CRM** - Müşteri İlişkileri Yönetimi
3. **Helpdesk** - Müşteri Destek Sistemi
4. **Payments** - Ödeme Gateway Entegrasyonları

## 🚀 Hızlı Başlangıç

### Dokploy'da Deploy

```bash
Repository: https://github.com/ubden/frappe_docker
Branch: main
Compose Path: dokploy/docker-compose.yml
```

**Environment Variables**:
```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=your_secure_password
DB_PASSWORD=your_db_password
HTTP_PORT=8080
```

**Domain + SSL**:
- Domain ekleyin: `erp.yourdomain.com`
- Enable HTTPS ✅ (Let's Encrypt otomatik)
- Force HTTPS ✅

**Deploy** butonuna tıklayın → 10-15 dakikada hazır! ✨

## 🔧 Teknik Detaylar

- **Frontend Port**: 8088
- **SSL**: Dokploy otomatik (Let's Encrypt)
- **Build Süresi**: 10-15 dakika
- **Disk Kullanımı**: 3-4 GB
- **Frappe**: v15
- **ERPNext**: v15

## 📚 Dokümantasyon

- [Hızlı Başlangıç](QUICKSTART.md) - 5 dakikada deploy
- [SSL Kurulumu](SSL_SETUP.md) - HTTPS konfigürasyonu
- [Environment Variables](ENV_VARIABLES.md) - Tüm ayarlar
- [Deployment Kılavuzu](DEPLOYMENT.md) - Detaylı adımlar

## 💡 İlk Giriş

```
URL: https://erp.yourdomain.com
Username: Administrator
Password: [ADMIN_PASSWORD değeriniz]
```

## 🔄 Backup

```bash
# Container'a girin
docker exec -it <backend-container> bash

# Backup oluşturun
bench --site <site-name> backup --with-files

# Backup dosyaları
ls sites/<site-name>/private/backups/
```

## 🆘 Destek

- [GitHub Issues](https://github.com/ubden/frappe_docker/issues)
- [Frappe Forum](https://discuss.frappe.io)
- [ERPNext Docs](https://docs.erpnext.com)

---

**Versiyon**: 1.0.0  
**Apps**: 4 (ERPNext, CRM, Helpdesk, Payments)  
**Port**: 8088  
**SSL**: Auto
