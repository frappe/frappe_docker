# Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.

## [1.0.0] - 2025-10-13

### İlk Release

Production-ready Frappe ERPNext Dokploy deployment paketi.

#### Uygulamalar (4)
- ✅ ERPNext (version-15)
- ✅ CRM (main, v1.53.1)
- ✅ Helpdesk (v1.14.0)
- ✅ Payments (main)

#### Özellikler
- Dokploy-optimized Docker Compose
- Otomatik SSL/HTTPS (Let's Encrypt)
- Frontend port 8080 (standard Frappe port)
- Production-ready konfigürasyon
- Environment-based configuration
- Health checks
- Auto-restart policies

#### Performans
- Build süresi: 10-15 dakika
- Disk kullanımı: 3-4 GB
- Memory kullanımı: ~2 GB
- Fast startup

#### Güvenlik
- Non-root container
- Secret management
- HTTPS/SSL ready
- Secure defaults

#### Dokümantasyon
- README.md - Genel bilgi
- QUICKSTART.md - Hızlı başlangıç
- DEPLOYMENT.md - Detaylı kılavuz
- SSL_SETUP.md - SSL konfigürasyonu
- ENV_VARIABLES.md - Environment variables
- CHECKLIST.md - Deployment checklist
- SUMMARY.md - Paket özeti
- CHANGELOG.md - Bu dosya

---

**Toplam Apps**: 4  
**Build Time**: 10-15 min  
**Disk**: 3-4 GB  
**Port**: 8088
