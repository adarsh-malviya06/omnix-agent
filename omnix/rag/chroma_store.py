"""
Embedding model and ChromaDB client singleton manager for OMNIX RAG.
Uses sentence-transformers/all-MiniLM-L6-v2 and local PersistentClient.
"""

from functools import lru_cache
import os
from typing import List, Optional

# Ensure local offline cache is prioritized and Chroma telemetry is disabled
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from omnix.core.config import get_settings

COLLECTION_NAME = "omnix_procurement_knowledge"


class EmbeddingManager:
    """Manages local SentenceTransformer embedding generation."""

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute 384-dimensional dense embeddings for a list of strings."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Compute normalized vector for a single query."""
        emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        return emb[0].tolist()


@lru_cache()
def get_embedding_manager() -> EmbeddingManager:
    """Return cached singleton instance of EmbeddingManager."""
    return EmbeddingManager()


class ChromaDBManager:
    """Manages persistent ChromaDB vector store collection lifecycle."""

    def __init__(self, persist_directory: Optional[str] = None):
        settings = get_settings()
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, collection_name: str = COLLECTION_NAME):
        """Retrieve or create the procurement knowledge collection using cosine distance."""
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )


@lru_cache()
def get_chroma_manager() -> ChromaDBManager:
    """Return cached singleton instance of ChromaDBManager."""
    return ChromaDBManager()
