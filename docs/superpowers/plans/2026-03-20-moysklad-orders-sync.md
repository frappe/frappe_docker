# МойСклад: синхронизация заказов покупателей — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить синхронизацию заказов покупателей (customerorder) из МойСклада в очередь комплектации наравне с перемещениями.

**Architecture:** Расширяем существующий `Picking List` полем `source_type`, добавляем префикс `move:`/`order:` к `ms_id` (снимаем unique-констрейнт), добавляем `sync_picking_orders()` и `sync_all()` в `api.py`, обновляем UI попапа.

**Tech Stack:** Python (Frappe), JSON DocType definitions, vanilla JS (jQuery/Frappe dialogs)

---

## Файловая структура

| Файл | Действие | Что меняем |
|------|----------|------------|
| `/home/mkr/picking_app/picking/doctype/picking_settings/picking_settings.json` | Modify | Добавить поле `ms_order_state` |
| `/home/mkr/picking_app/picking/doctype/picking_list/picking_list.json` | Modify | Добавить `source_type`, убрать `unique` с `ms_id` |
| `/home/mkr/picking_app/picking/api.py` | Modify | `sync_picking_list()` backfill, новые `sync_picking_orders()` + `sync_all()`, фикс бага `added_rows`, обновить `get_picking_list_items()` |
| `/home/mkr/picking_app/picking/page/picking_doc/picking_doc.js` | Modify | UI: кнопка → `sync_all`, колонка Тип, фильтр-табы |

> **Важно:** `/home/mkr/picking_app/` смонтирован как read-only том в контейнер `frappe-project-backend-1` в `/home/frappe/frappe-bench/apps/picking_app/picking_app/`. Все изменения делаются в файлах на хосте. После изменений JS нужно пересобрать: `docker exec frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local migrate"`. После изменений JSON-схем нужен `bench migrate`. После изменений JS — `bench build --app picking_app` или перезагрузка страницы в dev-режиме.

---

## Task 1: Добавить поле `ms_order_state` в Picking Settings

**Files:**
- Modify: `/home/mkr/picking_app/picking/doctype/picking_settings/picking_settings.json`

- [ ] **Step 1: Открыть файл и найти конец массива `fields`**

```bash
cat /home/mkr/picking_app/picking/doctype/picking_settings/picking_settings.json
```

- [ ] **Step 2: Добавить поле после `ms_account_id`**

В массив `fields` добавить перед закрывающей `]`:

```json
        ,{
            "fieldname": "ms_order_state",
            "fieldtype": "Data",
            "label": "Статус заказа для синхронизации",
            "description": "Название статуса в МоёмСкладе для фильтрации заказов покупателей",
            "default": "Подтверждён",
            "reqd": 1
        }
```

- [ ] **Step 3: Применить миграцию**

```bash
docker exec frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local migrate"
```

Ожидаемый вывод: `Migrating erp.local` … `Done`

- [ ] **Step 4: Проверить что поле появилось**

```bash
echo "
result = frappe.db.get_value('Picking Settings', 'Default', 'ms_order_state')
print('ms_order_state:', repr(result))
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep "ms_order_state:"
```

Ожидаемый вывод: `ms_order_state: 'Подтверждён'`

- [ ] **Step 5: Commit**

```bash
cd /home/mkr/picking_app
git add picking/doctype/picking_settings/picking_settings.json
git commit -m "feat: add ms_order_state field to Picking Settings"
```

---

## Task 2: Обновить Picking List — добавить `source_type`, убрать `unique` с `ms_id`

**Files:**
- Modify: `/home/mkr/picking_app/picking/doctype/picking_list/picking_list.json`

- [ ] **Step 1: Убрать `"unique": 1` из поля `ms_id`**

В `picking_list.json` найти блок поля `ms_id`:
```json
{
    "fieldname": "ms_id",
    "fieldtype": "Data",
    "label": "МойСклад ID",
    "unique": 1,
    "reqd": 1
}
```
Изменить на:
```json
{
    "fieldname": "ms_id",
    "fieldtype": "Data",
    "label": "МойСклад ID",
    "reqd": 1
}
```

- [ ] **Step 2: Добавить поле `source_type` после поля `synced_at`**

