# Dokploy Klasörü - İçerik İndeksi

Bu dosya, `dokploy/` klasöründeki tüm dosyaları kategorize eder ve hızlı erişim sağlar.

## 📚 Dosya İndeksi

### 🔧 Konfigürasyon Dosyaları

| Dosya | Açıklama | Kullanım |
|-------|----------|----------|
| `apps.json` | Kurulacak Frappe uygulamaları listesi | Dockerfile build |
| `Dockerfile` | Özel ERPNext image tanımı | Image build |
| `docker-compose.yml` | Development/test deployment | `docker-compose up -d` |
| `docker-compose.prod.yml` | Production-optimized deployment | Production deployment |
| `.env.example` | Environment variables template | `.env` oluşturmak için |
| `dokploy.json` | Dokploy platform metadata | Dokploy UI |
| `.dockerignore` | Docker build ignore listesi | Build optimization |
| `.gitignore` | Git ignore listesi | Repository güvenliği |

### 🚀 Otomasyon

| Dosya | Açıklama | Çalıştırma |
|-------|----------|------------|
| `install.sh` | Otomatik kurulum scripti | `chmod +x install.sh && ./install.sh` |

### 📖 Dokümantasyon - Kullanıcı Kılavuzları

| Dosya | İçerik | Hedef Kitle | Sayfa |
|-------|--------|-------------|-------|
| `README.md` | Ana dokümantasyon | Tüm kullanıcılar | 15+ |
| `QUICKSTART.md` | 5 dakikada deployment | Yeni kullanıcılar | 20+ |
| `DEPLOYMENT.md` | Detaylı deployment ve maintenance | System adminler | 30+ |
| `CHECKLIST.md` | Deployment kontrol listesi | DevOps | 15+ |

### 📖 Dokümantasyon - Teknik Referans

| Dosya | İçerik | Hedef Kitle | Sayfa |
|-------|--------|-------------|-------|
| `SUMMARY.md` | Teknik özet ve mimari | Teknik liderler | 25+ |
| `ENV_VARIABLES.md` | Environment variables detayları | Tüm kullanıcılar | 30+ |
| `MODULAR_SETUP.md` | Modüler yapı kılavuzu | Geliştiriciler | 20+ |
| `FILES.md` | Dosya yapısı açıklamaları | Contributors | 15+ |
| `CHANGELOG.md` | Versiyon geçmişi | Herkes | 8+ |
| `INDEX.md` | Bu dosya - içerik indeksi | Herkes | 5+ |

## 🎯 Hangi Dosyayı Okumalıyım?

### Yeni Başlıyorum
```
1. README.md          → Genel bakış
2. QUICKSTART.md      → Hızlı deployment
3. CHECKLIST.md       → Öncesi/sonrası kontroller
```

### Production'a Deploy Edeceğim
```
1. DEPLOYMENT.md      → Full kılavuz
2. ENV_VARIABLES.md   → Ayarları anlama
3. CHECKLIST.md       → Production checklist
4. .env.example       → Konfigürasyon
```

### Development Yapacağım
```
1. MODULAR_SETUP.md   → Modüler yapı
2. ENV_VARIABLES.md   → Variables açıklamaları
3. FILES.md           → Dosya yapısı
4. docker-compose.yml → Servis tanımları
5. Dockerfile         → Image yapısı
```

### Sorun Giderme
```
1. DEPLOYMENT.md      → Troubleshooting bölümü
2. QUICKSTART.md      → Common issues
3. ENV_VARIABLES.md   → Variable sorunları
```

### Katkıda Bulunacağım
```
1. FILES.md           → Dosya yapısı
2. MODULAR_SETUP.md   → Modüler yaklaşım
3. CHANGELOG.md       → Version notları
4. docker-compose.yml → Servis yapısı
```

## 📊 Dosya Kategorileri ve İlişkiler

### Deployment Akışı
```
.env.example
    ↓ (kopyala)
.env
    ↓ (kullan)
docker-compose.yml
    ↓ (çalıştır)
    ├→ Dockerfile (build)
    └→ apps.json (install apps)
```

