# План: Telegram Importer (`tg_importer.py`)

## 1. `storage.py` — расширение

Добавить поддержку поля `created_at` в `bulk_add_to_buffer`:

- Сигнатура: `bulk_add_to_buffer(records: list[tuple[str, str, str, str | None]])`
- Если 4-й элемент передан — вставляется явно, иначе `DEFAULT datetime('now')`

## 2. `tg_importer.py` — новый файл

| Функция | Назначение |
|---------|-----------|
| `extract_clean_text(text_field: str \| list) -> str` | Рекурсивная нормализация: str → trim; list → обход (str как есть, dict → `["text"]`) → склейка |
| `parse_telegram_export(filepath: str, min_length: int = 15) -> list[dict]` | Читает `result.json`, достаёт `name` (чат) из корня, фильтрует `type == "message"`, текст > min_length, формирует enriched text, возвращает список записей |
| `import_telegram(filepath: str, min_length: int = 15) -> dict` | Вызывает `parse_telegram_export`, пишет через `storage.bulk_add_to_buffer`, возвращает статистику |

**CLI-вход** (при запуске как `python tg_importer.py`):
- `argparse` с `-f`/`--file`, `--min-length`
- `--db` игнорируется (используем `config.DB_PATH`)

**Формат обогащённого текста:**
```
Автор: {from_name}{fwd_info}
Дата: {date}
Сообщение:
{clean_text}
```

**Source:** `{chat_name}_msg_{message_id}`

## 3. `cli.py` — новая подкоманда

```bash
python cli.py import-tg -f export.json --min-length 15
```

Реализация — импорт `tg_importer.import_telegram`, вывод статистики.

## Файлы для изменений

| Файл | Тип изменений |
|------|--------------|
| `storage.py` | Добавить поддержку `created_at` в `bulk_add_to_buffer` |
| `tg_importer.py` | **Новый файл** (~80-100 строк) |
| `cli.py` | Подкоманда `import-tg` (~10-15 строк) |

## Утверждённые решения

- `bulk_add_to_buffer` сигнатура: 4-й опциональный параметр `created_at` в кортеже
- `import_telegram` возвращает словарь `{"total": int, "skipped": int, "imported": int}`
- Путь к БД из `config.DB_PATH` (параметр `--db` из ТЗ игнорируется)
- `--db` не включаем в CLI
- Имя файла: `tg_importer.py`
