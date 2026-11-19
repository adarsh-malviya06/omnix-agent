"""
Document processing and ingestion pipeline for OMNIX RAG Knowledge System.
Loads text/markdown policy documents, extracts metadata, chunks text semantically,
generates embeddings, and stores them in ChromaDB.
"""

import glob
import os
import re
from typing import Any, Dict, List, Optional, TypeAlias

from omnix.rag.chroma_store import COLLECTION_NAME, get_chroma_manager, get_embedding_manager
from omnix.schemas.rag import DocumentChunk

# Type alias representing extracted document metadata dictionary structure
Tuple_Doc_Meta: TypeAlias = Dict[str, Any]


def extract_metadata_from_markdown(text: str, filename: str) -> Tuple_Doc_Meta:
    """
    Parse document header metadata (Document ID, Category, Title, Version)
    from markdown content.
    """
    lines = text.split("\n")
    title = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").title()
    doc_id = title
    category = "General Policy"
    version = "1.0"

    for line in lines[:15]:
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            title = stripped[2:].strip()
        elif stripped.startswith("Document ID:"):
            doc_id = stripped.replace("Document ID:", "").strip()
        elif stripped.startswith("Category:"):
            category = stripped.replace("Category:", "").strip()
        elif stripped.startswith("Version:"):
            version = stripped.replace("Version:", "").strip()

    meta = {
        "title": title,
        "document_id": doc_id,
        "category": category,
        "version": version,
        "source_file": os.path.basename(filename),
    }
    return meta


def chunk_document_by_sections(
    text: str, metadata: Dict[str, Any], max_chunk_chars: int = 800, overlap_chars: int = 100
) -> List[DocumentChunk]:
    """
    Chunk markdown documents preserving section headers and semantic boundaries.
    """
    # Split by section headers (## or ###)
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    chunks: List[DocumentChunk] = []
    chunk_index = 0

    doc_id = metadata.get("document_id", "DOC")
    title = metadata.get("title", "Document")
    category = metadata.get("category", "General")

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # If section is small enough, keep as single chunk
        if len(section) <= max_chunk_chars:
            chunk_id = f"{doc_id}_{chunk_index:03d}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    title=title,
                    category=category,
                    content=section,
                    metadata={**metadata, "chunk_index": chunk_index},
                )
            )
            chunk_index += 1
        else:
            # Sub-split long section with sliding window
            start = 0
            while start < len(section):
                end = min(start + max_chunk_chars, len(section))
                sub_text = section[start:end].strip()
                if sub_text:
                    chunk_id = f"{doc_id}_{chunk_index:03d}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=doc_id,
                            title=title,
                            category=category,
                            content=sub_text,
                            metadata={**metadata, "chunk_index": chunk_index},
                        )
                    )
                    chunk_index += 1
                start += max_chunk_chars - overlap_chars

    return chunks


def ingest_file(file_path: str, collection_name: str = COLLECTION_NAME) -> int:
    """
    Process, embed, and ingest a single text/markdown document into ChromaDB.
    Returns the count of chunks indexed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    metadata = extract_metadata_from_markdown(text, file_path)
    chunks = chunk_document_by_sections(text, metadata)

    if not chunks:
        return 0

    chroma_mgr = get_chroma_manager()
    embed_mgr = get_embedding_manager()
    collection = chroma_mgr.get_or_create_collection(collection_name)

    chunk_texts = [c.content for c in chunks]
    chunk_ids = [c.chunk_id for c in chunks]
    chunk_metas = [
        {
            "document_id": c.document_id,
            "title": c.title,
            "category": c.category,
            "source_file": metadata.get("source_file", ""),
            "version": metadata.get("version", "1.0"),
            "chunk_index": c.metadata.get("chunk_index", 0),
        }
        for c in chunks
    ]

    embeddings = embed_mgr.embed_texts(chunk_texts)

    collection.upsert(
        ids=chunk_ids,
        documents=chunk_texts,
        metadatas=chunk_metas,
        embeddings=embeddings,
    )

    return len(chunks)


def ingest_knowledge_directory(directory_path: str, collection_name: str = COLLECTION_NAME) -> int:
    """
    Batch process and index all markdown and text files in directory_path.
    Returns total chunks ingested.
    """
    if not os.path.isdir(directory_path):
        return 0

    md_files = glob.glob(os.path.join(directory_path, "*.md")) + glob.glob(os.path.join(directory_path, "*.txt"))
    total_indexed = 0

    for file_path in md_files:
        count = ingest_file(file_path, collection_name=collection_name)
        total_indexed += count

    return total_indexed
