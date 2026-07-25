# OpenRouter Fallback + Settings UI

## Цель

Добавить поддержку OpenRouter как primary LLM с автоматическим fallback на локальную модель при ошибках сети/ключа/баланса/tаймаута, и создать UI для управления настройками.

## Решения (согласованы)

- **Хранение настроек**: SQLite таблица `settings` (key/value)
- **Выбор модели в GUI**: Dropdown с предустановленными моделями OpenRouter + кастомный ввод
- **Индикация активной модели**: Статус-бар внизу чата (`🌐 OpenRouter` / `🏠 Local Qwen 1.5B`)

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `config.py` | Добавить `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_TIMEOUT`, `OPENROUTER_MAX_TOKENS` |
| `requirements.txt` | Добавить `llama-index-llms-openrouter` |
| `storage.py` | Добавить таблицу `settings` + функции `get_setting()`, `set_setting()`, `get_all_settings()` |
| `query.py` | Рефакторинг: вынести LLM в `_get_remote_llm()` / `_get_local_llm()`. Обе `ask_rag()` и `ask_rag_stream()` получают `api_key`, `model_name`, `force_local`. Логика: remote → fallback → local |
| `cli.py` | Аргументы `--model`, `--force-local` для `ask` |
| `app.py` | Кнопка "⚙ Settings" в AppBar, открывающая `SettingsView` |
| `views/settings_view.py` (новый) | Диалог настроек: API Key, Dropdown моделей, Switch "Force local" |
| `views/chat_view.py` | Статус-бар внизу; читать настройки из БД в `on_ask()`; обновлять статус-бар после ответа |

## Логика Fallback (query.py)

```
if not force_local and api_key:
    try:
        OpenLRouter(api_key, model, timeout=10)
        → query_engine.query(query)
    except (ConnectionError, Timeout, AuthenticationError, ...) as e:
        warning → fallback
if response is None:
    local LlamaCPP → query_engine.query(query)
```

## API

### query.py — сигнатуры

```python
def ask_rag(
    query: str,
    api_key: str = "",
    model_name: str = "",
    force_local: bool = False,
) -> str: ...

def ask_rag_stream(
    query: str,
    chat_context: str = "",
    stop_event: threading.Event | None = None,
    api_key: str = "",
    model_name: str = "",
    force_local: bool = False,
) -> Generator[str, None, None]: ...
```

### CLI

```bash
python cli.py ask "question" --model "qwen/qwen-2.5-72b-instruct" --force-local
```

### GUI

- Settings dialog with:
  - `API Key` (password field + visibility toggle)
  - `Model` (Dropdown with presets + custom)
  - `Force local` (Switch)
- Status bar in Chat tab showing `🌐 OpenRouter: <model>` or `🏠 Local: Qwen 1.5B`
