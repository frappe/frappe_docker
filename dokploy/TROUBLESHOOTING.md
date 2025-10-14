# Sorun Giderme Kılavuzu

## 🐛 Yaygın Sorunlar ve Çözümler

### Frontend: "websocket:9000 host not found"

**Hata**:
```
[emerg] host not found in upstream "websocket:9000"
```

**Sebep**: WebSocket container başlamadı veya başlatılamadı

**Çözüm 1**: WebSocket container loglarını kontrol edin
```bash
docker-compose logs websocket

# Eğer "socket.io module not found" hatası varsa:
# Image'i yeniden build edin (node_modules kaldırılmış olabilir)
docker-compose build --no-cache
docker-compose up -d
```

**Çözüm 2**: Container'ları sırayla başlatın
```bash
# Tüm container'ları durdurun
docker-compose down

# create-site container'ını çalıştırın
docker-compose up create-site

# Sonra diğerlerini başlatın
docker-compose up -d
```

### WebSocket: "Cannot find module 'socket.io'"

**Hata**:
```
Error: Cannot find module 'socket.io'
```

**Sebep**: Node.js dependencies eksik

**Çözüm**: Container'a girin ve socket.io'yu yeniden yükleyin
```bash
# Backend container'a girin
docker exec -it <backend-container> bash

# Frappe klasörüne gidin
cd /home/frappe/frappe-bench/apps/frappe

# Socket.io'yu yükleyin
npm install socket.io redis socket.io-redis

# Restart
exit
docker-compose restart websocket frontend
```

**Kalıcı Çözüm**: Image'i yeniden build edin
```bash
# Dokploy'da
1. Service → Settings → Redeploy
2. Build cache temizlenecek
3. Dependencies doğru yüklenecek
```

### Site Açılmıyor

**Kontroller**:
```bash
# 1. Backend çalışıyor mu?
docker-compose ps backend

# 2. Backend logları
docker-compose logs backend

# 3. create-site başarılı mı?
docker-compose logs create-site

# 4. Database bağlantısı
docker-compose exec backend wait-for-it mariadb:3306
```

### "Site not found"

**Çözüm**:
```bash
# Site listesini kontrol edin
docker exec <backend> bench --site all list-apps

# Site yoksa yeniden oluşturun
docker-compose up create-site
```

## 🔄 Genel Çözümler

### Temiz Başlangıç

```bash
# Tüm container'ları silin
docker-compose down -v

# Yeniden başlatın
docker-compose up -d

# Logları izleyin
docker-compose logs -f
```

### Image Yeniden Build

```bash
# Local'de
docker-compose build --no-cache
docker-compose up -d

# Dokploy'da
Service → Settings → Redeploy (Build Cache: No Cache)
```

### Container Sıralaması

Container'lar doğru sırayla başlamalı:
```
1. MariaDB, Redis → healthy
2. Configurator → complete
3. create-site → complete
4. backend → healthy
5. websocket → healthy
6. frontend → healthy
7. workers, scheduler → running
```

## 📊 Health Check

```bash
# Tüm container'lar healthy mi?
docker-compose ps

# Beklenen çıktı:
NAME                    STATUS
mariadb                 Up (healthy)
redis-cache             Up (healthy)
redis-queue             Up (healthy)
backend                 Up (healthy)
websocket               Up
frontend                Up (healthy)
queue-short             Up
queue-long              Up
scheduler               Up
```

## 🔍 Debug Mode

```bash
# Backend container'a girin
docker exec -it <backend> bash

# Bench console
bench console

# Python'da:
import frappe
frappe.init(site='<site-name>')
frappe.connect()

# Test
frappe.db.get_list('User', limit=1)
```

---

**Common Issues**: websocket, site not found, dependencies  
**Solution**: Rebuild image, restart containers, check logs

