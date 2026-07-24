import hashlib
import json
import os
import time

import chromadb
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE
from embeddings import LlamaCPPEmbedding
from storage import get_unprocessed, mark_processed, parse_docx, save_indexing_run


def _load_known_hashes() -> set[str]:
    path = f"{CHROMA_DIR}/known_hashes.json"
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f))
    return set()


def _save_known_hashes(hashes: set[str]):
    os.makedirs(CHROMA_DIR, exist_ok=True)
    path = f"{CHROMA_DIR}/known_hashes.json"
    with open(path, "w") as f:
        json.dump(list(hashes), f)


def run_indexer():
    records = get_unprocessed()
    if not records:
        print("No new records to index.")
        return

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection("myrag")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    embed_model = LlamaCPPEmbedding()

    known_hashes = _load_known_hashes()

    new_docs = []
    skipped = 0
    processed_ids: list[int] = []
    for rec in records:
        content = rec["content"]
        doc_type = rec["type"]

        if doc_type == "docx":
            try:
                content = parse_docx(content)
            except Exception as e:
                print(f"  Failed to parse docx '{rec['source']}': {e}")
                continue

        doc_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if doc_hash in known_hashes:
            skipped += 1
            processed_ids.append(rec["id"])
            continue

        doc = Document(
            text=content,
            id_=doc_hash,
            metadata={
                "source": rec["source"],
                "type": doc_type,
                "created_at": rec.get("created_at", ""),
                "content_hash": doc_hash,
            },
        )
        new_docs.append(doc)
        processed_ids.append(rec["id"])

    if not new_docs:
        if processed_ids:
            mark_processed(processed_ids)
        print(
            f"No new documents to index ({skipped} skipped by dedup)."
        )
        if len(processed_ids) < len(records):
            print(
                f"  {len(records) - len(processed_ids)} records kept unprocessed due to errors."
            )
        return

    print(
        f"Indexing {len(new_docs)} new documents "
        f"({skipped} skipped by dedup)..."
    )

    docstore_path = f"{CHROMA_DIR}/docstore.json"
    docstore = SimpleDocumentStore()
    try:
        docstore = SimpleDocumentStore.from_persist_path(docstore_path)
    except (FileNotFoundError, ValueError):
        pass

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        docstore=docstore,
    )

    splitter = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    t0 = time.time()

    VectorStoreIndex.from_documents(
        new_docs,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[splitter],
        show_progress=True,
    )

    storage_context.docstore.persist(docstore_path)

    t1 = time.time()

    known_hashes.update(d.metadata["content_hash"] for d in new_docs)
    _save_known_hashes(known_hashes)

    mark_processed(processed_ids)
    print(f"Done. Indexed {len(new_docs)} documents.")

    duration = t1 - t0
    save_indexing_run(len(new_docs), duration)
    print(f"Indexing took {duration:.1f}s ({duration/60:.1f}min).")
