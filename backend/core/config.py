from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CompanyOS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://sureflow_user:sureflow_password@localhost:5432/sureflow_db"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Gemini
    GEMINI_API_KEY: str | None = None

    # ── Agent Brain Models ────────────────────────────────────────────────────
    CEO_MODEL: str = "gemini-1.5-pro"
    CMO_MODEL: str = "gemini-1.5-pro"
    RESEARCH_MODEL: str = "gemini-1.5-pro"
    SDR_MODEL: str = "gemini-1.5-pro"
    AE_MODEL: str = "gemini-1.5-pro"
    ANALYST_MODEL: str = "gemini-1.5-pro"
    EMAIL_MODEL: str = "gemini-1.5-pro"
    RISK_MODEL: str = "gemini-1.5-pro"          # NEW: Risk Analysis Brain
    POST_GEN_MODEL: str = "gemini-1.5-pro"      # NEW: Post Generation Brain
    AUTOMATION_MODEL: str = "gemini-1.5-pro"    # NEW: Automation Brain

    # ── Confidence Thresholds ─────────────────────────────────────────────────
    AUTO_APPROVE_CONFIDENCE: int = 75      # >= this → auto approve
    MANAGER_APPROVAL_CONFIDENCE: int = 50  # >= this → manager approval
    # < MANAGER threshold → CEO approval

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
