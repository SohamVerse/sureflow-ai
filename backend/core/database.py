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
    """Create all tables defined in models, then apply light additive migrations."""
    from models import vault, memory, auth, alert, kpi_snapshot  # noqa: F401
    from evaluation import models as evaluation_models  # noqa: F401
    from skill_registry import models as skill_registry_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _run_light_migrations()


def _run_light_migrations():
    """
    Idempotent ADD COLUMN migrations for columns introduced after a table was
    first created (create_all never ALTERs existing tables). Postgres supports
    IF NOT EXISTS, so this is safe to run on every startup.
    """
    from sqlalchemy import text
    statements = [
        "ALTER TABLE episodic_memories ADD COLUMN IF NOT EXISTS plant_id VARCHAR(50)",
        "ALTER TABLE reflection_memories ADD COLUMN IF NOT EXISTS plant_id VARCHAR(50)",
    ]
    try:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
    except Exception as e:
        import logging
        logging.getLogger("companyos.database").warning(f"Light migration skipped: {e}")
