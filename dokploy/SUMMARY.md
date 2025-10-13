# Frappe ERPNext - Dokploy Kurulum Özeti

## 📦 Paket İçeriği

Bu Dokploy paketi, Frappe ERPNext'i ve 8 ek uygulamayı tek seferde deploy etmenizi sağlar.

### İçerilen Uygulamalar

| Uygulama | Açıklama | Branch |
|----------|----------|--------|
| **ERPNext** | Tam özellikli açık kaynak ERP sistemi | version-15 |
| **CRM** | Müşteri İlişkileri Yönetimi | main |
| **LMS** | Öğrenme Yönetim Sistemi (e-Learning) | main |
| **Builder** | Drag & Drop Web Sitesi Oluşturucu | main |
| **Print Designer** | Özel Yazdırma Şablonu Tasarımcısı | main |
| **Payments** | Ödeme Gateway Entegrasyonları | develop |
| **Wiki** | Bilgi Tabanı ve Dokümantasyon Sistemi | main |
| **Twilio Integration** | SMS ve Telefon Araması Entegrasyonu | master |
| **ERPNext Shipping** | Kargo Firmalarıyla Entegrasyon | main |

## 🏗️ Mimari

```
┌─────────────────────────────────────────┐
│           Dokploy Platform              │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │    Docker Compose         │
    └─────────────┬─────────────┘
                  │
    ┌─────────────┴─────────────────────────┐
    │                                       │
    ▼                                       ▼
┌───────────┐                      ┌────────────┐
│  Frontend │                      │   Backend  │
│  (Nginx)  │◄─────────────────────┤ (Gunicorn) │
└─────┬─────┘                      └──────┬─────┘
      │                                   │
      │         ┌─────────────────────────┤
      │         │                         │
      ▼         ▼                         ▼
┌──────────┐ ┌──────────┐         ┌─────────────┐
│WebSocket │ │  Workers │         │  Scheduler  │
│  (Node)  │ │ (Short)  │         │   (Cron)    │
└────┬─────┘ └────┬─────┘         └──────┬──────┘
     │            │                      │
     │            └──────────┬───────────┘
     │                       │
     ▼                       ▼
┌─────────────┐      ┌──────────────┐
│   Redis     │      │   MariaDB    │
│   Cache     │      │  Database    │
└─────────────┘      └──────────────┘
```

## 📋 Dosya Yapısı

```
dokploy/
├── apps.json                 # Kurulacak uygulamaların listesi
├── Dockerfile               # Özel Frappe ERPNext image tanımı
├── docker-compose.yml       # Development/local kullanım için
├── docker-compose.prod.yml  # Production için optimize edilmiş
├── .env                     # Environment variables (kopyalanacak)
├── .dockerignore           # Docker build için ignore dosyası
├── dokploy.json            # Dokploy metadata
├── install.sh              # Otomatik kurulum scripti
├── README.md               # Ana dokümantasyon
├── QUICKSTART.md           # Hızlı başlangıç kılavuzu
├── DEPLOYMENT.md           # Detaylı deployment kılavuzu
└── SUMMARY.md              # Bu dosya
```

## 🚀 Hızlı Başlangıç

### 1 Dakikada Deploy

```bash
# Dokploy Dashboard → New Project → Docker Compose
Repository: https://github.com/ubden/frappe_docker
Branch: main
Compose Path: dokploy/docker-compose.yml

# Environment Variables ekle:
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=your_secure_password
DB_PASSWORD=your_db_password

# Deploy butonuna tıkla!
```

Detaylı bilgi: [QUICKSTART.md](QUICKSTART.md)

## ⚙️ Konfigürasyon

### Temel Ayarlar

| Variable | Varsayılan | Açıklama |
|----------|-----------|----------|
| `SITE_NAME` | `site1.localhost` | Site domain adı |
| `ADMIN_PASSWORD` | `admin` | Administrator şifresi |
| `DB_PASSWORD` | `changeit` | MariaDB root şifresi |
| `HTTP_PORT` | `80` | HTTP port |

### Gelişmiş Ayarlar

| Variable | Varsayılan | Açıklama |
|----------|-----------|----------|
| `CLIENT_MAX_BODY_SIZE` | `50m` | Maksimum upload boyutu |
| `PROXY_READ_TIMEOUT` | `120` | Proxy timeout (saniye) |
| `FRAPPE_SITE_NAME_HEADER` | `$$host` | Site resolution header |

## 🔧 Servisler

### Core Services
- **frontend**: Nginx reverse proxy (Port 8080)
- **backend**: Gunicorn application server
- **websocket**: Socket.IO server (real-time)

### Data Services
- **mariadb**: MariaDB 10.6 (utf8mb4)
- **redis-cache**: Redis cache layer
- **redis-queue**: Redis job queue

### Worker Services
- **queue-short**: Kısa süreli işler
- **queue-long**: Uzun süreli işler
- **scheduler**: Zamanlanmış görevler

### Setup Services (One-time)
- **configurator**: İlk konfigürasyon
- **create-site**: Site oluşturma

## 💾 Volumes (Veri Depolama)

```yaml
volumes:
  mariadb-data:      # Database verileri
  redis-cache-data:  # Redis cache
  redis-queue-data:  # Redis queue
  sites:             # Frappe sites ve dosyalar
  logs:              # Application logs
```

**⚠️ ÖNEMLİ**: Bu volume'ları silmeden önce mutlaka backup alın!

## 🔒 Güvenlik

### Önerilen Güvenlik Ayarları

1. **Güçlü Şifreler**
   ```
   Min 12 karakter
   Büyük/küçük harf + sayı + özel karakter
   ```

