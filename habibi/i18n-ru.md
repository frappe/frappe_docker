# Русская локализация Habibi (Frappe v16 / ERPNext v16)

Рабочий справочник: почему часть интерфейса остаётся на английском при
русском языке пользователя, какие есть слои перевода, что чинить где.
Файл живой — по мере проверок дописываем «Журнал проверок» внизу.

## Коротко

Строка показывается по-русски, только если выполнены **оба** условия:

1. код прогоняет её через `__()` (JS) / `_()` (Python);
2. для неё есть перевод в словаре языка сессии.

Почти всё в desk через `__()` проходит — включая заголовки виджетов
дашборда (`frappe/public/js/frappe/widgets/base_widget.js`, `set_title()`
рендерит `${__(title)}`). Значит проблема почти всегда во втором пункте:
**перевода просто нет в апстриме**.

Масштаб (замерено на `version-16`, 2026-08-23):

| каталог | записей | без перевода |
| ------- | ------- | ------------ |
| `frappe/locale/ru.po`  | 6201  | 215 (3%)   |
| `erpnext/locale/ru.po` | 10075 | 1331 (13%) |

Плюс отдельный класс строк, которых в каталогах **нет вообще** — имена
документов-данных (Dashboard Chart, Number Card, Workspace, отчёты),
если babel-экстрактор их не подобрал. Пример: `Opportunity Trends`
и `Incoming Leads` — это штатные ERPNext-чарты (`is_standard: 1`,
модуль CRM, созданы в 2020), но их `chart_name` в `erpnext/locale/ru.po`
отсутствует как msgid. Никакой `bench update-po-files` их не добавит
на нашей стороне — только правка апстрима либо наш override.

## Как Frappe собирает словарь

`frappe/translate.py`, `get_all_translations(lang)` → `_merge_translations()`:

```
for app in installed_apps:            # порядок из Installed Applications
    dict.update(app/translations/<lang>.csv)
    dict.update(app/locale/<lang>.mo)  # скомпилировано из .po
dict.update(Translation doctype, language=<lang>)   # ← перебивает всё
```

Приоритет снизу вверх:

1. `.po/.mo` апстрима (frappe, потом erpnext);
2. `translations/<lang>.csv` **нашего** приложения — `habibi_core` стоит
   в списке после `erpnext`, поэтому перебивает его;
3. записи доктайпа **Translation** — перебивают вообще всё.

Порядок приложений на `erp.habibi-erp.com`:
`frappe, erpnext, saas_bridge, habibi_core, habibi_telegram, habibi_whatsapp, habibi_ui`.

Кеш — **две ступени, и это главная ловушка**:

1. словарь языка (`lang_user_translations`, `merged_translations`) —
   `Translation.on_update` чистит его сам при сохранении записи;
2. **bootinfo сессии** — desk получает готовый словарь (~15 тыс. строк)
   инлайном в HTML бута, и он лежит в кеше сессии. Первая ступень его
   **не инвалидирует**.

Поэтому после сохранения записи Translation обычный reload (даже hard)
ничего не покажет: придёт старый bootinfo.

И вторая ловушка поверх первой: **bootinfo кешируется отдельно на каждого
пользователя** — `frappe.cache.hset("bootinfo", frappe.session.user, ...)`
(`frappe/sessions.py:147`). А кнопка «Reload» в desk вызывает
`frappe.sessions.clear` → `clear_user_cache(frappe.session.user)`, то есть
чистит **только свой** кеш. Отсюда типичная картина: у того, кто вносил
перевод, всё видно, у всех остальных по-прежнему английский — и так до
бесконечности, пока их кеш кто-нибудь не сбросит.

Чем сбрасывать:

| способ | что чистит | кому годится |
| ------ | ---------- | ------------ |
| меню «⋯» → Reload (`frappe.ui.toolbar.clear_cache()`) | только текущего пользователя | проверить свою правку |
| логаут → логин | только этого пользователя (`auth.py:153`) | разовая помощь одному коллеге |
| `bench --site <site> clear-cache` | **все ключи сайта**, значит bootinfo всех пользователей (`cache_manager.py:295`) | штатный способ после любой правки переводов |

Правило: своя проверка — «Reload», выкат на людей — `bench clear-cache`.

И ещё: переводы **посайтовые**. Запись Translation на `erp.habibi-erp.com`
никак не влияет на `client1.habibi-erp.com`. Это второй довод за CSV
в `habibi_core`: он едет с образом и работает на всех тенантах сразу.

