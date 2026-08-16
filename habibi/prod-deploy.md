# Развёртывание Habibi на сервере

Разворачивание прод-стека с нуля: Frappe v16 + ERPNext + `saas_bridge`,
MariaDB, Redis, Traefik с Let's Encrypt. Локальная (dev) схема описана в
[dev-setup.md](dev-setup.md), здесь — только сервер.

## Что получилось

|            |                                                                                       |
| ---------- | ------------------------------------------------------------------------------------- |
| Хост       | Oracle Cloud, Ampere **ARM** (`aarch64`), Ubuntu, пользователь `ubuntu`               |
| Домен      | `habibi-erp.com`, регистратор Dynadot, зона в Cloudflare, проксирование **выключено** |
| Сайты      | поддомен на клиента (`erp.`, `client1.`…) по wildcard-записи `*`                      |
| TLS        | Let's Encrypt, один wildcard `*.habibi-erp.com`, dns-01 через API Cloudflare          |
| Образ      | `ghcr.io/dhi-partners/habibi`, собирается **в CI**, на сервер приезжает готовым       |
| Приложения | `frappe`, `erpnext` (чистый апстрим), `habibi_core`, `saas_bridge`, `habibi_telegram` |
| Данные     | bind-mount в `/u01/frappe`, не в `/var/lib/docker/volumes`                            |
| Каталог    | `~/habibi_docker`                                                                     |

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
cp habibi/prod.example.env .env
nano .env
```

Заполнить руками:

| Переменная          | Значение                                                                                      |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `DB_PASSWORD`       | `openssl rand -base64 32`. **После создания сайта не меняется** — уходит в `site_config.json` |
| `LETSENCRYPT_EMAIL` | реальный ящик, туда придут письма об истечении сертификата                                    |
| `CF_DNS_API_TOKEN`  | токен Cloudflare с правами Zone:DNS:Edit на зону — см. раздел «5. DNS»                        |
| `BASE_DOMAIN`       | `habibi-erp.com`, без поддомена — из него строится имя wildcard-сертификата                   |
| `SITES_RULE`        | ``HostRegexp(`^[a-z0-9-]+\.habibi-erp\.com$`)`` — правится только при смене домена            |
| `SITE_NAME`         | `erp.habibi-erp.com` — полный домен, обязан попадать под `SITES_RULE`                          |
| `DATA_ROOT`         | `/u01/frappe`, абсолютный путь                                                                |
| `PLATFORM`          | `linux/arm64` на этом сервере, `linux/amd64` на x86                                           |
| `GUNICORN_WORKERS`  | `(2 × vCPU) + 1`, каждый воркер ~400 МБ — сверить с `free -h`                                 |

`COMPOSE_FILE` уже собран в шаблоне и определяет весь стек:

```
compose.yaml
overrides/compose.mariadb.yaml
overrides/compose.redis.yaml
overrides/compose.https.yaml
overrides/compose.migrator.yaml
habibi/overrides/compose.bindmounts.yaml
habibi/overrides/compose.platform.yaml
habibi/overrides/compose.wildcard-tls.yaml
```

Порядок значим: `compose.platform.yaml` обязан идти **после**
`compose.migrator.yaml`, иначе у `migrator` останется `linux/amd64`;
`compose.wildcard-tls.yaml` — **после** `compose.https.yaml`, иначе резолвер
Let's Encrypt останется на http-01 и wildcard не выпустится.

`FRAPPE_SITE_NAME_HEADER` оставляем пустым — тогда nginx резолвит сайт по
заголовку `Host`, и имя сайта обязано совпадать с доменом.

## 4. Образ

Сервер образ **не собирает**. Его собирает CI — воркфлоу
`.github/workflows/habibi-image.yml` — и пушит в `ghcr.io` двумя тегами:

- `:16` — скользящий, всегда последний;
- `:16-<hash>` — неизменяемый, hash из фактических SHA всех приложений
  из [apps.json](apps.json).

В `.env` держим **версионный** тег. Он и есть механизм отката: вернуться
на предыдущий код — это правка `CUSTOM_TAG` и `docker compose up -d`.
Со скользящим `:16` возврата нет, тег уже перезаписан.

Хеш берётся из вывода воркфлоу, шаг «Итоговые теги». Список доступных:

```bash
docker image ls ghcr.io/dhi-partners/habibi          # локально скачанные
gh api /orgs/DHI-Partners/packages/container/habibi/versions \
  --jq '.[].metadata.container.tags[]' | head -20     # все в registry
