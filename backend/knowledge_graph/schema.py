"""
One-time Neo4j constraint setup — CompanyOS V3.1 Strategic Knowledge Graph.
Called from main.py at startup, mirroring core/database.py::create_tables().
"""
from __future__ import annotations
import logging

from knowledge_graph.client import get_driver

logger = logging.getLogger("companyos.knowledge_graph")


def setup_constraints() -> None:
    """Idempotent — CREATE CONSTRAINT IF NOT EXISTS is safe to run on every startup.
    Never lets a Neo4j outage block app startup; logs a warning and continues."""
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT competitor_name_unique IF NOT EXISTS "
                "FOR (c:Competitor) REQUIRE c.name IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT trend_name_unique IF NOT EXISTS "
                "FOR (t:Trend) REQUIRE t.name IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT research_run_id_unique IF NOT EXISTS "
                "FOR (r:ResearchRun) REQUIRE r.run_id IS UNIQUE"
            )
        logger.info("Neo4j constraints ready.")
    except Exception as e:
        logger.warning(f"Neo4j not reachable, skipping constraint setup: {e}")
