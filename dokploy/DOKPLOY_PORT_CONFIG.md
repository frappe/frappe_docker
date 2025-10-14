# Dokploy Port Konfigürasyonu

## 🔧 Port Yönetimi

Dokploy'da port mapping **Dokploy UI'dan** yapılır, docker-compose.yml'de değil!

### ✅ Doğru Yaklaşım (Dokploy)

**docker-compose.yml**:
```yaml
frontend:
  expose:
    - "8080"  # Internal port (Dokploy yönetir)
  # ports: kullanmayın!
```

**Dokploy UI**:
```
Service → Settings → Ports
Container Port: 8080
External Port: [Dokploy otomatik atar]
```

### ❌ Yanlış Yaklaşım

```yaml
# KULLANMAYIN (Dokploy'da port çakışması yaratır):
ports:
  - "80:8080"
  - "8080:8080"
```

## 🌐 Erişim Yöntemleri

### Dokploy ile (Önerilen)

1. **Domain ekleyin**: `erp.yourdomain.com`
2. **Port**: Dokploy otomatik atar
3. **HTTPS**: Enable HTTPS ✅
4. **Erişim**: `https://erp.yourdomain.com`

### Manuel Docker Compose

Eğer Dokploy kullanmıyorsanız:

```yaml
# docker-compose.override.yml oluşturun
services:
  frontend:
    ports:
      - "8080:8080"
```

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

## 🔒 SSL ile Port Yapısı

### Dokploy Proxy Akışı

```
User Browser
    ↓
HTTPS (443) ← Dokploy Proxy (SSL termination)
    ↓
HTTP (8080) ← Frontend Container (internal)
    ↓
HTTP (8000) ← Backend Container
```

**Not**: Container'lar arası tüm trafik HTTP'dir (internal network, güvenli).

## 🐛 Port Çakışması Hatası

### Hata

```
Bind for 0.0.0.0:80 failed: port is already allocated
```

### Sebep

- docker-compose.yml'de `ports: "80:8080"` tanımlı
- Başka bir servis zaten 80 portunu kullanıyor
- Dokploy'da port management conflict

### Çözüm

**docker-compose.yml'de**:
```yaml
# Önceden (HATALI):
ports:
  - "${HTTP_PORT:-8080}:8080"

# Şimdi (DOĞRU):
expose:
  - "8080"
```

**Dokploy UI'da**:
- Domain ekleyin
- Enable HTTPS
- Dokploy otomatik port yönetir

## 📋 Dokploy Deployment Adımları

### 1. Repository Ekle

```
Repository: https://github.com/ubden/frappe_docker
Branch: main
Compose: dokploy/docker-compose.yml
```

### 2. Environment Variables

```env
SITE_NAME=erp.yourdomain.com
ADMIN_PASSWORD=YourPass123!
DB_PASSWORD=DBPass456!
# HTTP_PORT tanımlamayın (Dokploy yönetir)
```

### 3. Domain + SSL

```
Domain: erp.yourdomain.com
Enable HTTPS: ✅
Force HTTPS: ✅
```

Port otomatik atanır!

### 4. Deploy

Deploy → Bekle → Hazır!

**Erişim**: `https://erp.yourdomain.com`

## ✅ Önerilen Konfigürasyon

### Dokploy için (Production)

- ✅ `expose: ["8080"]` kullan
- ✅ `ports:` kullanma
- ✅ Domain ekle
- ✅ HTTPS aktif et
- ✅ Dokploy port'u yönetsin

### Manuel için (Development)

- ✅ `ports: ["8080:8080"]` kullan
- ✅ Local'de test et
- ✅ HTTP ile erişim

## 🔍 Port Kontrolü

### Container içinden

```bash
# Frontend container'a girin
docker exec -it <frontend> bash

# Nginx'in dinlediği portu kontrol edin
netstat -tuln | grep 8080
# 0.0.0.0:8080 olmalı
```

### Dışarıdan

```bash
# Dokploy'da domain varsa
curl https://erp.yourdomain.com

# Yoksa (geliştirme)
curl http://localhost:8080
```

---

**Dokploy**: `expose` kullan, port yönetimini Dokploy'a bırak  
**Manuel**: `ports` kullan, manuel yönet  
**SSL**: Dokploy otomatik (443 → 8080 internal)