Проверено 2026-08-23, см. журнал.

Для CSV — то же самое плюс новый образ: `bench --site <site> clear-cache`
(или миграция / перезапуск контейнера).

## Куда что класть

### 1. `habibi_core/translations/ru.csv` — основной канал

Обычный CSV без заголовка, 2 колонки (`source,translation`), третья
необязательная — контекст:

```csv
Opportunity Trends,Динамика возможностей
Incoming Leads,Входящие лиды
Open Opportunity,Открытые возможности
```

Плюсы: один файл в git, едет с образом, никакого состояния в БД, не
нужен babel/`.po`-тулинг. В v16 формат по-прежнему поддерживается
(`get_translations_from_csv`). Сюда — всё массовое.

### 2. Доктайп **Translation** — точечные и потенантные правки

Уже используется в проекте: на сайте лежат 4 записи с фиксированными
именами `habibi-brand-*` (`ERPNext → Habibi ERP`,
`ERPNext Settings → Настройки`), их идемпотентно проставляет
`habibi_core`. Тот же приём годится для строк, которые существуют
только в БД конкретного тенанта, и для быстрых фиксов без выката.

Минус: сотни записей в БД вместо одного файла — для массового перевода
не годится.

### 3. Апстрим

Реально отсутствующие в ERPNext строки стоит донести до апстрима
(translate.frappe.io / Crowdin). Наш CSV — немедленный локальный
override, который не ждёт мержа.

### Чего этими способами НЕ перевести

Пользовательские данные — названия Item, имена Customer и т.п. — через
`__()` не рендерятся. Галка `translatable` у DocField существует, но
Frappe учитывает её только в `desk/reportview.py` при **экспорте**
значений. Переводить номенклатуру через Translation бессмысленно —
переименовывать записи.

Переводятся, наоборот, нормально: label и description полей, названия
доктайпов, опции Select, заголовки чартов / карточек / воркспейсов,
имена отчётов.

## Штатная процедура: перевести строку

Один и тот же порядок для любой строки — так правки остаются
воспроизводимыми, а результат видят **все** пользователи, а не только
автор правки. Шаг 4 не пропускать, он и есть причина 90% «не работает».

### Шаг 1. Точный исходный текст

Должен совпасть посимвольно, включая множественное число и скобки.
Не списывайте с экрана — берите из документа. Для чарта это `chart_name`,
для карточки — `label`, для поля — `label` из DocField:

```
/api/resource/Dashboard Chart?filters=[["name","like","%Opportunity%"]]&fields=["name","chart_name"]
```

Осторожно: на дашборде CRM показан `Opportunity Trends`, а не
`Opportunity Trend`, как кажется на глаз.

### Шаг 2. Понять, дырка это или замена

```bash
grep -A1 'msgid "Opportunity Trends"' erpnext/locale/ru.po
```

Нет msgid — апстрим строку вообще не переводит, мы закрываем дырку.
Есть, но не нравится формулировка — мы перебиваем чужой перевод, и
стоит проверить, не разъедется ли терминология по остальному интерфейсу.

### Шаг 3. Внести перевод

**Быстро, для примерки формулировки** — запись Translation,
`/app/translation/new`:

| поле            | значение                |
| --------------- | ----------------------- |
| Language        | `ru`                    |
| Source Text     | точный текст из шага 1  |
| Translated Text | перевод                 |
| Context         | пусто                   |

**Штатно, когда формулировка утверждена** — строка в
`habibi_core/translations/ru.csv`, коммит, сборка образа, выкат.
Запись Translation после переноса удалить, чтобы не было двух
источников правды.

### Шаг 4. Сбросить кеш — обязательно, всем

Словарь приезжает инлайном в bootinfo, а bootinfo кешируется **на
каждого пользователя отдельно**. Пока кеш конкретного человека жив, он
видит старый текст сколько угодно долго. Поэтому:

**Если есть доступ к серверу — только так:**

```bash
docker compose exec backend bench --site erp.habibi-erp.com clear-cache
```

Чистит все ключи сайта, то есть bootinfo всех пользователей разом
(`cache_manager.py:295`). Это же нужно после выката образа с новым
`ru.csv`.

**Если доступа к серверу нет** — из консоли браузера под System Manager.
Сохранение карточки User дёргает `frappe.clear_cache(user=...)`
(`user/user.py:325`), поэтому пересохраняем всех включённых
пользователей их же значением языка — язык не меняется, кеш слетает:

