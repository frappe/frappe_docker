# Frappe ERPNext - Dokploy için Hazır Kurulum

Bu klasör, Frappe ERPNext'i tüm popüler uygulamalarıyla birlikte Dokploy'da kolayca deploy etmek için hazırlanmıştır.

## İçerilen Uygulamalar

1. **ERPNext** - Tam özellikli ERP sistemi (built-in CRM dahil)
2. **HRMS** - İnsan Kaynakları Yönetim Sistemi  
3. **CRM** - Müşteri İlişkileri Yönetimi ([v1.53.1](https://github.com/frappe/crm/releases/tag/v1.53.1))
4. **Helpdesk** - Müşteri Destek ve Ticket Sistemi
5. **LMS** - Öğrenme Yönetim Sistemi (E-Learning)
6. **Builder** - Web sitesi oluşturucu
7. **Print Designer** - Yazdırma şablonu tasarımcısı
8. **Payments** - Ödeme gateway entegrasyonları
9. **Wiki** - Bilgi tabanı sistemi

**Not**: Tüm uygulamalar Frappe v15 ile test edilmiş ve uyumludur. İlk deployment'ta hata alırsanız clean build yapın (Dokploy'da service'i silip yeniden oluşturun).

## Dokploy'da Kurulum

### Yöntem 1: GitHub'dan Direkt Deploy (Önerilen)

1. Dokploy dashboard'unuza giriş yapın
2. "New Project" veya "New Service" butonuna tıklayın
3. "Docker Compose" seçeneğini seçin
4. Repository URL olarak GitHub fork'unuzu girin: `https://github.com/ubden/frappe_docker`
5. Branch: `main`
6. Docker Compose Path: `dokploy/docker-compose.yml`
7. Environment variables'ı ekleyin (`.env.example` dosyasına bakın)
8. Deploy butonuna tıklayın

**💡 İpucu**: Tüm environment variables listesi ve detaylı açıklamaları için:
- `.env.example` dosyasına bakın (örneklerle birlikte)
- `ENV_VARIABLES.md` dosyasında detaylı açıklamalar bulunur

### Yöntem 2: Manuel Kurulum

1. Repository'yi klonlayın:
   ```bash
   git clone https://github.com/ubden/frappe_docker.git
   cd frappe_docker/dokploy
   ```

2. `.env.example` dosyasını `.env` olarak kopyalayın:
   ```bash
   cp .env.example .env
   ```

3. `.env` dosyasını düzenleyin:
   ```bash
   nano .env
   ```
   
   Aşağıdaki zorunlu değerleri güncelleyin:
   - `SITE_NAME`: Domain adınız (örn: erp.yourdomain.com)
   - `ADMIN_PASSWORD`: Güçlü bir şifre
   - `DB_PASSWORD`: Güçlü bir database şifresi

4. Docker Compose ile başlatın:
   ```bash
   docker-compose up -d
   ```

**📚 Detaylı Bilgi**: `.env.example` dosyasındaki tüm ayarların açıklamaları ve örnekleri için `ENV_VARIABLES.md` dosyasına bakın.

## Environment Variables

### Hızlı Başlangıç (Minimum Ayarlar)

Dokploy'da aşağıdaki zorunlu environment variables'ları ayarlayın:

```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=YourSecure@Pass123!
DB_PASSWORD=YourDB@Pass456!
```

### Tüm Ayarlar

`.env.example` dosyasında **50+ environment variable** ve detaylı açıklamaları bulunur:

- ✅ **Zorunlu Ayarlar**: Site name, passwords
- 🌐 **Network Ayarları**: Ports, timeouts
- 🔧 **Frappe Ayarları**: Site resolution, real IP
- 📦 **Docker Ayarları**: Image, tags, pull policy
- 💾 **Database Ayarları**: MariaDB configuration
- 🔴 **Redis Ayarları**: Cache & Queue
- 🚀 **Performance Ayarları**: Timeouts, limits
- 🔐 **Güvenlik Ayarları**: SSL, secrets

**📖 Detaylı Dokümantasyon**: 
- Tüm değişkenler: `.env.example`
- Açıklamalar ve örnekler: `ENV_VARIABLES.md`
- Konfigürasyon örnekleri: Development, Staging, Production

### Örnek Konfigürasyonlar

#### Development
```env
SITE_NAME=dev.localhost
HTTP_PORT=8080
PULL_POLICY=build
DEVELOPER_MODE=1
```

#### Production
```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=Prod@SecurePass789!
DB_PASSWORD=Prod@DBSecure012!
PROXY_READ_TIMEOUT=300
CLIENT_MAX_BODY_SIZE=100m
PULL_POLICY=always
RESTART_POLICY=unless-stopped
```

Daha fazla örnek için `.env.example` dosyasına bakın.

## İlk Kurulumdan Sonra

1. Site'a erişim için domain adınızı Dokploy'da yapılandırın
2. İlk giriş bilgileri:
   - **Kullanıcı Adı**: `Administrator`
   - **Şifre**: `.env` dosyasında belirlediğiniz `ADMIN_PASSWORD`

3. Tüm uygulamalar otomatik olarak kurulur ve kullanıma hazırdır

## Önemli Notlar

### Volumes (Veri Saklama)

Aşağıdaki volumes sistem tarafından oluşturulur ve verilerinizi saklar:
- `mariadb-data`: Veritabanı verileri
- `redis-cache-data`: Redis cache verileri
- `redis-queue-data`: Redis queue verileri
- `sites`: Frappe site dosyaları
- `logs`: Uygulama logları

### Performans Ayarları

MariaDB için optimize edilmiş ayarlar:
- Max connections: 500
- InnoDB buffer pool: 2GB
- InnoDB log file: 512MB

Gerekirse `docker-compose.yml` dosyasındaki bu değerleri sunucu kapasitesine göre ayarlayabilirsiniz.

### Backup

Site verilerinizi yedeklemek için:

```bash
# Container'a bağlanın
docker exec -it <backend-container-name> bash

# Backup oluşturun
bench --site <site-name> backup --with-files

# Backup dosyaları şu dizinde bulunur:
# /home/frappe/frappe-bench/sites/<site-name>/private/backups/
```

### Güncelleme

Uygulamaları güncellemek için:

```bash
# Container'a bağlanın
docker exec -it <backend-container-name> bash

# Uygulamaları güncelleyin
bench --site <site-name> migrate

# Frontend assets'leri derleyin
bench build
```

## Sorun Giderme

### Site açılmıyor
- Browser cache'i temizleyin
- Backend container loglarını kontrol edin: `docker logs <container-name>`
- Database bağlantısını kontrol edin

### Yavaş çalışıyor
- MariaDB buffer pool ayarlarını artırın
- Worker sayısını artırın (docker-compose.yml'de gunicorn workers)
- Redis memory limit'i kontrol edin

### Kurulum başarısız
- Database şifresinin doğru olduğundan emin olun
- Container'ların healthy olup olmadığını kontrol edin: `docker ps`
- Configurator container loglarını inceleyin

## Destek ve Dokümantasyon

- [Frappe Docs](https://frappeframework.com/docs)
- [ERPNext Docs](https://docs.erpnext.com)
- [Frappe Docker GitHub](https://github.com/frappe/frappe_docker)

## Lisans

Bu proje Frappe ERPNext'in lisans koşullarına tabidir.