```

Забрать и проверить состав:

```bash
cd ~/habibi_docker
docker compose pull backend
docker compose run --rm --entrypoint bash backend -lc 'ls -1 apps'
# erpnext
# frappe
# habibi_core
# habibi_telegram
# saas_bridge
```

Имена из этого вывода идут в `--install-app` при создании сайта. Они берутся
из `hooks.py` самих приложений и не обязаны совпадать с именами репозиториев —
поэтому список смотрим через `ls -1 apps`, а не по `apps.json`.

Приватные репозитории приложений: положить готовый `apps.json` с токеном
в секрет `APPS_JSON` репозитория на GitHub. Воркфлоу подставит его вместо
версии из git и передаст дальше BuildKit-секретом, так что в слои образа
токен не попадёт. Через `--build-arg` его передавать нельзя — build-args
навсегда остаются в `docker image history`.

**Если до registry не дотянуться** — сборка на месте:

```bash
habibi/build.sh
```

Скрипт считает `CACHE_BUST` из SHA приложений сам. Он обязателен при каждой
пересборке: `apps.json` передаётся секретом, а секреты не входят в ключ кэша
слоя, и без него docker переиспользует старый слой `bench init` — сборка
пройдёт «успешно» со старым кодом. В `.env` тогда вариант Б: `CUSTOM_IMAGE=habibi`,
`PULL_POLICY=never`.

## 5. DNS и wildcard-сертификат

Домен `habibi-erp.com` зарегистрирован в **Dynadot**, но зону обслуживает
**Cloudflare**: NS-серверы переключены на него в Dynadot (My Domains → домен →
Name Servers). Регистратор остаётся Dynadot, продление домена там же.

Cloudflare здесь не ради CDN, а потому что wildcard-сертификат Let's Encrypt
выдаёт **только по dns-01**, и Traefik должен уметь класть TXT-запись в зону
через API. У Dynadot такого провайдера в lego нет — на нём wildcard недоступен
в принципе.

Записи в зоне:

| Имя | Тип | Значение | Proxy |
| --- | --- | --- | --- |
| `@` | A | `216.198.79.1` | DNS only |
| `www` | CNAME | `…vercel-dns-017.com` | DNS only |
| `*` | A | IP сервера | DNS only |

Апекс и `www` держат лендинг на Vercel и остаются нетронутыми: **wildcard не
перебивает явные записи**, поэтому лендинг и ERP живут на одном домене. Все
поддомены первого уровня уходят на сервер, и заводить DNS на каждого клиента
не нужно — это единственная запись на всю мультитенантность.

```bash
dig +short zzz-test.habibi-erp.com   # любое несуществующее имя -> IP сервера
```

**Токен для dns-01.** Cloudflare → My Profile → API Tokens → Create Token →
шаблон **Edit zone DNS**, в Zone Resources выбрать только `habibi-erp.com`.
Полученную строку в `.env` как `CF_DNS_API_TOKEN`. Токен нужен Traefik только
на выпуск и продление, то есть примерно раз в 60 дней.

Проверка, что сертификат именно wildcard:

```bash
echo | openssl s_client -connect erp.habibi-erp.com:443 -servername erp.habibi-erp.com 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName
# subject=CN=*.habibi-erp.com
```

Серое облако (**DNS only**) обязательно на этапе настройки. С dns-01 оранжевое
облако сертификату больше не мешает — в отличие от http-01 — но включать его
можно только вместе с SSL/TLS mode = **Full (strict)**, иначе редирект-петля.
Для записей Vercel проксирование не включать.

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
docker compose exec backend bench new-site erp.habibi-erp.com \
  --mariadb-user-host-login-scope='%' \
  --db-root-password "$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" \
  --admin-password '<сильный-пароль>' \
  --install-app erpnext \
  --install-app habibi_core \
  --install-app saas_bridge \
  --install-app habibi_telegram

docker compose exec backend bench --site erp.habibi-erp.com migrate
docker compose exec backend bench --site erp.habibi-erp.com enable-scheduler
```

`--mariadb-user-host-login-scope='%'` обязателен. Без него пользователь БД
привязывается к текущему IP контейнера, и после любого пересоздания сети
(`docker compose down && up`) подсеть меняется, а сайт отваливается с
`Access denied for user '_xxxx'@'172.18.0.11'`.