2. **HTTPS/SSL**
   - Dokploy otomatik Let's Encrypt
   - Domain ekle + "Enable HTTPS"

3. **Firewall**
   ```bash
   Açık portlar: 80, 443
   SSH: Sadece güvenli IP'ler
   ```

4. **2FA (Two-Factor Authentication)**
   - User ayarlarından aktif edin
   - TOTP app kullanın (Google Authenticator vb.)

5. **Düzenli Backup**
   - Günlük otomatik backup
   - Off-site backup storage

## 📊 Sistem Gereksinimleri

### Minimum (Test/Development)
```
CPU:  2 cores
RAM:  4GB
Disk: 20GB
```

### Önerilen (Production)
```
CPU:  4+ cores
RAM:  8GB+
Disk: 50GB+ SSD
```

### Optimal (Enterprise)
```
CPU:  8+ cores
RAM:  16GB+
Disk: 100GB+ NVMe SSD
```

## 📈 Performans Ayarları

### MariaDB Optimizasyonu
```yaml
innodb-buffer-pool-size: 4G  # RAM'in %50-75'i
max-connections: 1000
innodb-log-file-size: 1G
```

### Gunicorn Workers
```python
workers = CPU_count × 2
threads = 8
timeout = 300
```

### Redis Memory
```
redis-cache:  2GB (LRU eviction)
redis-queue:  1GB (No eviction)
```

## 🛠️ Maintenance

### Güncellemeler

```bash
# Dokploy'da: Redeploy butonu

# Manuel:
docker exec <backend> bench update --reset
docker exec <backend> bench migrate
docker exec <backend> bench build
```

### Backup

```bash
# Otomatik (Cron)
0 2 * * * docker exec <backend> bench --site <site> backup --with-files

# Manuel
docker exec <backend> bench --site <site> backup --with-files
```

### Monitoring

```bash
# Container durumu
docker-compose ps

# Loglar
docker-compose logs -f [service-name]

# Resource kullanımı
docker stats
```

## 🐛 Yaygın Sorunlar

| Sorun | Çözüm |
|-------|-------|
| Site açılmıyor | Browser cache temizle, container loglarını kontrol et |
| "Site not found" | `docker-compose up create-site` çalıştır |
| Yavaş çalışıyor | Worker/buffer pool ayarlarını artır |
| DB bağlantı hatası | MariaDB container'ın healthy olduğunu kontrol et |

Detaylı sorun giderme: [DEPLOYMENT.md#troubleshooting](DEPLOYMENT.md)

## 📚 Dokümantasyon

- 🚀 [Hızlı Başlangıç](QUICKSTART.md) - 5 dakikada deploy
- 📖 [Deployment Kılavuzu](DEPLOYMENT.md) - Detaylı adımlar
- 📝 [Ana README](README.md) - Genel bilgiler
- 🌐 [Frappe Docs](https://frappeframework.com/docs) - Framework dokümantasyonu
- 📘 [ERPNext Docs](https://docs.erpnext.com) - Uygulama dokümantasyonu

## 🎯 Kullanım Senaryoları

### 1. Küçük İşletme
```
✓ Muhasebe ve Finans (ERPNext)
✓ Müşteri Yönetimi (CRM)
✓ Web Sitesi (Builder)
✓ Bilgi Tabanı (Wiki)
```

### 2. E-Ticaret
```
✓ Ürün/Stok Yönetimi (ERPNext)
✓ Kargo Entegrasyonu (Shipping)
✓ Ödeme İşlemleri (Payments)
✓ Müşteri İletişimi (CRM + Twilio)
```

### 3. Eğitim Kurumu
```
✓ Online Kurslar (LMS)
✓ Öğrenci Yönetimi (ERPNext)
✓ Dökümanlar (Wiki)
✓ Web Sitesi (Builder)
```

### 4. Hizmet Şirketi
```
✓ Proje Yönetimi (ERPNext)
✓ CRM (Müşteri Takibi)
✓ Faturalandırma (ERPNext)
✓ SMS Bildirimleri (Twilio)
```

## 🔄 Versiyon Bilgisi

- **Frappe Framework**: v15
- **ERPNext**: v15
- **Python**: 3.11.6
- **Node.js**: 20.19.2
- **MariaDB**: 10.6
- **Redis**: 7
- **Nginx**: Latest (Debian Bookworm)

## 🤝 Destek

### Community Support
- 💬 [Frappe Forum](https://discuss.frappe.io)
- 💭 [GitHub Discussions](https://github.com/ubden/frappe_docker/discussions)

### Issues & Bugs
- 🐛 [GitHub Issues](https://github.com/ubden/frappe_docker/issues)

### Commercial Support
- 📧 [Frappe Cloud](https://frappecloud.com) - Managed hosting
- 🏢 [Frappe Technologies](https://frappe.io/support) - Enterprise support

## 📄 Lisans

Bu proje ve içerdiği uygulamalar çeşitli açık kaynak lisansları altında sunulmaktadır:

- **Frappe Framework**: MIT License
- **ERPNext**: GNU GPLv3
- **Diğer Uygulamalar**: İlgili repository'lerindeki lisanslar

Detaylar için: [LICENSE](../LICENSE)

## 🙏 Teşekkürler

Bu proje şu harika açık kaynak projelere dayanmaktadır:

- [Frappe](https://github.com/frappe/frappe)
- [ERPNext](https://github.com/frappe/erpnext)
- [Frappe Docker](https://github.com/frappe/frappe_docker)
- [Dokploy](https://dokploy.com)

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0  
**Maintainer**: [@ubden](https://github.com/ubden)