После блока `synced_at`, перед `items`:
```json
        ,{
            "fieldname": "source_type",
            "fieldtype": "Select",
            "label": "Тип источника",
            "options": "\nMove\nOrder",
            "default": "Move"
        }
```

- [ ] **Step 3: Применить миграцию**

```bash
docker exec frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local migrate"
```

- [ ] **Step 4: Проверить что поле создалось и unique снят**

```bash
echo "
exec('''
import frappe
# Проверить что source_type существует
cols = frappe.db.get_table_columns(\"tabPicking List\")
print(\"source_type in columns:\", \"source_type\" in cols)

# Проверить что unique снят — должна пройти вставка двух записей с одинаковым ms_id (НЕ делаем, просто проверим мета)
meta = frappe.get_meta(\"Picking List\")
ms_id_field = next((f for f in meta.fields if f.fieldname == \"ms_id\"), None)
print(\"ms_id unique:\", getattr(ms_id_field, \"unique\", None))
''')
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep -E "source_type|ms_id unique"
```

Ожидаемый вывод:
```
source_type in columns: True
ms_id unique: 0
```

- [ ] **Step 5: Commit**

```bash
cd /home/mkr/picking_app
git add picking/doctype/picking_list/picking_list.json
git commit -m "feat: add source_type to Picking List, remove unique from ms_id"
```

---

## Task 3: Миграция существующих записей Picking List — добавить префикс `move:` к ms_id

**Files:**
- Нет изменений в файлах — только разовая миграция данных в БД

> **Выполнить до Task 4.** Без этого шага после обновления `sync_picking_list()` существующие записи с чистыми UUID не будут найдены при поиске по `move:{uuid}` — возникнут дубликаты.

- [ ] **Step 1: Проверить количество записей для миграции**

```bash
echo "
exec('''
import frappe
total = frappe.db.count(\"Picking List\")
already_prefixed = frappe.db.sql(\"SELECT COUNT(*) FROM \`tabPicking List\` WHERE ms_id LIKE \\\"move:%\\\" OR ms_id LIKE \\\"order:%\\\"\")[0][0]
needs_migration = total - already_prefixed
print(f\"Всего: {total}, уже с префиксом: {already_prefixed}, требуют миграции: {needs_migration}\")
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep "Всего:"
```

- [ ] **Step 2: Выполнить миграцию**

```bash
echo "
exec('''
import frappe
rows = frappe.db.sql(
    \"SELECT name, ms_id FROM \`tabPicking List\` WHERE ms_id NOT LIKE \\\"move:%\\\" AND ms_id NOT LIKE \\\"order:%\\\"\",
    as_dict=True
)
updated = 0
for row in rows:
    new_ms_id = f\"move:{row.ms_id}\"
    frappe.db.set_value(\"Picking List\", row.name, \"ms_id\", new_ms_id)
    updated += 1
frappe.db.commit()
print(f\"Обновлено записей: {updated}\")
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep "Обновлено"
```

Ожидаемый вывод: `Обновлено записей: N` (N ≥ 0, не ошибка)

- [ ] **Step 3: Верифицировать — не должно остаться записей без префикса**

```bash
echo "
exec('''
import frappe
orphans = frappe.db.sql(
    \"SELECT COUNT(*) FROM \`tabPicking List\` WHERE ms_id NOT LIKE \\\"move:%\\\" AND ms_id NOT LIKE \\\"order:%\\\"\",
)[0][0]
print(\"Без префикса:\", orphans)
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep "Без префикса:"
```

Ожидаемый вывод: `Без префикса: 0`

---

## Task 4: Обновить `sync_picking_list()` — prefixed ms_id + backfill source_type

**Files:**
- Modify: `/home/mkr/picking_app/picking/api.py`

Текущая логика `sync_picking_list()` ищет записи через `frappe.db.get_value("Picking List", {"ms_id": ms_id}, "name")` где `ms_id` — чистый UUID. После этого изменения поиск и хранение будут через `move:{uuid}`.

- [ ] **Step 1: Найти строку с `ms_id = move.get("id")`**

```bash
grep -n "ms_id\|existing\|source_type" /home/mkr/picking_app/picking/api.py | head -30
```

- [ ] **Step 2: Обновить функцию `sync_picking_list()`**

