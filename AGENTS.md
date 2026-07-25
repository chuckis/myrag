# MyRAG — Local RAG System

## Module Layout

| Module | Purpose |
|--------|---------|
| `config.py` | Paths (models, DB, Chroma), tuning params. All imports go through this. |
| `storage.py` | SQLite backend. Tables: `staging` (content buffer), `chat_history`, `chats`, `indexing_stats`, `settings` (key/value). Singleton connection with WAL mode. |
| `embeddings.py` | `LlamaCPPEmbedding` — custom `BaseEmbedding` subclass wrapping `llama_cpp.Llama(embedding=True)`. |
| `indexer.py` | Batch indexer: reads `staging` → SHA256 dedup → `SentenceSplitter` → `ChromaVectorStore`. |
| `query.py` | RAG query engine: `ask_rag()` (sync) and `ask_rag_stream()` (token-by-token generator). Supports OpenRouter with automatic fallback to local `LlamaCPP`. |
| `cli.py` | `argparse`-based CLI: `add`, `index`, `ask`, `status`. `ask` accepts `--model`, `--api-key`, `--force-local`. |
| `app.py` | Flet GUI entry point. Two-tab layout (Add + Chat). Toggle theme. Settings dialog. Web mode via `MYRAG_WEB` env var. |
| `views/add_view.py` | Add/index tab: text/docx input, indexer runner with stdout capture in a thread. |
| `views/chat_view.py` | Chat tab: streaming answers, `ListView` for history, threading for async generation, status bar (remote/local indicator). |
| `views/settings_view.py` | Settings dialog: API Key, model dropdown (10 presets + custom), Force Local switch. Persists to SQLite `settings` table. |

## Data Flow

```
[CLI / GUI] → SQLite staging (fast write)
                  ↓ (manual or cron)
           LlamaIndex Indexer (chunking + embeddings)
                  ↓
           ChromaDB (vector store)
                  ↑
           LlamaIndex Query Engine (retrieval + LLM)
```

## Code Conventions

- **Typing**: full type annotations required (`list[float]`, `-> None`, `|` union syntax)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Strings**: f-strings preferred
- **Error handling**: standard `try/except` with `Exception`; no custom exception classes
- **Imports**: standard lib → third-party → local (grouped with blank lines)
- **GUI threading**: long-running tasks (indexing, LLM streaming) run in `threading.Thread(daemon=True)`; UI updated via `page.update()`
- **DB pattern**: module-level `_conn` singleton via `_get_conn()`; `check_same_thread=False`; `PRAGMA journal_mode=WAL`
- **Config imports**: always import from `config.py`, never hardcode paths
- **Stdout capture**: `add_view.py` captures `sys.stdout` into `StringIO` for indexer log display

## Workflow

1. **README sync**: after every significant change, ask the user if README.md needs updating.
2. **Commit flow**: ask "коммитим?" before committing. If yes, write a brief English commit message (one-liner summary + bullet details) and run `git add -A && git commit -m "..."`.
