import queue
import threading
from typing import Generator, Sequence

import chromadb
from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import (
    CHROMA_DIR, LLM_MODEL_PATH, N_THREADS, N_CTX, TOP_K,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_TIMEOUT, OPENROUTER_MAX_TOKENS,
)
from embeddings import LlamaCPPEmbedding

QA_PROMPT = PromptTemplate(
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the query.\n"
    "Query: {query_str}\n"
    "Answer: "
)


def messages_to_prompt(messages: Sequence[ChatMessage]) -> str:
    prompt = ""
    for msg in messages:
        role = msg.role.value
        content = msg.content
        prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt


def completion_to_prompt(completion: str) -> str:
    return (
        f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
        f"<|im_start|>user\n{completion}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def _get_local_llm() -> LlamaCPP:
    return LlamaCPP(
        model_path=LLM_MODEL_PATH,
        temperature=0.1,
        max_new_tokens=512,
        context_window=N_CTX,
        model_kwargs={"n_threads": N_THREADS, "verbose": False},
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        verbose=False,
    )


def _build_index():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection("myrag")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    embed_model = LlamaCPPEmbedding()
    return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)


def ask_rag(
    query: str,
    api_key: str = "",
    model_name: str = "",
    force_local: bool = False,
) -> str:
    index = _build_index()

    response = None
    effective_api_key = api_key or OPENROUTER_API_KEY
    effective_model = model_name or OPENROUTER_MODEL

    if not force_local and effective_api_key:
        try:
            from llama_index.llms.openrouter import OpenRouter

            remote_llm = OpenRouter(
                api_key=effective_api_key,
                model=effective_model,
                max_tokens=OPENROUTER_MAX_TOKENS,
                temperature=0.1,
                timeout=OPENROUTER_TIMEOUT,
            )
            query_engine = index.as_query_engine(
                llm=remote_llm,
                similarity_top_k=TOP_K,
                text_qa_template=QA_PROMPT,
            )
            response = query_engine.query(query)
        except Exception as e:
            print(
                f"\n⚠️ OpenRouter failed ({type(e).__name__}: {e}) — "
                f"falling back to local...",
                file=__import__("sys").stderr,
            )

    if response is None:
        local_llm = _get_local_llm()
        query_engine = index.as_query_engine(
            llm=local_llm,
            similarity_top_k=TOP_K,
            text_qa_template=QA_PROMPT,
        )
        response = query_engine.query(query)

    return str(response).strip()


def ask_rag_stream(
    query: str,
    chat_context: str = "",
    stop_event: threading.Event | None = None,
    api_key: str = "",
    model_name: str = "",
    force_local: bool = False,
) -> Generator[str, None, None]:
    index = _build_index()
    effective_api_key = api_key or OPENROUTER_API_KEY
    effective_model = model_name or OPENROUTER_MODEL

    if not force_local and effective_api_key:
        try:
            from llama_index.llms.openrouter import OpenRouter

            remote_llm = OpenRouter(
                api_key=effective_api_key,
                model=effective_model,
                max_tokens=OPENROUTER_MAX_TOKENS,
                temperature=0.1,
                timeout=OPENROUTER_TIMEOUT,
            )
            query_engine = index.as_query_engine(
                llm=remote_llm,
                similarity_top_k=TOP_K,
                text_qa_template=QA_PROMPT,
            )
            response = query_engine.query(query)
            yield str(response)
            return
        except Exception as e:
            yield (
                f"\n⚠️ OpenRouter failed ({type(e).__name__}: {e}) — "
                f"falling back to local...\n"
            )

    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(query)
    context = "\n\n".join(n.node.text for n in nodes)

    if chat_context:
        query_str = f"{chat_context}\n\nUser: {query}"
    else:
        query_str = query

    prompt = QA_PROMPT.format(context_str=context, query_str=query_str)
    full_prompt = completion_to_prompt(prompt)

    if stop_event and stop_event.is_set():
        return

    from llama_cpp import Llama

    llm = Llama(
        model_path=LLM_MODEL_PATH,
        n_threads=N_THREADS,
        n_ctx=N_CTX,
        verbose=False,
    )

    token_queue: queue.Queue[str | Exception | None] = queue.Queue(maxsize=4)

    def _produce():
        try:
            stream = llm.create_completion(
                full_prompt,
                max_tokens=512,
                temperature=0.1,
                stream=True,
            )
            for output in stream:
                if stop_event and stop_event.is_set():
                    break
                token = output["choices"][0]["text"]
                if token:
                    token_queue.put(token)
        except Exception as e:
            token_queue.put(e)
        finally:
            token_queue.put(None)

    threading.Thread(target=_produce, daemon=True).start()

    while True:
        try:
            item = token_queue.get(timeout=0.2)
        except queue.Empty:
            if stop_event and stop_event.is_set():
                break
            continue
        if item is None:
            break
        if isinstance(item, Exception):
            raise item
        yield item
