import os
from pathlib import Path

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = str(BASE_DIR / "buffer.db")
CHROMA_DIR = str(BASE_DIR / "chroma_db")

MODELS_DIR = os.path.expanduser("~/models")
LLM_MODEL_PATH = f"{MODELS_DIR}/qwen2.5-1.5b-instruct-q4_k_m.gguf"
EMBED_MODEL_PATH = f"{MODELS_DIR}/nomic-embed-text-v1.5.Q4_K_M.gguf"

N_THREADS = 4
N_CTX = 2048

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
TOP_K = 3
