# Миры/Пространства — отдельные контекстные пространства

## Мотивация

Несколько независимых "журналов" или "миров", каждый со своими источниками,
индексом (ChromaDB), чатами и настройками. Источники, индекс и история чатов
изолированы между мирами.

## 1. База данных — таблица `worlds`

```sql
CREATE TABLE IF NOT EXISTS worlds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
```

Миграция: при старте создать дефолтный мир `"Default"`, добавить `world_id`
во все таблицы (с `DEFAULT 1`).

## 2. ChromaDB — отдельные директории

```
chroma_db/
  world_1/     # Default — существующие данные остаются здесь
  world_2/     # Новый мир — своя БД Chroma
  ...
```

Логика:
```python
chroma_client = chromadb.PersistentClient(path=f"{CHROMA_DIR}/world_{world_id}")
collection = chroma_client.get_or_create_collection("myrag")
```

`known_hashes.json` тоже хранить внутри `chroma_db/world_{id}/`.

## 3. Storage — новые функции + параметр world_id

- `create_world(name, desc) -> int`
- `list_worlds() -> list[dict]`
- `delete_world(world_id)` — каскадное удаление + очистка Chroma
- `rename_world(world_id, name)`
- Во все существующие функции добавить `world_id: int = 1`

## 4. UI — WorldsView + Dropdown в AppBar

**`views/worlds_view.py`** (новый):
- GridView карточек: название, описание, кол-во чатов/источников
- Кнопка "Создать мир" → диалог
- Кнопка "Удалить мир" → подтверждение
- Клик по карточке → вход в мир

**`app.py`**:
- `WorldsView` показывается при старте (если миров > 0 и нет active_world)
- После выбора мира: `page.session.set("world_id", id)` → показывается
  основной интерфейс
- Dropdown в AppBar со списком миров для быстрого переключения
- Переключение мира → перезагрузка AddView и ChatView с новым world_id

**`views/chat_view.py`** и **`views/add_view.py`**:
- Принимают `world_id` в конструктор или получают из сессии
- Все вызовы storage идут с текущим world_id

## 5. CLI — флаг `--world` + команда `world`

```bash
myrag --world "Имя мира" add "text"
myrag --world 2 ask "question"
myrag world list
myrag world create --name "Работа" --desc "Рабочие документы"
myrag world delete --id 2
```

## 6. Файлы для изменения/создания

| Файл | Действие |
|---|---|
| `config.py` | + `DEFAULT_WORLD_ID = 1` |
| `storage.py` | + таблица `worlds`, миграции, new API, world_id в существующие функции |
| `indexer.py` | chroma_client path = `world_{id}` |
| `query.py` | chroma_client path = `world_{id}` |
| `cli.py` | + `--world`, + подпарсер `world` |
| `app.py` | WorldsView + Dropdown + session |
| `views/worlds_view.py` | **новый файл** |
| `views/add_view.py` | world_id в storage calls |
| `views/chat_view.py` | world_id в storage/query calls |
| `views/settings_view.py` | без изменений |

## 7. Принятые решения (UI/UX)

| Решение | Выбор |
|---|---|
| Экран выбора миров | **Карточки (GridView)** |
| Изоляция ChromaDB | **Отдельные БД Chroma** (вложенные папки `world_{id}/`) |
| Индикатор в AppBar | **Dropdown** со списком миров |
| Импортёры к миру | **Только в текущий мир** (без явного выбора) |