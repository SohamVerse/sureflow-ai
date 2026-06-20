"""
KnowledgeGraphStore — CompanyOS V3.1 Strategic Knowledge Graph.

Turns the Research brain's competitor_intelligence/key_trends output (see
agents/research.py) into a queryable Neo4j graph with provenance: every
Competitor/Trend node is linked back to the ResearchRun(s) that identified it,
rather than collapsing everything into a single mutable "current belief" blob.

This is a structured memory of what the Research brain has concluded over
time — not ground-truth market data (no real web research/search integration
exists). Every method degrades gracefully (logs a warning, returns empty) if
Neo4j is unreachable, so an outage here never breaks a research call.
"""
from __future__ import annotations
import logging

from knowledge_graph.client import get_driver
from knowledge_graph.extraction import extract_competitors, extract_trends

logger = logging.getLogger("companyos.knowledge_graph")


class KnowledgeGraphStore:
    def record_research_output(self, research_output: dict, run_id: str, goal: str) -> None:
        """Persist this run's competitors/trends, linked to a ResearchRun node."""
        competitors = extract_competitors(research_output)
        trends = extract_trends(research_output)
        if not competitors and not trends:
            return
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(self._write_research_run, run_id, goal, competitors, trends)
            logger.info(
                "Recorded research run %s: %d competitor(s), %d trend(s)",
                run_id, len(competitors), len(trends),
            )
        except Exception as e:
            logger.warning(f"Failed to record research output to Neo4j: {e}")

    @staticmethod
    def _write_research_run(tx, run_id: str, goal: str, competitors: list[dict], trends: list[dict]):
        tx.run(
            "MERGE (r:ResearchRun {run_id: $run_id}) "
            "ON CREATE SET r.goal = $goal, r.created_at = datetime()",
            run_id=run_id, goal=goal,
        )
        for c in competitors:
            tx.run(
                """
                MERGE (comp:Competitor {name: $name})
                ON CREATE SET comp.mention_count = 1, comp.first_seen = datetime()
                ON MATCH SET comp.mention_count = comp.mention_count + 1
                SET comp.recent_moves = $recent_moves,
                    comp.weakness = $weakness,
                    comp.threat_level = $threat_level,
                    comp.last_seen = datetime()
                WITH comp
                MATCH (r:ResearchRun {run_id: $run_id})
                MERGE (r)-[:IDENTIFIED]->(comp)
                """,
                name=c["name"], recent_moves=c["recent_moves"], weakness=c["weakness"],
                threat_level=c["threat_level"], run_id=run_id,
            )
        for t in trends:
            tx.run(
                """
                MERGE (trend:Trend {name: $name})
                ON CREATE SET trend.mention_count = 1, trend.first_seen = datetime()
                ON MATCH SET trend.mention_count = trend.mention_count + 1
                SET trend.signal_strength = $signal_strength,
                    trend.implication = $implication,
                    trend.urgency = $urgency,
                    trend.last_seen = datetime()
                WITH trend
                MATCH (r:ResearchRun {run_id: $run_id})
                MERGE (r)-[:IDENTIFIED]->(trend)
                """,
                name=t["name"], signal_strength=t["signal_strength"], implication=t["implication"],
                urgency=t["urgency"], run_id=run_id,
            )

    # ── Prompt context (injected into RESEARCH_SYSTEM_PROMPT) ──────────────────

    def get_competitor_context(self, limit: int = 5) -> str:
        """Formatted text block of the most recently-seen competitors."""
        try:
            driver = get_driver()
            with driver.session() as session:
                rows = session.execute_read(self._read_competitors, limit)
        except Exception as e:
            logger.warning(f"Failed to read competitor context from Neo4j: {e}")
            return "Knowledge graph unavailable — proceed without competitor history."

        if not rows:
            return "No competitors on record yet."
        lines = ["Known competitors from past research (most recent first):"]
        for r in rows:
            lines.append(
                f"  • {r['name']} — threat: {r['threat_level']}, "
                f"mentioned {r['mention_count']}x, weakness: {r['weakness'] or 'unknown'}"
            )
        return "\n".join(lines)

    def get_trend_context(self, limit: int = 5) -> str:
        """Formatted text block of the most recently-seen trends."""
        try:
            driver = get_driver()
            with driver.session() as session:
                rows = session.execute_read(self._read_trends, limit)
        except Exception as e:
            logger.warning(f"Failed to read trend context from Neo4j: {e}")
            return "Knowledge graph unavailable — proceed without trend history."

        if not rows:
            return "No trends on record yet."
        lines = ["Known trends from past research (most recent first):"]
        for r in rows:
            lines.append(
                f"  • {r['name']} — signal: {r['signal_strength']}, mentioned {r['mention_count']}x"
            )
        return "\n".join(lines)

    # ── API-facing reads ─────────────────────────────────────────────────────────

    def get_competitors(self) -> list[dict]:
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_competitors, 100)
        except Exception as e:
            logger.warning(f"Failed to list competitors from Neo4j: {e}")
            return []

    def get_trends(self) -> list[dict]:
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_trends, 100)
        except Exception as e:
            logger.warning(f"Failed to list trends from Neo4j: {e}")
            return []

    def get_competitor_detail(self, name: str) -> dict | None:
        """One competitor plus the goals of every ResearchRun that identified it."""
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_competitor_detail, name)
        except Exception as e:
            logger.warning(f"Failed to read competitor detail from Neo4j: {e}")
            return None

    @staticmethod
    def _read_competitors(tx, limit: int) -> list[dict]:
        result = tx.run(
            "MATCH (c:Competitor) RETURN c.name AS name, c.threat_level AS threat_level, "
            "c.weakness AS weakness, c.recent_moves AS recent_moves, "
            "c.mention_count AS mention_count, toString(c.last_seen) AS last_seen "
            "ORDER BY c.last_seen DESC LIMIT $limit",
            limit=limit,
        )
        return [dict(r) for r in result]

    @staticmethod
    def _read_trends(tx, limit: int) -> list[dict]:
        result = tx.run(
            "MATCH (t:Trend) RETURN t.name AS name, t.signal_strength AS signal_strength, "
            "t.implication AS implication, t.urgency AS urgency, "
            "t.mention_count AS mention_count, toString(t.last_seen) AS last_seen "
            "ORDER BY t.last_seen DESC LIMIT $limit",
            limit=limit,
        )
        return [dict(r) for r in result]

    @staticmethod
    def _read_competitor_detail(tx, name: str) -> dict | None:
        result = tx.run(
            """
            MATCH (c:Competitor {name: $name})
            OPTIONAL MATCH (r:ResearchRun)-[:IDENTIFIED]->(c)
            RETURN c.name AS name, c.threat_level AS threat_level, c.weakness AS weakness,
                   c.recent_moves AS recent_moves, c.mention_count AS mention_count,
                   toString(c.last_seen) AS last_seen,
                   collect({run_id: r.run_id, goal: r.goal}) AS research_runs
            """,
            name=name,
        )
        record = result.single()
        return dict(record) if record else None


knowledge_graph = KnowledgeGraphStore()
