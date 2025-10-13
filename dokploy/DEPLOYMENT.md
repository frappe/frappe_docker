# Dokploy Deployment Kılavuzu

Bu kılavuz, Frappe ERPNext'i Dokploy'da deploy etmek için adım adım talimatları içerir.

## Ön Gereksinimler

1. Dokploy kurulu bir sunucu
2. En az 4GB RAM ve 20GB disk alanı
3. Domain adı (isteğe bağlı, localhost ile de çalışır)

## Deployment Yöntemleri

### Yöntem 1: Dokploy UI ile GitHub'dan Deploy (En Kolay)

1. **Dokploy Dashboard'a Giriş**
   - Dokploy panel adresinize gidin (örn: `https://dokploy.example.com`)
   - Giriş yapın

2. **Yeni Proje Oluşturma**
   - Sol menüden "Projects" seçeneğine tıklayın
   - "Create Project" butonuna tıklayın
   - Proje adı: `frappe-erpnext`
   - Açıklama: `Frappe ERPNext with all apps`

3. **Yeni Service Oluşturma**
   - Oluşturduğunuz projenin içinde "Add Service" butonuna tıklayın
   - Service Type: `Docker Compose`
   - Service Name: `erpnext-complete`

4. **Git Repository Bağlama**
   - Repository Type: `GitHub`
   - Repository URL: `https://github.com/ubden/frappe_docker`
   - Branch: `main`
   - Compose File Path: `dokploy/docker-compose.yml`

5. **Environment Variables Ayarlama**
   
   Aşağıdaki değişkenleri ekleyin:
   
   ```
   SITE_NAME=erp.yourdomain.com
   ADMIN_PASSWORD=your_secure_password_here
   DB_PASSWORD=your_db_password_here
   HTTP_PORT=80
   ```
   
   **ÖNEMLİ**: 
   - `SITE_NAME` değerini domain adınız veya IP adresiniz ile değiştirin
   - `ADMIN_PASSWORD` ve `DB_PASSWORD` için güçlü şifreler kullanın
   - Şifreleri "Secret" olarak işaretleyin

6. **Domain Yapılandırması** (İsteğe Bağlı)
   - "Domains" sekmesine gidin
   - Domain adınızı ekleyin (örn: `erp.yourdomain.com`)
   - SSL sertifikası için "Enable HTTPS" seçeneğini işaretleyin

7. **Deploy**
   - "Deploy" butonuna tıklayın
   - Deployment loglarını izleyin
   - İlk deployment 10-15 dakika sürebilir (image build ve tüm uygulamaların kurulumu)

8. **Deployment Durumunu Kontrol**
   - "Logs" sekmesinden container loglarını izleyin
   - "create-site" servisinin başarıyla tamamlandığından emin olun
   - Tüm servislerin "healthy" durumunda olmasını bekleyin

### Yöntem 2: CLI ile Deploy

1. **Dokploy CLI Kurulumu**
   ```bash
   npm install -g @dokploy/cli
   ```

2. **Login**
   ```bash
   dokploy login https://your-dokploy-instance.com
   ```

3. **Proje Oluşturma**
   ```bash
   dokploy project create frappe-erpnext
   ```

4. **Service Deploy**
   ```bash
   cd dokploy
   dokploy deploy \
     --project frappe-erpnext \
     --service erpnext-complete \
     --compose docker-compose.yml \
     --env .env
   ```

### Yöntem 3: Manuel Docker Compose

Dokploy kullanmadan direkt sunucuda:

```bash
# Repository'yi klonlayın
git clone https://github.com/ubden/frappe_docker.git
cd frappe_docker/dokploy

# .env dosyasını düzenleyin
nano .env

# Deploy
chmod +x install.sh
./install.sh
```

## Deployment Sonrası

### İlk Giriş

1. Browser'da site adresinize gidin: `http://your-site-name` veya `https://your-domain.com`
2. Giriş bilgileri:
   - **Username**: `Administrator`
   - **Password**: `.env` dosyasında belirlediğiniz `ADMIN_PASSWORD`

### Kurulu Uygulamaları Kontrol

