"""Cross-encoder reranking for retrieved passages."""

import os

from sentence_transformers import CrossEncoder

DEFAULT_RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)
DEFAULT_MIN_RERANK_SCORE = float(os.getenv("MIN_RERANK_SCORE", "-2.0"))


class PassageReranker:
    def __init__(self, model_name: str | None = None, min_score: float | None = None):
        self.model_name = model_name or DEFAULT_RERANKER_MODEL
        self.min_score = DEFAULT_MIN_RERANK_SCORE if min_score is None else min_score
        self._model = CrossEncoder(self.model_name)

    def rerank(self, query: str, passages: list[str], top_k: int = 3) -> list[str]:
        if not passages:
            return []

        pairs = [[query, passage] for passage in passages]
        scores = self._model.predict(pairs)
        ranked = sorted(zip(passages, scores), key=lambda item: item[1], reverse=True)

        selected = []
        for passage, score in ranked[:top_k]:
            if score >= self.min_score:
                selected.append(passage)

        return selected if selected else [ranked[0][0]]
