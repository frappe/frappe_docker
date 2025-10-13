# Changelog

Frappe ERPNext Dokploy paketindeki tüm önemli değişiklikler bu dosyada belgelenecektir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardına dayanmaktadır.

## [1.0.0] - 2025-10-13

### Eklenen
- 🎉 İlk Dokploy-ready release
- ✨ 9 uygulama içeren tek image (ERPNext, CRM, LMS, Builder, Print Designer, Payments, Wiki, Twilio Integration, ERPNext Shipping)
- 🐳 Production-optimized Docker Compose konfigürasyonu
- 🐳 Development Docker Compose konfigürasyonu
- 📦 Özel Dockerfile tüm uygulamalarla
- 🔧 Otomatik site oluşturma ve uygulama kurulumu
- 📝 Kapsamlı dokümantasyon (README, QUICKSTART, DEPLOYMENT, SUMMARY)
- 🔐 Güvenlik best practices
- 💾 Volume yönetimi ve persistence
- ❤️ Health check'ler tüm servisler için
- 🚀 Otomatik kurulum scripti (install.sh)
- 🔄 GitHub Actions workflow (build-dokploy.yml)
- 📋 Dokploy metadata (dokploy.json)
- 🌐 Multi-platform support (amd64, arm64)

### Konfigürasyon
- Environment-based konfigürasyon (.env)
- Dokploy-friendly environment variables
- Güvenli secret yönetimi
- Esnek port konfigürasyonu

### Optimizasyonlar
- MariaDB performans ayarları
  - InnoDB buffer pool: 2-4GB
  - Max connections: 500-1000
  - Query cache disabled (InnoDB için)
- Gunicorn worker ayarları
  - 2-4 workers
  - 4-8 threads
  - Request timeout: 120-300s
- Redis memory limits
  - Cache: 2GB (LRU)
  - Queue: 1GB (No eviction)
- Nginx optimizasyonları
  - Proxy read timeout: 120-300s
  - Client max body size: 50-100m

### Servisler
- **frontend**: Nginx reverse proxy
- **backend**: Gunicorn WSGI server
- **websocket**: Socket.IO real-time server
- **mariadb**: MariaDB 10.6 database
- **redis-cache**: Redis cache layer
- **redis-queue**: Redis job queue
- **queue-short**: Short job workers
- **queue-long**: Long job workers
- **scheduler**: Cron scheduler
- **configurator**: Initial configuration (one-time)
- **create-site**: Site creation (one-time)

### Dokümantasyon
- `README.md`: Ana dokümantasyon
- `QUICKSTART.md`: 5 dakikada deploy kılavuzu
- `DEPLOYMENT.md`: Detaylı deployment ve maintenance kılavuzu
- `SUMMARY.md`: Paket özeti ve referans
- `CHANGELOG.md`: Bu dosya

### CI/CD
- GitHub Actions workflow
- Otomatik Docker image build
- Multi-platform build (amd64, arm64)
- GitHub Container Registry push
- Pull request test deployment

### Güvenlik
- Non-root container execution
- Secret-based password yönetimi
- HTTPS/SSL hazır altyapı
- 2FA desteği
- Güvenli default ayarlar

### Dokploy Entegrasyonu
- One-click deploy desteği
- Otomatik domain yapılandırması
- Built-in SSL/TLS (Let's Encrypt)
- Health check monitoring
- Log aggregation
- Resource limits

## [Gelecek Sürümler]

### Planlanıyor (v1.1.0)
- [ ] Otomatik backup cron job
- [ ] S3/MinIO backup entegrasyonu
- [ ] Email alert sistemi
- [ ] Prometheus metrics export
- [ ] Grafana dashboard template
- [ ] Multi-site support
- [ ] Database replication setup

### Değerlendiriliyor (v2.0.0)
- [ ] Kubernetes/Helm chart
- [ ] Horizontal scaling support
- [ ] Redis Cluster mode
- [ ] MariaDB Galera Cluster
- [ ] Advanced caching strategies
- [ ] CDN entegrasyonu
- [ ] Object storage entegrasyonu

## Bilinen Sorunlar

### v1.0.0
- İlk deployment 10-15 dakika sürebilir (tüm uygulamaların kurulması)
- Windows'da install.sh scripti çalışmaz (WSL kullanın)
- Çok büyük dosya upload'ları (>100MB) zaman aşımına uğrayabilir

### Workarounds
- Deployment süresi: Normal davranış, sabırla bekleyin
- Windows: WSL2 veya Git Bash kullanın
- Büyük dosyalar: `CLIENT_MAX_BODY_SIZE` ve `PROXY_READ_TIMEOUT` artırın

## Yükseltme Notları

### v1.0.0'dan Sonraki Sürümlere
Henüz yok - ilk release.

---

## Versiyonlama

Bu proje [Semantic Versioning](https://semver.org/) kullanmaktadır:
- **MAJOR**: Uyumsuz API değişiklikleri
- **MINOR**: Geriye uyumlu yeni özellikler
- **PATCH**: Geriye uyumlu bug fix'ler

## Katkıda Bulunma

Değişiklik önerileri için:
1. [GitHub Issue](https://github.com/ubden/frappe_docker/issues) açın
2. Pull Request gönderin
3. Changelog'u güncelleyin

---

**Not**: Bu changelog, deployment ve kullanıcıya yönelik değişiklikleri içerir. Detaylı commit geçmişi için Git log'larına bakın.