```js
const csrf = frappe.csrf_token || frappe.boot.csrf_token;
const users = (await (await fetch(
  '/api/resource/User?fields=["name","language"]&filters=[["enabled","=",1],["name","not in",["Guest"]]]&limit_page_length=0',
  {headers:{Accept:'application/json'}})).json()).data;
for (const u of users) {
  await fetch('/api/resource/User/' + encodeURIComponent(u.name), {
    method:'PUT',
    headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf},
    body: JSON.stringify({language: u.language})
  });
}
frappe.ui.toolbar.clear_cache();   // себе, заодно перезагрузит страницу
```

Годится на десяток пользователей. На большом сайте — только `bench`.

Чего **не** хватит: обычный reload, hard reload, `frappe.ui.toolbar.clear_cache()`
в одиночку (чистит только свой кеш), удаление cookies.

### Шаг 5. Проверить

Перезагрузить страницу и убедиться глазами. Если сомнение — в консоли:

```js
frappe._messages['Opportunity Trends']   // → "Динамика возможностей"
```

Пусто при `frappe.boot.lang === "ru"` — кеш не сброшен, вернуться к шагу 4.

### Шаг 6. Дописать сюда

Любая правка переводов — строка в «Журнал проверок» внизу: что, где,
какой формулировкой, что при этом выяснилось. Файл для того и заведён.

### Про язык пользователя

Язык берётся из `User.language`, при пустом — из System Settings.
`?_lang=ru` в URL desk **не работает**: `boot.py` перетирает язык через
`set_user_lang(session.user)`. Менять в `/app/user/<email>` → Language,
либо аватар → My Settings → Language, либо глобально
`/app/system-settings` → Language (дефолт для всех с пустым полем).


## Полезные ссылки в исходниках

| что | где |
| --- | --- |
| сборка словаря, приоритеты | `frappe/translate.py: get_all_translations` |
| чтение CSV приложения | `frappe/translate.py: get_translations_from_csv` |
| чтение записей Translation | `frappe/translate.py: get_user_translations` |
| сброс кеша при сохранении | `frappe/core/doctype/translation/translation.py` |
| перевод заголовка виджета | `frappe/public/js/frappe/widgets/base_widget.js: set_title` |
| выбор языка запроса | `frappe/translate.py: get_language`, `frappe/boot.py` |
| `translatable` только при экспорте | `frappe/desk/reportview.py` |

## Журнал проверок

### 2026-08-23 — CRM Dashboard, `erp.habibi-erp.com`

Разбор до проверки:

- `Won Opportunities` и `New Lead (Last 1 Month)` в `erpnext/locale/ru.po`
  есть; `Opportunity Trends`, `Incoming Leads`, `Open Opportunity`
  отсутствуют как msgid вообще.
- Заголовки виджетов идут через `__()` — переводимы в принципе.
- `?_lang=ru` на desk не действует: `boot.py` перетирает язык через
  `set_user_lang(session.user)`.
- Порядок приложений даёт `habibi_core` приоритет над `erpnext`.

Живая проверка на `Opportunity Trends` — **успешно**. Что делали:

1. `User/Administrator.language`: пусто → `ru`. Reload: интерфейс стал
   русским («Панель инструментов», «Лид», «Возможность», «Последний
   квартал»), при этом `Incoming Leads`, `Opportunity Trends` и
   `Open Opportunity` остались английскими — ровно та картина, с которой
   пришёл вопрос. Гипотеза «дырка в апстримном каталоге» подтвердилась
   визуально.
2. Создана запись Translation `6867jrd91p`:
   `ru` / `Opportunity Trends` → `Динамика возможностей`.
3. Reload — **ничего не изменилось**. В консоли: `frappe.boot.lang == "ru"`,
   в словаре 15045 строк, но `frappe._messages['Opportunity Trends']` пусто.
   Причина — кеш bootinfo сессии, словарь приезжает инлайном в буте и
   первой ступенью сброса кеша не инвалидируется.
4. `frappe.ui.toolbar.clear_cache()` → заголовок стал
   **«Динамика возможностей»**. Соседние `Incoming Leads` и
   `Open Opportunity` остались английскими, как и ожидалось — для них
   записей не заводили.

Вывод: механизм рабочий, но пункт 3 обязателен — без сброса кеша правка
выглядит как «не сработало».

Состояние прода после проверки (**не откатывалось**):

| что | значение | как вернуть |
| --- | -------- | ----------- |
| `User/Administrator.language` | `ru` (было пусто) | `/app/user/Administrator` → Language → очистить → Save |
| Translation `6867jrd91p` | `Opportunity Trends` → `Динамика возможностей` | `/app/translation/6867jrd91p` → Delete |

