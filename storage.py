import sqlite3

from config import DB_PATH


_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS staging (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('chat', 'docx', 'text')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                is_processed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        _conn.commit()
    return _conn


def init_db():
    _get_conn()


def add_to_buffer(content: str, source: str, type_: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO staging (content, source, type) VALUES (?, ?, ?)",
        (content, source, type_),
    )
    conn.commit()


def bulk_add_to_buffer(records: list[tuple[str, str, str, str | None]]):
    conn = _get_conn()
    conn.executemany(
        "INSERT INTO staging (content, source, type, created_at) VALUES (?, ?, ?, COALESCE(?, datetime('now')))",
        records,
    )
    conn.commit()


def get_unprocessed() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM staging WHERE is_processed = 0 ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def mark_processed(ids: list[int]):
    if not ids:
        return
    conn = _get_conn()
    placeholders = ",".join("?" * len(ids))
    conn.execute(
        f"UPDATE staging SET is_processed = 1 WHERE id IN ({placeholders})", ids
    )
    conn.commit()


def get_stats() -> dict:
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM staging").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM staging WHERE is_processed = 0"
    ).fetchone()[0]
    return {"total": total, "pending": pending}


def save_chat(query: str, answer: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_history (query, answer) VALUES (?, ?)",
        (query, answer),
    )
    conn.commit()


def load_chat_history(limit: int = 5) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def load_recent_chat_context(n: int = 5) -> str:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT query, answer FROM chat_history ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    rows = list(reversed(rows))
    parts: list[str] = []
    for r in rows:
        parts.append(f"User: {r['query']}")
        parts.append(f"Assistant: {r['answer']}")
    return "\n".join(parts)


def parse_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
