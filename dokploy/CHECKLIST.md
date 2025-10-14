# Dokploy Deployment Checklist

## ✅ Deployment Öncesi

### Gereksinimler
- [ ] Dokploy kurulu ve erişilebilir
- [ ] Domain adı hazır (production için)
- [ ] DNS kayıtları yapılandırılmış
- [ ] Minimum 4GB RAM
- [ ] 2+ CPU cores
- [ ] 15GB+ disk alanı

### Konfigürasyon
- [ ] `.env` dosyası hazırlandı veya environment variables belirlendi
- [ ] `SITE_NAME` belirlendi
- [ ] `ADMIN_PASSWORD` güçlü şifre (12+ karakter)
- [ ] `DB_PASSWORD` güçlü şifre (12+ karakter)
- [ ] Port 8088 kullanılacak

### Güvenlik
- [ ] Tüm şifreler güçlü ve unique
- [ ] Şifreler password manager'da saklandı
- [ ] SSL/HTTPS planlandı
- [ ] Backup stratejisi belirlendi

## 🚀 Deployment

### Dokploy Konfigürasyonu
- [ ] Yeni proje oluşturuldu
- [ ] Docker Compose service eklendi
- [ ] Repository: `https://github.com/ubden/frappe_docker`
- [ ] Branch: `main`
- [ ] Compose path: `dokploy/docker-compose.yml`

### Environment Variables
- [ ] `SITE_NAME` eklendi
- [ ] `ADMIN_PASSWORD` eklendi (Secret)
- [ ] `DB_PASSWORD` eklendi (Secret)
- [ ] `HTTP_PORT=8088` eklendi

### Domain & SSL
- [ ] Domain eklendi
- [ ] DNS A kaydı doğrulandı
- [ ] Enable HTTPS işaretlendi
- [ ] Force HTTPS işaretlendi

### Deploy
- [ ] Deploy butonu tıklandı
- [ ] Build logları izlendi (~10-15 dakika)
- [ ] Build başarıyla tamamlandı

## ✅ Deployment Sonrası

### Container Kontrolü
- [ ] Tüm container'lar running
- [ ] create-site servisi Exit 0
- [ ] backend servisi healthy
- [ ] frontend servisi healthy
- [ ] mariadb servisi healthy
- [ ] redis servisleri healthy

### Erişim
- [ ] Site browser'da açılıyor
- [ ] HTTPS çalışıyor
- [ ] Login sayfası görünüyor
- [ ] Admin girişi başarılı

### Uygulama Kontrolü
- [ ] ERPNext modülleri açılıyor
- [ ] CRM açılıyor
- [ ] Helpdesk açılıyor
- [ ] Payments yapılandırılabilir

### İlk Yapılandırma
- [ ] Setup Wizard tamamlandı
- [ ] Şirket bilgileri girildi
- [ ] Email ayarları yapıldı
- [ ] İlk kullanıcılar oluşturuldu

### Test
- [ ] Yeni dokuman oluşturulabiliyor
- [ ] Arama çalışıyor
- [ ] Dosya upload çalışıyor
- [ ] Real-time updates çalışıyor

## 🔒 Güvenlik

### Production Güvenlik
- [ ] Administrator şifresi değiştirildi
- [ ] 2FA aktif edildi
- [ ] Session timeout ayarlandı
- [ ] Firewall kuralları uygulandı

## 💾 Backup

### Backup Sistemi
- [ ] Manuel backup test edildi
- [ ] Otomatik backup planlandı
- [ ] Backup saklama yeri belirlendi
- [ ] Restore testi yapıldı

---

**Tüm checklistler tamamlandı mı?** ✅  
**Sistem production'a hazır mı?** 🚀
