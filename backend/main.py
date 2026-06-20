"""
Sureflow Agentic OS — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import create_tables
from core.telemetry import setup_telemetry
from knowledge_graph.schema import setup_constraints
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    print("🚀 Sureflow Agentic OS starting...")
    create_tables()
    print("✅ PostgreSQL tables ready (pgvector Knowledge Vault included).")
    setup_constraints()
    print("✅ Neo4j Strategic Knowledge Graph ready.")
    print("🤖 All agents standing by.")
    yield
    print("👋 Sureflow shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-agent company management OS powered by local LLMs via Ollama.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

setup_telemetry(app)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }
