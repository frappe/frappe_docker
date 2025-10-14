# 🚀 Dokploy Hızlı Başlangıç

Frappe ERPNext'i Dokploy'da 5 dakikada deploy edin!

## ⚡ Hızlı Deploy (Önerilen)

### Adım 1: Dokploy'da Yeni Proje

1. Dokploy dashboard'unuza gidin
2. **Projects** → **Create Project** butonuna tıklayın
3. Proje adı: `frappe-erpnext`

### Adım 2: Service Ekleyin

1. **Add Service** → **Docker Compose** seçin
2. Aşağıdaki bilgileri girin:
   - **Name**: `erpnext-complete`
   - **Repository**: `https://github.com/ubden/frappe_docker`
   - **Branch**: `main`
   - **Compose Path**: `dokploy/docker-compose.yml`

### Adım 3: Environment Variables

Aşağıdaki değişkenleri ekleyin (hepsini **Secret** olarak işaretleyin):

| Variable | Değer | Açıklama |
|----------|-------|----------|
| `SITE_NAME` | `erp.yourdomain.com` | Site domain adı |
| `ADMIN_PASSWORD` | `YourSecurePass123!` | Admin şifresi |
| `DB_PASSWORD` | `DBSecurePass456!` | Database şifresi |
| `HTTP_PORT` | `80` | HTTP port |

**⚠️ ÖNEMLİ**: 
- Güçlü şifreler kullanın!
- Production için `SITE_NAME`'i gerçek domain adınızla değiştirin

### Adım 4: Deploy!

1. **Deploy** butonuna tıklayın
2. ☕ Deployment 10-15 dakika sürer (kahve molası zamanı!)
3. Logları izleyin: `create-site` servisi "Exit 0" göstermeli

### Adım 5: Domain Yapılandırması (İsteğe Bağlı)

1. **Domains** sekmesine gidin
2. Domain adınızı ekleyin: `erp.yourdomain.com`
3. **Enable HTTPS** işaretleyin (otomatik SSL sertifikası)

### Adım 6: Giriş Yapın!

1. Browser'da sitenize gidin: `https://erp.yourdomain.com`
2. Giriş bilgileri:
   - 👤 **Username**: `Administrator`
   - 🔑 **Password**: `ADMIN_PASSWORD` değeriniz

## ✅ Kurulu Uygulamalar (Minimal Setup)

Deploy sonrası otomatik olarak şu uygulamalar kurulu gelir:

- ✅ **ERPNext** - ERP Core (Accounting, Inventory, Sales, Purchase, Manufacturing)
- ✅ **HRMS** - İnsan Kaynakları (Payroll, Leave, Attendance, Performance)
- ✅ **CRM** - Müşteri İlişkileri (Lead, Deal, Contact Management)
- ✅ **Helpdesk** - Destek Sistemi (Ticket, SLA, Knowledge Base)
- ✅ **Payments** - Ödeme Entegrasyonları (Stripe, PayPal, Razorpay)

**Toplam**: 5 Uygulama (Minimal ve hızlı kurulum)

### 🔧 Manuel Eklenebilir

İhtiyaç halinde sonradan ekleyebilirsiniz:
- LMS (E-Learning)
- Builder (Website Builder)
- Print Designer (Custom Print Formats)
- Wiki (Knowledge Base)

## 📊 Sistem Gereksinimleri

### Minimum
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB

### Önerilen (Production)
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD

## 🔧 İlk Yapılandırma

### 1. Setup Wizard
İlk girişte Setup Wizard otomatik açılır:
- Şirket bilgilerini girin
- Para birimi seçin
- Sektör bilgisi
- Chart of Accounts

### 2. Email Ayarları
**Settings** → **Email Account**:
- SMTP server bilgileri
- Gönderen email adresi
- Notifications için email

### 3. Kullanıcı Ekleyin
**User Management** → **Add User**:
- Email adresi
- Rol atamaları
- İzinler

## 🔄 Güncellemeler

### Otomatik Güncelleme
Dokploy'da:
1. Service'inize gidin
2. **Redeploy** butonuna tıklayın
3. Yeni image build edilir ve deploy edilir

### Manuel Güncelleme
```bash
docker exec -it <backend-container> bash
bench update --reset
bench --site <site-name> migrate
bench build
```

## 💾 Backup

### Otomatik Backup Kurulumu

1. Dokploy service ayarlarında **Cron Job** ekleyin:
   ```bash
   0 2 * * * docker exec <backend-container> bench --site <site-name> backup --with-files
   ```

2. Backup dosyaları: `/home/frappe/frappe-bench/sites/<site-name>/private/backups/`

### Manuel Backup

