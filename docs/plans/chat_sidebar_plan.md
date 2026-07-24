# Chat Sidebar — план улучшений

## Цель
Добавить сайдбар со списком чатов, создание нового чата, переименование, удаление. Контекст LLM строится из сообщений текущей сессии, а не из всей БД.

## Изменения

### 1. `storage.py`

**Новая таблица `chats`:**
```sql
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
```

**Миграция** (в `_get_conn`):
- `ALTER TABLE chat_history ADD COLUMN chat_id INTEGER REFERENCES chats(id)` (try/except)
- Если нет ни одного чата — создать `title="General"`, всем существующим сообщениям проставить `chat_id=1`

**Новые функции:**
- `create_chat(title: str) -> int`
- `rename_chat(chat_id: int, title: str)`
- `delete_chat(chat_id: int)` — удаляет чат + все `chat_history` с этим `chat_id`
- `list_chats() -> list[dict]` — список (id, title, created_at)
- `save_chat(query, answer, chat_id)` — обновлённая сигнатура (+chat_id)
- `load_chat_history(chat_id, limit=50)` — фильтр по чату
- `load_recent_chat_context(chat_id, n=5)` — фильтр по чату

### 2. `views/chat_view.py`

**Новые поля:**
- `current_chat_id: int | None`
- `current_messages: list[tuple[str, str]]` — сообщения текущей сессии для контекста LLM
- `sidebar_list: ft.ListView`
- `new_chat_btn: ft.ElevatedButton`

**Layout:**
```python
ft.Row([
    ft.Container(self.sidebar, width=220),
    ft.Column([chat_list, input_row], expand=True),
], expand=True)
```

**Методы:**
- `switch_chat(chat_id)` — загружает историю из БД, заполняет `current_messages`
- `load_chat_list()` — обновляет sidebar
- `on_new_chat()` — `create_chat("New Chat")` → switch → load_chat_list
- `on_delete_chat(chat_id)` — диалог подтверждения → delete → переключиться на первый чат
- `on_rename_chat(chat_id)` — диалог с вводом → rename_chat
- `on_ask()` — после ответа: `rename_chat(current_chat_id, query[:50])` если это первый запрос; контекст LLM из `current_messages[-5:]`

**Подсветка активного чата** в sidebar (другой bgcolor).

### 3. `app.py`
- В `on_change` таба при переключении на Chat вызывать `chat_view.load_chat_list()`

### 4. `query.py` / `cli.py`
- Без изменений

## Будущее расширение (не сейчас)
Для индексации чат-сообщений в RAG достаточно добавить в `save_chat()`:
```python
add_to_buffer(
    f"User: {query}\nAssistant: {answer}",
    source=f"chat:{chat_id}",
    type="chat",
)
```
