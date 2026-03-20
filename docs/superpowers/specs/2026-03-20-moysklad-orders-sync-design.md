# МойСклад: синхронизация заказов покупателей

**Дата:** 2026-03-20
**Приложение:** `picking_app`

## Цель

Расширить существующую интеграцию с МойСкладом: добавить синхронизацию заказов покупателей (customerorder) в очередь комплектации наравне с перемещениями (move).

## Контекст

В `picking_app` уже реализована синхронизация перемещений (`sync_picking_list()`), хранение токена в `Picking Settings`, пагинация через `nextHref`. Заказы должны попасть в ту же очередь с минимальными изменениями в UI и логике комплектации.

## Модель данных

### Picking Settings — новое поле
| Поле | Тип | Значение по умолчанию |
|------|-----|----------------------|
| `ms_order_state` | Data | `"Подтверждён"` |

### Picking List — новое поле
| Поле | Тип | Значение |
|------|-----|---------|
| `source_type` | Select | `"Move"` / `"Order"` |

Для существующих записей `source_type` не проставляется (остаётся пустым — UI трактует как Move).

## Логика синхронизации

### `sync_picking_orders()`
1. Читает `ms_order_state` из `Picking Settings` (fallback: `"Подтверждён"`)
2. Тянет `customerorder` из МС:
   ```
   GET /entity/customerorder
   expand=state,positions.assortment,positions.assortment.uom
   limit=100
   order=moment,desc
   ```
3. Фильтрует на клиенте: `order["state"]["name"] == ms_order_state`
4. `to_warehouse` берётся из `store` объекта заказа (склад отгрузки); `from_warehouse` — пустой
5. Создаёт/обновляет `Picking List` с `source_type = "Order"` по той же логике что `sync_picking_list()`

### `sync_all()` — новая публичная функция (`@frappe.whitelist`)
Вызывает последовательно `sync_picking_list()` и `sync_picking_orders()`, возвращает суммарный результат:
```json
{"status": "ok", "moves": {"created": N, "updated": N}, "orders": {"created": N, "updated": N}}
```

Существующая `sync_picking_list()` при создании новых записей проставляет `source_type = "Move"`.

## UI

В попап-диалоге выбора позиций:
- Добавить колонку **Тип** (`source_type`): отображает "Перемещение" / "Заказ"
- Добавить фильтр по типу: табы или кнопки **Все / Перемещения / Заказы**
- Логика добавления позиций в `Picking Document` — без изменений

## Что не меняется
- Структура `Picking List Item`
- Логика `add_items_from_picking_list()`
- Логика `get_picking_list_items()` — добавить опциональный параметр `source_type` для фильтрации
- Статусная машина Picking List (Draft → Partial → Added)

## Ограничения
- Фильтрация по статусу происходит на стороне клиента (МС API не поддерживает фильтр по `state.name` напрямую через query params без знания UUID состояния)
- `from_warehouse` у заказов не заполняется
