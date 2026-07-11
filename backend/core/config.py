from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CompanyOS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://sureflow_user:sureflow_password@localhost:5432/sureflow_db"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Gemini
    GEMINI_API_KEY: str | None = None

    # Neo4j (Industrial Knowledge Graph)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "sureflow_password"

    # ── Industrial Intelligence Agent Models (Phase 2) ─────────────────────────
    DOC_INTELLIGENCE_MODEL: str = "gemini-3.5-flash"    # Document Intelligence — OCR + entity extraction
    KG_AGENT_MODEL: str = "gemini-3.5-flash"          # Knowledge Graph Agent — entity resolution + graph writes
    SEARCH_AGENT_MODEL: str = "gemini-3.5-flash"        # Industrial Copilot — hybrid search + synthesis
    MAINTENANCE_MODEL: str = "gemini-3.5-flash"         # Maintenance Intelligence — RCA + failure prediction
    LESSONS_LEARNED_MODEL: str = "gemini-3.5-flash"   # Lessons Learned — incident parsing + warnings
    COMPLIANCE_MODEL: str = "gemini-3.5-flash"        # Compliance — regulation gap analysis

    # ── ModelBroker ────────────────────────────────────────────────────────────
    # Must match a model tag actually present in `ollama list` — if it isn't
    # pulled locally, LangChain's .with_fallbacks() swallows the fallback's own
    # error and re-raises the *original* (primary) error, which looks like the
    # fallback silently did nothing. Override via .env if you have a different
    # model pulled.
    FALLBACK_MODEL: str = "llama3.2"  # local Ollama model used when a primary model errors

    # ── OCR (Phase 5) ──────────────────────────────────────────────────────────
    # Path to the Tesseract binary — required on Windows where it isn't on PATH.
    # e.g. "C:\\Program Files\\Tesseract-OCR\\tesseract.exe". Leave unset on
    # Linux/Mac if tesseract is installed via a package manager (on PATH).
    TESSERACT_CMD: str | None = None
    # Path to the Poppler `bin` directory — required by pdf2image on Windows.
    POPPLER_PATH: str | None = None

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
