# Развёртывание Habibi на сервере

Разворачивание прод-стека с нуля: Frappe v16 + форк ERPNext + `saas_bridge`,
MariaDB, Redis, Traefik с Let's Encrypt. Локальная (dev) схема описана в
[frappe-setup.md](frappe-setup.md), здесь — только сервер.

## Что получилось

| | |
|---|---|
| Хост | Oracle Cloud, Ampere **ARM** (`aarch64`), Ubuntu, пользователь `ubuntu` |
| Домен | `erp.ayntayba.com`, DNS в Cloudflare, проксирование **выключено** |
| TLS | Let's Encrypt, http-01 challenge через Traefik |
| Образ | `habibi:16`, собирается **на сервере**, registry не используется |
| Приложения | `frappe`, `erpnext` (форк `DHI-Partners/habibi-erp`), `saas_bridge` |
| Данные | bind-mount в `/u01/frappe`, не в `/var/lib/docker/volumes` |
| Каталог | `~/habibi_docker` |

Сервисы: `proxy` (Traefik), `frontend` (nginx), `backend` (gunicorn),
`websocket`, `queue-short`, `queue-long`, `scheduler`, `db`, `redis-cache`,
`redis-queue`. Плюс два одноразовых: `configurator` и `migrator` — они
отрабатывают и выходят с кодом 0, это нормальный статус `Exited (0)`.

---

## 1. Docker

В репозиториях Ubuntu лежит устаревший docker без нужного compose v2, поэтому
ставим из официального репозитория:

```bash
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 \
  docker-doc docker-buildx podman-docker containerd runc | cut -f1)

sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER" && newgrp docker
docker compose version
```

## 2. Каталоги для данных

Состояние стека живёт на отдельном разделе `/u01`, а не внутри докера:

```bash
sudo mkdir -p /u01/frappe/{sites,logs,mariadb,redis,traefik}
sudo chown -R 1000:1000 /u01/frappe/{sites,logs}   # пользователь frappe в образе
sudo chown -R 999:999   /u01/frappe/{mariadb,redis} # mysql в mariadb, redis в redis
sudo chown -R 0:0       /u01/frappe/traefik         # traefik работает от root
sudo chmod 700          /u01/frappe/traefik         # в acme.json приватный ключ
```

UID числовые — они захардкожены в образах, пользователь хоста роли не играет.
Каталоги обязаны существовать **до** первого `up -d`: при `driver_opts: o: bind`
docker не создаёт `device` сам, контейнер падает с `no such file or directory`.

Отдельного каталога под бэкапы нет намеренно — см. «Грабли».

## 3. Репозиторий и конфиг

```bash
git clone https://github.com/DHI-Partners/habibi_docker.git ~/habibi_docker
cd ~/habibi_docker
cp prod.example.env .env
nano .env
```

Заполнить руками:

| Переменная | Значение |
|---|---|
| `DB_PASSWORD` | `openssl rand -base64 32`. **После создания сайта не меняется** — уходит в `site_config.json` |
| `LETSENCRYPT_EMAIL` | реальный ящик, туда придут письма об истечении сертификата |
| `SITES_RULE` | ``Host(`erp.ayntayba.com`)`` |
| `SITE_NAME` | `erp.ayntayba.com` — должно совпадать с доменом из `SITES_RULE` |
| `DATA_ROOT` | `/u01/frappe`, абсолютный путь |
| `PLATFORM` | `linux/arm64` на этом сервере, `linux/amd64` на x86 |
| `GUNICORN_WORKERS` | `(2 × vCPU) + 1`, каждый воркер ~400 МБ — сверить с `free -h` |

`COMPOSE_FILE` уже собран в шаблоне и определяет весь стек:

```
compose.yaml
overrides/compose.mariadb.yaml
overrides/compose.redis.yaml
overrides/compose.https.yaml
overrides/compose.migrator.yaml
overrides/compose.bindmounts.yaml
overrides/compose.platform.yaml
```

Порядок значим: `compose.platform.yaml` обязан идти **после**
`compose.migrator.yaml`, иначе у `migrator` останется `linux/amd64`.

`FRAPPE_SITE_NAME_HEADER` оставляем пустым — тогда nginx резолвит сайт по
заголовку `Host`, и имя сайта обязано совпадать с доменом.

## 4. Сборка образа

