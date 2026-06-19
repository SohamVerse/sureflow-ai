from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Auto-detect database type from URL
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite: no pool_size, needs check_same_thread=False
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL: full connection pool
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
    from models import pipeline, leads  # noqa: F401
    Base.metadata.create_all(bind=engine)
