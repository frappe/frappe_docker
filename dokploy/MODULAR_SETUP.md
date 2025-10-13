# Modüler Yapı Kılavuzu

Bu doküman, Frappe ERPNext Dokploy deployment'ının modüler yapısını ve environment variable yönetimini açıklar.

## 🎯 Modüler Yapının Avantajları

1. **Esneklik**: Her environment için farklı konfigürasyon
2. **Güvenlik**: Hassas bilgiler .env dosyasında, Git'te değil
3. **Tekrar Kullanılabilirlik**: Aynı setup, farklı ayarlar
4. **Versiyonlama**: .env.example Git'te, gerçek .env dışında
5. **Dokümantasyon**: Her değişken açıklamalı
6. **Bakım Kolaylığı**: Merkezi konfigürasyon yönetimi

## 📁 Dosya Yapısı

```
dokploy/
├── .env.example              # Tüm değişkenler + açıklamalar + örnekler
├── .env                      # Gerçek ayarlar (Git'e commit edilmez!)
├── docker-compose.yml        # Ana deployment (environment variables kullanır)
├── docker-compose.prod.yml   # Production optimized (environment variables kullanır)
├── Dockerfile               # Image definition
├── ENV_VARIABLES.md         # Detaylı değişken dokümantasyonu
└── MODULAR_SETUP.md         # Bu dosya
```

## 🔄 Environment Variable Akışı

```
┌──────────────────┐
│  .env.example    │  Template (Git'te)
│  (Template)      │  - Tüm değişkenler
└────────┬─────────┘  - Varsayılan değerler
         │            - Açıklamalar
         │ Kopyala    - Örnekler
         ▼
┌──────────────────┐
│      .env        │  Gerçek Konfigürasyon (Git'te DEĞİL!)
│  (Actual Config) │  - Özelleştirilmiş değerler
└────────┬─────────┘  - Production şifreleri
         │            - Gerçek domain'ler
         │ Okunur
         ▼
┌──────────────────┐
│ docker-compose   │  Deployment
│     .yml         │  - ${VARIABLE:-default} formatı
└────────┬─────────┘  - Fallback değerler
         │            - Tüm servisler
         │ Deploy
         ▼
┌──────────────────┐
│   Containers     │  Çalışan Sistem
│    (Running)     │  - Konfigüre edilmiş
└──────────────────┘  - Production ready
```

## 🛠️ Kurulum Adımları

### 1. Template'i Kopyalama

```bash
# Dokploy klasörüne gidin
cd dokploy

# .env.example'ı .env olarak kopyalayın
cp .env.example .env
```

### 2. Konfigürasyon Düzenleme

```bash
# .env dosyasını açın
nano .env

# Veya
vim .env

# Veya favorite editörünüz
code .env
```

### 3. Zorunlu Değerleri Güncelleme

Minimum olarak şunları değiştirin:

```env
# Site bilgisi
SITE_NAME=erp.yourdomain.com

# Güçlü şifreler (ÖNEMLİ!)
ADMIN_PASSWORD=YourSecurePassword123!
DB_PASSWORD=YourDatabasePassword456!
```

### 4. İsteğe Bağlı Optimizasyonlar

İhtiyaca göre şunları da ayarlayın:

```env
# Performance
PROXY_READ_TIMEOUT=300
CLIENT_MAX_BODY_SIZE=100m

# Deployment stratejisi
PULL_POLICY=always
RESTART_POLICY=unless-stopped

# Versions
MARIADB_VERSION=10.6
REDIS_VERSION=7
```

### 5. Deployment

```bash
# Docker Compose ile deploy
docker-compose up -d

# Veya production config ile
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Environment Variable Kategorileri

### 1. Zorunlu Değişkenler
```env
SITE_NAME=           # Site domain
ADMIN_PASSWORD=      # Admin şifresi
DB_PASSWORD=         # DB şifresi
```

### 2. Network & Port
```env
HTTP_PORT=80
UPSTREAM_REAL_IP_ADDRESS=127.0.0.1
UPSTREAM_REAL_IP_HEADER=X-Forwarded-For
```

### 3. Frappe Framework
```env
FRAPPE_SITE_NAME_HEADER=$$host
FRAPPE_BRANCH=version-15
```

### 4. Nginx
```env
PROXY_READ_TIMEOUT=120
CLIENT_MAX_BODY_SIZE=50m
```

### 5. Docker
```env
CUSTOM_IMAGE=erpnext-complete
CUSTOM_TAG=latest
PULL_POLICY=build
RESTART_POLICY=unless-stopped
```

### 6. Database
```env
DB_HOST=mariadb
DB_PORT=3306
MARIADB_VERSION=10.6
```

### 7. Redis
```env
REDIS_CACHE=redis-cache:6379
REDIS_QUEUE=redis-queue:6379
REDIS_VERSION=7
```

## 🔐 Güvenlik Best Practices

### .env Dosyası Yönetimi

1. **Asla Git'e Commit Etmeyin**
   ```bash
   # .gitignore kontrol
   cat .gitignore | grep .env
   
   # Output: .env (olmalı!)
   ```

2. **Güvenli Depolama**
   - Password manager kullanın
   - Encrypted backup alın
   - Team'le güvenli paylaşın (1Password, LastPass vb.)

3. **Şifre Güvenliği**
   ```bash
   # Güçlü şifre oluşturma
   openssl rand -base64 32
   
   # Veya
   pwgen -s 20 1
   ```

### Environment Separation

**Development (.env.dev)**
```env
SITE_NAME=dev.localhost
ADMIN_PASSWORD=DevPassword123
PULL_POLICY=build
DEVELOPER_MODE=1
```

**Staging (.env.staging)**
```env
SITE_NAME=staging.yourdomain.com
ADMIN_PASSWORD=StagingSecure456!
PULL_POLICY=always
CUSTOM_TAG=develop
```

**Production (.env.prod)**
```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=ProdVerySecure789!
PULL_POLICY=always
CUSTOM_TAG=v1.0.0
RESTART_POLICY=unless-stopped
```

## 🔄 Değişken Güncellemeleri

### Değişiklik Yapma

```bash
# 1. .env dosyasını düzenleyin
nano .env

