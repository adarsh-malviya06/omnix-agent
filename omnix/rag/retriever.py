"""
Semantic search and knowledge retrieval service for OMNIX RAG.
Executes vector similarity search with cosine distance filtering and metadata enrichment.
"""

from typing import List, Optional

from omnix.rag.chroma_store import COLLECTION_NAME, get_chroma_manager, get_embedding_manager
from omnix.schemas.rag import DocumentChunk, KnowledgeQueryResponse


def retrieve_relevant_knowledge(
    query: str,
    top_k: int = 3,
    category_filter: Optional[str] = None,
    min_similarity: float = 0.30,
    collection_name: str = COLLECTION_NAME,
) -> KnowledgeQueryResponse:
    """
    Perform semantic search over the ingested procurement documents.

    Args:
        query: Natural language query.
        top_k: Maximum number of relevant chunks to return.
        category_filter: Optional category restriction.
        min_similarity: Minimum cosine similarity threshold (1.0 - cosine_distance).
        collection_name: ChromaDB collection name.

    Returns:
        KnowledgeQueryResponse with filtered, sorted chunks and metadata.
    """
    embed_mgr = get_embedding_manager()
    chroma_mgr = get_chroma_manager()
    collection = chroma_mgr.get_or_create_collection(collection_name)

    # Check if collection is empty
    if collection.count() == 0:
        return KnowledgeQueryResponse(
            query=query,
            total_results=0,
            chunks=[],
            has_relevant_content=False,
        )

    query_embedding = embed_mgr.embed_query(query)

    where_filter = None
    if category_filter and isinstance(category_filter, str) and category_filter.strip():
        where_filter = {"category": category_filter.strip()}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 2, max(collection.count(), 1)),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks: List[DocumentChunk] = []

    if results and results.get("ids") and results["ids"][0]:
        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for cid, text, meta, dist in zip(ids, docs, metas, distances):
            # In Chroma with cosine space: distance is (1 - cosine_similarity)
            # Thus similarity = 1.0 - distance
            similarity = round(max(0.0, 1.0 - float(dist)), 4)
            if similarity >= min_similarity:
                chunks.append(
                    DocumentChunk(
                        chunk_id=cid,
                        document_id=meta.get("document_id", "DOC"),
                        title=meta.get("title", "Untitled Policy"),
                        category=meta.get("category", "General"),
                        content=text,
                        metadata=meta,
                        similarity_score=similarity,
                    )
                )

    # Sort descending by similarity score and truncate to top_k
    chunks.sort(key=lambda x: x.similarity_score or 0.0, reverse=True)
    chunks = chunks[:top_k]

    return KnowledgeQueryResponse(
        query=query,
        total_results=len(chunks),
        chunks=chunks,
        has_relevant_content=len(chunks) > 0,
    )
