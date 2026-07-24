# MyRAG — Local RAG on GGUF Models

Fully offline RAG system for accumulating, indexing, and querying text over local GGUF models (LLM + embeddings).

## Data Flow

```
Source(s) → SQLite staging → LlamaIndex indexer (chunking + embeddings) → ChromaDB → LLM query engine
```

## Requirements

- **OS:** Linux (x86_64, AVX2), Python 3.10+
- **RAM:** 4 GB min, 8+ GB recommended
- **Models** (pre-downloaded to `~/models/`):
  - `qwen2.5-1.5b-instruct-q4_k_m.gguf` (LLM)
  - `nomic-embed-text-v1.5.Q4_K_M.gguf` (embedding)

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
CMAKE_ARGS="-DGGML_AVX2=ON -DGGML_FMA=ON" pip install llama-cpp-python
pip install -r requirements.txt
```

## Usage

```bash
# Add text
python cli.py add "your text" --source note --type text

# Add file (.docx / .pdf / .json for Telegram/Logseq export)
python cli.py add /path/to/file.docx --source report --type docx
python cli.py import-pdf -f doc.pdf
python cli.py import-tg -f telegram.json
python cli.py import-logseq -f logseq.json

# Index pending records
python cli.py index

# Ask a question
python cli.py ask "What is Python?"

# Show stats
python cli.py status
```

## GUI (Flet)

```bash
python app.py          # desktop window
MYRAG_WEB=1 python app.py   # web browser
./run.sh               # desktop
./run.sh --web         # web browser
```

## Configuration (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `N_THREADS` | 4 | CPU threads for LLM/embedding |
| `N_CTX` | 2048 | Context window size |
| `CHUNK_SIZE` | 512 | Chunk size in tokens |
| `CHUNK_OVERLAP` | 50 | Chunk overlap |
| `TOP_K` | 3 | Retrieved chunks per query |

## Performance (i5-4590, 16 GB)

| Operation | Time |
|-----------|------|
| 100 records → buffer | ~21 ms |
| Index 1 document | ~0.5 s |
| Index 100 documents | ~50 s |
| Answer a question | ~3–8 s |

## Schedule (cron)

```cron
0 3 * * * cd /home/user/myrag && .venv/bin/python cli.py index
```