`bench migrate` после создания сайта нужен: `install-app` не всегда синхронизирует
DocType'ы свежепоставленного приложения, и таблицы появляются только на миграции.

### Ещё один клиент

Той же командой с другим именем — и всё:

```bash
docker compose exec backend bench new-site client1.habibi-erp.com \
  --mariadb-user-host-login-scope='%' \
  --db-root-password "$(grep '^DB_PASSWORD=' .env | cut -d= -f2-)" \
  --admin-password '<сильный-пароль>' \
  --install-app erpnext --install-app habibi_core

docker compose exec backend bench --site client1.habibi-erp.com migrate
```

Ни DNS, ни `.env`, ни рестарт стека не трогаются: имя попадает под wildcard
`*.habibi-erp.com` в DNS, под `SITES_RULE` в Traefik и под wildcard-сертификат,
а nginx находит сайт по каталогу в `sites/`. Именно ради этого стоит
`compose.wildcard-tls.yaml` — со штатным `Host(...)` каждый клиент требовал бы
правки `.env` и пересоздания `frontend`.

Ограничение одно: имя — **один** уровень из `[a-z0-9-]`. `a.b.habibi-erp.com`
не заработает, сертификата на второй уровень нет.

Свой домен клиента (`erp.clientcorp.com`) сюда не попадает — wildcard его не
покрывает. Под такой случай понадобится отдельный роутер с http-01; проще
всего через file provider Traefik, чтобы не перезапускать стек. Пока таких
клиентов нет, это не сделано.

### Переезд на другой домен

Имя каталога в `sites/` обязано совпадать с доменом, поэтому переезд — это
переименование каталога. Имя базы лежит в `site_config.json` и от каталога не
зависит, так что данные остаются на месте:

```bash
cd ~/habibi_docker
docker compose exec -T backend bench --site all backup    # до всего остального
docker compose down

sudo mv /u01/frappe/sites/erp.ayntayba.com /u01/frappe/sites/erp.habibi-erp.com
sudo sed -i 's/erp\.ayntayba\.com/erp.habibi-erp.com/' /u01/frappe/sites/currentsite.txt

nano .env        # SITE_NAME, BASE_DOMAIN, SITES_RULE, CF_DNS_API_TOKEN
docker compose config >/dev/null && echo "config ok"
docker compose up -d
```

Проверить `site_config.json` на ключ `host_name` — если он там есть, поправить
тоже. Сертификат Traefik закажет заново сам, старый в `acme.json` просто
перестанет использоваться; чистить том `cert-data` не нужно.

Отдельно, вне стека: перерегистрировать вебхуки Telegram и WhatsApp на новый
домен (см. раздел 9), проверить Website Settings и System Settings на
захардкоженный старый URL и `redirect_uri` в интеграциях OAuth.

## 9. Телеграм-бот

Делается **после** выпуска сертификата: Telegram регистрирует вебхук только на
публичном https-адресе и проверяет цепочку сертификатов сам.

