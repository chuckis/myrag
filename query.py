from typing import Generator, Sequence

import chromadb
from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import CHROMA_DIR, LLM_MODEL_PATH, N_THREADS, N_CTX, TOP_K
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


def ask_rag(query: str) -> str:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection("myrag")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    embed_model = LlamaCPPEmbedding()

    llm = LlamaCPP(
        model_path=LLM_MODEL_PATH,
        temperature=0.1,
        max_new_tokens=512,
        context_window=N_CTX,
        model_kwargs={"n_threads": N_THREADS, "verbose": False},
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        verbose=False,
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )

    query_engine = index.as_query_engine(
        llm=llm,
        similarity_top_k=TOP_K,
        text_qa_template=QA_PROMPT,
    )

    response = query_engine.query(query)
    return str(response).strip()


def ask_rag_stream(query: str) -> Generator[str, None, None]:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection("myrag")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    embed_model = LlamaCPPEmbedding()

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )

    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(query)
    context = "\n\n".join(n.node.text for n in nodes)

    prompt = QA_PROMPT.format(context_str=context, query_str=query)
    full_prompt = completion_to_prompt(prompt)

    from llama_cpp import Llama

    llm = Llama(
        model_path=LLM_MODEL_PATH,
        n_threads=N_THREADS,
        n_ctx=N_CTX,
        verbose=False,
    )

    stream = llm.create_completion(
        full_prompt,
        max_tokens=512,
        temperature=0.1,
        stream=True,
    )

    for output in stream:
        token = output["choices"][0]["text"]
        if token:
            yield token
