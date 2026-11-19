"""
FastAPI router for OMNIX RAG Knowledge System endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Query

from omnix.rag.document_loader import ingest_knowledge_directory
from omnix.rag.groq_service import GroqRAGService
from omnix.rag.retriever import retrieve_relevant_knowledge
from omnix.schemas.rag import (
    KnowledgeAnswerRequest,
    KnowledgeAnswerResponse,
    KnowledgeQueryResponse,
)

router = APIRouter(prefix="/knowledge", tags=["RAG Knowledge System"])


@router.get("/search", response_model=KnowledgeQueryResponse)
async def search_knowledge(
    q: str = Query(..., description="Natural language search query"),
    top_k: int = 3,
    category: Optional[str] = None,
    min_similarity: float = 0.30,
):
    """
    Search procurement policies and contracts using vector semantic similarity.
    """
    return retrieve_relevant_knowledge(
        query=q,
        top_k=top_k,
        category_filter=category,
        min_similarity=min_similarity,
    )


@router.post("/ask", response_model=KnowledgeAnswerResponse)
async def ask_policy_question(request: KnowledgeAnswerRequest):
    """
    Ask an operational procurement question and receive a grounded answer with citations.
    """
    service = GroqRAGService()
    return service.answer_question(
        question=request.question,
        top_k=request.top_k,
        category_filter=request.category_filter,
    )


@router.post("/reindex", response_model=dict)
async def reindex_knowledge():
    """
    Trigger re-indexing of all standard policy documents in data/knowledge/.
    """
    import os
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "knowledge")
    knowledge_dir = os.path.abspath(knowledge_dir)
    chunks_indexed = ingest_knowledge_directory(knowledge_dir)
    return {
        "status": "success",
        "directory": knowledge_dir,
        "chunks_indexed": chunks_indexed,
    }
