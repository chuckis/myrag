import argparse
import json
import sys
from typing import Any

from storage import bulk_add_to_buffer, init_db


def extract_clean_text(text_field: str | list) -> str:
    if isinstance(text_field, str):
        return text_field.strip()

    parts: list[str] = []
    for item in text_field:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            parts.append(item.get("text", ""))
    return "".join(parts).strip()


def parse_telegram_export(filepath: str, min_length: int = 15) -> list[dict[str, Any]]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    chat_name = data.get("name", "unknown_chat")
    messages = data.get("messages", [])

    records: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("type") != "message":
            continue

        clean_text = extract_clean_text(msg.get("text", ""))
        if len(clean_text) < min_length:
            continue

        from_name = msg.get("from", "Unknown")
        fwd_info = msg.get("forwarded_from", "")
        fwd_suffix = f" (fwd from {fwd_info})" if fwd_info else ""
        date = msg.get("date", "")

        enriched = (
            f"Автор: {from_name}{fwd_suffix}\n"
            f"Дата: {date}\n"
            f"Сообщение:\n"
            f"{clean_text}\n"
        )

        source = f"{chat_name}_msg_{msg['id']}"

        records.append({
            "content": enriched,
            "source": source,
            "type": "chat",
            "created_at": date,
        })

    return records


def import_telegram(filepath: str, min_length: int = 15) -> dict[str, int]:
    init_db()
    records = parse_telegram_export(filepath, min_length)

    if not records:
        return {"total": 0, "skipped": 0, "imported": 0}

    tuples = [
        (r["content"], r["source"], r["type"], r["created_at"])
        for r in records
    ]
    bulk_add_to_buffer(tuples)

    return {
        "total": len(records),
        "skipped": 0,
        "imported": len(records),
    }


def main():
    parser = argparse.ArgumentParser(description="Import Telegram export into RAG buffer")
    parser.add_argument("-f", "--file", default="result.json", help="Path to result.json")
    parser.add_argument("--min-length", type=int, default=15, help="Minimum text length to import")
    args = parser.parse_args()

    stats = import_telegram(args.file, args.min_length)
    print(f"Total messages: {stats['total']}")
    print(f"Imported:       {stats['imported']}")


if __name__ == "__main__":
    main()