Найти блок (примерно строки 298–365 в api.py):
```python
        ms_id = move.get("id")
        if not ms_id:
            continue
        ...
        existing = frappe.db.get_value("Picking List", {"ms_id": ms_id}, "name")
        if existing:
            pl = frappe.get_doc("Picking List", existing)
            pl.ms_number = ms_number
            ...
            pl.save(ignore_permissions=True)
            updated += 1
        else:
            frappe.get_doc({
                "doctype": "Picking List",
                "ms_id": ms_id,
                ...
            }).insert(ignore_permissions=True)
            created += 1
```

Изменить на:
```python
        raw_id = move.get("id")
        if not raw_id:
            continue
        ms_id = f"move:{raw_id}"
        ...
        existing = frappe.db.get_value("Picking List", {"ms_id": ms_id}, "name")
        if existing:
            pl = frappe.get_doc("Picking List", existing)
            pl.ms_number = ms_number
            pl.ms_date = ms_date
            pl.from_warehouse = from_wh
            pl.to_warehouse = to_wh
            pl.synced_at = synced_at
            pl.source_type = "Move"          # backfill
            if pl.status != "Added":
                _update_pl_items(pl, positions)
            pl.save(ignore_permissions=True)
            updated += 1
        else:
            frappe.get_doc({
                "doctype": "Picking List",
                "ms_id": ms_id,
                "ms_number": ms_number,
                "ms_date": ms_date,
                "from_warehouse": from_wh,
                "to_warehouse": to_wh,
                "status": "Draft",
                "source_type": "Move",
                "synced_at": synced_at,
                "items": [_item_from_position(p) for p in positions],
            }).insert(ignore_permissions=True)
            created += 1
```

- [ ] **Step 3: Проверить синтаксис**

```bash
python3 -c "import ast; ast.parse(open('/home/mkr/picking_app/picking/api.py').read()); print('OK')"
```

- [ ] **Step 4: Commit**

```bash
cd /home/mkr/picking_app
git add picking/api.py
git commit -m "feat: prefix ms_id with move:, backfill source_type in sync_picking_list"
```

---

## Task 5: Добавить `sync_picking_orders()` и `sync_all()`

**Files:**
- Modify: `/home/mkr/picking_app/picking/api.py`

> **Порядок шагов важен:** сначала обновляем `_ms_fetch_all()` (Step 1), затем добавляем `sync_picking_orders()` которая его использует (Step 2).

- [ ] **Step 1: Обновить `_ms_fetch_all()` — добавить параметр `max_pages`**

Найти функцию `_ms_fetch_all`:
```python
def _ms_fetch_all(endpoint, params):
    """Получить все строки с автопагинацией через nextHref."""
    headers = _ms_headers()
    rows = []
    url = f"{MS_BASE}/{endpoint}"
    while url:
        data = _ms_get(url, params=params, headers=headers)
        rows.extend(data.get("rows", []))
        url = data.get("meta", {}).get("nextHref")
        params = None
    return rows
```

Изменить на:
```python
def _ms_fetch_all(endpoint, params, max_pages=None):
    """Получить все строки с автопагинацией через nextHref.

    max_pages: ограничить количество страниц (None = без ограничения).
    """
    headers = _ms_headers()
    rows = []
    url = f"{MS_BASE}/{endpoint}"
    page = 0
    while url:
        if max_pages and page >= max_pages:
            break
        data = _ms_get(url, params=params, headers=headers)
        rows.extend(data.get("rows", []))
        url = data.get("meta", {}).get("nextHref")
        params = None
        page += 1
    return rows
```

- [ ] **Step 2: Добавить функцию `sync_picking_orders()` после `sync_picking_list()`**

Вставить после функции `sync_picking_list()` (перед `def _update_pl_items`):

