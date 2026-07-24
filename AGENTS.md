# MyRAG — Local RAG System

## Project Overview

A fully offline, local RAG (Retrieval-Augmented Generation) system using GGUF quantized models. Supports CLI and a Flet-based GUI. Data flows: sources → SQLite buffer → batch indexer (LlamaIndex + ChromaDB) → LLM query engine.

## Architecture

### Module Layout

| Module | Purpose |
|--------|---------|
| `config.py` | Paths (models, DB, Chroma), tuning params. All imports go through this. |
| `storage.py` | SQLite backend. Two tables: `staging` (content buffer) and `chat_history`. Singleton connection with WAL mode. |
| `embeddings.py` | `LlamaCPPEmbedding` — custom `BaseEmbedding` subclass wrapping `llama_cpp.Llama(embedding=True)`. |
| `indexer.py` | Batch indexer: reads `staging` → SHA256 dedup → `SentenceSplitter` → `ChromaVectorStore`. |
| `query.py` | RAG query engine: `ask_rag()` (sync) and `ask_rag_stream()` (token-by-token generator). Uses `LlamaCPP` for LLM. |
| `cli.py` | `argparse`-based CLI: `add`, `index`, `ask`, `status`. |
| `app.py` | Flet GUI entry point. Two-tab layout (Add + Chat). Toggle theme. Web mode via `MYRAG_WEB` env var. |
| `views/add_view.py` | Add/index tab: text/docx input, indexer runner with stdout capture in a thread. |
| `views/chat_view.py` | Chat tab: streaming answers, `ListView` for history, threading for async generation. |

### Data Flow

```
[CLI / GUI] → SQLite staging (fast write)
                  ↓ (manual or cron)
           LlamaIndex Indexer (chunking + embeddings)
                  ↓
           ChromaDB (vector store)
                  ↑
           LlamaIndex Query Engine (retrieval + LLM)
```

## Key Dependencies

- `llama-index` — RAG orchestration
- `chromadb` — vector store
- `llama-cpp-python` — local GGUF inference
- `flet` — GUI framework
- `python-docx` — .docx parsing
- `llama-index-vector-stores-chroma`, `llama-index-llms-llama-cpp`

## Models (must be pre-downloaded to `~/models/`)

- **LLM**: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- **Embedding**: `nomic-embed-text-v1.5.Q4_K_M.gguf`

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

## Key Commands

```bash
# Run CLI
python cli.py add "text content" --source my_source --type text
python cli.py add /path/to/doc.docx --source report --type docx
python cli.py index
python cli.py ask "your question"
python cli.py status

# Run GUI (desktop window)
python app.py

# Run GUI (web browser)
MYRAG_WEB=1 python app.py

# Via run.sh
./run.sh           # desktop
./run.sh --web     # web browser
```

## Configuration (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `N_THREADS` | 4 | CPU threads for LLM/embedding |
| `N_CTX` | 2048 | Context window size |
| `CHUNK_SIZE` | 512 | Chunk size in tokens |
| `CHUNK_OVERLAP` | 50 | Chunk overlap |
| `TOP_K` | 3 | Retrieved chunks per query |
