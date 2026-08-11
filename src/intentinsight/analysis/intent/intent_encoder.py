"""Semantic embedding encoder for pull-request intent."""

from __future__ import annotations

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_VERSION = "v1"


class IntentEncoder:
    """Encode pull-request intent text into semantic embeddings."""

    def __init__(
            self,
            model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self.model_name = model_name
        self.model_version = MODEL_VERSION
        self._model = SentenceTransformer(model_name)

    def encode(
            self,
            text: str,
    ) -> list[float]:
        """Encode one intent text."""

        embedding = self._model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embedding.astype(float).tolist()

    def encode_many(
            self,
            texts: Sequence[str],
    ) -> list[list[float]]:
        """Encode multiple intent texts."""

        embeddings = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return [
            embedding.astype(float).tolist()
            for embedding in embeddings
        ]