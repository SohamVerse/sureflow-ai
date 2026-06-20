from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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
    from models import pipeline, leads, vault, memory, constitution  # noqa: F401
    from evaluation import models as evaluation_models  # noqa: F401
    from meta_learning import models as meta_learning_models  # noqa: F401
    from skill_registry import models as skill_registry_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