```bash
cd ~/habibi_docker
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=CACHE_BUST="$(date +%s)" \
  --secret=id=apps_json,src=apps.json \
  --tag=habibi:16 \
  --file=images/layered/Containerfile .
```

15–30 минут. Проверить, что приложения попали внутрь:

```bash
docker run --rm --entrypoint bash habibi:16 -lc 'ls -1 apps'
# erpnext
# frappe
# saas_bridge
```

Имена из этого вывода идут в `--install-app` при создании сайта. Форк
`habibi-erp` встаёт как `erpnext` — так называется приложение в его `hooks.py`.

`CACHE_BUST` обязателен при **каждой** пересборке: `apps.json` передаётся
секретом, а секреты не входят в ключ кэша слоя. Без него docker переиспользует
старый слой `bench init`, и новые коммиты приложений в образ не попадут.

Репозитории приложений публичные, поэтому токен не нужен. Если станут
приватными — подставить его в URL во временный файл и скормить как секрет:

```bash
umask 077
sed "s|https://github.com/|https://x-access-token:${PAT}@github.com/|" apps.json > /tmp/apps.json
docker build ... --secret=id=apps_json,src=/tmp/apps.json ...
rm -f /tmp/apps.json
```

Через `--build-arg` токен передавать нельзя — build-args навсегда остаются
в `docker image history`.

## 5. DNS

В Cloudflare: `A`-запись `erp` → IP сервера, **Proxy status = DNS only**
(серое облако).

```bash
getent ahostsv4 erp.ayntayba.com   # должен вернуть IP сервера, не 104.*/172.67.*
```

Оранжевое облако ломает выпуск сертификата: Let's Encrypt при http-01 стучится
в Cloudflare, а не на сервер. Включить проксирование можно **после** выпуска,
одновременно выставив SSL/TLS mode = **Full (strict)** — иначе редирект-петля.

## 6. Firewall

Два независимых фильтра, нужны оба.

**iptables на машине.** В Oracle-образах открыт только 22, а в конце цепочки
стоит `REJECT` — правила надо вставлять **перед** ним:

```bash
sudo iptables -L INPUT -n --line-numbers    # найти номер строки с REJECT
sudo iptables -I INPUT 5 -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
sudo iptables -L INPUT -n --line-numbers    # 80 и 443 выше REJECT
```

**Security List в облаке.** Консоль Oracle → Networking → VCN → Security Lists
→ Add Ingress Rules: `0.0.0.0/0`, TCP, порты `80` и `443`. Без этого пакеты не
доходят до машины вообще и iptables ни при чём.

## 7. Запуск

```bash
cd ~/habibi_docker
docker compose config >/dev/null && echo "config ok"   # все переменные подставились
docker compose up -d
docker compose ps
```

`COMPOSE_FILE` берётся из `.env`, флаги `-f` не нужны.

Ожидаемое состояние: `db` — `Up (healthy)`, `configurator` и `migrator` —
`Exited (0)`, остальные `Up`. В `/u01/frappe/sites/` должны появиться только
`apps.txt` и `common_site_config.json`.

## 8. Создание сайта

```bash
docker compose exec backend bench new-site erp.ayntayba.com \
  --mariadb-user-host-login-scope='%' \
  --db-root-password "$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" \
  --admin-password '<сильный-пароль>' \
  --install-app erpnext \
  --install-app saas_bridge

docker compose exec backend bench --site erp.ayntayba.com enable-scheduler
```

`--mariadb-user-host-login-scope='%'` обязателен. Без него пользователь БД
привязывается к текущему IP контейнера, и после любого пересоздания сети
(`docker compose down && up`) подсеть меняется, а сайт отваливается с
`Access denied for user '_xxxx'@'172.18.0.11'`.

## 9. Проверка

```bash
curl -sI https://erp.ayntayba.com/ | head -1              # HTTP/2 200
curl -s https://erp.ayntayba.com/api/method/frappe.ping   # {"message":"pong"}
docker compose logs proxy | grep -i acme                  # выдача сертификата
ls -la /u01/frappe/sites/erp.ayntayba.com/                # данные на диске
```

Сертификат снаружи:

```bash
openssl s_client -connect erp.ayntayba.com:443 -servername erp.ayntayba.com </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
```

---

## Обновление

Приложения обновляются пересборкой образа — исходники лежат внутри него, а не
на диске:

