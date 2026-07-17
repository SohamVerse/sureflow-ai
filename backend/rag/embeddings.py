"""
Embeddings pipeline for the Knowledge Vault.
Handles ingestion of documents into pgvector-backed collections using Ollama embeddings.
"""
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from core.config import settings
from core.database import SessionLocal
from models.vault import VaultDocument
from skill_registry.registry import skill_registry

# Knowledge Vault collections matching the 6 synced folders
VAULT_COLLECTIONS = {
    "01-fintech-trends": "FinTech market trends and user engagement data",
    "02-lms-insights": "LMS/EdTech platform benchmarks and content",
    "03-icp-saas": "Ideal Customer Profile for Web/Mobile SaaS",
    "04-revenue-generation": "Strategies for generating new revenue streams",
    "05-social-media": "Recent social media trends and algorithm updates",
    "06-brand-voice": "Brand voice for a premium software development agency",
}

# Industrial Intelligence collections (Phase 1 extension)
INDUSTRIAL_COLLECTIONS = {
    "10-oem-manuals": "OEM equipment manuals and technical documentation",
    "11-compliance-regs": "OSHA, ISO, Factory Act, and regulatory texts",
    "12-sops": "Internal Standard Operating Procedures",
    "13-maintenance-logs": "Historical maintenance and work order records",
    "14-inspection-records": "Equipment inspection reports and audit findings",
    "15-incident-reports": "Safety incidents, near-misses, and CAPA reports",
}

# Combined registry for unified stat reporting
ALL_COLLECTIONS = {**VAULT_COLLECTIONS, **INDUSTRIAL_COLLECTIONS}


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
    embeddings = skill_registry.execute("ollama.embed", lambda: embedder.embed_documents(texts))

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


@lru_cache(maxsize=256)
def _embed_query_cached(query: str) -> tuple[float, ...]:
    """
    Cached query embedding — the Copilot and dashboards re-query the same
    handful of collections with overlapping/repeated questions, and each
    embed_query() call is a network round-trip to Ollama. Keyed on the exact
    query text, since embeddings are deterministic for a given model/text.
    """
    embedder = get_embeddings()
    vector = skill_registry.execute("ollama.embed", lambda: embedder.embed_query(query))
    return tuple(vector)


def query_collection(collection_name: str, query: str, n_results: int = 5, plant_id: Optional[str] = None) -> list[dict]:
    """
    Semantic search over a collection via pgvector cosine distance.
    Returns list of matching document chunks with metadata.
    """
    query_embedding = list(_embed_query_cached(query))

    db = SessionLocal()
    try:
        distance = VaultDocument.embedding.cosine_distance(query_embedding)
        base_query = db.query(VaultDocument, distance.label("distance")).filter(VaultDocument.collection == collection_name)
        
        if plant_id:
            base_query = base_query.filter(VaultDocument.meta_data["plant_id"].astext == plant_id)
            
        rows = base_query.order_by(distance).limit(n_results).all()
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
    """Return document counts for all Knowledge Vault collections (including industrial)."""
    db = SessionLocal()
    try:
        stats = {}
        for collection_name in ALL_COLLECTIONS.keys():
            stats[collection_name] = (
                db.query(VaultDocument)
                .filter(VaultDocument.collection == collection_name)
                .count()
            )
        return stats
    finally:
        db.close()
