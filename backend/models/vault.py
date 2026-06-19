from sqlalchemy import Column, String, Text, DateTime, JSON, Uuid
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
import uuid
from core.database import Base

# Embedding dimension for the local Ollama "nomic-embed-text" model.
EMBEDDING_DIM = 768


class VaultDocument(Base):
    """A chunk of Knowledge Vault content, embedded for semantic search via pgvector."""
    __tablename__ = "vault_documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
