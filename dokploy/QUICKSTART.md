# 🚀 Hızlı Başlangıç Kılavuzu

Frappe ERPNext'i 4 temel uygulama ile 5 dakikada deploy edin!

## ⚡ 1 Dakikada Deploy

### Adım 1: Dokploy'da Yeni Service

1. Dokploy dashboard → **Projects** → **Create Project**
2. Proje adı: `frappe-erp`

### Adım 2: Docker Compose Service

1. **Add Service** → **Docker Compose**
2. Bilgileri girin:
   - **Name**: `erpnext`
   - **Repository**: `https://github.com/ubden/frappe_docker`
   - **Branch**: `main`
   - **Compose Path**: `dokploy/docker-compose.yml`

### Adım 3: Environment Variables

| Variable | Değer | Açıklama |
|----------|-------|----------|
| `SITE_NAME` | `erp.yourdomain.com` | Site domain adı |
| `ADMIN_PASSWORD` | `YourPass123!` | Admin şifresi (güçlü) |
| `DB_PASSWORD` | `DBPass456!` | Database şifresi (güçlü) |
| `HTTP_PORT` | `8080` | Frontend port |

**⚠️ ÖNEMLİ**: Şifreleri "Secret" olarak işaretleyin!

### Adım 4: Domain + SSL

1. **Domains** sekmesi → **Add Domain**
2. Domain: `erp.yourdomain.com`
3. Port: `8088`
4. **Enable HTTPS** ✅
5. **Force HTTPS** ✅

### Adım 5: Deploy!

**Deploy** butonuna tıklayın → 10-15 dakika bekleyin → Hazır! 🎉

## ✅ Kurulu Uygulamalar

- ✅ **ERPNext** - ERP Core
- ✅ **CRM** - Müşteri Yönetimi
- ✅ **Helpdesk** - Destek Sistemi
- ✅ **Payments** - Ödeme Entegrasyonları

## 🌐 İlk Giriş

```
URL: https://erp.yourdomain.com
Username: Administrator
Password: [ADMIN_PASSWORD değeriniz]
```

## 📊 Sistem Gereksinimleri

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 15 GB

**Önerilen**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 30 GB SSD

## 🔧 İlk Yapılandırma

1. Setup Wizard'ı tamamlayın
2. Şirket bilgilerini girin
3. Email ayarlarını yapın
4. İlk kullanıcıları ekleyin

## 💾 Backup

```bash
docker exec -it <backend> bench --site <site> backup --with-files
```

## 🐛 Sorun Giderme

**Site açılmıyor**:
- Browser cache temizleyin
- Container loglarını kontrol edin

**"Site not found"**:
- create-site container loglarını kontrol edin
- Site oluşturuldu mu?

---

**Toplam Süre**: 15 dakika (deployment dahil)  
**Uygulama Sayısı**: 4  
**SSL**: Otomatik
