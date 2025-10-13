# Release Kılavuzu

Bu doküman, Frappe ERPNext Dokploy projesinde yeni versiyon yayınlama sürecini açıklar.

## 🏷️ Versiyon Numaralandırma

Projede [Semantic Versioning](https://semver.org/) kullanılır:

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Uyumsuz API değişiklikleri
- **MINOR**: Geriye uyumlu yeni özellikler
- **PATCH**: Geriye uyumlu bug fix'ler

### Örnekler
- `1.0.0` - İlk stable release
- `1.1.0` - Yeni özellik eklendi
- `1.1.1` - Bug fix
- `2.0.0` - Breaking change

## 📋 Release Öncesi Checklist

### 1. Kod Hazırlığı
- [ ] Tüm özellikler tamamlandı
- [ ] Testler passed (varsa)
- [ ] Linter/formatter çalıştırıldı
- [ ] Breaking changes dokümante edildi
- [ ] Migration guide hazırlandı (breaking change varsa)

### 2. Dokümantasyon
- [ ] `CHANGELOG.md` güncellendi
- [ ] `dokploy/VERSION` dosyası güncellendi
- [ ] README.md gerekirse güncellendi
- [ ] Environment variables değişiklikleri `.env.example`'a eklendi
- [ ] Migration notları eklendi (gerekirse)

### 3. Testing
- [ ] Development'ta test edildi
- [ ] Staging'de test edildi (varsa)
- [ ] Docker image build testi yapıldı
- [ ] Deployment testi yapıldı

## 🚀 Release Süreci

### Yöntem 1: GitHub UI ile (Önerilen)

1. **GitHub'a gidin**
   - Repository: `https://github.com/ubden/frappe_docker`

2. **Actions sekmesine tıklayın**

3. **"Create Release Tag" workflow'u seçin**

4. **"Run workflow" butonuna tıklayın**

5. **Versiyon numarasını girin**
   - Format: `1.0.0` (v prefix olmadan)
   - Pre-release ise checkbox'ı işaretleyin

6. **"Run workflow" butonuna tıklayın**

7. **Workflow tamamlanmasını bekleyin**
   - Tag oluşturulacak
   - GitHub Release oluşturulacak
   - Docker image build edilecek

### Yöntem 2: Manuel Git Tag

```bash
# 1. Local'e en son değişiklikleri çekin
git checkout main
git pull origin main

# 2. VERSION dosyasını güncelleyin
echo "1.0.0" > dokploy/VERSION

# 3. CHANGELOG.md'yi güncelleyin
nano dokploy/CHANGELOG.md

# 4. Değişiklikleri commit edin
git add dokploy/VERSION dokploy/CHANGELOG.md
git commit -m "Bump version to 1.0.0"
git push origin main

# 5. Tag oluşturun
git tag -a v1.0.0 -m "Release v1.0.0"

# 6. Tag'i push edin
git push origin v1.0.0

# 7. GitHub'da manuel release oluşturun
# https://github.com/ubden/frappe_docker/releases/new
```

## 📝 CHANGELOG Güncelleme

`dokploy/CHANGELOG.md` dosyasını [Keep a Changelog](https://keepachangelog.com/) formatında güncelleyin:

```markdown
## [1.0.0] - 2025-10-13

### Added
- Yeni özellik 1
- Yeni özellik 2

### Changed
- Değişiklik 1
- Değişiklik 2

### Fixed
- Bug fix 1
- Bug fix 2

### Removed
- Kaldırılan özellik

### Security
- Güvenlik güncellemesi
```

## 🐳 Docker Image Tags

Her release için otomatik olarak şu tag'ler oluşturulur:

```
ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0      # Tam versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:1.0        # Minor versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:1          # Major versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:latest     # En son stable
```

## 🔍 Release Sonrası Kontroller

### 1. GitHub Release
- [ ] Release oluşturuldu mu?
- [ ] Release notes doğru mu?
- [ ] Assets yüklendi mi? (varsa)

### 2. Docker Image
- [ ] Image build edildi mi?
- [ ] Image push edildi mi?
- [ ] Tag'ler doğru mu?
- [ ] Image pull testi yapıldı mı?

```bash
# Image test
docker pull ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0
docker images | grep erpnext-complete
```

### 3. Deployment Test
- [ ] Yeni image ile deployment test edildi mi?
- [ ] Tüm servisler çalışıyor mu?
- [ ] Migration gerekiyorsa uygulandı mı?

```bash
# Test deployment
cd dokploy
docker-compose down
docker-compose pull
docker-compose up -d
```

### 4. Dokümantasyon
- [ ] Release announcement hazırlandı mı? (gerekirse)
- [ ] Documentation güncellendi mi?
- [ ] Breaking changes communicated mi?

## 🎯 Release Tipleri

### Patch Release (1.0.x)
- Bug fixes
- Minor improvements
- Security patches
- Documentation updates

**Sıklık**: Gerektiğinde (haftada/ayda)

### Minor Release (1.x.0)
- Yeni özellikler (geriye uyumlu)
- Yeni uygulamalar ekleme
- Performance improvements
- Deprecation notices

**Sıklık**: Ayda/çeyrek dönemde bir

### Major Release (x.0.0)
- Breaking changes
- Major refactoring
- Frappe/ERPNext major version upgrade
- Architecture changes

**Sıklık**: Yılda bir veya gerektiğinde

## 🔄 Hotfix Süreci

Acil bug fix için:

```bash
# 1. Hotfix branch oluştur
git checkout -b hotfix/1.0.1 v1.0.0

# 2. Fix'i uygula
git commit -m "Fix critical bug"

# 3. Main'e merge et
git checkout main
git merge hotfix/1.0.1

# 4. Tag oluştur
git tag -a v1.0.1 -m "Hotfix v1.0.1"

# 5. Push et
git push origin main
git push origin v1.0.1

# 6. Hotfix branch'i sil
git branch -d hotfix/1.0.1
```

## 📧 Communication

### Internal
- Team'e release notları paylaş
- Breaking changes vurgula
- Migration guide linkle

### External
- GitHub Discussions'da announce
- README badges güncelle
- Social media (varsa)

## 🛠️ Troubleshooting

### Tag zaten var
```bash
# Tag'i sil
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Yeniden oluştur
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Docker build başarısız
```bash
# Local'de test et
cd dokploy
docker build -f Dockerfile -t test:latest ..

# Logs'u kontrol et
docker logs <container-id>
```

### Release oluşturulamadı
- GitHub permissions kontrol edin
- GITHUB_TOKEN geçerli mi?
- Workflow syntax doğru mu?

## 📚 Kaynaklar

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Docker Tags](https://docs.docker.com/engine/reference/commandline/tag/)

## 🎓 Best Practices

1. **Sık ve küçük release'ler tercih edin**
2. **Her release için CHANGELOG güncelleyin**
3. **Breaking changes'i versiyondan önce duyurun**
4. **Test coverage'ı artırın**
5. **Migration guide'lar ekleyin**
6. **Deprecation warnings verin**
7. **Semantic versioning'e sadık kalın**

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0

