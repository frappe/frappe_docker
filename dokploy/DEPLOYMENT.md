# Dokploy Deployment Kılavuzu

Frappe ERPNext'i 4 temel uygulama ile Dokploy'da deploy etme kılavuzu.

## 📦 İçerilen Uygulamalar

1. **ERPNext** - ERP Core
2. **CRM** - Müşteri İlişkileri
3. **Helpdesk** - Destek Sistemi
4. **Payments** - Ödeme Entegrasyonları

## 🚀 Hızlı Deployment (Dokploy UI)

### Adım 1: Yeni Proje

1. Dokploy Dashboard → **Projects** → **Create Project**
2. Proje adı: `frappe-erp`

### Adım 2: Service Ekle

1. **Add Service** → **Docker Compose**
2. Ayarlar:
   - Name: `erpnext`
   - Repository: `https://github.com/ubden/frappe_docker`
   - Branch: `main`
   - Compose Path: `dokploy/docker-compose.yml`

### Adım 3: Environment Variables

```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=YourSecurePass123!
DB_PASSWORD=YourDBPass456!
HTTP_PORT=8088
```

### Adım 4: Domain + SSL

1. **Domains** → **Add Domain**
2. Domain: `erp.yourdomain.com`
3. Port: `8088`
4. **Enable HTTPS** ✅
5. **Force HTTPS** ✅

### Adım 5: Deploy

**Deploy** butonu → 10-15 dakika → Hazır! 🎉

## 🌐 Erişim

```
URL: https://erp.yourdomain.com
Username: Administrator
Password: [ADMIN_PASSWORD]
```

## 🔧 İlk Yapılandırma

1. **Setup Wizard** tamamlayın
2. **Email ayarları** yapın
3. **Kullanıcılar** ekleyin
4. **Şirket bilgileri** güncelleyin

## 💾 Backup

```bash
# Container'a girin
docker exec -it <backend-container> bash

# Backup oluşturun
bench --site <site-name> backup --with-files

# Backup'ları görüntüleyin
ls sites/<site-name>/private/backups/
```

## 🔄 Güncelleme

```bash
# Dokploy'da: Redeploy butonu

# Veya manuel:
docker exec -it <backend> bash
bench update --reset
bench --site <site> migrate
bench build
```

## 🐛 Sorun Giderme

### Site Açılmıyor

```bash
# Container durumlarını kontrol edin
docker-compose ps

# Backend loglarını kontrol edin
docker-compose logs backend
```

### "Site not found"

```bash
# create-site loglarını kontrol edin
docker-compose logs create-site

# Site'ı kontrol edin
docker exec <backend> bench --site all list-apps
```

### SSL Çalışmıyor

- DNS doğru mu kontrol edin
- Domain Dokploy'da doğru eklenmiş mi?
- Let's Encrypt rate limit kontrolü

## 📚 Dokümantasyon

- [README](README.md) - Genel bilgi
- [QUICKSTART](QUICKSTART.md) - Hızlı başlangıç
- [SSL_SETUP](SSL_SETUP.md) - SSL detayları
- [ENV_VARIABLES](ENV_VARIABLES.md) - Tüm ayarlar

---

**Build Time**: 10-15 min  
**Apps**: 4  
**Port**: 8088  
**SSL**: Otomatik
