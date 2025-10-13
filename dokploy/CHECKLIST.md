# Dokploy Deployment Checklist

Bu checklist, Dokploy'a deployment öncesi ve sonrası kontrol edilmesi gereken tüm öğeleri içerir.

## ✅ Deployment Öncesi

### Gereksinimler
- [ ] Dokploy kurulu ve erişilebilir durumda
- [ ] Domain adı hazır (isteğe bağlı, localhost ile de çalışır)
- [ ] DNS kayıtları yapılandırılmış (production için)
- [ ] Minimum sistem gereksinimleri karşılanıyor
  - [ ] 4GB+ RAM
  - [ ] 2+ CPU cores
  - [ ] 20GB+ disk alanı

### Konfigürasyon Hazırlığı
- [ ] `.env` dosyası oluşturuldu veya environment variables hazırlandı
- [ ] `SITE_NAME` belirlendi (örn: erp.yourdomain.com)
- [ ] `ADMIN_PASSWORD` güçlü bir şifre olarak belirlendi
  - [ ] En az 12 karakter
  - [ ] Büyük/küçük harf, sayı, özel karakter karışımı
- [ ] `DB_PASSWORD` güçlü bir şifre olarak belirlendi
- [ ] Port ayarları yapılandırıldı (varsayılan: 80)

### Güvenlik
- [ ] Tüm şifreler güvenli ve unique
- [ ] Şifreler password manager'da saklandı
- [ ] Production için SSL/HTTPS planlandı
- [ ] Firewall kuralları planlandı
- [ ] Backup stratejisi belirlendi

### Dokümantasyon İncelemesi
- [ ] [QUICKSTART.md](QUICKSTART.md) okundu
- [ ] [DEPLOYMENT.md](DEPLOYMENT.md) okundu
- [ ] [SUMMARY.md](SUMMARY.md) incelendi

## 🚀 Deployment Süreci

### Dokploy Konfigürasyonu
- [ ] Yeni proje oluşturuldu
- [ ] Service eklendi (Docker Compose)
- [ ] Repository URL girildi: `https://github.com/ubden/frappe_docker`
- [ ] Branch seçildi: `main`
- [ ] Compose path girildi: `dokploy/docker-compose.yml`

### Environment Variables
- [ ] `SITE_NAME` eklendi
- [ ] `ADMIN_PASSWORD` eklendi (Secret olarak işaretlendi)
- [ ] `DB_PASSWORD` eklendi (Secret olarak işaretlendi)
- [ ] `HTTP_PORT` eklendi (gerekirse)
- [ ] Ek ayarlar eklendi (isteğe bağlı)

### Domain & SSL (Production)
- [ ] Domain eklendi
- [ ] DNS A kaydı eklendi
- [ ] SSL/HTTPS aktif edildi (Let's Encrypt)
- [ ] SSL sertifikası doğrulandı

### Deploy
- [ ] Deploy butonu tıklandı
- [ ] Deployment logları izlendi
- [ ] Build işlemi başarıyla tamamlandı (~10 dakika)

## ✅ Deployment Sonrası

### Container Kontrolü
- [ ] Tüm container'lar running durumda
- [ ] `create-site` servisi "Exit 0" ile tamamlandı
- [ ] `backend` servisi healthy durumda
- [ ] `frontend` servisi healthy durumda
- [ ] `mariadb` servisi healthy durumda
- [ ] `redis-cache` servisi healthy durumda
- [ ] `redis-queue` servisi healthy durumda
- [ ] Worker'lar çalışıyor durumda
- [ ] Scheduler çalışıyor durumda

### Erişilebilirlik
- [ ] Site browser'da açılıyor
- [ ] HTTPS çalışıyor (production)
- [ ] Login sayfası görüntüleniyor
- [ ] Admin girişi başarılı
  - Username: Administrator
  - Password: `ADMIN_PASSWORD` değeriniz

### Uygulama Kontrolü
- [ ] Setup Wizard açıldı/tamamlandı
- [ ] Dashboard yükleniyor
- [ ] Kurulu uygulamalar kontrol edildi:
  - [ ] ERPNext
  - [ ] CRM
  - [ ] LMS
  - [ ] Builder
  - [ ] Print Designer
  - [ ] Payments
  - [ ] Wiki
  - [ ] Twilio Integration
  - [ ] ERPNext Shipping

### Fonksiyonellik Testleri
- [ ] Yeni sayfa/modül açılıyor
- [ ] Veri oluşturma çalışıyor
- [ ] Arama çalışıyor
- [ ] Rapor oluşturma çalışıyor
- [ ] Dosya upload çalışıyor
- [ ] Real-time updates çalışıyor (WebSocket)

### Log Kontrolü
- [ ] Backend loglarında hata yok
- [ ] Frontend loglarında kritik hata yok
- [ ] Database loglarında hata yok
- [ ] Worker loglarında sorun yok

## ⚙️ İlk Yapılandırma

### Sistem Ayarları
- [ ] Setup Wizard tamamlandı
  - [ ] Şirket bilgileri girildi
  - [ ] Para birimi seçildi
  - [ ] Ülke/Bölge ayarlandı
  - [ ] Sektör bilgisi girildi
- [ ] Sistem timezone ayarlandı
- [ ] Dil tercihi yapıldı (Türkçe varsa)

### Email Ayarları
- [ ] Email Account oluşturuldu
- [ ] SMTP ayarları yapılandırıldı
- [ ] Test email gönderildi
- [ ] Email notifications aktif

### Kullanıcı Yönetimi
- [ ] Ek kullanıcılar oluşturuldu
- [ ] Roller atandı
- [ ] İzinler yapılandırıldı
- [ ] 2FA aktif edildi (önerilir)

### Güvenlik Ayarları
- [ ] Administrator şifresi değiştirildi (farklı bir şifre kullanıldı)
- [ ] Session timeout ayarlandı
- [ ] Password policy yapılandırıldı
- [ ] Login attempts limit ayarlandı

### Yedekleme
- [ ] Manuel backup test edildi
- [ ] Backup dosyaları erişilebilir
- [ ] Otomatik backup planlandı
- [ ] Backup saklama yeri belirlendi

## 📊 Monitoring & Maintenance

### Performans Kontrolü
- [ ] Sayfa yüklenme süreleri kabul edilebilir
- [ ] Database query performansı iyi
- [ ] Memory kullanımı normal seviyelerde
- [ ] CPU kullanımı normal seviyelerde
- [ ] Disk kullanımı izleniyor

### Monitoring Setup
- [ ] Dokploy metrics kontrol edildi
- [ ] Resource alerts yapılandırıldı
- [ ] Uptime monitoring ayarlandı (isteğe bağlı)
- [ ] Log aggregation yapılandırıldı (isteğe bağlı)

### Düzenli Bakım Planı
- [ ] Günlük backup schedule oluşturuldu
- [ ] Haftalık sistem kontrolü planlandı
- [ ] Aylık güncelleme schedule'ı belirlendi
- [ ] Kapasite planlaması yapıldı

## 🎯 Production Checklist (Ek)

### Güvenlik Sertleştirme
- [ ] Firewall kuralları uygulandı
- [ ] Gereksiz portlar kapatıldı
- [ ] SSH key-based authentication
- [ ] Fail2ban veya benzeri kuruldu
- [ ] SSL/TLS sertifikası doğrulandı
- [ ] Security headers yapılandırıldı

### Yedeklilik
- [ ] Off-site backup yapılandırıldı
- [ ] Disaster recovery planı oluşturuldu
- [ ] Backup restore test edildi
- [ ] Database replication planlandı (isteğe bağlı)

### Dokümantasyon
- [ ] Deployment bilgileri dokümante edildi
- [ ] Şifreler güvenli şekilde saklandı
- [ ] Acil durum kontakları belirlendi
- [ ] Runbook oluşturuldu

### Compliance & Legal
- [ ] GDPR/KVKK gereksinimleri kontrol edildi
- [ ] Veri saklama politikaları belirlendi
- [ ] Kullanım şartları hazırlandı
- [ ] Privacy policy oluşturuldu

## 📝 Notlar

### Deployment Bilgileri
```
Deployment Tarihi: _______________
Dokploy URL: _____________________
Site URL: ________________________
Versiyon: ________________________
Deployed By: _____________________
```

### Credentials (Güvenli yerde saklayın!)
```
Administrator Password: [PASSWORD_MANAGER]
Database Password: [PASSWORD_MANAGER]
Domain Registrar: ________________
SSL Provider: ____________________
Backup Location: _________________
```

### Önemli Linkler
- Dokploy Dashboard: _______________
- Site URL: ________________________
- GitHub Repo: https://github.com/ubden/frappe_docker
- Documentation: ___________________

### Sorun Giderme Notları
```
Karşılaşılan Sorunlar:
1. 
2. 
3. 

Çözümler:
1. 
2. 
3. 
```

## 🎉 Tamamlandı!

- [ ] Tüm checklist maddeleri tamamlandı
- [ ] Sistem production'a hazır
- [ ] Stakeholder'lar bilgilendirildi
- [ ] Go-live approval alındı

---

**Önemli**: Bu checklist'i her deployment için kullanın ve özel gereksinimlerinize göre güncelleyin.

**Son Güncelleme**: 2025-10-13  
**Versiyon**: 1.0.0