Следующий шаг, когда формулировка устроит: перенести строку в
`habibi_core/translations/ru.csv`, запись Translation удалить.
Кандидаты в тот же заход — `Incoming Leads`, `Open Opportunity`
и остальные 1331 непереведённых записей `erpnext/locale/ru.po`.

### 2026-08-23, продолжение — «у меня не видно»

Проверено на свежей загрузке страницы: на сервере всё на месте —
`frappe.boot.lang` = `ru`, в словаре 15046 строк,
`frappe._messages['Opportunity Trends']` = «Динамика возможностей»,
заголовок виджета отрисован по-русски. Правка живая и переживает
перезагрузку.

Если её не видно у кого-то ещё — причина в кеше bootinfo, который
хранится **на каждого пользователя отдельно**, а кнопка «Reload» в desk
чистит только свой (разобрано выше в разделе про кеш). Лечится
`bench --site erp.habibi-erp.com clear-cache`.

Второе, что проверить, если не помогло: тот ли это сайт. Переводы
посайтовые, запись заведена только на `erp.habibi-erp.com`.

### 2026-08-23, продолжение — сброс кеша конкретному пользователю

Ситуация: под `Administrator` перевод виден, под `timur.msk@gmail.com` —
нет. Язык у него уже был `ru`, дело только в персональном кеше bootinfo.

Доступа к `bench` из сессии не было, поэтому сбросили кеш **сохранением
записи User**: `User.on_update` вызывает `frappe.clear_cache(user=self.name)`
(`frappe/core/doctype/user/user.py:325`), а `clear_user_cache` удаляет
для этого пользователя ключ `bootinfo` (`cache_manager.py:48,89`).
Достаточно PUT с тем же значением — save отработает, `modified`
обновится, кеш слетит.

```
PUT /api/resource/User/timur.msk@gmail.com   {"language": "ru"}
```

Приём полезный: **сохранение карточки пользователя = сброс его
персонального кеша**, без доступа к серверу. Для одного-двух человек
годится, на всех — всё равно `bench clear-cache`.

Языки пользователей на `erp.habibi-erp.com` на эту дату:
`Administrator` `ru` (выставлен в ходе проверки, было пусто),
`dosnet2200@gmail.com` `ru`, `timur.msk@gmail.com` `ru`,
`nizam@missionmeans.com` `en-US`, System Settings — `en-US`.

### 2026-08-23, продолжение — `Incoming Leads`

Тот же порядок, уже без сюрпризов:

1. Запись Translation `tij8644ben`: `ru` / `Incoming Leads` →
   `Входящие лиды`.
2. Сброс кеша: себе — `frappe.ui.toolbar.clear_cache()`,
   `timur.msk@gmail.com` и `dosnet2200@gmail.com` — сохранением карточки
   User (приём из предыдущей записи).
3. Проверено: заголовок чарта — «Входящие лиды».

На дашборде CRM по-английски остался только number card
**`Open Opportunity`** (в `erpnext/locale/ru.po` его тоже нет).

Записи Translation на `erp.habibi-erp.com`, заведённые в ходе разбора:

| name | source | ru |
| ---- | ------ | -- |
| `6867jrd91p` | `Opportunity Trends` | Динамика возможностей |
| `tij8644ben` | `Incoming Leads` | Входящие лиды |

Обе — временные, до переноса в `habibi_core/translations/ru.csv`.

### 2026-08-23, итог — процедура зафиксирована

Раздел «Штатная процедура» переписан так, чтобы сброс кеша **всем**
пользователям был обязательным шагом, а не примечанием. Туда же положен
браузерный сниппет на случай, когда до `bench` не дотянуться.

Сниппет прогнан на живом сайте, кеш сброшен всем включённым
пользователям, языки при этом не поехали:

| пользователь | язык | результат |
| ------------ | ---- | --------- |
| `Administrator` | `ru` | 200 |
| `dosnet2200@gmail.com` | `ru` | 200 |
| `nizam@missionmeans.com` | `en-US` | 200 |
| `timur.msk@gmail.com` | `ru` | 200 |

То есть обе правки (`Opportunity Trends`, `Incoming Leads`) сейчас видны
всем, кто сидит под `ru`. У `nizam@missionmeans.com` язык `en-US` — он
по-прежнему видит английский интерфейс целиком, это его настройка, а не
проблема переводов.
