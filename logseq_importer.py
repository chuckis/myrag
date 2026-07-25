import json
import sys
import time
from typing import Any

from storage import bulk_add_to_buffer, init_db


def _extract_blocks(
    blocks: list[dict],
    page_name: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for block in blocks:
        content = block.get("content", "")
        if content and content.strip():
            records.append({
                "content": content.strip(),
                "source": page_name,
                "type": "logseq",
                "created_at": None,
            })
        children = block.get("children", [])
        if children:
            records.extend(_extract_blocks(children, page_name))
    return records


def parse_logseq_export(filepath: str) -> list[dict[str, Any]]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    blocks = data.get("blocks", [])
    records: list[dict[str, Any]] = []

    for block in blocks:
        page_name = block.get("page-name", "unknown_page")
        records.extend(_extract_blocks([block], page_name))

    return records


def import_logseq(filepath: str) -> dict[str, int]:
    init_db()

    t0 = time.perf_counter()
    records = parse_logseq_export(filepath)
    t1 = time.perf_counter()

    if not records:
        return {"total": 0, "imported": 0}

    tuples = [
        (r["content"], r["source"], r["type"], r["created_at"])
        for r in records
    ]

    t2 = time.perf_counter()
    bulk_add_to_buffer(tuples)
    t3 = time.perf_counter()

    print(f"[logseq] Parse: {t1-t0:.3f}s | SQLite: {t3-t2:.3f}s | Records: {len(records)}", file=sys.stderr)

    return {
        "total": len(records),
        "imported": len(records),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Import Logseq JSON export into RAG buffer")
    parser.add_argument("-f", "--file", default="export.json", help="Path to Logseq JSON export")
    args = parser.parse_args()

    stats = import_logseq(args.file)
    print(f"Total blocks: {stats['total']}")
    print(f"Imported:     {stats['imported']}")


if __name__ == "__main__":
    main()