```bash
cd ~/habibi_docker
git pull                                     # если менялись compose-файлы

docker compose exec backend bench --site all backup   # перед миграцией

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=CACHE_BUST="$(date +%s)" \
  --secret=id=apps_json,src=apps.json \
  --tag=habibi:16 \
  --file=images/layered/Containerfile .

docker compose up -d --force-recreate migrator   # прогнать миграции
docker compose logs -f migrator                  # дождаться Exited (0)
docker compose up -d
docker compose ps
```

`--force-recreate` для `migrator` нужен потому, что это одноразовый контейнер:
если ID образа не изменился, обычный `up -d` его не перезапустит и миграции
молча не выполнятся.

Тег `habibi:16` перезаписывается на месте, отдельных версий нет — откатиться
можно только пересборкой из старого коммита приложений. Если это станет нужно
регулярно — переходить на GHCR с тегами по SHA (вариант Б в `prod.example.env`).

## Бэкапы

`bench backup` кладёт дампы в `sites/<site>/private/backups`, то есть в
`/u01/frappe/sites/erp.ayntayba.com/private/backups` — на диске они уже есть.

```bash
docker compose exec backend bench --site all backup             # только БД
docker compose exec backend bench --site all backup --with-files # + вложения
```

Автоматизация — `overrides/compose.backup-cron.yaml` (ofelia, по умолчанию
каждые 6 часов, интервал в `BACKUP_CRONSTRING`). Добавляется в `COMPOSE_FILE`.
Вывоз дампов за пределы сервера не настроен.

## Логи

```bash
docker compose logs -f backend        # stdout контейнера
ls /u01/frappe/logs/                  # логи bench: web, worker, schedule
docker compose logs frontend          # nginx пишет в stdout, не в logs/
```

---

## Грабли

Всё перечисленное реально стреляло при первом развёртывании.

**ARM-хост против `platform: linux/amd64`.** В `compose.yaml` у всех сервисов
захардкожена amd64. На Ampere образ собирается нативно под arm64, и `up -d`
падает с `image with reference habibi:16 was found but does not provide the
specified platform (linux/amd64)`. Лечится оверрайдом
[compose.platform.yaml](overrides/compose.platform.yaml) и `PLATFORM=linux/arm64`.

**Cloudflare с оранжевым облаком.** Домен резолвится в адреса Cloudflare,
http-01 challenge не доходит до сервера, Traefik долбит ACME и упирается в
rate limit (5 неудач в час на домен). Выпускать сертификат при `DNS only`.

**Правила iptables после `REJECT`.** `iptables -I INPUT 6` при `REJECT` на
позиции 5 вставляет правило ниже него — оно мертво, хотя в выводе выглядит
добавленным. Смотреть на порядок, а не на факт наличия.

**Bind-mount каталога `backups`.** Монтирование `${DATA_ROOT}/backups` в
`sites/<site>/private/backups` заставляет docker создать промежуточные
`sites/<site>/private` **от root** ещё до создания сайта. `bench new-site`
видит существующий каталог и отказывается: `Site already exists`. Поэтому
отдельного тома под бэкапы нет — они и так на диске внутри `sites/`.

**Смена тома с обычного на bind.** Работает только пока том пуст. Если стек
уже поднимался, docker молча игнорирует новые `driver_opts`, и данные остаются
в `/var/lib/docker/volumes`. Решать до `bench new-site`.

**`COMPOSE_FILE` в `.env`.** Без неё `docker compose` видит только базовый
`compose.yaml` и при `up -d --remove-orphans` сносит db, redis и proxy как
лишние.

**`.env` нигде не хранится.** Он в `.gitignore`, на сервере собран руками.
Шаблон — [prod.example.env](prod.example.env); реальные значения `DB_PASSWORD`
и пароля администратора держать в менеджере паролей.

## Что не сделано

- **CI/CD.** Сборка и деплой руками. Автоматизация требует воркфлоу с пушем
  образа в GHCR и деплой-скриптом на сервере — в репозитории их сейчас нет.
- **Мониторинг и алерты.** Ни аптайма, ни уведомлений об истечении сертификата
  (кроме писем Let's Encrypt на `LETSENCRYPT_EMAIL`).
- **Вывоз бэкапов с сервера.** Дампы лежат на том же диске, что и база.
- **Реальный IP клиента за Cloudflare.** Если включить проксирование, в
  `X-Forwarded-For` будут адреса Cloudflare; настоящий IP приходит в
  `CF-Connecting-IP` и требует отдельной настройки nginx.
