# SSL/HTTPS Konfigürasyonu

Bu dokümanda Dokploy üzerinde SSL/HTTPS kurulumu açıklanır.

## 🔒 SSL Aktivasyonu (Dokploy)

### Otomatik SSL (Let's Encrypt)

Dokploy otomatik olarak Let's Encrypt sertifikası oluşturur:

#### Adım 1: Domain Yapılandırması

1. **Dokploy Dashboard'a gidin**
2. Service'inizi seçin
3. **Domains** sekmesine tıklayın
4. **Add Domain** butonuna tıklayın

#### Adım 2: Domain Ekleyin

```
Domain: erp.yourdomain.com
Port: 8080 (standard Frappe port)
Enable HTTPS: ✅ (işaretleyin)
```

#### Adım 3: DNS Ayarları

DNS provider'ınızda A kaydı oluşturun:

```
Type: A
Host: erp (veya subdomain)
Value: [Sunucu IP adresi]
TTL: 300 (5 dakika)
```

#### Adım 4: SSL Sertifikası

Dokploy otomatik olarak:
- ✅ Let's Encrypt sertifikası oluşturur
- ✅ HTTPS'i aktif eder
- ✅ HTTP'den HTTPS'e redirect yapar
- ✅ Sertifikayı otomatik yeniler (90 günde bir)

## 🌐 Port Yapılandırması

### Frontend Port: 8080

```env
# .env dosyasında
HTTP_PORT=8080
```

### Erişim URL'leri

**HTTP** (development):
```
http://erp.yourdomain.com:8080
```

**HTTPS** (production - Dokploy):
```
https://erp.yourdomain.com
```

**Not**: Dokploy HTTPS aktif olduğunda port 443 kullanır ve :8088 belirtmeye gerek kalmaz.

## 🔧 Site Config Ayarları

### SSL ile Çalışma

Site oluşturulduktan sonra SSL için ek ayar gerekmez. Dokploy reverse proxy olarak çalışır:

```
Browser (HTTPS:443)
    ↓
Dokploy Proxy (SSL termination)
    ↓
Frontend Container (HTTP:8080)
    ↓
Backend Container (HTTP:8000)
```

### Force HTTPS (İsteğe Bağlı)

Eğer tüm trafiği HTTPS'e yönlendirmek isterseniz:

```bash
# Container'a girin
docker exec -it <backend-container> bash

# Site config'e ekleyin
bench --site <site-name> set-config force_https 1
```

## 📝 Environment Variables

### SSL ile İlgili Değişkenler

```env
# .env dosyasında

# Site domain (HTTPS için gerçek domain kullanın)
SITE_NAME=erp.yourdomain.com

# Frontend port (Dokploy internal)
HTTP_PORT=8088

# Real IP headers (SSL proxy arkasında)
UPSTREAM_REAL_IP_ADDRESS=127.0.0.1
UPSTREAM_REAL_IP_HEADER=X-Forwarded-For
UPSTREAM_REAL_IP_RECURSIVE=off

# Site name resolution
FRAPPE_SITE_NAME_HEADER=$$host
```

## 🔍 SSL Doğrulama

### 1. Domain Erişimi

```bash
# HTTPS çalışıyor mu?
curl -I https://erp.yourdomain.com

# Beklenen:
HTTP/2 200
strict-transport-security: max-age=31536000
```

### 2. Sertifika Kontrolü

```bash
# SSL sertifikası detayları
openssl s_client -connect erp.yourdomain.com:443 -servername erp.yourdomain.com

# Veya browser'da:
# Adres çubuğunda kilit ikonu → Sertifika detayları
```

### 3. Redirect Kontrolü

```bash
# HTTP → HTTPS redirect
curl -I http://erp.yourdomain.com

# Beklenen:
HTTP/1.1 301 Moved Permanently
Location: https://erp.yourdomain.com
```

## 🐛 Sorun Giderme

### SSL Sertifikası Oluşturmuyor

**Kontrol**:
1. Domain DNS'i doğru mu?
   ```bash
   nslookup erp.yourdomain.com
   # Sunucu IP'sini göstermeli
   ```

2. Port 80 ve 443 açık mı?
   ```bash
   sudo ufw status
   # 80/tcp, 443/tcp ALLOW
   ```

3. Domain'e erişilebiliyor mu?
   ```bash
   curl http://erp.yourdomain.com:8088
   # Site açılmalı
   ```

**Çözüm**:
- DNS propagation'ı bekleyin (5-30 dakika)
- Dokploy'da domain'i silip tekrar ekleyin
- Firewall kurallarını kontrol edin

### "Site not secure" Uyarısı

**Sebep**: Sertifika henüz oluşmadı veya geçersiz

**Çözüm**:
1. Dokploy logs kontrol edin
2. Let's Encrypt rate limit'e takılmadınızdan emin olun
3. Domain'in doğru olduğunu kontrol edin

### Mixed Content Uyarısı

**Sebep**: HTTPS sitede HTTP kaynak yükleniyor

**Çözüm**:
```bash
# Site config'de force https aktif edin
bench --site <site-name> set-config force_https 1

# Nginx config'de HSTS header'ı kontrol edin
# (Dokploy otomatik ekler)
```

## 📚 Dokploy SSL Özellikleri

### Otomatik Özellikler

✅ **Let's Encrypt Integration**
- Otomatik sertifika oluşturma
- Otomatik yenileme (90 günde bir)
- Wildcard sertifika desteği

✅ **HTTP → HTTPS Redirect**
- Otomatik yönlendirme
- HSTS header
- Secure cookie flags

✅ **SSL Termination**
- Proxy seviyesinde SSL
- Backend HTTP kullanır (performans)
- Zero-config

## 🎯 Production Checklist

### SSL İçin

- [ ] Gerçek domain adı var
- [ ] DNS A kaydı eklendi
- [ ] Dokploy'da domain eklendi
- [ ] "Enable HTTPS" işaretlendi
- [ ] Sertifika oluşturuldu
- [ ] HTTPS erişim test edildi
- [ ] HTTP redirect çalışıyor
- [ ] Force HTTPS aktif (site config)

### Güvenlik

- [ ] HSTS header aktif
- [ ] Secure cookies
- [ ] TLS 1.2+ kullanılıyor
- [ ] Mixed content yok
- [ ] SSL Labs testi yapıldı (A+ rating)

## 🔗 Yararlı Kaynaklar

- [Dokploy SSL Docs](https://dokploy.com/docs/ssl)
- [Let's Encrypt](https://letsencrypt.org)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [Mozilla SSL Config Generator](https://ssl-config.mozilla.org)

---

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0  
**Frontend Port**: 8088  
**SSL**: Dokploy otomatik (Let's Encrypt)

