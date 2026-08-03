# Frappe: от нуля до своего образа

Конспект по развёртыванию Frappe/ERPNext в Docker — dev-окружение и production-схема.
Версия фреймворка: **version-16**. Хост чистый, всё живёт в контейнерах.

---

## Из чего состоит стек

Прежде чем что-то запускать, полезно понимать, что вообще поднимается.

| Компонент | Что делает |
|---|---|
| **nginx** (frontend) | Отдаёт статику, проксирует остальное на backend |
| **gunicorn** (backend) | Обрабатывает HTTP-запросы, основное приложение |
| **socketio** (websocket) | Realtime — уведомления, обновления списков без перезагрузки |
| **worker** (queue-short/long) | Фоновые задачи из очереди |
| **scheduler** | Задачи по расписанию (ночные пересчёты, автоповторы) |
| **MariaDB** | Данные. У каждого сайта своя БД |
| **Redis** | Два инстанса: кэш и очередь задач |
| **sites/** | Файлы и конфиги сайтов |

Два ключевых понятия, которые надо развести:

- **apps/** — код. Общий для всего бенча, лежит на диске.
- **sites/** — данные. Своя БД у каждого сайта, свой список установленных приложений.

Поэтому приложение не «ставится в систему», а **устанавливается в конкретный сайт**.
Порядок всегда жёсткий: `bench` → `сайт` → `приложение`.

---

## Часть 1. Dev-окружение (devcontainer)

Здесь код лежит на хосте и монтируется в контейнер — правишь файл, сервер подхватывает
на лету. Для разработки.

### Подготовка

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

```bash
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
```

Папки `.devcontainer` в репозитории нет — она в `.gitignore`, чтобы каждый настраивал под
себя. Копируем из примера.

### Запуск контейнеров

```bash
docker compose -f .devcontainer/docker-compose.yml up -d
docker compose -f .devcontainer/docker-compose.yml exec frappe bash
```

Поднимутся четыре контейнера: `frappe` (bench CLI со всеми инструментами), `mariadb`,
`redis-cache`, `redis-queue`.

Важно: в контейнере `frappe` **ничего из Frappe ещё нет** — только утилита bench.
Фреймворк появится на следующем шаге.

С VS Code то же самое делается через расширение Dev Containers → «Reopen in Container».

### Создание бенча (внутри контейнера)

```bash
cd /workspace/development
bench init --skip-redis-config-generation --frappe-branch version-16 frappe-bench
cd frappe-bench
```

`frappe-bench` в конце — это имя каталога, который создастся. Аргумент обязательный.

`--skip-redis-config-generation` — не генерировать конфиги для локального Redis.
Без флага bench полезет за бинарником `redis-server` на этой машине и упадёт: Redis
у нас в соседних контейнерах.

### Настройка подключений

```bash
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
```

Флаг `-g` = global, пишет в `sites/common_site_config.json` — общий конфиг для всех
сайтов бенча. По умолчанию bench ищет БД на `localhost`, а она в контейнере с именем
`mariadb`. Без этих строк создание сайта упадёт с `Can't connect to server on '127.0.0.1'`.

Проверить, что записалось:

```bash
cat sites/common_site_config.json
```

### Создание сайта

```bash
bench new-site dev.localhost \
  --mariadb-user-host-login-scope='%' \
  --db-root-password 123 \
  --admin-password admin
```

`--mariadb-user-host-login-scope='%'` — с каких хостов пользователю БД разрешено
подключаться. В Docker сайт и БД — разные машины с точки зрения MariaDB, поэтому нужен
wildcard. Раньше это был флаг `--no-mariadb-socket`, сейчас он объявлен устаревшим.

`--db-root-password 123` — пароль root в MariaDB, зашит в devcontainer-конфиге.
Это **не** то, что вы придумываете.

`--admin-password admin` — а вот это уже ваш пароль для входа в веб-интерфейс
под пользователем `Administrator`.

### Финал

```bash
bench use dev.localhost
bench --site dev.localhost set-config developer_mode 1
bench start
```

`developer_mode 1` обязателен для разработки: без него DocType, созданные через UI,
пишутся только в БД и не попадают в файлы, а значит и в git.

`bench start` поднимает все процессы через honcho по `Procfile`. Сайт на `localhost:8000`.

### Установка приложений

```bash
bench get-app https://github.com/USER/REPO --branch ВЕТКА
ls apps/
bench --site dev.localhost install-app ИМЯ_ИЗ_LS
```

Имя приложения ≠ имя репозитория. Форк `habibi-erp` внутри бенча называется `erpnext` —
имя берётся из самого приложения. Всегда проверяйте через `ls apps/`.

Своё приложение с нуля:

```bash
bench new-app my_app
bench --site dev.localhost install-app my_app
```

---

## Часть 2. Production (свой образ)

Здесь код запечён в образ, контейнеры одноразовые, состояние только в томах.
Никакого `bench init` и `bench start`.

### apps.json

Создаётся вручную в корне `frappe_docker`, рядом с `compose.yaml`.
Перечисляем **всё кроме frappe** — фреймворк ставится всегда и задаётся отдельно.

```json
[
  {
    "url": "https://github.com/DHI-Partners/habibi-erp",
    "branch": "habibi-v16"
  },
  {
    "url": "https://github.com/DHI-Partners/saas_bridge",
    "branch": "version-16"
  }
]
```

Порядок важен: приложения ставятся сверху вниз, зависимости идут раньше.

Приватный репозиторий — токен прямо в URL:
`https://ghp_ТОКЕН@github.com/USER/REPO`

**Добавьте `apps.json` в `.gitignore`** до первого коммита.

### Сборка образа

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=habibi/apps.json \
  --tag=habibi:16 \
  --file=images/layered/Containerfile .
```

Точка в конце — контекст сборки, обязательна.

`--secret`, а не `--build-arg`: аргументы сборки навсегда видны в `docker image history`,
токен бы утёк. Секрет монтируется только на время сборки.

`images/layered/` собирает поверх готовых образов `frappe/base` и `frappe/build`
с Docker Hub — быстро, 5–15 минут. Есть ещё `images/custom/` (с нуля, дольше, но
контролируешь версии Python и Node) и `images/production/` (только frappe + erpnext,
apps.json не поддерживает).

Проверить, что попало внутрь:

```bash
docker images | grep habibi
docker run --rm habibi:16 ls apps
```

### Настройка .env

```bash
cp example.env .env
nano .env
```

Минимум, который нужно задать:

```dotenv
ERPNEXT_VERSION=v16.30.0
CUSTOM_IMAGE=habibi
CUSTOM_TAG=16
PULL_POLICY=never
DB_PASSWORD=123
HTTP_PUBLISH_PORT=8080
FRAPPE_SITE_NAME_HEADER=habibi.localhost
```

`CUSTOM_IMAGE` / `CUSTOM_TAG` / `PULL_POLICY` в `example.env` отсутствуют — дописываются
руками. `PULL_POLICY=never` обязателен, иначе Docker полезет искать ваш образ на Docker Hub.

`FRAPPE_SITE_NAME_HEADER` — какой сайт отдавать. По умолчанию nginx резолвит по хосту
запроса, и при заходе на `localhost:8080` будет искать сайт с таким именем.

### Запуск

```bash
alias dc='docker compose \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml'

dc up -d
dc ps
```

Базовый `compose.yaml` описывает только сервисы. Что подключать снаружи — задаётся
оверрайдами:

| Оверрайд | Зачем |
|---|---|
| `compose.mariadb.yaml` | Добавляет контейнер с БД |
| `compose.redis.yaml` | Добавляет два Redis |
| `compose.noproxy.yaml` | Публикует порт наружу напрямую |
| `compose.https.yaml` | Traefik + Let's Encrypt (для сервера) |
| `compose.proxy.yaml` | Traefik без HTTPS |

**Без оверрайда с прокси порт наружу не публикуется вообще** — контейнеры поднимутся,
но `curl` не достучится, а в `docker compose ps` у frontend будет пустая колонка PORTS.

`configurator` отработает и выйдет со статусом Exited — так и задумано. Он один раз
пропишет адреса БД и Redis в `common_site_config.json`, то есть сделает то, что в dev
мы делали руками через `bench set-config -g`.

### Создание сайта

```bash
dc exec backend bench new-site habibi.localhost \
  --mariadb-user-host-login-scope='%' \
  --db-root-password 123 \
  --admin-password admin \
  --install-app erpnext \
  --install-app saas_bridge
```

Сайт создаётся **после** запуска контейнеров, не при сборке.

```bash
dc exec backend bench --site habibi.localhost enable-scheduler
```

Открывается на `http://localhost:8080`, логин `Administrator`.

---

## Работа с форком ERPNext

Главное правило: **ветка форка должна соответствовать версии фреймворка**.
Форк от develop (v17) на version-16 не заведётся — упадёт на проверке зависимостей.

Посмотреть ветки, не клонируя:

```bash
git ls-remote --heads https://github.com/USER/REPO
git ls-remote --heads https://github.com/USER/REPO | grep version-16
```

Понять, что в форке своего, а что унаследовано от апстрима:

```bash
cd apps/erpnext
git fetch --unshallow upstream
git remote add erpnext https://github.com/frappe/erpnext.git
git fetch erpnext develop
git log --oneline upstream/develop --not erpnext/develop
```

Здесь `upstream` — ваш форк (bench называет remote именно так, освобождая `origin`),
а `erpnext` — оригинальный репозиторий, добавленный вручную. Названия сбивают с толку.

`--unshallow` нужен, потому что `bench init` клонирует с `--depth 1` — других веток
в локальной копии просто нет.

Отвести ветку от стабильной версии и перенести правки:

```bash
git checkout -b habibi-v16 erpnext/version-16
git cherry-pick ХЕШ1 ХЕШ2
git push upstream habibi-v16
```

Пуш обязателен: сборка образа тянет код с GitHub, локальные коммиты в контейнер не попадут.

### Стоит ли вообще форкать

Frappe спроектирован так, чтобы менять поведение ERPNext **из отдельного приложения**:
`hooks.py` умеет переопределять классы DocType, подменять whitelisted-методы, вешать
обработчики на события документов. Custom Field добавляет поля без правки кода.

Форк оправдан, когда правки лезут туда, куда хуками не дотянуться: SQL внутри отчётов,
`.js` формы ядра, изменение схемы стандартных DocType. В остальных случаях своё
приложение рядом с чистым ERPNext обновляется в разы дешевле.

---

## Русский язык

Переводы (`.mo` файлы) компилируются автоматически при сборке образа — в логах `get-app`
видны строки вида `MO file created at .../locale/ru/LC_MESSAGES/erpnext.mo`. Но из коробки
язык всё равно не появится: нужно создать записи Language и включить нужную.

### Три шага

```bash
# 1. Синхронизировать языки из frappe/geo/languages.json в БД сайта
dc exec backend bench --site SITE execute frappe.core.doctype.language.language.sync_languages

# 2. Включить нужный язык и выставить его по умолчанию
dc exec backend bench --site SITE console
```

```python
frappe.db.set_value("Language", "ru", "enabled", 1)
frappe.db.set_single_value("System Settings", "language", "ru")
frappe.db.set_value("User", "Administrator", "language", "ru")
frappe.db.commit()
exit()
```

```bash
# 3. Сбросить кэш и перезапустить
dc exec backend bench --site SITE clear-cache
dc restart backend frontend
```

Несколько языков сразу:

```python
for lang in ["ru", "en", "ar"]:
    frappe.db.set_value("Language", lang, "enabled", 1)
frappe.db.commit()
```

### Почему не работает с первого раза

Проблема трёхслойная, и каждый слой маскирует следующий:

| Слой | Симптом | Проверка |
|---|---|---|
| Нет записей Language | Список языков пуст | `frappe.db.count("Language")` — должно быть ~82 |
| Язык выключен | Языка нет в выпадающем списке | `frappe.db.get_value("Language", "ru", "enabled")` — должно быть 1 |
| Кэш | Настройки верные, интерфейс английский | Открыть сайт в инкогнито |

Frappe кэширует переводы **и на сервере, и в localStorage браузера**. Обычный Ctrl+Shift+R
localStorage не трогает — проверяйте в режиме инкогнито, иначе будете чинить то,
что уже починено.

Ещё одна ловушка: язык пользователя перебивает системный. Если в System Settings стоит `ru`,
а интерфейс английский — смотрите `frappe.db.get_value("User", "ИМЯ", "language")`.

### Про консоль

В IPython выводится результат **только последнего выражения**. Если вставить два запроса
подряд, увидите ответ лишь на второй — легко решить, что первый вернул пустоту.
Спрашивайте по одному.

### Что переведено

Ядро Frappe и ERPNext переведены прилично. Кастомные приложения (`saas_bridge`, ваши правки
в форке) останутся английскими, пока кто-то не наполнит их `.po` файлы.

---

## Шпаргалка

```bash
# состояние
dc ps
dc logs -f backend
dc logs --tail=30 frontend

# внутрь контейнера
dc exec backend bash
dc exec backend ls apps
dc exec backend cat sites/common_site_config.json

# сайты
dc exec backend bench list-sites
dc exec backend bench --site SITE migrate
dc exec backend bench --site SITE list-apps
dc exec backend bench --site SITE backup --with-files
dc exec backend bench --site SITE console

# остановка
dc down          # контейнеры, данные остаются
dc down -v       # вместе с томами — БД удалится

# проверка конфига до запуска
dc config | grep 'image:'
dc config | grep published
```

Обновление кода в production делается **не** через `bench update`, а пересборкой образа
с новым тегом и перезапуском.

---

## Грабли, на которые мы наступили

**`FileNotFoundError: 'uv'`** — свежие версии bench используют uv для создания venv.
Ставится через `pipx install uv` (в devcontainer уже есть).

**`redis-server: not found`** — забыт флаг `--skip-redis-config-generation` при `bench init`.

**`Can't connect to server on '127.0.0.1'`** — не задан `db_host`. Проверьте, что все
четыре `set-config -g` реально выполнились: при копипасте блока команд первая строка
часто теряется.

**`Remote branch X not found`** — ветки с таким именем в репозитории нет. Проверяйте
через `git ls-remote --heads` перед `get-app`.

**`does not satisfy required version '>=17.0.0-dev'`** — приложение собрано под develop,
а фреймворк стабильный. Либо меняем ветку приложения, либо переводим фреймворк на develop.

**`ls: cannot access '.devcontainer'`** — не сделан `cp -R devcontainer-example .devcontainer`,
либо папка уже существовала и копия легла внутрь неё.

**`invalid reference format` / `frappe/erpnext:`** — compose не видит `.env` или в нём
не заданы `CUSTOM_IMAGE` и `CUSTOM_TAG`.

**`No such image: habibi:16`** — образ не собран. `.env` уже ссылается на него,
а `docker build` ещё не запускался.

**Порт не отвечает, PORTS пустой** — не подключён `overrides/compose.noproxy.yaml`
(или другой оверрайд с прокси).

**Предупреждения от whoosh про `\w` и `\S`** — безобидные. Устаревший синтаксис регулярок
в стороннем пакете, в Python 3.14 он стал ругаться громче.

**`dc: unrecognized option '--site'`** — алиас потерялся при открытии нового терминала,
и подхватился системный `dc` (калькулятор из coreutils). Алиасы живут только в текущей
сессии — прописывайте в `~/.bashrc`.

**Русский язык не появляется** — см. раздел выше. Коротко: `sync_languages`, затем
`enabled = 1`, затем сброс кэша и проверка в инкогнито.

---

## Что дальше

Для деплоя на сервер:

1. `compose.noproxy.yaml` → `compose.https.yaml`
2. В `.env`: `SITES_RULE=Host(\`erp.example.com\`)` и `LETSENCRYPT_EMAIL`
3. Локальную сборку заменить на CI: GitHub Actions собирает образ теми же аргументами,
   пушит в registry с версионным тегом. На сервере только `docker compose pull && up -d`.
4. `PULL_POLICY=never` → `always`, `CUSTOM_IMAGE` — полный путь к registry.

Сервер при этом ничего не собирает: сборка ест RAM и CPU, требует git и токенов доступа.
Registry даёт воспроизводимость — в проде физически тот же образ, что прошёл тесты.
Откат сводится к смене `CUSTOM_TAG` на предыдущую версию.

Структура `compose.yaml` при этом не меняется вообще.