1. Взять токен у [@BotFather](https://t.me/BotFather).
2. В Desk завести **Telegram Bot**, вставить токен, сохранить. Токен проверяется
   через `getMe`, оттуда же подтянется username.
3. Нажать **Set Webhook**.

Из консоли то же самое:

```bash
docker compose exec backend bench --site erp.habibi-erp.com telegram list-bots
docker compose exec backend bench --site erp.habibi-erp.com telegram set-webhook <имя-бота>
docker compose exec backend bench --site erp.habibi-erp.com telegram webhook-info <имя-бота>
```

Адрес вебхука собирается из имени сайта, отдельно домен нигде не настраивается:

```
https://erp.habibi-erp.com/api/method/habibi_telegram.api.webhook?bot=<имя-бота>
```

Это работает потому, что имя сайта здесь и есть домен — `FRAPPE_SITE_NAME_HEADER`
пуст, и nginx резолвит сайт по заголовку `Host`. Схема всегда `https`: TLS
терминируется на Traefik, сам frappe видит только http. Если сайт и домен когда-то
разойдутся — адрес переопределяется через `host_name` в `site_config.json`.

Если бот молчит — сначала `telegram webhook-info`: там видно, что о вебхуке
думает сам Telegram, включая `last_error_message` и число зависших апдейтов.

## 10. Проверка

```bash
curl -sI https://erp.habibi-erp.com/ | head -1              # HTTP/2 200
curl -s https://erp.habibi-erp.com/api/method/frappe.ping   # {"message":"pong"}
docker compose logs proxy | grep -i acme                  # выдача сертификата
ls -la /u01/frappe/sites/erp.habibi-erp.com/                # данные на диске
```

Сертификат снаружи:

```bash
openssl s_client -connect erp.habibi-erp.com:443 -servername erp.habibi-erp.com </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
```

---

## Обновление

Приложения обновляются сменой образа — исходники лежат внутри него, а не
на диске. Сборку сделал CI, на сервере остаётся забрать и мигрировать:

```bash
cd ~/habibi_docker
git pull                                     # если менялись compose-файлы

docker compose exec backend bench --site all backup --with-files   # перед миграцией

nano .env                                    # CUSTOM_TAG=16-<новый hash>
docker compose pull

docker compose up -d --force-recreate migrator   # прогнать миграции
docker compose logs -f migrator                  # дождаться Exited (0)
docker compose up -d
docker compose ps
```

`--force-recreate` для `migrator` нужен потому, что это одноразовый контейнер:
если ID образа не изменился, обычный `up -d` его не перезапустит и миграции
молча не выполнятся.

### Откат

```bash
nano .env                                    # CUSTOM_TAG=16-<предыдущий hash>
docker compose pull
docker compose up -d
```

Важно понимать границы: это откат **кода**, не данных. `bench migrate` уже
изменил схему базы, и обратной миграции у Frappe нет. Если новая версия
успела поменять схему несовместимо — поднимать базу из дампа, снятого перед
обновлением. Поэтому строка с `backup --with-files` выше не факультативная.

### Новое приложение на живом сайте

Пересборка выше кладёт приложение в образ, но на существующий сайт его не
ставит — это отдельный шаг после `up -d`:

```bash
docker compose run --rm --entrypoint bash backend -lc 'ls -1 apps'   # приложение в образе?
docker compose exec backend bench --site erp.habibi-erp.com install-app <приложение>
docker compose exec backend bench --site erp.habibi-erp.com migrate
docker compose exec backend bench --site erp.habibi-erp.com list-apps
```

Порядок важен: `install-app` обязан выполняться уже в пересозданном `backend`.
Пока `up -d` не подменил контейнер, внутри старый образ, где приложения нет, и
команда упадёт с `App not found`.

## Бэкапы

`bench backup` кладёт дампы в `sites/<site>/private/backups`, то есть в
`/u01/frappe/sites/erp.habibi-erp.com/private/backups`.

```bash
docker compose exec backend bench --site all backup             # только БД
docker compose exec backend bench --site all backup --with-files # + вложения
```

По расписанию — `overrides/compose.backup-cron.yaml` (ofelia, интервал
в `BACKUP_CRONSTRING`, по умолчанию 6 часов). Уже включён в `COMPOSE_FILE`
шаблона.

**Локальных копий хватает примерно на сутки.** Ежечасная задача Frappe
`delete_downloadable_backups` оставляет последние `backup_limit` штук —
это System Settings, по умолчанию 3. При интервале 6 часов история
получается около 18 часов, и лежит она на том же диске, что и база.

Поэтому вывоз обязателен: `habibi/overrides/compose.backup-offsite.yaml`,
rclone по расписанию `OFFSITE_CRONSTRING`. Настройка — в шапке файла,
проверка вручную:

```bash
docker compose run --rm backup-offsite
rclone ls "$RCLONE_REMOTE" | tail            # что реально доехало
```

Раз в месяц полезно проверять не наличие файла, а **восстановимость**:
поднять дамп на отдельном сайте и открыть его. Бэкап, который никто
не разворачивал, — это предположение, а не бэкап.

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

- **Автодеплой.** Образ собирается в CI, но на сервер накатывается руками:
  правка `CUSTOM_TAG`, `pull`, `up -d`. Это осознанно — миграции Frappe
  необратимы, и шаг с бэкапом перед ними стоит держать под присмотром.
- **Мониторинг и алерты.** Ни аптайма, ни уведомлений об истечении сертификата
  (кроме писем Let's Encrypt на `LETSENCRYPT_EMAIL`).
- **Проверка восстановимости бэкапов.** Вывоз настроен, регулярного
  тестового восстановления нет.
- **Реальный IP клиента за Cloudflare.** Если включить проксирование, в
  `X-Forwarded-For` будут адреса Cloudflare; настоящий IP приходит в
  `CF-Connecting-IP` и требует отдельной настройки nginx.
