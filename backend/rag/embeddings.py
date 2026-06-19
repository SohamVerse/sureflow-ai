"""
Embeddings pipeline for the Knowledge Vault.
Handles ingestion of documents into pgvector-backed collections using Ollama embeddings.
"""
import hashlib
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from core.config import settings
from core.database import SessionLocal
from models.vault import VaultDocument

# Knowledge Vault collections matching the 6 synced folders
VAULT_COLLECTIONS = {
    "01-fintech-trends": "FinTech market trends and user engagement data",
    "02-lms-insights": "LMS/EdTech platform benchmarks and content",
    "03-icp-saas": "Ideal Customer Profile for Web/Mobile SaaS",
    "04-revenue-generation": "Strategies for generating new revenue streams",
    "05-social-media": "Recent social media trends and algorithm updates",
    "06-brand-voice": "Brand voice for a premium software development agency",
}


def get_embeddings():
    """Return the Ollama embeddings model (nomic-embed-text, 768 dims)."""
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model="nomic-embed-text",
    )


def _file_hash(path: str) -> str:
    """Return MD5 hash of file content for deduplication."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def ingest_document(file_path: str, collection_name: str, metadata: Optional[dict] = None) -> dict:
    """
    Load, chunk, embed, and store a document as pgvector rows in the given collection.
    Returns a summary of what was ingested.
    """
    embedder = get_embeddings()

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    # Load document based on extension
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    documents = loader.load()

    # Chunk documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    chunks = splitter.split_documents(documents)

    file_hash = _file_hash(file_path)
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embedder.embed_documents(texts)

    db = SessionLocal()
    try:
        for text, embedding in zip(texts, embeddings):
            meta = {"source": path.name, "file_hash": file_hash}
            if metadata:
                meta.update(metadata)
            db.add(VaultDocument(
                collection=collection_name,
                content=text,
                embedding=embedding,
                meta_data=meta,
            ))
        db.commit()
    finally:
        db.close()

    return {
        "collection": collection_name,
        "file": path.name,
        "chunks_ingested": len(chunks),
        "file_hash": file_hash,
    }


def query_collection(collection_name: str, query: str, n_results: int = 5) -> list[dict]:
    """
    Semantic search over a collection via pgvector cosine distance.
    Returns list of matching document chunks with metadata.
    """
    embedder = get_embeddings()
    query_embedding = embedder.embed_query(query)

    db = SessionLocal()
    try:
        distance = VaultDocument.embedding.cosine_distance(query_embedding)
        rows = (
            db.query(VaultDocument, distance.label("distance"))
            .filter(VaultDocument.collection == collection_name)
            .order_by(distance)
            .limit(n_results)
            .all()
        )
    finally:
        db.close()

    return [
        {
            "content": doc.content,
            "metadata": doc.meta_data,
            "relevance_score": round(1 - dist, 4),
        }
        for doc, dist in rows
    ]


def get_vault_stats() -> dict:
    """Return document counts for all Knowledge Vault collections."""
    db = SessionLocal()
    try:
        stats = {}
        for collection_name in VAULT_COLLECTIONS.keys():
            stats[collection_name] = (
                db.query(VaultDocument)
                .filter(VaultDocument.collection == collection_name)
                .count()
            )
        return stats
    finally:
        db.close()
