"""
Sureflow Agentic OS — FastAPI Application Entry Point
"""
import sys

# Some log lines use emoji. On Windows, a process's stdout defaults to the
# system codepage (e.g. cp1252) rather than UTF-8 unless the console/terminal
# itself is UTF-8, which raises UnicodeEncodeError the first time an emoji is
# printed and crashes the request. Reconfiguring here makes stdout/stderr
# tolerate any Unicode regardless of how this process is launched or its
# output redirected.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import create_tables
from core.telemetry import setup_telemetry
from knowledge_graph.industrial_schema import setup_industrial_constraints
from api.routes import router
from api.industrial_routes import router as industrial_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    print("[START] Sureflow Agentic OS starting...")
    create_tables()
    print("[OK] PostgreSQL tables ready (pgvector Knowledge Vault included).")
    setup_industrial_constraints()
    print("[OK] Neo4j Industrial Knowledge Graph ready.")
    print("[READY] All agents standing by.")
    yield
    print("[STOP] Sureflow shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Industrial Intelligence Platform powered by local LLMs via Ollama.",
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
app.include_router(industrial_router, prefix="/api/v1")

setup_telemetry(app)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }
