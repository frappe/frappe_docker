# Dokploy Klasörü - Dosya Açıklamaları

Bu dokümanda `dokploy/` klasöründeki tüm dosyalar ve amaçları açıklanmaktadır.

## 📋 Dosya Listesi

### Konfigürasyon Dosyaları

#### `apps.json`
**Amaç**: Frappe bench'e kurulacak uygulamaların listesi
**İçerik**: 
- ERPNext, CRM, LMS, Builder, Print Designer, Payments, Wiki, Twilio Integration, ERPNext Shipping
- Her uygulama için GitHub URL ve branch bilgisi
**Kullanım**: Dockerfile build sırasında uygulamaları yüklemek için kullanılır

#### `Dockerfile`
**Amaç**: Özel ERPNext image'i oluşturmak
**Özellikler**:
- Tüm uygulamaları içeren single image
- Multi-stage build (base, build, builder, final)
- Production-optimized
- Health check desteği
**Build Komutu**: `docker build -f dokploy/Dockerfile -t erpnext-complete .`

#### `docker-compose.yml`
**Amaç**: Development ve test deployment için
**Servisler**:
- MariaDB, Redis (cache + queue)
- Frontend (Nginx), Backend (Gunicorn)
- WebSocket, Workers, Scheduler
- Configurator, Create-site (one-time)
**Kullanım**: `docker-compose -f dokploy/docker-compose.yml up -d`

#### `docker-compose.prod.yml`
**Amaç**: Production deployment için optimize edilmiş versiyon
**Farklar**:
- Pre-built image kullanır (GitHub Container Registry)
- Resource limits tanımlı
- Performans optimizasyonları
- Horizontal scaling desteği
**Kullanım**: Production environment'larda

#### `.env`
**Amaç**: Environment variables (Git'e commit edilmemeli)
**İçerik**:
- SITE_NAME, ADMIN_PASSWORD, DB_PASSWORD
- Port, timeout, size limitleri
- Redis ve database ayarları
**Not**: Bu dosya .gitignore'da, sadece örnek olarak oluşturuldu

#### `dokploy.json`
**Amaç**: Dokploy platform metadata
**İçerik**:
- Proje açıklaması
- Environment variable tanımları
- Port mapping bilgileri
- Volume tanımları
- Health check ayarları
**Kullanım**: Dokploy UI'da otomatik form oluşturmak için

### Dokümantasyon Dosyaları

#### `README.md`
**Amaç**: Ana dokümantasyon
**İçerik**:
- Genel bilgi ve özellikler
- Kurulum yöntemleri
- Konfigürasyon açıklamaları
- Sorun giderme
**Hedef Kitle**: Tüm kullanıcılar

#### `QUICKSTART.md`
**Amaç**: Hızlı başlangıç kılavuzu (5 dakika)
**İçerik**:
- Adım adım Dokploy deployment
- Minimum konfigürasyon
- İlk giriş bilgileri
- Temel troubleshooting
**Hedef Kitle**: Yeni kullanıcılar, hızlı deploy isteyenler

#### `DEPLOYMENT.md`
**Amaç**: Detaylı deployment ve maintenance kılavuzu
**İçerik**:
- Tüm deployment yöntemleri (UI, CLI, Manuel)
- İlk yapılandırma adımları
- Güncelleme prosedürleri
- Backup/restore işlemleri
- Performans optimizasyonu
- Güvenlik best practices
- Kapsamlı troubleshooting
**Hedef Kitle**: System adminler, DevOps

#### `SUMMARY.md`
**Amaç**: Paket özeti ve hızlı referans
**İçerik**:
- Uygulama listesi
- Mimari diyagram
- Servis açıklamaları
- Konfigürasyon referansı
- Sistem gereksinimleri
- Kullanım senaryoları
**Hedef Kitle**: Karar vericiler, teknik liderler

#### `CHANGELOG.md`
**Amaç**: Versiyon geçmişi ve değişiklikler
**İçerik**:
- Versiyon notları
- Yeni özellikler
- Bug fix'ler
- Breaking changes
- Migration notları
**Format**: Keep a Changelog standardı
**Güncelleme**: Her release'de

#### `CHECKLIST.md`
**Amaç**: Deployment öncesi/sonrası kontrol listesi
**İçerik**:
- Pre-deployment kontroller
- Deployment adımları
- Post-deployment doğrulamalar
- Production checklist
- Maintenance planı
**Kullanım**: Her deployment için checkbox'ları işaretleyin

#### `FILES.md`
**Amaç**: Bu dosya - dosya yapısı dokümantasyonu
**İçerik**:
- Tüm dosyaların açıklamaları
- Kullanım amaçları
- İlişkiler ve dependencies
**Hedef Kitle**: Geliştiriciler, contributors

### Script Dosyaları

#### `install.sh`
**Amaç**: Otomatik kurulum scripti (Linux/Mac)
**Fonksiyonlar**:
- Gereksinim kontrolü (Docker, Docker Compose)
- .env dosyası oluşturma
- Image build
- Container başlatma
- Kurulum durumu takibi
**Kullanım**: `chmod +x install.sh && ./install.sh`
**Not**: Windows'da WSL veya Git Bash gerekir

### Yardımcı Dosyalar

#### `.dockerignore`
**Amaç**: Docker build'den hariç tutulacak dosyalar
**İçerik**:
- Git dosyaları
- Documentation
- Tests
- IDE ayarları
- Log dosyaları
**Fayda**: Build süresini kısaltır, image boyutunu küçültür

#### `.gitignore`
**Amaç**: Git'e commit edilmeyecek dosyalar
**İçerik**:
- .env dosyası (şifreler!)
- Log dosyaları
- Temporary dosyalar
- OS-specific dosyalar
- Backup dosyaları
**Önemli**: .env asla commit edilmemeli!

## 📊 Dosya İlişkileri

```
Dockerfile
    ├─> apps.json (build sırasında uygulamaları yükler)
    └─> resources/nginx-* (base image'e kopyalar)

docker-compose.yml
    ├─> Dockerfile (build eder veya registry'den çeker)
    ├─> .env (environment variables)
    └─> volumes (veri persistence)

docker-compose.prod.yml
    ├─> Pre-built image (GHCR)
    └─> .env (production ayarları)

README.md
    ├─> QUICKSTART.md (referans)
    ├─> DEPLOYMENT.md (referans)
    └─> SUMMARY.md (referans)

dokploy.json
    └─> docker-compose.yml (deployment tanımı)
```

## 🔄 Kullanım Akışı

### Development/Test
```
1. apps.json → Uygulamaları tanımla
2. Dockerfile → Image build et
3. docker-compose.yml → Container'ları başlat
4. .env → Konfigüre et
5. install.sh → Otomatik kur (opsiyonel)
```

### Production (Dokploy)
```
1. dokploy.json → Dokploy'a metadata ver
2. docker-compose.yml veya .prod.yml → Deploy tanımı
3. .env → Production ayarları
4. DEPLOYMENT.md → Adımları takip et
5. CHECKLIST.md → Kontrolleri yap
```

### Dokümantasyon Okuma Sırası
```
Yeni Kullanıcı:
1. README.md → Genel bakış
2. QUICKSTART.md → Hemen başla
3. DEPLOYMENT.md → Detaylı bilgi (gerekirse)

Admin/DevOps:
1. SUMMARY.md → Teknik özet
2. DEPLOYMENT.md → Full kılavuz
3. CHECKLIST.md → Kontrol listesi
4. CHANGELOG.md → Versiyon notları

Developer:
1. FILES.md → Bu dosya
2. Dockerfile → Image yapısı
3. docker-compose.yml → Servis yapısı
4. apps.json → Uygulama listesi
```

## 📏 Dosya Boyutları (Tahmini)

| Dosya | Boyut | Tip |
|-------|-------|-----|
| `apps.json` | ~500 bytes | JSON |
| `Dockerfile` | ~5 KB | Docker |
| `docker-compose.yml` | ~8 KB | YAML |
| `docker-compose.prod.yml` | ~10 KB | YAML |
| `.env` | ~1 KB | Config |
| `dokploy.json` | ~3 KB | JSON |
| `install.sh` | ~5 KB | Shell |
| `README.md` | ~15 KB | Markdown |
| `QUICKSTART.md` | ~20 KB | Markdown |
| `DEPLOYMENT.md` | ~30 KB | Markdown |
| `SUMMARY.md` | ~25 KB | Markdown |
| `CHANGELOG.md` | ~8 KB | Markdown |
| `CHECKLIST.md` | ~15 KB | Markdown |
| `FILES.md` | ~8 KB | Markdown |
| `.dockerignore` | ~500 bytes | Text |
| `.gitignore` | ~400 bytes | Text |
| **TOPLAM** | **~154 KB** | - |

## 🎯 Önemli Notlar

### Güvenlik
- ⚠️ `.env` dosyası asla Git'e commit edilmemeli
- ⚠️ Şifreler mutlaka değiştirilmeli (default'lar güvensiz)
- ⚠️ Production'da güçlü şifreler kullanılmalı

### Bakım
- 📝 `CHANGELOG.md` her release'de güncellenmeli
- 📝 Documentation değişikliklerde sync tutulmalı
- 📝 Version numaraları consistent olmalı

### Katkı
- Yeni dosya eklendiğinde bu listeye eklenmeli
- Major değişiklikler CHANGELOG'a yazılmalı
- Documentation güncel tutulmalı

## 🔗 İlgili Kaynaklar

- Parent repository: [frappe/frappe_docker](https://github.com/frappe/frappe_docker)
- Fork: [ubden/frappe_docker](https://github.com/ubden/frappe_docker)
- Dokploy: [dokploy.com](https://dokploy.com)
- Frappe: [frappeframework.com](https://frappeframework.com)
- ERPNext: [erpnext.com](https://erpnext.com)

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0  
**Maintainer**: [@ubden](https://github.com/ubden)
