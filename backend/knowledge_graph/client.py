"""
Neo4j driver — CompanyOS V3.1 Strategic Knowledge Graph.
"""
from __future__ import annotations
import logging

from neo4j import Driver, GraphDatabase

from core.config import settings

logger = logging.getLogger("companyos.knowledge_graph")

_driver: Driver | None = None


def get_driver() -> Driver:
    """
    Lazily creates a single module-level driver (the neo4j driver manages its
    own connection pool internally — one Driver per process is correct).

    connection_timeout and max_transaction_retry_time are both cut down from
    the driver's 30s defaults to 3s: graph_store.py's whole point is to never
    let a Neo4j outage slow down or break a research call, but the default
    timeouts mean three calls (competitor context, trend context, record) each
    independently retrying for up to 30s turns "degrades gracefully" into a
    90+ second tax on every research call when Neo4j is down. Confirmed via a
    live test (stopped the neo4j container mid-run).
    """
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=3,
            max_transaction_retry_time=3,
        )
    return _driver
