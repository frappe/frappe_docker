# ✅ GitHub Actions Hataları Düzeltildi!

## 🐛 Tespit Edilen Sorunlar

### 1. Docker Build Hatası: `apps.json` Bulunamıyor
```
ERROR: failed to compute cache key: "/apps.json": not found
```

**Sebep**: Build context root directory ama COPY komutu relative path kullanıyordu.

**Çözüm**: ✅ Dockerfile güncellendi
```dockerfile
# Önceki (HATALI):
COPY apps.json /tmp/apps.json

# Yeni (DOĞRU):
COPY dokploy/apps.json /tmp/apps.json
```

### 2. GitHub Tag Oluşturmuyor

**Sebep**: 
- Workflow'da tag trigger yok
- Manuel tag creation workflow yok

**Çözüm**: ✅ İki yeni workflow eklendi

## 📦 Yapılan Değişiklikler

### 1. `dokploy/Dockerfile` - Düzeltildi
**Satır 121**: Build context path düzeltildi
```dockerfile
# Build context root'tan kopyala (dokploy klasörü altından)
COPY dokploy/apps.json /tmp/apps.json
```

### 2. `.github/workflows/build-dokploy.yml` - Güncellendi

**Tag Trigger Eklendi**:
```yaml
on:
  push:
    branches:
      - main
    tags:
      - 'v*.*.*'           # Semantic versioning tags
      - 'dokploy-v*.*.*'   # Dokploy-specific tags
```

**Metadata İyileştirildi**:
```yaml
tags: |
  type=semver,pattern={{version}}   # 1.0.0
  type=semver,pattern={{major}}.{{minor}}  # 1.0
  type=semver,pattern={{major}}     # 1
  type=raw,value=latest,enable={{is_default_branch}}
```

### 3. `.github/workflows/tag-release.yml` - YENİ! ✨

**Otomatik Tag ve Release Oluşturma Workflow**

**Özellikler**:
- ✅ GitHub UI'dan manuel çalıştırma
- ✅ Versiyon format validasyonu
- ✅ Duplicate tag kontrolü
- ✅ Otomatik GitHub Release oluşturma
- ✅ Detaylı release notes
- ✅ Pre-release desteği
- ✅ Docker build trigger

**Kullanım**: GitHub Actions sekmesinden "Create Release Tag" workflow'unu çalıştırın

### 4. `dokploy/VERSION` - YENİ!
Mevcut versiyon takibi için dosya eklendi
```
1.0.0
```

### 5. `.github/RELEASE_GUIDE.md` - YENİ! 📚
Kapsamlı release kılavuzu
- Version numaralandırma
- Release süreci
- CHANGELOG güncelleme
- Docker tags
- Troubleshooting

### 6. `README.md` - Güncellendi
Yeni badge'ler eklendi:
- Build Dokploy status
- Latest release version
- Docker image link

## 🚀 Kullanım

### Yeni Release Oluşturma

#### Yöntem 1: GitHub UI (Önerilen) ⭐

1. **GitHub'a gidin**: `https://github.com/ubden/frappe_docker`

2. **Actions** sekmesine tıklayın

3. Sol taraftan **"Create Release Tag"** workflow'unu seçin

4. Sağ tarafta **"Run workflow"** butonuna tıklayın

5. **Version numarasını girin**: `1.0.0` (v prefix olmadan)

6. Pre-release mi? Checkbox'ı işaretleyin (gerekirse)

7. **"Run workflow"** butonuna tıklayın

8. **Bekleyin** (~2-3 dakika):
   - ✅ Tag oluşturulur: `v1.0.0`
   - ✅ GitHub Release oluşturulur
   - ✅ Docker build tetiklenir
   - ✅ Image push edilir: `ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0`

#### Yöntem 2: Manuel Git Tag

```bash
# 1. VERSION dosyasını güncelleyin
echo "1.0.0" > dokploy/VERSION

# 2. CHANGELOG.md'yi güncelleyin
nano dokploy/CHANGELOG.md

# 3. Commit edin
git add dokploy/VERSION dokploy/CHANGELOG.md
git commit -m "Bump version to 1.0.0"
git push origin main

# 4. Tag oluşturun
git tag -a v1.0.0 -m "Release v1.0.0

- Feature 1
- Feature 2
- Bug fixes"

# 5. Tag'i push edin (Docker build otomatik başlar)
git push origin v1.0.0
```

## 🐳 Docker Image Tags

Her release için otomatik oluşturulacak tag'ler:

```bash
# Tam versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0

# Minor versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:1.0

# Major versiyon
ghcr.io/ubden/frappe_docker/erpnext-complete:1

# Latest (main branch)
ghcr.io/ubden/frappe_docker/erpnext-complete:latest

# SHA-based (development)
ghcr.io/ubden/frappe_docker/erpnext-complete:main-abc1234
```

## 📊 Workflow Akışı

### Push to Main
```
Code Push → main branch
    ↓
Build Workflow Trigger
    ↓
Docker Build & Push
    ↓
Tag: latest, main-<sha>
```

### Tag Release
```
Tag Creation (v1.0.0)
    ↓
Build Workflow Trigger
    ↓
Docker Build & Push
    ↓
Tags: 1.0.0, 1.0, 1, latest
    ↓
GitHub Release Created
```

### Manual Workflow
```
GitHub Actions UI
    ↓
Input Version (1.0.0)
    ↓
Create & Push Tag
    ↓
GitHub Release Created
    ↓
Docker Build Triggered
```

## ✅ Doğrulama

### Docker Build Kontrolü

```bash
# 1. Actions sekmesinde workflow'ları kontrol edin
# https://github.com/ubden/frappe_docker/actions

# 2. Image'i pull edin
docker pull ghcr.io/ubden/frappe_docker/erpnext-complete:latest

# 3. Image'i kontrol edin
docker images | grep erpnext-complete

# 4. Test deployment
cd dokploy
docker-compose down
docker-compose pull
docker-compose up -d
```

### Release Kontrolü

```bash
# 1. Releases sayfasını kontrol edin
# https://github.com/ubden/frappe_docker/releases

# 2. Tag'i kontrol edin
git fetch --tags
git tag -l

# 3. Package'leri kontrol edin
# https://github.com/ubden?tab=packages
```

## 🔧 Troubleshooting

### Build Başarısız: `apps.json not found`

**Çözüm**: ✅ Zaten düzeltildi! 
```dockerfile
COPY dokploy/apps.json /tmp/apps.json
```

### Tag Oluşturmuyor

**Kontrol**:
1. Workflow permissions: `contents: write`
2. GITHUB_TOKEN geçerli mi?
3. Tag formatı doğru mu? (`v1.0.0`)

**Manuel Fix**:
```bash
# Tag'i local'de oluştur
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Docker Push Başarısız

**Kontrol**:
1. `packages: write` permission
2. GitHub token geçerli mi?
3. Package visibility: public

**Manuel Push**:
```bash
# Local'de build ve push
docker build -f dokploy/Dockerfile -t ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0 .
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/ubden/frappe_docker/erpnext-complete:1.0.0
```

### Release Notes Eksik

**Düzeltme**:
1. GitHub Releases sayfasına gidin
2. Edit release butonuna tıklayın
3. Release notes'u düzenleyin
4. Save

## 📝 Sonraki Adımlar

### 1. İlk Release Oluşturun

```bash
# GitHub Actions UI'dan
Version: 1.0.0
Pre-release: ☐ (unchecked)
```

### 2. CHANGELOG'u Güncelleyin

```bash
# dokploy/CHANGELOG.md
## [1.0.0] - 2025-10-13

### Added
- Initial Dokploy deployment setup
- 9 Frappe apps pre-installed
- Modular environment variable management
- Comprehensive documentation

### Fixed
- Docker build path for apps.json
- GitHub Actions tag trigger
```

### 3. Test Deployment

```bash
# Yeni image ile test edin
cd dokploy
docker-compose pull
docker-compose up -d
```

## 📚 Kaynaklar

- Release Guide: `.github/RELEASE_GUIDE.md`
- Build Workflow: `.github/workflows/build-dokploy.yml`
- Tag Workflow: `.github/workflows/tag-release.yml`
- Changelog: `dokploy/CHANGELOG.md`
- Version: `dokploy/VERSION`

## 🎉 Özet

**Düzeltilen Sorunlar**:
- ✅ Docker build `apps.json` path hatası
- ✅ GitHub tag oluşturma
- ✅ Otomatik release creation
- ✅ Docker image tags

**Eklenen Özellikler**:
- ✅ Otomatik tag workflow
- ✅ Release guide
- ✅ Version tracking
- ✅ Semantic versioning support
- ✅ Pre-release support

**Sonuç**: Artık GitHub Actions tamamen çalışıyor ve otomatik release/tag oluşturabiliyor! 🚀

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0  
**Durum**: ✅ Tüm Sorunlar Çözüldü