```bash
# Container'a girin
docker exec -it <backend-container> bash

# Backup oluştur
bench --site <site-name> backup --with-files

# Backup'ları görüntüle
ls -lh sites/<site-name>/private/backups/
```

### Backup'ları İndirme

```bash
# Docker volume'dan local'e kopyala
docker cp <container>:/home/frappe/frappe-bench/sites/<site-name>/private/backups/. ./backups/
```

## 📈 Monitoring

### Dokploy Dashboard
- **Logs**: Tüm servislerin logları
- **Metrics**: CPU, RAM, Disk kullanımı
- **Health**: Container durumları

### Manuel Kontrol

```bash
# Container durumları
docker-compose ps

# Logları görüntüle
docker-compose logs -f

# Resource kullanımı
docker stats
```

## 🛠️ Sorun Giderme

### Site Açılmıyor

**Çözüm 1**: Container'ları kontrol edin
```bash
docker-compose ps
# Tüm servisler "healthy" olmalı
```

**Çözüm 2**: Logları kontrol edin
```bash
docker-compose logs backend
docker-compose logs create-site
```

**Çözüm 3**: Browser cache'i temizleyin
- Ctrl+Shift+Delete (Chrome/Edge)
- Cmd+Shift+Delete (Safari)

### "Site not found" Hatası

```bash
# Site'ı kontrol et
docker exec <backend-container> bench --site all list-apps

# Eğer site yoksa, yeniden oluştur
docker-compose up create-site
```

### Database Bağlantı Hatası

```bash
# MariaDB çalışıyor mu?
docker-compose ps mariadb

# MariaDB logları
docker-compose logs mariadb

# Manuel bağlantı testi
docker exec <backend-container> wait-for-it mariadb:3306
```

### Yavaş Çalışıyor

1. **Server kaynaklarını kontrol edin**:
   ```bash
   docker stats
   ```

2. **MariaDB buffer pool artırın** (docker-compose.yml):
   ```yaml
   mariadb:
     command:
       - --innodb-buffer-pool-size=4G
   ```

3. **Worker sayısını artırın**:
   ```yaml
   backend:
     command:
       - --workers=4
       - --threads=8
   ```

## 🔐 Güvenlik İpuçları

1. **Güçlü Şifreler Kullanın**
   - En az 12 karakter
   - Büyük/küçük harf, sayı, özel karakter karışımı

2. **HTTPS Aktif Edin**
   - Dokploy otomatik Let's Encrypt sertifikası oluşturur
   - Domain'i ekleyin ve "Enable HTTPS" işaretleyin

3. **Firewall Kuralları**
   - Sadece 80 (HTTP) ve 443 (HTTPS) portlarını açın
   - SSH (22) sadece güvenli IP'lerden erişilebilir olmalı

4. **Düzenli Backup**
   - Günlük otomatik backup kurun
   - Backup'ları farklı lokasyonda saklayın

5. **2FA Aktif Edin**
   - **User** → **Two Factor Authentication**
   - TOTP app ile (Google Authenticator, Authy vb.)

## 📚 Yararlı Linkler

- 📖 [Detaylı Deployment Kılavuzu](DEPLOYMENT.md)
- 🌐 [Frappe Docs](https://frappeframework.com/docs)
- 📘 [ERPNext Docs](https://docs.erpnext.com)
- 💬 [Frappe Forum](https://discuss.frappe.io)
- 🐛 [GitHub Issues](https://github.com/ubden/frappe_docker/issues)

## 🎯 Sonraki Adımlar

1. ✅ Setup Wizard'ı tamamlayın
2. ✅ Email ayarlarını yapın
3. ✅ Ek kullanıcılar oluşturun
4. ✅ Şirket bilgilerini güncelleyin
5. ✅ İlk ürün/hizmetinizi ekleyin
6. ✅ İlk müşterinizi ekleyin
7. ✅ Otomatik backup kurun

## 💡 Pro İpuçları

1. **Bench Console**: Gelişmiş Python komutları çalıştırın
   ```bash
   docker exec -it <backend-container> bench console
   ```

2. **Clear Cache**: Site yavaşladıysa
   ```bash
   bench --site <site-name> clear-cache
   bench --site <site-name> clear-website-cache
   ```

3. **Rebuild Search Index**: Arama çalışmıyorsa
   ```bash
   bench --site <site-name> rebuild-global-search
   ```

4. **Migrate**: Update sonrası
   ```bash
   bench --site <site-name> migrate
   ```

---

## 🎉 Tebrikler!

Frappe ERPNext artık hazır! İyi çalışmalar! 🚀

Sorularınız için: [GitHub Discussions](https://github.com/ubden/frappe_docker/discussions)

