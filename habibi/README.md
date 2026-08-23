# habibi/

Всё, что Добавлено Поверх апстрима [frappe/frappe_docker](https://github.com/frappe/frappe_docker),
лежит здесь. Остальные файлы репозитория — апстримные, их не трогаем, чтобы
`git pull` из апстрима проходил без конфликтов.

| Файл                                                                           | Что это                                                                           |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| [prod-deploy.md](prod-deploy.md)                                               | рунбук развёртывания на сервере: с нуля до работающего `https://erp.ayntayba.com` |
| [dev-setup.md](dev-setup.md)                                                   | локальная разработка: bench, кастомные приложения, сборка образа                  |
| [i18n-ru.md](i18n-ru.md)                                                       | русская локализация: слои перевода, что чинить где, журнал проверок               |
| [prod.example.env](prod.example.env)                                           | шаблон серверного `.env`; копируется в корень репозитория как `.env`              |
| [apps.json](apps.json)                                                         | список приложений для сборки образа; передаётся в build как BuildKit-секрет       |
| [build.sh](build.sh)                                                           | ручная сборка образа, когда до registry не дотянуться                             |
| [overrides/compose.bindmounts.yaml](overrides/compose.bindmounts.yaml)         | данные стека в каталоги хоста (`DATA_ROOT`) вместо `/var/lib/docker/volumes`      |
| [overrides/compose.platform.yaml](overrides/compose.platform.yaml)             | снимает захардкоженный `platform: linux/amd64`; нужен на ARM                      |
| [overrides/compose.backup-offsite.yaml](overrides/compose.backup-offsite.yaml) | вывоз бэкапов с сервера через rclone                                              |
| [overrides/compose.appmount.yaml](overrides/compose.appmount.yaml)             | подмена кода приложения рабочей копией с хоста; только для разработки             |

Вне этого каталога наш только `.github/workflows/habibi-image.yml` — сборка
образа в CI. Он обязан лежать в `.github/`, туда его требует GitHub.

## Как собирается образ

Штатно — в CI. Воркфлоу `habibi-image.yml` собирает layered-образ из
[apps.json](apps.json) и пушит в `ghcr.io` двумя тегами: скользящим `:16`
и неизменяемым `:16-<hash>`, где hash считается из фактических SHA всех
приложений. В `.env` на сервере держите **версионный** тег — тогда откат
это правка одной строки, а не пересборка.

Сервер ничего не собирает: сборка ест RAM и CPU боевой машины и требует
на ней git и доступа к репозиториям. Ручная сборка через [build.sh](build.sh)
остаётся на случай, когда до registry не дотянуться.

## Про ERPNext

Собираем **чистый** `frappe/erpnext`. Форка нет: всё, ради чего он
существовал (подписи «ERPNext» и «ERPNext Settings» в интерфейсе), живёт
в `habibi_core` записями Translation — эти строки уходят на экран через
функцию перевода, и подменяются без единой правки в ERPNext.

Правило прежнее: любые доработки — из своего приложения через `hooks.py`.
Форк оправдан только там, куда хуками не дотянуться: SQL внутри отчётов,
`.js` формы ядра, изменение схемы стандартных DocType.

## Подключение оверрайдов

Наши оверрайды подключаются в `COMPOSE_FILE` вместе с апстримными,
с префиксом `habibi/`:

```
COMPOSE_FILE=compose.yaml:overrides/compose.mariadb.yaml:...:habibi/overrides/compose.platform.yaml
```

Порядок значим:

- `compose.platform.yaml` — **после** `compose.migrator.yaml`, иначе у
  `migrator` останется `linux/amd64`;
- `compose.backup-offsite.yaml` — **после** `compose.backup-cron.yaml`,
  сервис `cron` (ofelia) определён там.

Относительные пути внутри compose-файлов резолвятся от корня проекта, а не
от каталога самого файла, поэтому расположение в `habibi/` на них не влияет.

Единственный файл `.env` живёт в корне репозитория: `docker compose` читает
его только оттуда, из каталога проекта. Он в `.gitignore`, шаблон — здесь.
`apps.json` копировать в корень не нужно: `--secret` читает файл по
произвольному пути, в командах сборки указывается `habibi/apps.json`.