```python
@frappe.whitelist()
def sync_picking_orders():
    """Синхронизировать заказы покупателей из МоёгоСклада в Picking List.

    Фильтрация по state.name == ms_order_state (из Picking Settings).
    Лимит: 10 страниц × 100 заказов = 1000 за синхронизацию.
    """
    settings_name = frappe.db.get_value("Picking Settings", {}, "name")
    order_state = (
        frappe.db.get_value("Picking Settings", settings_name, "ms_order_state")
        if settings_name else None
    ) or "Подтверждён"

    orders = _ms_fetch_all("entity/customerorder", {
        "limit": 100,
        "order": "moment,desc",
        "expand": "state,store,positions.assortment,positions.assortment.uom",
    }, max_pages=10)

    wh_cache = _build_wh_cache()
    synced_at = now_datetime()
    created = updated = 0

    for order in orders:
        state_obj = order.get("state") or {}
        if state_obj.get("name") != order_state:
            continue

        raw_id = order.get("id")
        if not raw_id:
            continue
        ms_id = f"order:{raw_id}"

        ms_number = order.get("name", "")
        ms_date = _parse_ms_datetime(order.get("moment", ""))

        store_id, store_name = _extract_store_id(order.get("store"))
        to_wh = wh_cache.get(store_id) or wh_cache.get(store_name)

        positions = _positions_from_move(order)

        existing = frappe.db.get_value("Picking List", {"ms_id": ms_id}, "name")
        if existing:
            pl = frappe.get_doc("Picking List", existing)
            pl.ms_number = ms_number
            pl.ms_date = ms_date
            pl.to_warehouse = to_wh
            pl.synced_at = synced_at
            pl.source_type = "Order"
            if pl.status != "Added":
                _update_pl_items(pl, positions)
            pl.save(ignore_permissions=True)
            updated += 1
        else:
            frappe.get_doc({
                "doctype": "Picking List",
                "ms_id": ms_id,
                "ms_number": ms_number,
                "ms_date": ms_date,
                "to_warehouse": to_wh,
                "status": "Draft",
                "source_type": "Order",
                "synced_at": synced_at,
                "items": [_item_from_position(p) for p in positions],
            }).insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "updated": updated, "total": len(orders)}


@frappe.whitelist()
def sync_all():
    """Синхронизировать перемещения и заказы покупателей из МоёгоСклада."""
    moves = sync_picking_list()
    orders = sync_picking_orders()
    return {
        "status": "ok",
        "moves": {"created": moves["created"], "updated": moves["updated"]},
        "orders": {"created": orders["created"], "updated": orders["updated"]},
    }
```

- [ ] **Step 3: Проверить синтаксис**

```bash
python3 -c "import ast; ast.parse(open('/home/mkr/picking_app/picking/api.py').read()); print('OK')"
```

- [ ] **Step 4: Проверить что функции доступны через bench**

```bash
echo "
exec('''
import picking_app.picking.api as api
print(\"sync_picking_orders:\", callable(api.sync_picking_orders))
print(\"sync_all:\", callable(api.sync_all))
''')
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep -E "sync_picking|sync_all"
```

Ожидаемый вывод:
```
sync_picking_orders: True
sync_all: True
```

- [ ] **Step 5: Commit**

```bash
cd /home/mkr/picking_app
git add picking/api.py
git commit -m "feat: add sync_picking_orders() and sync_all()"
```

---

## Task 6: Исправить баг `added_rows` и обновить `get_picking_list_items()`

**Files:**
- Modify: `/home/mkr/picking_app/picking/api.py`

- [ ] **Step 1: Исправить `added_rows` → `added_row_names` в `add_items_from_picking_list()`**

Найти строку (примерно строка 462):
```python
    return {"status": "ok", "added": len(added_rows), "items": updated_items}
```
Изменить на:
```python
    return {"status": "ok", "added": len(added_row_names), "items": updated_items}
```

- [ ] **Step 2: Обновить `get_picking_list_items()` — добавить параметр `source_type` и поле в ответ**

Найти функцию:
```python
@frappe.whitelist()
def get_picking_list_items(from_warehouse=None, to_warehouse=None):
    """Вернуть Picking List для попап-диалога (только не полностью добавленные)."""
    filters = {"status": ["!=", "Added"]}
    if from_warehouse:
        filters["from_warehouse"] = from_warehouse
    if to_warehouse:
        filters["to_warehouse"] = to_warehouse

    pls = frappe.get_all(
        "Picking List",
        filters=filters,
        fields=["name", "ms_id", "ms_number", "ms_date", "from_warehouse", "to_warehouse", "status", "synced_at"],
        order_by="ms_date desc",
        limit=200
    )
```