### Dokümantasyon Hiyerarşisi
```
INDEX.md (bu dosya)
    ├→ README.md (ana giriş)
    │   ├→ QUICKSTART.md (hızlı başlangıç)
    │   ├→ DEPLOYMENT.md (detaylı kılavuz)
    │   └→ CHECKLIST.md (kontrol listesi)
    │
    ├→ SUMMARY.md (teknik özet)
    │
    ├→ ENV_VARIABLES.md (variable referansı)
    │   └→ .env.example (template)
    │
    ├→ MODULAR_SETUP.md (modüler yapı)
    │
    ├→ FILES.md (dosya yapısı)
    │
    └→ CHANGELOG.md (versiyon notları)
```

## 🔍 Hızlı Arama

### Konuya Göre

#### Kurulum
- Hızlı: `QUICKSTART.md`
- Detaylı: `DEPLOYMENT.md`
- Otomatik: `install.sh`

#### Konfigürasyon
- Template: `.env.example`
- Açıklamalar: `ENV_VARIABLES.md`
- Örnekler: `MODULAR_SETUP.md`

#### Mimari
- Genel: `SUMMARY.md`
- Docker: `docker-compose.yml`, `Dockerfile`
- Uygulamalar: `apps.json`

#### Sorun Giderme
- Deployment: `DEPLOYMENT.md` → Troubleshooting
- Quick fixes: `QUICKSTART.md` → Troubleshooting
- Variables: `ENV_VARIABLES.md` → Troubleshooting

#### Güvenlik
- Best practices: `MODULAR_SETUP.md` → Security
- Checklist: `CHECKLIST.md` → Security
- Variables: `.env.example` → Production Checklist

#### Performance
- Optimizasyon: `SUMMARY.md` → Performance
- Settings: `ENV_VARIABLES.md` → Performance
- Production: `docker-compose.prod.yml`

## 📏 Dosya Boyutları

| Kategori | Dosya Sayısı | Toplam Boyut |
|----------|--------------|--------------|
| Konfigürasyon | 8 | ~50 KB |
| Dokümantasyon | 10 | ~180 KB |
| Otomasyon | 1 | ~5 KB |
| **TOPLAM** | **19** | **~235 KB** |

## 🎓 Okuma Önerileri

### Yeni Kullanıcılar İçin (Sırayla)
1. `INDEX.md` (bu dosya) - 5 dakika
2. `README.md` - 10 dakika
3. `QUICKSTART.md` - 15 dakika
4. `.env.example` düzenle - 10 dakika
5. Deploy! - 15 dakika
6. `CHECKLIST.md` kontrol - 10 dakika

**Toplam Süre**: ~1 saat (deployment dahil)

### Deneyimli Kullanıcılar İçin
1. `SUMMARY.md` - Teknik özet
2. `.env.example` - Konfigürasyon
3. `docker-compose.yml` - Servis yapısı
4. Deploy!

**Toplam Süre**: ~30 dakika

### DevOps Ekip İçin
1. `DEPLOYMENT.md` - Full kılavuz
2. `ENV_VARIABLES.md` - Variable referansı
3. `MODULAR_SETUP.md` - Modüler yapı
4. `CHECKLIST.md` - Production checklist

**Toplam Süre**: ~2 saat (production deployment dahil)

## 🔗 Harici Kaynaklar

### Frappe & ERPNext
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [ERPNext User Manual](https://docs.erpnext.com)
- [Frappe Forum](https://discuss.frappe.io)

### Docker
- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Dokploy
- [Dokploy Documentation](https://dokploy.com/docs)
- [Dokploy GitHub](https://github.com/dokploy/dokploy)

### Parent Repository
- [frappe/frappe_docker](https://github.com/frappe/frappe_docker)
- [Fork: ubden/frappe_docker](https://github.com/ubden/frappe_docker)

## 📝 Güncelleme Notları

Bu index dosyası her yeni dosya eklendiğinde veya major değişiklik olduğunda güncellenmektedir.

### Versiyon 1.0.0 (2025-10-13)
- ✅ İlk dokümantasyon seti tamamlandı
- ✅ 19 dosya oluşturuldu
- ✅ ~235 KB dokümantasyon
- ✅ Modüler yapı kuruldu
- ✅ .env.example ile konfigürasyon yönetimi

## 🎯 Sonraki Adımlar

Deployment için:
1. Bu index'i okudunuz ✅
2. `QUICKSTART.md` dosyasına gidin →
3. Deployment'ı başlatın! 🚀

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0  
**Maintainer**: [@ubden](https://github.com/ubden)

