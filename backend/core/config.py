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

    # ── Agent Brain Models ────────────────────────────────────────────────────
    # gemini-2.5-pro has a 0-request free-tier quota on this key (confirmed via
    # 429 RESOURCE_EXHAUSTED) and ~40s latency even on trivial prompts due to
    # extended thinking — gemini-2.5-flash is used wherever Gemini is needed.
    CEO_MODEL: str = "gemini-1.5-pro"
    CMO_MODEL: str = "gemini-1.5-pro"
    RESEARCH_MODEL: str = "gemini-1.5-pro"
    SDR_MODEL: str = "gemini-1.5-pro"
    AE_MODEL: str = "gemini-1.5-pro"
    ANALYST_MODEL: str = "gemini-1.5-pro"
    EMAIL_MODEL: str = "gemini-2.5-flash"       # cheap/fast tier — high volume outreach drafting
    RISK_MODEL: str = "gemini-2.5-flash"        # NEW: Risk Analysis Brain — see note below
    POST_GEN_MODEL: str = "gemini-2.5-flash"    # NEW: Post Generation Brain
    AUTOMATION_MODEL: str = "gemini-2.5-flash"  # NEW: Automation Brain

    # ── ModelBroker ────────────────────────────────────────────────────────────
    FALLBACK_MODEL: str = "llama3:8b"  # local Ollama model used when a primary model errors

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
