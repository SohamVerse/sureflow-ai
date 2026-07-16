from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# NeonDB requires SSL. The pooler endpoint already handles server-side
# connection pooling, so we keep the client pool small and use
# pool_pre_ping to detect dropped idle connections.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined in models."""
    from models import vault, memory  # noqa: F401
    from evaluation import models as evaluation_models  # noqa: F401
    from skill_registry import models as skill_registry_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
