#!/bin/bash

# Frappe ERPNext Dokploy Kurulum Scripti
# Bu script, Dokploy sunucusunda manuel kurulum için kullanılabilir

set -e

echo "==================================="
echo "Frappe ERPNext Dokploy Kurulumu"
echo "==================================="
echo ""

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Gerekli araçları kontrol et
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker kurulu değil. Lütfen Docker'ı kurun.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose kurulu değil. Lütfen Docker Compose'u kurun.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ Docker ve Docker Compose bulundu${NC}"
echo ""

# .env dosyası kontrolü
if [ ! -f .env ]; then
    echo -e "${YELLOW}! .env dosyası bulunamadı${NC}"
    echo "  .env.example dosyasından .env oluşturuluyor..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env dosyası oluşturuldu${NC}"
    echo ""
    echo -e "${YELLOW}ÖNEMLİ: .env dosyasını düzenleyerek ayarlarınızı yapılandırın!${NC}"
    echo "  Site adı: SITE_NAME"
    echo "  Admin şifresi: ADMIN_PASSWORD"
    echo "  Database şifresi: DB_PASSWORD"
    echo ""
    read -r -p "Devam etmek için .env dosyasını düzenleyin ve Enter'a basın..."
fi

# Ayarları yükle
# shellcheck source=/dev/null
source .env

echo "Kurulum Ayarları:"
echo "  Site Adı: ${SITE_NAME:-site1.localhost}"
echo "  HTTP Port: ${HTTP_PORT:-80}"
echo ""

# Onay al
read -r -p "Bu ayarlarla devam edilsin mi? (y/n) " -n 1
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Kurulum iptal edildi${NC}"
    exit 1
fi

echo ""
echo "==================================="
echo "Docker Image'i Build Ediliyor..."
echo "==================================="
echo ""

# Docker image build et
docker-compose build --no-cache

echo ""
echo -e "${GREEN}✓ Docker image başarıyla build edildi${NC}"
echo ""

echo "==================================="
echo "Container'lar Başlatılıyor..."
echo "==================================="
echo ""

# Container'ları başlat
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Container'lar başlatıldı${NC}"
echo ""

echo "==================================="
echo "Kurulum Bekleniyor..."
echo "==================================="
echo ""

# Site kurulumunun tamamlanmasını bekle (maksimum 10 dakika)
TIMEOUT=600
ELAPSED=0
INTERVAL=10

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    if docker-compose ps | grep -q "create-site.*Exit 0"; then
        echo -e "${GREEN}✓ Site kurulumu tamamlandı${NC}"
        break
    fi

    if docker-compose ps | grep -q "create-site.*Exit [^0]"; then
        echo -e "${RED}✗ Site kurulumu başarısız oldu${NC}"
        echo "Logları kontrol edin: docker-compose logs create-site"
        exit 1
    fi

    echo "Kurulum devam ediyor... ($ELAPSED/$TIMEOUT saniye)"
    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo -e "${YELLOW}! Kurulum zaman aşımına uğradı${NC}"
    echo "Manuel olarak kontrol edin: docker-compose logs create-site"
fi

echo ""
echo "==================================="
echo "Container Durumu"
echo "==================================="
echo ""

docker-compose ps

echo ""
echo "==================================="
echo "Kurulum Tamamlandı!"
echo "==================================="
echo ""
echo -e "${GREEN}Frappe ERPNext başarıyla kuruldu!${NC}"
echo ""
echo "Erişim Bilgileri:"
echo "  URL: http://localhost:${HTTP_PORT:-80}"
echo "  Kullanıcı: Administrator"
echo "  Şifre: ${ADMIN_PASSWORD:-admin}"
echo ""
echo "Yüklenen Uygulamalar:"
echo "  ✓ ERPNext"
echo "  ✓ CRM"
echo "  ✓ LMS"
echo "  ✓ Builder"
echo "  ✓ Print Designer"
echo "  ✓ Payments"
echo "  ✓ Wiki"
echo "  ✓ Twilio Integration"
echo "  ✓ ERPNext Shipping"
echo ""
echo "Yararlı Komutlar:"
echo "  Logları görüntüle: docker-compose logs -f"
echo "  Container'ları durdur: docker-compose down"
echo "  Container'ları başlat: docker-compose up -d"
echo "  Backup oluştur: docker-compose exec backend bench --site ${SITE_NAME:-site1.localhost} backup"
echo ""