1. Sol menüden "App Manager" seçeneğine gidin (veya `/app` URL'sine)
2. Aşağıdaki uygulamaların kurulu olduğunu doğrulayın:
   - ✅ ERPNext
   - ✅ CRM
   - ✅ LMS
   - ✅ Builder
   - ✅ Print Designer
   - ✅ Payments
   - ✅ Wiki
   - ✅ Twilio Integration
   - ✅ ERPNext Shipping

### İlk Yapılandırma

1. **System Settings**
   - Setup Wizard'ı tamamlayın (şirket bilgileri, para birimi vb.)
   
2. **Email Ayarları**
   - Email Account oluşturun (SMTP ayarları)
   - Notifications için email göndericisini ayarlayın

3. **Kullanıcı Oluşturma**
   - Ek kullanıcılar oluşturun
   - Roller ve izinler atayın

## Güncelleme

### Dokploy UI ile

1. Dokploy dashboard'da service'inize gidin
2. "Redeploy" butonuna tıklayın
3. Yeni image build edilecek ve container'lar güncellenecektir

### Manuel Güncelleme

```bash
# Container'a bağlanın
docker exec -it <backend-container-name> bash

# Uygulamaları güncelleyin
cd /home/frappe/frappe-bench
bench update --reset

# Site'ı migrate edin
bench --site <site-name> migrate

# Assets'leri build edin
bench build

# Container'ları yeniden başlatın
exit
docker-compose restart
```

## Backup ve Restore

### Otomatik Backup (Cron ile)

1. `compose.backup-cron.yaml` dosyasını kullanın:
   ```bash
   docker-compose -f docker-compose.yml -f ../overrides/compose.backup-cron.yaml up -d
   ```

### Manuel Backup

```bash
# Container'a girin
docker exec -it <backend-container-name> bash

# Backup oluştur
bench --site <site-name> backup --with-files

# Backup'ları listele
ls -lh sites/<site-name>/private/backups/
```

### Restore

```bash
# Container'a girin
docker exec -it <backend-container-name> bash

# Database restore
bench --site <site-name> --force restore \
  /home/frappe/frappe-bench/sites/<site-name>/private/backups/[database-file].sql.gz

# Files restore (isteğe bağlı)
bench --site <site-name> --force restore \
  --with-private-files /path/to/private-files.tar \
  --with-public-files /path/to/public-files.tar
```

## Monitoring ve Loglar

### Dokploy Dashboard

- "Logs" sekmesinden tüm servislerin loglarını görebilirsiniz
- "Metrics" sekmesinden kaynak kullanımını izleyebilirsiniz

### CLI ile

```bash
# Tüm servislerin logları
docker-compose logs -f

# Belirli bir servisin logları
docker-compose logs -f backend

# Create-site servisinin logları
docker-compose logs create-site
```

## Performans Optimizasyonu

### Database

`docker-compose.yml` içinde MariaDB ayarlarını günceleyin:

```yaml
mariadb:
  command:
    - --innodb-buffer-pool-size=4G  # RAM'in %50-75'i
    - --innodb-log-file-size=1G
    - --max-connections=1000
```

### Gunicorn Workers

Backend servisi için worker sayısını artırın:

```yaml
backend:
  command:
    - gunicorn
    - --workers=4  # CPU core sayısı x 2
    - --threads=8
```

## Troubleshooting

### Site açılmıyor

```bash
# Container'ların durumunu kontrol et
docker-compose ps

# Backend loglarını kontrol et
docker-compose logs backend

# Database bağlantısını kontrol et
docker-compose exec mariadb mysql -u root -p
```

### "Site not found" hatası

```bash
# Site'ların listesini kontrol et
docker-compose exec backend bench --site all list-apps

# Site config'i kontrol et
docker-compose exec backend cat sites/<site-name>/site_config.json
```

### Yavaş çalışıyor

1. Redis memory'yi kontrol edin
2. MariaDB buffer pool'u artırın
3. Worker sayısını artırın
4. Server kaynaklarını kontrol edin (CPU, RAM, Disk I/O)

### Database bağlantı hatası

```bash
# MariaDB healthy mi kontrol et
docker-compose ps mariadb

# MariaDB loglarını kontrol et
docker-compose logs mariadb

# Manuel bağlantı testi
docker-compose exec backend wait-for-it mariadb:3306 -t 30
```

## Güvenlik

### Şifreleri Güncelleme

```bash
# Administrator şifresini değiştir
docker-compose exec backend bench --site <site-name> set-admin-password <new-password>

# Database şifresini değiştir (dikkatli olun!)
# Hem database'de hem de site_config.json'da güncelleyin
```

### SSL/HTTPS

Dokploy otomatik olarak Let's Encrypt sertifikası oluşturabilir:
1. Domain'inizi DNS'e ekleyin
2. Dokploy'da domain'i ekleyin
3. "Enable HTTPS" seçeneğini işaretleyin

### Firewall

Sadece gerekli portları açın:
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH - sadece güvenli IP'lerden)

## Destek

- [Frappe Forum](https://discuss.frappe.io)
- [ERPNext Docs](https://docs.erpnext.com)
- [Dokploy Docs](https://dokploy.com/docs)
- GitHub Issues: https://github.com/ubden/frappe_docker/issues

## Yararlı Komutlar

```bash
# Container'lara bağlan
docker-compose exec backend bash
docker-compose exec mariadb bash

# Servisleri yeniden başlat
docker-compose restart

# Logları temizle
docker-compose logs --tail=100

# Volumes'ları temizle (DİKKAT: Tüm veriler silinir!)
docker-compose down -v

# Resource kullanımını göster
docker stats

# Container'ları güncelle
docker-compose pull
docker-compose up -d
```

