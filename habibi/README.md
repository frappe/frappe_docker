# habibi/

Всё, что добавлено поверх апстрима [frappe/frappe_docker](https://github.com/frappe/frappe_docker),
лежит здесь. Остальные файлы репозитория — апстримные, их не трогаем, чтобы
`git pull` из апстрима проходил без конфликтов.

| Файл | Что это |
|---|---|
| [prod-deploy.md](prod-deploy.md) | рунбук развёртывания на сервере: с нуля до работающего `https://erp.ayntayba.com` |
| [dev-setup.md](dev-setup.md) | локальная разработка: bench, форк ERPNext, сборка образа |
| [prod.example.env](prod.example.env) | шаблон серверного `.env`; копируется в корень репозитория как `.env` |
| [overrides/compose.bindmounts.yaml](overrides/compose.bindmounts.yaml) | данные стека в каталоги хоста (`DATA_ROOT`) вместо `/var/lib/docker/volumes` |
| [overrides/compose.platform.yaml](overrides/compose.platform.yaml) | снимает захардкоженный `platform: linux/amd64`; нужен на ARM |

Наши оверрайды подключаются в `COMPOSE_FILE` вместе с апстримными, с префиксом
`habibi/`:

```
COMPOSE_FILE=compose.yaml:overrides/compose.mariadb.yaml:...:habibi/overrides/compose.platform.yaml
```

Относительные пути внутри compose-файлов резолвятся от корня проекта, а не от
каталога самого файла, поэтому перенос в `habibi/` на них не влияет. Оба наших
оверрайда и так используют абсолютные пути через `${DATA_ROOT}`.

Вне этого каталога нами добавлен только `apps.json` в корне — он остаётся там,
потому что путь к нему зашит в команду сборки (`--secret=id=apps_json,src=apps.json`)
и в апстримную документацию.
