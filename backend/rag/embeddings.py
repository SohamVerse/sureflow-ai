"""
Embeddings pipeline for the Knowledge Vault.
Handles ingestion of documents into ChromaDB collections using Ollama embeddings.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional

import chromadb
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from rag.chroma_client import get_chroma_client, VAULT_COLLECTIONS
from core.config import settings


def get_embeddings():
    """Return the Ollama embeddings model (uses nomic-embed-text if available, else CEO model)."""
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
    Load, chunk, embed, and store a document in the specified ChromaDB collection.
    Returns a summary of what was ingested.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(collection_name)
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

    # Embed and store
    file_hash = _file_hash(file_path)
    ids = [f"{file_hash}-{i}" for i in range(len(chunks))]
    texts = [chunk.page_content for chunk in chunks]
    embeddings = embedder.embed_documents(texts)

    meta_list = []
    for chunk in chunks:
        m = {"source": str(path.name), "file_hash": file_hash}
        if metadata:
            m.update(metadata)
        meta_list.append(m)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=meta_list,
    )

    return {
        "collection": collection_name,
        "file": path.name,
        "chunks_ingested": len(chunks),
        "file_hash": file_hash,
    }


def query_collection(collection_name: str, query: str, n_results: int = 5) -> list[dict]:
    """
    Query a ChromaDB collection with semantic search.
    Returns list of matching document chunks with metadata.
    """
    client = get_chroma_client()
    embedder = get_embeddings()

    collection = client.get_or_create_collection(collection_name)
    query_embedding = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "content": doc,
            "metadata": meta,
            "relevance_score": round(1 - distance, 4),
        })

    return output


def get_vault_stats() -> dict:
    """Return document counts for all Knowledge Vault collections."""
    client = get_chroma_client()
    stats = {}
    for collection_name in VAULT_COLLECTIONS.keys():
        try:
            col = client.get_or_create_collection(collection_name)
            stats[collection_name] = col.count()
        except Exception:
            stats[collection_name] = 0
    return stats
