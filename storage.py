import sqlite3

from config import DB_PATH


_conn: sqlite3.Connection | None = None


def get_setting(key: str) -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_all_settings() -> dict[str, str]:
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


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
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS indexing_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_count INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        _migrate()
        _conn.commit()
    return _conn


def _migrate():
    try:
        _conn.execute(
            "ALTER TABLE chat_history ADD COLUMN chat_id INTEGER REFERENCES chats(id)"
        )
    except sqlite3.OperationalError:
        pass

    row = _conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
    if row == 0:
        _conn.execute("INSERT INTO chats (title) VALUES (?)", ("General",))
        default_id = _conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        _conn.execute(
            "UPDATE chat_history SET chat_id = ? WHERE chat_id IS NULL",
            (default_id,),
        )

    _migrate_staging_types()


def _migrate_staging_types():
    try:
        _conn.execute(
            "ALTER TABLE staging ADD COLUMN _migrated INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        return

    _conn.execute(
        """CREATE TABLE staging_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('chat', 'docx', 'text', 'logseq')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            is_processed INTEGER NOT NULL DEFAULT 0
        )"""
    )
    _conn.execute(
        "INSERT INTO staging_new (id, content, source, type, created_at, is_processed) "
        "SELECT id, content, source, type, created_at, is_processed FROM staging"
    )
    _conn.execute("DROP TABLE staging")
    _conn.execute("ALTER TABLE staging_new RENAME TO staging")


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


def create_chat(title: str = "New Chat") -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO chats (title) VALUES (?)", (title,)
    )
    conn.commit()
    return cur.lastrowid


def rename_chat(chat_id: int, title: str):
    conn = _get_conn()
    conn.execute(
        "UPDATE chats SET title = ?, updated_at = datetime('now') WHERE id = ?",
        (title, chat_id),
    )
    conn.commit()


def delete_chat(chat_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()


def list_chats() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at FROM chats ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_chat_title(chat_id: int) -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT title FROM chats WHERE id = ?", (chat_id,)
    ).fetchone()
    return row["title"] if row else None


def save_chat(query: str, answer: str, chat_id: int | None = None):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_history (query, answer, chat_id) VALUES (?, ?, ?)",
        (query, answer, chat_id),
    )
    conn.commit()


def load_chat_history(chat_id: int, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_history WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def load_recent_chat_context(chat_id: int, n: int = 5) -> str:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT query, answer FROM chat_history WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, n),
    ).fetchall()
    rows = list(reversed(rows))
    parts: list[str] = []
    for r in rows:
        parts.append(f"User: {r['query']}")
        parts.append(f"Assistant: {r['answer']}")
    return "\n".join(parts)


def save_indexing_run(doc_count: int, duration: float):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO indexing_stats (doc_count, duration_seconds) VALUES (?, ?)",
        (doc_count, duration),
    )
    conn.commit()


def get_indexing_estimate(pending_count: int) -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT SUM(doc_count), SUM(duration_seconds), COUNT(*) FROM indexing_stats"
    ).fetchone()
    if not row or row[2] == 0 or row[0] is None or row[0] == 0:
        return None
    total_docs, total_secs, runs = row
    avg_secs_per_doc = total_secs / total_docs
    est_secs = avg_secs_per_doc * pending_count
    return f"~{est_secs:.0f}s ({runs} previous run{'s' if runs != 1 else ''})"


def parse_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