Изменить на:
```python
@frappe.whitelist()
def get_picking_list_items(from_warehouse=None, to_warehouse=None, source_type=None):
    """Вернуть Picking List для попап-диалога (только не полностью добавленные).

    source_type=None — все записи (включая legacy без source_type).
    source_type="Move" — Move + NULL (обратная совместимость).
    source_type="Order" — только Order.
    """
    filters = {"status": ["!=", "Added"]}
    if from_warehouse:
        filters["from_warehouse"] = from_warehouse
    if to_warehouse:
        filters["to_warehouse"] = to_warehouse
    if source_type == "Order":
        filters["source_type"] = "Order"
    elif source_type == "Move":
        # Frappe хранит пустой Select как пустую строку, не NULL
        # Пустая строка = legacy-запись до добавления source_type (считается Move)
        filters["source_type"] = ["in", ["Move", ""]]

    pls = frappe.get_all(
        "Picking List",
        filters=filters,
        fields=["name", "ms_id", "ms_number", "ms_date", "from_warehouse",
                "to_warehouse", "status", "synced_at", "source_type"],
        order_by="ms_date desc",
        limit=200
    )
```

- [ ] **Step 3: Проверить синтаксис**

```bash
python3 -c "import ast; ast.parse(open('/home/mkr/picking_app/picking/api.py').read()); print('OK')"
```

- [ ] **Step 4: Commit**

```bash
cd /home/mkr/picking_app
git add picking/api.py
git commit -m "fix: added_rows NameError in add_items_from_picking_list; feat: source_type filter in get_picking_list_items"
```

---

## Task 7: Обновить UI попапа — фильтр-табы и колонка Тип

**Files:**
- Modify: `/home/mkr/picking_app/picking/page/picking_doc/picking_doc.js`

Все изменения в методах `_showMsDialog()` и `_loadMsList()`.

- [ ] **Step 1: Добавить таб-фильтр в HTML диалога**

В `_showMsDialog()` найти HTML фильтров (строки с `ms-filter-from`, `ms-filter-to`) и добавить после них строку с табами:

```html
<div id="ms-type-filter" style="display:flex;gap:6px;margin-bottom:8px;">
    <button class="btn btn-xs btn-default ms-type-btn active" data-type="">Все</button>
    <button class="btn btn-xs btn-default ms-type-btn" data-type="Move">Перемещения</button>
    <button class="btn btn-xs btn-default ms-type-btn" data-type="Order">Заказы</button>
</div>
```

- [ ] **Step 2: Добавить обработчик клика по табам**

В `_showMsDialog()` добавить обработчик после других `dialog.$body.on(...)`:

```javascript
dialog.$body.on('click', '.ms-type-btn', function() {
    dialog.$body.find('.ms-type-btn').removeClass('active btn-primary').addClass('btn-default');
    $(this).removeClass('btn-default').addClass('btn-primary active');
    self._loadMsList(dialog);
});
```

- [ ] **Step 3: Обновить кнопку синхронизации — вызывать `sync_all` вместо `sync_picking_list`**

Найти:
```javascript
method: 'picking_app.picking.api.sync_picking_list'
```
Заменить на:
```javascript
method: 'picking_app.picking.api.sync_all'
```

Найти строку с отображением результата:
```javascript
$status.text(`Готово: создано ${d.created || 0}, обновлено ${d.updated || 0} (всего ${d.total || 0})`);
```
Заменить на:
```javascript
const m = d.moves || {};
const o = d.orders || {};
$status.text(
    `Перемещения: +${m.created || 0} / ~${m.updated || 0}  |  Заказы: +${o.created || 0} / ~${o.updated || 0}`
);
```

- [ ] **Step 4: Передавать `source_type` при вызове `get_picking_list_items`**

В методе `_loadMsList(dialog)` найти весь блок:
```javascript
    async _loadMsList(dialog) {
        const from_wh = dialog.$body.find('#ms-filter-from').val().trim();
        const to_wh   = dialog.$body.find('#ms-filter-to').val().trim();
        const $cont   = dialog.$body.find('#ms-list-container');
        $cont.html('<div style="text-align:center;color:#888;padding:20px">Загрузка...</div>');

        try {
            const r = await frappe.call({
                method: 'picking_app.picking.api.get_picking_list_items',
                args: { from_warehouse: from_wh || null, to_warehouse: to_wh || null }
            });
```

