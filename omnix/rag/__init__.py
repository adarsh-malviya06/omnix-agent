"""
OMNIX RAG Knowledge System package initialization.
"""

from omnix.rag.chroma_store import (
    COLLECTION_NAME,
    ChromaDBManager,
    EmbeddingManager,
    get_chroma_manager,
    get_embedding_manager,
)
from omnix.rag.document_loader import (
    chunk_document_by_sections,
    extract_metadata_from_markdown,
    ingest_file,
    ingest_knowledge_directory,
)
from omnix.rag.groq_service import GroqRAGService
from omnix.rag.retriever import retrieve_relevant_knowledge

__all__ = [
    "COLLECTION_NAME",
    "ChromaDBManager",
    "EmbeddingManager",
    "get_chroma_manager",
    "get_embedding_manager",
    "extract_metadata_from_markdown",
    "chunk_document_by_sections",
    "ingest_file",
    "ingest_knowledge_directory",
    "retrieve_relevant_knowledge",
    "GroqRAGService",
]
