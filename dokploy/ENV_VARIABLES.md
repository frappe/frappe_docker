# Environment Variables Kılavuzu

Bu doküman, Frappe ERPNext Dokploy deployment'ında kullanılan tüm environment variable'ları detaylı olarak açıklar.

## 📋 İçindekiler

1. [Zorunlu Değişkenler](#zorunlu-değişkenler)
2. [Network ve Port Ayarları](#network-ve-port-ayarları)
3. [Frappe Framework Ayarları](#frappe-framework-ayarları)
4. [Nginx Ayarları](#nginx-ayarları)
5. [Docker Image Ayarları](#docker-image-ayarları)
6. [Database Ayarları](#database-ayarları)
7. [Redis Ayarları](#redis-ayarları)
8. [İsteğe Bağlı Ayarlar](#isteğe-bağlı-ayarlar)
9. [Gelişmiş Ayarlar](#gelişmiş-ayarlar)
10. [Harici Servisler](#harici-servisler)
11. [Örnek Konfigürasyonlar](#örnek-konfigürasyonlar)

## Zorunlu Değişkenler

### `SITE_NAME`
- **Açıklama**: Frappe site'ın domain adı veya hostname'i
- **Varsayılan**: `site1.localhost`
- **Örnekler**: 
  - `erp.yourdomain.com` (production)
  - `site1.localhost` (development)
  - `192.168.1.100` (IP tabanlı)
- **Notlar**: 
  - Production'da gerçek domain kullanın
  - DNS kaydı bu domain'i sunucunuza yönlendirmeli
  - Subdomain kullanabilirsiniz

### `ADMIN_PASSWORD`
- **Açıklama**: Administrator kullanıcısının şifresi
- **Varsayılan**: `admin` (GÜVENSİZ!)
- **Gereksinimler**: 
  - Minimum 12 karakter
  - En az bir büyük harf
  - En az bir küçük harf
  - En az bir sayı
  - En az bir özel karakter
- **Örnekler**: `MySecure@Pass123!`
- **⚠️ ÖNEMLİ**: Production'da MUTLAKA değiştirin!

### `DB_PASSWORD`
- **Açıklama**: MariaDB root kullanıcı şifresi
- **Varsayılan**: `changeit` (GÜVENSİZ!)
- **Gereksinimler**: Admin password ile aynı
- **Örnekler**: `DB@Secure456!`
- **⚠️ ÖNEMLİ**: 
  - Production'da MUTLAKA değiştirin!
  - Admin şifresinden farklı kullanın
  - Asla paylaşmayın

## Network ve Port Ayarları

### `HTTP_PORT`
- **Açıklama**: Frontend Nginx servisinin publish edilecği port
- **Varsayılan**: `80`
- **Örnekler**: 
  - `80` (production HTTP)
  - `8080` (development/test)
  - `443` (HTTPS - Dokploy otomatik halleder)
- **Notlar**: 
  - Dokploy genelde otomatik port atar
  - Local test için 8080 kullanabilirsiniz
  - Production'da 80 veya 443 kullanın

## Frappe Framework Ayarları

### `FRAPPE_SITE_NAME_HEADER`
- **Açıklama**: HTTP header'dan site çözümlemesi
- **Varsayılan**: `$$host`
- **Seçenekler**:
  - `$$host`: Domain'den otomatik (önerilen)
  - `mysite`: Sabit site adı
- **Kullanım**: 
  - Multi-site setup'larda domain'e göre site seçimi
  - Single-site'da `$$host` kullanın

### `UPSTREAM_REAL_IP_ADDRESS`
- **Açıklama**: Güvenilir upstream proxy adresi
- **Varsayılan**: `127.0.0.1`
- **Örnekler**: 
  - `127.0.0.1` (local)
  - `10.0.0.0/8` (internal network)
- **Kullanım**: Reverse proxy arkasında çalışırken

### `UPSTREAM_REAL_IP_HEADER`
- **Açıklama**: Real IP için kullanılacak header
- **Varsayılan**: `X-Forwarded-For`
- **Seçenekler**: 
  - `X-Forwarded-For` (standart)
  - `X-Real-IP`
  - `CF-Connecting-IP` (Cloudflare)

### `UPSTREAM_REAL_IP_RECURSIVE`
- **Açıklama**: Recursive real IP search
- **Varsayılan**: `off`
- **Seçenekler**: `on`, `off`
- **Kullanım**: Multiple proxy chain varsa `on`

## Nginx Ayarları

### `PROXY_READ_TIMEOUT`
- **Açıklama**: Proxy okuma timeout süresi (saniye)
- **Varsayılan**: `120`
- **Önerilen**: 
  - Development: `120`
  - Production: `300`
  - Heavy operations: `600`
- **Kullanım**: 
  - Uzun süren raporlar
  - Büyük data export/import
  - Kompleks hesaplamalar

### `CLIENT_MAX_BODY_SIZE`
- **Açıklama**: Maximum upload dosya boyutu
- **Varsayılan**: `50m`
- **Örnekler**: 
  - `50m` (development)
  - `100m` (production)
  - `500m` (large file support)
- **Format**: Nginx size format (k, m, g)
- **Kullanım**: Büyük dosya upload'ları için

## Docker Image Ayarları

### `CUSTOM_IMAGE`
- **Açıklama**: Kullanılacak Docker image adı
- **Varsayılan**: `erpnext-complete`
- **Seçenekler**:
  - `erpnext-complete` (local build)
  - `ghcr.io/ubden/frappe_docker/erpnext-complete` (GitHub Registry)
- **Kullanım**: Production'da registry image kullanın

### `CUSTOM_TAG`
- **Açıklama**: Docker image tag'i
- **Varsayılan**: `latest`
- **Seçenekler**:
  - `latest`: En son stable
  - `develop`: Development branch
  - `v1.0.0`: Specific version
  - `main`: Main branch build
- **Notlar**: Production'da version tag kullanın

### `PULL_POLICY`
- **Açıklama**: Image pull stratejisi
- **Varsayılan**: `build`
- **Seçenekler**:
  - `build`: Local'de build et
  - `always`: Her zaman registry'den çek
  - `never`: Sadece local image
  - `missing`: Yoksa çek
- **Önerilen**: 
  - Development: `build`
  - Production: `always`

### `RESTART_POLICY`
- **Açıklama**: Container restart politikası
- **Varsayılan**: `unless-stopped`
- **Seçenekler**:
  - `unless-stopped`: Manuel durdurulmadıkça (önerilen)
  - `always`: Her zaman
  - `on-failure`: Sadece hata durumunda
  - `no`: Asla
- **Önerilen**: Production için `unless-stopped`

## Database Ayarları

### `DB_HOST`
- **Açıklama**: MariaDB host adresi
- **Varsayılan**: `mariadb` (docker-compose service name)
- **Örnekler**:
  - `mariadb` (internal)
  - `db.example.com` (external)
  - `192.168.1.50` (IP)
- **Notlar**: External DB kullanıyorsanız değiştirin

### `DB_PORT`
- **Açıklama**: MariaDB port
- **Varsayılan**: `3306`
- **Notlar**: Standart MariaDB/MySQL portu

### `MARIADB_VERSION`
- **Açıklama**: MariaDB image versiyonu
- **Varsayılan**: `10.6`
- **Seçenekler**: `10.6`, `10.11`, `11.0`
- **Önerilen**: Frappe ile test edilmiş versiyon

## Redis Ayarları

### `REDIS_CACHE`
- **Açıklama**: Redis cache connection string
- **Varsayılan**: `redis-cache:6379`
- **Format**: `host:port`
- **Örnekler**:
  - `redis-cache:6379` (internal)
  - `redis.example.com:6379` (external)
  - `redis://redis-cache:6379/0` (full URL)

### `REDIS_QUEUE`
- **Açıklama**: Redis queue connection string
- **Varsayılan**: `redis-queue:6379`
- **Format**: Aynı REDIS_CACHE ile
- **Notlar**: Cache ve queue için ayrı instance önerilir

### `REDIS_VERSION`
- **Açıklama**: Redis image versiyonu
- **Varsayılan**: `7`
- **Seçenekler**: `6`, `7`
- **Önerilen**: En son stable (7)

## İsteğe Bağlı Ayarlar

### `ERPNEXT_VERSION`
- **Açıklama**: ERPNext versiyonu (build için)
- **Varsayılan**: `version-15`
- **Örnekler**: `v15.82.1`, `version-15`, `develop`

### `FRAPPE_BRANCH`
- **Açıklama**: Frappe framework branch
- **Varsayılan**: `version-15`
- **Örnekler**: `version-15`, `develop`, `version-14`

### `PYTHON_VERSION`
- **Açıklama**: Python versiyonu
- **Varsayılan**: `3.11.6`
- **Önerilen**: Frappe requirements ile uyumlu

### `NODE_VERSION`
- **Açıklama**: Node.js versiyonu
- **Varsayılan**: `20.19.2`
- **Önerilen**: LTS versiyon

## Gelişmiş Ayarlar

### `SOCKETIO_PORT`
- **Açıklama**: Socket.IO internal port
- **Varsayılan**: `9000`
- **Notlar**: Genelde değiştirmeyin

### `DEVELOPER_MODE`
- **Açıklama**: Developer mode aktif/pasif
- **Varsayılan**: `0` (kapalı)
- **Seçenekler**: `0` (kapalı), `1` (açık)
- **⚠️ ÖNEMLİ**: Production'da MUTLAKA `0`

### `MAINTENANCE_MODE`
- **Açıklama**: Maintenance mode
- **Varsayılan**: `0` (kapalı)
- **Seçenekler**: `0` (kapalı), `1` (açık)
- **Kullanım**: Güncelleme sırasında

## Harici Servisler

### `DB_PASSWORD_SECRETS_FILE`
- **Açıklama**: Docker secrets dosya yolu
- **Format**: `/run/secrets/db_password`
- **Kullanım**: Docker secrets kullanıyorsanız

### External Database
```env
DB_HOST=external-db.example.com
DB_PORT=3306
DB_PASSWORD=ExternalDBPass123!
```

### External Redis
```env
REDIS_CACHE=external-redis.example.com:6379
REDIS_QUEUE=external-redis.example.com:6380
```

## Örnek Konfigürasyonlar

### Development Setup

```env
# .env (Development)
SITE_NAME=dev.localhost
ADMIN_PASSWORD=admin
DB_PASSWORD=dev123
HTTP_PORT=8080
PULL_POLICY=build
DEVELOPER_MODE=1
PROXY_READ_TIMEOUT=120
CLIENT_MAX_BODY_SIZE=50m
```

### Staging Setup

```env
# .env (Staging)
SITE_NAME=staging.yourdomain.com
ADMIN_PASSWORD=Staging@Pass123!
DB_PASSWORD=Staging@DB456!
HTTP_PORT=80
PROXY_READ_TIMEOUT=300
CLIENT_MAX_BODY_SIZE=100m
PULL_POLICY=always
CUSTOM_IMAGE=ghcr.io/ubden/frappe_docker/erpnext-complete
CUSTOM_TAG=develop
RESTART_POLICY=unless-stopped
```

### Production Setup

```env
# .env (Production)
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=Prod@VerySecurePass789!
DB_PASSWORD=Prod@DBVerySecure012!
HTTP_PORT=80
PROXY_READ_TIMEOUT=300
CLIENT_MAX_BODY_SIZE=100m
PULL_POLICY=always
RESTART_POLICY=unless-stopped
CUSTOM_IMAGE=ghcr.io/ubden/frappe_docker/erpnext-complete
CUSTOM_TAG=v1.0.0
DEVELOPER_MODE=0
MAINTENANCE_MODE=0
LETSENCRYPT_EMAIL=admin@yourdomain.com
```

### High-Performance Setup

```env
# .env (High-Performance)
SITE_NAME=erp.enterprise.com
ADMIN_PASSWORD=Enterprise@SecurePass999!
DB_PASSWORD=Enterprise@DBSecure999!
PROXY_READ_TIMEOUT=600
CLIENT_MAX_BODY_SIZE=500m
MARIADB_VERSION=10.11
REDIS_VERSION=7

# External services
DB_HOST=db-cluster.internal
REDIS_CACHE=redis-cluster.internal:6379
REDIS_QUEUE=redis-cluster.internal:6380
```

## Best Practices

### Güvenlik

1. **Güçlü Şifreler**
   - Minimum 12 karakter
   - Karakter çeşitliliği
   - Password manager kullanın

2. **Environment Separation**
   - Dev, staging, production için ayrı .env
   - Farklı şifreler kullanın

3. **Secret Management**
   - .env dosyasını Git'e commit etmeyin
   - Hassas bilgileri şifreleyin
   - Docker secrets kullanmayı düşünün

### Performance

1. **Timeout Ayarları**
   - İş yüküne göre ayarlayın
   - Monitoring ile optimize edin

2. **Resource Limits**
   - Upload limit'i gerçekçi belirleyin
   - Database connection sayısını ayarlayın

3. **Caching**
   - Redis memory'i optimize edin
   - Cache invalidation stratejisi

### Maintenance

1. **Version Pinning**
   - Production'da specific version kullanın
   - Güncellemeleri kontrollü yapın

2. **Backup**
   - .env dosyasını güvenli yerde saklayın
   - Disaster recovery planı

3. **Documentation**
   - Değişiklikleri dokümante edin
   - Team ile paylaşın

## Troubleshooting

### Variable Tanınmıyor
```bash
# .env dosyasının doğru yerde olduğundan emin olun
ls -la .env

# Docker Compose'a .env dosyasını belirtin
docker-compose --env-file .env up
```

### Değişiklikler Uygulanmıyor
```bash
# Container'ları yeniden başlatın
docker-compose down
docker-compose up -d

# Image'i yeniden build edin
docker-compose build --no-cache
```

### Şifre Çalışmıyor
```bash
# Özel karakterleri escape edin veya tırnak kullanın
ADMIN_PASSWORD='MyPass@123!'

# Veya
ADMIN_PASSWORD="MyPass@123!"
```

## Referanslar

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Nginx Configuration](http://nginx.org/en/docs/)
- [MariaDB Configuration](https://mariadb.com/kb/en/server-system-variables/)

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0