Заменить на:
```javascript
    async _loadMsList(dialog) {
        const from_wh    = dialog.$body.find('#ms-filter-from').val().trim();
        const to_wh      = dialog.$body.find('#ms-filter-to').val().trim();
        const activeType = dialog.$body.find('.ms-type-btn.active').data('type') || null;
        const $cont      = dialog.$body.find('#ms-list-container');
        $cont.html('<div style="text-align:center;color:#888;padding:20px">Загрузка...</div>');

        try {
            const r = await frappe.call({
                method: 'picking_app.picking.api.get_picking_list_items',
                args: { from_warehouse: from_wh || null, to_warehouse: to_wh || null, source_type: activeType }
            });
```

- [ ] **Step 5: Добавить колонку "Тип" в заголовок каждой строки Picking List**

В методе `_loadMsList()` в функции рендеринга строки (`pls.map(pl => {...})`) найти строку с `from` и `to`:
```javascript
const from = pl.from_warehouse || '?';
const to   = pl.to_warehouse   || '?';
```
Добавить после:
```javascript
const typeLabel = pl.source_type === 'Order'
    ? '<span class="ms-badge" style="background:#cfe2ff;color:#084298">Заказ</span>'
    : '<span class="ms-badge" style="background:#e9ecef;color:#666">Перемещение</span>';
```

Добавить `${typeLabel}` в шаблон строки `.ms-pl-head` после `${statusBadge}`:
```javascript
${statusBadge}
${typeLabel}
```

- [ ] **Step 6: Пересобрать фронтенд и проверить**

```bash
docker exec frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench build --app picking_app" 2>&1 | tail -5
```

Открыть страницу Picking Document в браузере, нажать кнопку добавления из МС — проверить:
- Появились табы Все / Перемещения / Заказы
- В строках видна метка типа
- Синхронизация показывает статистику по двум типам

- [ ] **Step 7: Commit**

```bash
cd /home/mkr/picking_app
git add picking/page/picking_doc/picking_doc.js
git commit -m "feat: add source_type filter tabs and type badge to MoySklad popup"
```

---

## Task 8: Финальная проверка end-to-end

- [ ] **Step 1: Убедиться что токен заполнен**

Открыть в ERPNext: **Picking Settings → Default**, секция МойСклад, поле API-токен должно быть заполнено.

- [ ] **Step 2: Запустить `sync_all` вручную**

```bash
echo "
exec('''
import picking_app.picking.api as api
result = api.sync_all()
print(result)
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep -E "moves|orders|status"
```

Ожидаемый вывод вида:
```
{'status': 'ok', 'moves': {'created': N, 'updated': N}, 'orders': {'created': N, 'updated': N}}
```

- [ ] **Step 3: Проверить записи в БД**

```bash
echo "
exec('''
import frappe
moves = frappe.db.count(\"Picking List\", {\"source_type\": \"Move\"})
orders = frappe.db.count(\"Picking List\", {\"source_type\": \"Order\"})
nulls = frappe.db.count(\"Picking List\", {\"source_type\": [\"\", None]})
print(f\"Move: {moves}, Order: {orders}, NULL/legacy: {nulls}\")
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep -E "Move:|Order:"
```

- [ ] **Step 4: Проверить `get_picking_list_items` с фильтром**

```bash
echo "
exec('''
import picking_app.picking.api as api
all_items = api.get_picking_list_items()
order_items = api.get_picking_list_items(source_type=\"Order\")
move_items = api.get_picking_list_items(source_type=\"Move\")
print(f\"All: {len(all_items)}, Orders: {len(order_items)}, Moves: {len(move_items)}\")
# Проверяем что source_type возвращается
if all_items:
    print(\"source_type in response:\", \"source_type\" in all_items[0])
''', globals())
" | docker exec -i frappe-project-backend-1 bash -c "cd /home/frappe/frappe-bench && bench --site erp.local console" 2>&1 | grep -E "All:|source_type"
```

- [ ] **Step 5: Final commit tag**

```bash
cd /home/mkr/picking_app
git log --oneline -7
```
