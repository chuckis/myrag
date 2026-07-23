# Фронтенд на Flet — план реализации

## Конфигурация

| Параметр | Решение |
|----------|---------|
| Тема | Toggle ☀/🌙 (сохранять в `app.theme_mode`) |
| Загрузка файлов | Кнопка `FilePicker` |
| Стриминг | По токенам — генератор из `query.py` → обновление UI на каждый чанк |
| История чата | В SQLite — отдельная таблица `chat_history` рядом с `staging` |
| Парсинг `.md` | Не нужен, идёт как сырой текст |
| Иконка | Дефолтная Flet |
| Имя окна | MyRag |
| Лимит истории | 5 последних диалогов |

## Модификация существующих модулей

### `query.py`
- Добавить `ask_rag_stream(query)` — генератор, yield токенов

### `storage.py`
- Добавить таблицу `chat_history(id, query, answer, created_at)`
- `save_chat(query, answer)`
- `load_chat_history(limit=5)`

## Экраны

### 1. add_view.py — Добавление / Индексация

Поля: source, type (dropdown), text (multiline), FilePicker, кнопки Add и Index.
Лог индексатора, статус-бар (Total / Pending / Indexed).

### 2. chat_view.py — Поиск / Чат

ListView истории (5 последних), поле ввода вопроса, кнопка Ask.
Стриминг ответа по токенам, автоскролл.

## Файловая структура

```
myrag/
├── app.py
├── views/
│   ├── __init__.py
│   ├── add_view.py
│   └── chat_view.py
├── config.py
├── storage.py
├── indexer.py
├── query.py
├── embeddings.py
└── cli.py
```

## Зависимости

```bash
pip install flet
```

## Запуск

```bash
python3 app.py
```
