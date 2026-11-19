"""
Pydantic schemas for the RAG Knowledge Retrieval and LLM QA system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A semantic text chunk with associated document metadata."""
    chunk_id: str
    document_id: str
    title: str
    category: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: Optional[float] = Field(
        None, description="Cosine similarity score (0.0 to 1.0, higher is more relevant)"
    )


class KnowledgeQueryRequest(BaseModel):
    """User or agent semantic search request."""
    query: str = Field(..., description="Natural language search query or policy question")
    top_k: int = Field(default=3, ge=1, le=10, description="Maximum number of relevant chunks to retrieve")
    category_filter: Optional[str] = Field(
        None, description="Optional category filter (e.g. 'Spending Limits & Approval', 'Supplier Contract')"
    )
    min_similarity: float = Field(
        default=0.30, ge=0.0, le=1.0, description="Minimum relevance score threshold for filtering irrelevant chunks"
    )


class KnowledgeQueryResponse(BaseModel):
    """Response payload containing retrieved knowledge chunks and query context."""
    query: str
    total_results: int
    chunks: List[DocumentChunk]
    has_relevant_content: bool


class KnowledgeAnswerRequest(BaseModel):
    """Request to synthesize an authoritative grounded response using RAG + Groq LLM."""
    question: str = Field(..., description="User's operational or policy inquiry")
    top_k: int = Field(default=3, ge=1, le=6)
    category_filter: Optional[str] = None


class KnowledgeAnswerResponse(BaseModel):
    """Grounded LLM response backed by verified procurement source citations."""
    question: str
    answer: str
    is_grounded: bool = Field(description="True if answered from retrieved policy context; False if context was missing")
    sources_used: List[str] = Field(description="List of document IDs / titles cited in the response")
    retrieved_chunks: List[DocumentChunk] = Field(description="Context chunks supplied to the model")
    model_used: str
