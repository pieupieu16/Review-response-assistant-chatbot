"""Multilingual E5 embeddings with correct query/passage prefixes."""

import os

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "intfloat/multilingual-e5-large",
)


class MultilingualE5EmbeddingFunction(EmbeddingFunction[Documents]):
    """E5 models require 'query:' / 'passage:' prefixes for asymmetric retrieval."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self._model = SentenceTransformer(self.model_name)

    def embed_documents(self, texts: list[str]) -> Embeddings:
        prefixed = [f"passage: {text}" for text in texts]
        vectors = self._model.encode(prefixed, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        vector = self._model.encode([f"query: {query}"], normalize_embeddings=True)
        return vector[0].tolist()

    def __call__(self, input: Documents) -> Embeddings:
        return self.embed_documents(list(input))
