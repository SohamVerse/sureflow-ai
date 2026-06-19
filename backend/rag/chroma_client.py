import chromadb
from chromadb.config import Settings
from core.config import settings as app_settings


def get_chroma_client() -> chromadb.HttpClient:
    """Return a connected ChromaDB HTTP client."""
    return chromadb.HttpClient(
        host=app_settings.CHROMA_HOST,
        port=app_settings.CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )


# Knowledge Vault collections matching the 6 synced folders
VAULT_COLLECTIONS = {
    "01-fintech-trends": "FinTech market trends and user engagement data",
    "02-lms-insights": "LMS/EdTech platform benchmarks and content",
    "03-icp-saas": "Ideal Customer Profile for Web/Mobile SaaS",
    "04-revenue-generation": "Strategies for generating new revenue streams",
    "05-social-media": "Recent social media trends and algorithm updates",
    "06-brand-voice": "Brand voice for a premium software development agency",
}


def ensure_collections(client: chromadb.HttpClient):
    """Create all Knowledge Vault collections if they don't exist."""
    existing = {col.name for col in client.list_collections()}
    for name, description in VAULT_COLLECTIONS.items():
        if name not in existing:
            client.create_collection(
                name=name,
                metadata={"description": description, "hnsw:space": "cosine"},
            )
