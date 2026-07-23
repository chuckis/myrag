from typing import Any, Optional

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_cpp import Llama

from config import EMBED_MODEL_PATH, N_THREADS, N_CTX


class LlamaCPPEmbedding(BaseEmbedding):
    def __init__(
        self,
        model_path: str = EMBED_MODEL_PATH,
        n_threads: int = N_THREADS,
        n_ctx: int = N_CTX,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._model = Llama(
            model_path=model_path,
            n_threads=n_threads,
            n_ctx=n_ctx,
            verbose=False,
            embedding=True,
        )

    def _get_text_embedding(self, text: str) -> list[float]:
        result = self._model.create_embedding(text)
        return result["data"][0]["embedding"]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._get_text_embedding(t) for t in texts]

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)