# 2. Değişiklikleri uygulayın
docker-compose down
docker-compose up -d

# Veya sadece yeniden başlatma
docker-compose restart
```

### Runtime'da Değişiklik

Bazı değişiklikler container yeniden oluşturma gerektirir:

```bash
# Image değişikliği
docker-compose up -d --build

# Volume değişikliği  
docker-compose down -v
docker-compose up -d

# Tüm yeniden oluşturma
docker-compose up -d --force-recreate
```

## 📝 Dokümantasyon

### Değişken Ekleme

Yeni bir environment variable eklerken:

1. **.env.example'a ekleyin**
   ```env
   # Yeni Özellik
   # Açıklama: Ne işe yarar
   # Varsayılan: default_value
   # Örnek: example_value
   NEW_VARIABLE=default_value
   ```

2. **docker-compose.yml'e ekleyin**
   ```yaml
   environment:
     NEW_VARIABLE: ${NEW_VARIABLE:-default_value}
   ```

3. **ENV_VARIABLES.md'yi güncelleyin**
   - Detaylı açıklama
   - Kullanım örnekleri
   - Best practices

4. **CHANGELOG.md'ye not düşün**
   - Yeni özellik olarak işaretleyin
   - Migration notları ekleyin

## 🎯 Kullanım Senaryoları

### Senaryo 1: Multi-Environment Setup

```bash
# Development
cp .env.example .env.dev
nano .env.dev
docker-compose --env-file .env.dev up -d

# Production
cp .env.example .env.prod
nano .env.prod
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

### Senaryo 2: Team Collaboration

```bash
# Her developer kendi .env'ini oluşturur
cp .env.example .env.local
nano .env.local

# Ortak ayarlar .env.example'da
git add .env.example
git commit -m "Update environment template"
```

### Senaryo 3: CI/CD Integration

```yaml
# .github/workflows/deploy.yml
- name: Create .env
  run: |
    echo "SITE_NAME=${{ secrets.SITE_NAME }}" >> .env
    echo "ADMIN_PASSWORD=${{ secrets.ADMIN_PASSWORD }}" >> .env
    echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}" >> .env
    
- name: Deploy
  run: docker-compose up -d
```

### Senaryo 4: Dokploy Deployment

Dokploy UI'da environment variables:
- `.env.example` dosyasından kopyalayın
- Her değeri Dokploy'a yapıştırın
- Secret olanları "Secret" olarak işaretleyin

## 🔍 Troubleshooting

### Variable Tanınmıyor

```bash
# .env dosyası var mı?
ls -la .env

# Doğru formatta mı?
cat .env | grep SITE_NAME

# Docker Compose'a belirtin
docker-compose --env-file .env config
```

### Değişiklikler Uygulanmıyor

```bash
# Container'ları yeniden oluşturun
docker-compose up -d --force-recreate

# Image'i yeniden build edin
docker-compose build --no-cache

# Volume'ları temizleyin (DİKKAT: Veri kaybı!)
docker-compose down -v
```

### Özel Karakter Sorunları

```bash
# Tırnak kullanın
ADMIN_PASSWORD="MyPass@123!"

# Veya escape edin
ADMIN_PASSWORD=MyPass\@123\!
```

## 📚 İlgili Dokümantasyon

- `.env.example` - Tüm değişkenler ve örnekler
- `ENV_VARIABLES.md` - Detaylı değişken açıklamaları
- `DEPLOYMENT.md` - Deployment kılavuzu
- `QUICKSTART.md` - Hızlı başlangıç
- `docker-compose.yml` - Servis tanımları

## 🎓 Best Practices Özeti

✅ **DO (YAPIN)**
- `.env.example` kullanın template olarak
- Güçlü şifreler kullanın
- Her environment için ayrı .env
- Hassas bilgileri şifreleyin
- Dokümantasyonu güncel tutun
- Versiyonları pin'leyin (production)

❌ **DON'T (YAPMAYIN)**
- .env'i Git'e commit etmeyin
- Weak passwords kullanmayın
- Production'da default değerler bırakmayın
- .env dosyasını paylaşmayın (şifresiz)
- Dokümantasyonu skip etmeyin
- Test etmeden deploy etmeyin

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0

