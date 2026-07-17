"""
IndustrialGraphStore — Industrial Knowledge Graph for SureFlow OS.

Extends the strategic knowledge graph (graph_store.py) with an industrial
ontology: Plant → Area → Equipment → Incidents/WorkOrders/Documents.

Every method degrades gracefully (logs a warning, returns empty) if
Neo4j is unreachable, matching the existing graph_store.py contract.
"""
from __future__ import annotations
import logging
import time
from typing import Optional

from knowledge_graph.client import get_driver

logger = logging.getLogger("companyos.knowledge_graph.industrial")

# get_industrial_overview() is called on every single Copilot query (as prompt
# context) plus the KPI/graph-overview endpoints — the node/edge counts it
# reports change rarely, so a short TTL cache avoids hitting Neo4j on every
# call without ever serving data more than a few seconds stale.
_OVERVIEW_CACHE_TTL_SECONDS = 30


class IndustrialGraphStore:
    """
    Read/write interface for the Industrial Knowledge Graph.

    Ontology (from docs/hackathon/ontology.md):
      Spatial:  Plant → Area
      Assets:   AssetClass, Equipment, Sensor, Part
      Docs:     Document, DocumentChunk
      Events:   WorkOrder, Inspection, Incident, Audit
      People:   Operator, Engineer, Vendor, OEM
    """

    # ── Write Methods ──────────────────────────────────────────────────────────

    def record_plant(self, plant_id: str, name: str, location: str = "") -> None:
        """Create or update a Plant node."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_plant, plant_id, name, location
                )
            logger.info("Recorded plant: %s", name)
        except Exception as e:
            logger.warning(f"Failed to record plant to Neo4j: {e}")

    def record_area(self, area_id: str, name: str, plant_id: str) -> None:
        """Create an Area node and link it to its parent Plant."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_area, area_id, name, plant_id
                )
            logger.info("Recorded area: %s → Plant %s", name, plant_id)
        except Exception as e:
            logger.warning(f"Failed to record area to Neo4j: {e}")

    def record_equipment(
        self,
        equipment_tag: str,
        name: str,
        area_id: str,
        asset_class: str = "",
        oem: str = "",
    ) -> None:
        """Create an Equipment node linked to an Area (and optionally AssetClass/OEM)."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_equipment, equipment_tag, name, area_id, asset_class, oem
                )
            logger.info("Recorded equipment: %s in area %s", equipment_tag, area_id)
        except Exception as e:
            logger.warning(f"Failed to record equipment to Neo4j: {e}")

    def record_incident(
        self,
        incident_id: str,
        title: str,
        description: str,
        equipment_tag: str,
        severity: str = "medium",
        reported_by: str = "",
        date: str = "",
    ) -> None:
        """Create an Incident node linked to the involved Equipment."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_incident,
                    incident_id, title, description, equipment_tag,
                    severity, reported_by, date,
                )
            logger.info("Recorded incident: %s on %s", incident_id, equipment_tag)
        except Exception as e:
            logger.warning(f"Failed to record incident to Neo4j: {e}")

    def record_work_order(
        self,
        wo_id: str,
        title: str,
        description: str,
        equipment_tag: str,
        wo_type: str = "corrective",
        assigned_to: str = "",
        status: str = "open",
        incident_id: Optional[str] = None,
    ) -> None:
        """Create a WorkOrder node linked to Equipment (and optionally resolving an Incident)."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_work_order,
                    wo_id, title, description, equipment_tag,
                    wo_type, assigned_to, status, incident_id,
                )
            logger.info("Recorded work order: %s on %s", wo_id, equipment_tag)
        except Exception as e:
            logger.warning(f"Failed to record work order to Neo4j: {e}")

    def record_document(
        self,
        doc_id: str,
        title: str,
        doc_type: str,
        equipment_tag: str = "",
        area_id: str = "",
    ) -> None:
        """Create a Document node and optionally link to Equipment or Area."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_document, doc_id, title, doc_type, equipment_tag, area_id
                )
            logger.info("Recorded document: %s (%s)", title, doc_type)
        except Exception as e:
            logger.warning(f"Failed to record document to Neo4j: {e}")

    def record_inspection(
        self,
        inspection_id: str,
        title: str,
        equipment_tag: str,
        inspector: str = "",
        result: str = "pass",
        date: str = "",
    ) -> None:
        """Create an Inspection node linked to Equipment."""
        try:
            driver = get_driver()
            with driver.session() as session:
                session.execute_write(
                    self._merge_inspection,
                    inspection_id, title, equipment_tag, inspector, result, date,
                )
            logger.info("Recorded inspection: %s on %s", inspection_id, equipment_tag)
        except Exception as e:
            logger.warning(f"Failed to record inspection to Neo4j: {e}")

    # ── Read Methods ───────────────────────────────────────────────────────────

    def find_area_id(self, name_hint: str) -> Optional[str]:
        """
        Best-effort resolve a free-text area name — as extracted from an
        uploaded document, e.g. "Pump House A" rather than "AREA-100" — to an
        existing Area's area_id, so newly ingested Equipment/Document nodes
        link into the existing Plant hierarchy instead of ending up orphaned.
        """
        if not name_hint:
            return None
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_area_id_by_name, name_hint)
        except Exception as e:
            logger.warning(f"Failed to resolve area by name '{name_hint}': {e}")
            return None

    def get_asset_timeline(self, equipment_tag: str, limit: int = 20) -> list[dict]:
        """
        Traverse the graph to return all incidents, work orders, and inspections
        linked to a specific asset, in reverse chronological order.
        """
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_asset_timeline, equipment_tag, limit)
        except Exception as e:
            logger.warning(f"Failed to read asset timeline from Neo4j: {e}")
            return []

    def get_equipment_details(self, equipment_tag: str) -> dict | None:
        """Full details for a single Equipment node plus connected entities."""
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_equipment_detail, equipment_tag)
        except Exception as e:
            logger.warning(f"Failed to read equipment detail from Neo4j: {e}")
            return None

    def get_plant_hierarchy(self, plant_id: Optional[str] = None) -> list[dict]:
        """
        Return the full Plant -> Area -> Equipment tree as a nested
        {id, name, type, children, ...} structure — the shape the frontend's
        PlantHierarchyTree component renders.
        """
        try:
            driver = get_driver()
            with driver.session() as session:
                rows = session.execute_read(self._read_plant_hierarchy, plant_id)
            return [self._to_hierarchy_node(row) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to read plant hierarchy from Neo4j: {e}")
            return []

    @staticmethod
    def _to_hierarchy_node(row: dict) -> dict:
        """Convert one raw _read_plant_hierarchy row into a nested tree node."""
        area_nodes = []
        total_equipment = 0
        for area in (row.get("areas") or []):
            equipment_nodes = [
                {"id": eq.get("tag"), "name": eq.get("name"), "type": "equipment", "tag": eq.get("tag")}
                for eq in (area.get("equipment") or []) if eq.get("tag")
            ]
            total_equipment += len(equipment_nodes)
            area_nodes.append({
                "id": area.get("area_id"),
                "name": area.get("area_name"),
                "type": "area",
                "children": equipment_nodes,
                "equipment_count": len(equipment_nodes),
            })
        return {
            "id": row.get("plant_id"),
            "name": row.get("plant_name"),
            "type": "plant",
            "children": area_nodes,
            "equipment_count": total_equipment,
        }

    def get_all_equipment(self, plant_id: Optional[str] = None) -> list[dict]:
        """Return all equipment nodes."""
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_all_equipment, plant_id)
        except Exception as e:
            logger.warning(f"Failed to list equipment from Neo4j: {e}")
            return []

    def get_all_incidents(self, limit: int = 50, plant_id: Optional[str] = None) -> list[dict]:
        """Return recent incidents."""
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_all_incidents, limit, plant_id)
        except Exception as e:
            logger.warning(f"Failed to list incidents from Neo4j: {e}")
            return []

    def get_compliance_gaps(self, area_id: str) -> list[dict]:
        """
        Find equipment in an area that has incidents but no recent inspections,
        suggesting a compliance gap.
        """
        try:
            driver = get_driver()
            with driver.session() as session:
                return session.execute_read(self._read_compliance_gaps, area_id)
        except Exception as e:
            logger.warning(f"Failed to read compliance gaps from Neo4j: {e}")
            return []

    # ── Prompt Context (for agent injection) ───────────────────────────────────

    def get_equipment_context(self, equipment_tag: str) -> str:
        """Formatted text block for injecting into agent prompts."""
        detail = self.get_equipment_details(equipment_tag)
        if not detail:
            return f"No knowledge graph data for equipment '{equipment_tag}'."
        lines = [f"Equipment {detail['tag']} ({detail['name']}):"]
        lines.append(f"  Area: {detail.get('area', 'unknown')}")
        lines.append(f"  Class: {detail.get('asset_class', 'unknown')}")
        lines.append(f"  OEM: {detail.get('oem', 'unknown')}")
        if detail.get("incidents"):
            lines.append(f"  Recent incidents: {len(detail['incidents'])}")
            for inc in detail["incidents"][:3]:
                lines.append(f"    • [{inc.get('severity', '?')}] {inc.get('title', '')}")
        if detail.get("work_orders"):
            lines.append(f"  Recent work orders: {len(detail['work_orders'])}")
        return "\n".join(lines)

    _stats_cache: Optional[dict] = None
    _stats_cache_at: float = 0.0

    def _get_cached_graph_stats(self) -> dict:
        """Raw {label: count} node counts, cached for _OVERVIEW_CACHE_TTL_SECONDS
        since this hits Neo4j on every Copilot query and dashboard load for
        counts that rarely change. Backs both get_industrial_overview() (text,
        for agent prompt context) and get_graph_stats() (structured, for the
        dashboard API)."""
        now = time.monotonic()
        if self._stats_cache is not None and (now - self._stats_cache_at) < _OVERVIEW_CACHE_TTL_SECONDS:
            return self._stats_cache

        try:
            driver = get_driver()
            with driver.session() as session:
                stats = session.execute_read(self._read_graph_stats)
        except Exception as e:
            logger.warning(f"Failed to read graph stats: {e}")
            stats = {}

        self._stats_cache = stats
        self._stats_cache_at = now
        return stats

    def get_industrial_overview(self) -> str:
        """Summary of the industrial knowledge graph for CEO/Copilot context."""
        stats = self._get_cached_graph_stats()
        if not stats:
            return "Industrial Knowledge Graph unavailable."
        lines = ["Industrial Knowledge Graph Summary:"]
        for label, count in stats.items():
            lines.append(f"  • {label}: {count}")
        return "\n".join(lines)

    def get_graph_stats(self) -> dict:
        """Structured node counts for the dashboard's KPI tiles and Knowledge
        Graph Stats panel — matches the frontend's GraphOverview type exactly
        (plants, areas, equipment, incidents, work_orders, inspections,
        documents), unlike get_industrial_overview()'s prompt-context string."""
        stats = self._get_cached_graph_stats()
        return {
            "plants": stats.get("Plant", 0),
            "areas": stats.get("Area", 0),
            "equipment": stats.get("Equipment", 0),
            "incidents": stats.get("Incident", 0),
            "work_orders": stats.get("WorkOrder", 0),
            "inspections": stats.get("Inspection", 0),
            "documents": stats.get("Document", 0),
        }

    # ── Static transaction methods ─────────────────────────────────────────────

    @staticmethod
    def _merge_plant(tx, plant_id: str, name: str, location: str):
        tx.run(
            """
            MERGE (p:Plant {plant_id: $plant_id})
            ON CREATE SET p.name = $name, p.location = $location, p.created_at = datetime()
            ON MATCH SET p.name = $name, p.location = $location, p.updated_at = datetime()
            """,
            plant_id=plant_id, name=name, location=location,
        )

    @staticmethod
    def _merge_area(tx, area_id: str, name: str, plant_id: str):
        tx.run(
            """
            MERGE (a:Area {area_id: $area_id})
            ON CREATE SET a.name = $name, a.created_at = datetime()
            ON MATCH SET a.name = $name, a.updated_at = datetime()
            WITH a
            MATCH (p:Plant {plant_id: $plant_id})
            MERGE (p)-[:CONTAINS]->(a)
            """,
            area_id=area_id, name=name, plant_id=plant_id,
        )

    @staticmethod
    def _merge_equipment(tx, equipment_tag: str, name: str, area_id: str, asset_class: str, oem: str):
        tx.run(
            """
            MERGE (e:Equipment {tag: $tag})
            ON CREATE SET e.name = $name, e.created_at = datetime()
            ON MATCH SET e.name = $name, e.updated_at = datetime()
            WITH e
            MATCH (a:Area {area_id: $area_id})
            MERGE (a)-[:CONTAINS]->(e)
            """,
            tag=equipment_tag, name=name, area_id=area_id,
        )
        if asset_class:
            tx.run(
                """
                MERGE (ac:AssetClass {name: $ac_name})
                WITH ac
                MATCH (e:Equipment {tag: $tag})
                MERGE (e)-[:IS_TYPE]->(ac)
                """,
                ac_name=asset_class, tag=equipment_tag,
            )
        if oem:
            tx.run(
                """
                MERGE (o:OEM {name: $oem_name})
                WITH o
                MATCH (e:Equipment {tag: $tag})
                MERGE (e)-[:MANUFACTURED_BY]->(o)
                """,
                oem_name=oem, tag=equipment_tag,
            )

    @staticmethod
    def _merge_incident(
        tx, incident_id: str, title: str, description: str,
        equipment_tag: str, severity: str, reported_by: str, date: str,
    ):
        tx.run(
            """
            MERGE (i:Incident {incident_id: $incident_id})
            ON CREATE SET i.title = $title, i.description = $description,
                          i.severity = $severity, i.date = $date, i.created_at = datetime()
            ON MATCH SET  i.title = $title, i.description = $description,
                          i.severity = $severity, i.updated_at = datetime()
            WITH i
            MATCH (e:Equipment {tag: $tag})
            MERGE (i)-[:INVOLVED]->(e)
            """,
            incident_id=incident_id, title=title, description=description,
            severity=severity, tag=equipment_tag, date=date,
        )
        if reported_by:
            tx.run(
                """
                MERGE (op:Operator {name: $name})
                WITH op
                MATCH (i:Incident {incident_id: $incident_id})
                MERGE (i)-[:REPORTED_BY]->(op)
                """,
                name=reported_by, incident_id=incident_id,
            )

    @staticmethod
    def _merge_work_order(
        tx, wo_id: str, title: str, description: str, equipment_tag: str,
        wo_type: str, assigned_to: str, status: str, incident_id: Optional[str],
    ):
        tx.run(
            """
            MERGE (wo:WorkOrder {wo_id: $wo_id})
            ON CREATE SET wo.title = $title, wo.description = $description,
                          wo.type = $wo_type, wo.status = $status, wo.created_at = datetime()
            ON MATCH SET  wo.title = $title, wo.description = $description,
                          wo.type = $wo_type, wo.status = $status, wo.updated_at = datetime()
            WITH wo
            MATCH (e:Equipment {tag: $tag})
            MERGE (wo)-[:PERFORMED_ON]->(e)
            """,
            wo_id=wo_id, title=title, description=description,
            wo_type=wo_type, tag=equipment_tag, status=status,
        )
        if assigned_to:
            tx.run(
                """
                MERGE (op:Operator {name: $name})
                WITH op
                MATCH (wo:WorkOrder {wo_id: $wo_id})
                MERGE (wo)-[:ASSIGNED_TO]->(op)
                """,
                name=assigned_to, wo_id=wo_id,
            )
        if incident_id:
            tx.run(
                """
                MATCH (wo:WorkOrder {wo_id: $wo_id})
                MATCH (i:Incident {incident_id: $incident_id})
                MERGE (wo)-[:RESOLVED]->(i)
                """,
                wo_id=wo_id, incident_id=incident_id,
            )

    @staticmethod
    def _merge_document(tx, doc_id: str, title: str, doc_type: str, equipment_tag: str, area_id: str):
        tx.run(
            """
            MERGE (d:Document {doc_id: $doc_id})
            ON CREATE SET d.title = $title, d.type = $doc_type, d.created_at = datetime()
            ON MATCH SET  d.title = $title, d.type = $doc_type, d.updated_at = datetime()
            """,
            doc_id=doc_id, title=title, doc_type=doc_type,
        )
        if equipment_tag:
            tx.run(
                """
                MATCH (d:Document {doc_id: $doc_id})
                MATCH (e:Equipment {tag: $tag})
                MERGE (e)-[:HAS_MANUAL]->(d)
                """,
                doc_id=doc_id, tag=equipment_tag,
            )
        if area_id:
            tx.run(
                """
                MATCH (d:Document {doc_id: $doc_id})
                MATCH (a:Area {area_id: $area_id})
                MERGE (a)-[:GOVERNED_BY]->(d)
                """,
                doc_id=doc_id, area_id=area_id,
            )

    @staticmethod
    def _merge_inspection(
        tx, inspection_id: str, title: str, equipment_tag: str,
        inspector: str, result: str, date: str,
    ):
        tx.run(
            """
            MERGE (insp:Inspection {inspection_id: $inspection_id})
            ON CREATE SET insp.title = $title, insp.result = $result,
                          insp.date = $date, insp.created_at = datetime()
            ON MATCH SET  insp.title = $title, insp.result = $result, insp.updated_at = datetime()
            WITH insp
            MATCH (e:Equipment {tag: $tag})
            MERGE (insp)-[:INSPECTED]->(e)
            """,
            inspection_id=inspection_id, title=title, tag=equipment_tag,
            result=result, date=date,
        )
        if inspector:
            tx.run(
                """
                MERGE (eng:Engineer {name: $name})
                WITH eng
                MATCH (insp:Inspection {inspection_id: $inspection_id})
                MERGE (insp)-[:PERFORMED_BY]->(eng)
                """,
                name=inspector, inspection_id=inspection_id,
            )

    # ── Read transaction methods ───────────────────────────────────────────────

    @staticmethod
    def _read_area_id_by_name(tx, name_hint: str) -> Optional[str]:
        result = tx.run(
            """
            MATCH (a:Area)
            WHERE a.area_id = $name_hint
               OR toLower(a.name) CONTAINS toLower($name_hint)
               OR toLower($name_hint) CONTAINS toLower(a.name)
            RETURN a.area_id AS area_id
            LIMIT 1
            """,
            name_hint=name_hint,
        )
        record = result.single()
        return record["area_id"] if record else None

    @staticmethod
    def _read_asset_timeline(tx, equipment_tag: str, limit: int) -> list[dict]:
        result = tx.run(
            """
            MATCH (e:Equipment {tag: $tag})
            OPTIONAL MATCH (i:Incident)-[:INVOLVED]->(e)
            WITH e, collect(DISTINCT {type: 'incident', id: i.incident_id, title: i.title,
                    severity: i.severity, date: COALESCE(i.date, toString(i.created_at))}) AS incidents
            OPTIONAL MATCH (wo:WorkOrder)-[:PERFORMED_ON]->(e)
            WITH e, incidents, collect(DISTINCT {type: 'work_order', id: wo.wo_id, title: wo.title,
                    status: wo.status, date: toString(wo.created_at)}) AS work_orders
            OPTIONAL MATCH (insp:Inspection)-[:INSPECTED]->(e)
            WITH e, incidents, work_orders, collect(DISTINCT {type: 'inspection', id: insp.inspection_id,
                    title: insp.title, result: insp.result, date: COALESCE(insp.date, toString(insp.created_at))}) AS inspections
            RETURN incidents + work_orders + inspections AS timeline
            """,
            tag=equipment_tag,
        )
        record = result.single()
        if not record:
            return []
        timeline = [e for e in record["timeline"] if e.get("id")]
        return timeline[:limit]

    @staticmethod
    def _read_equipment_detail(tx, equipment_tag: str) -> dict | None:
        result = tx.run(
            """
            MATCH (e:Equipment {tag: $tag})
            OPTIONAL MATCH (a:Area)-[:CONTAINS]->(e)
            OPTIONAL MATCH (e)-[:IS_TYPE]->(ac:AssetClass)
            OPTIONAL MATCH (e)-[:MANUFACTURED_BY]->(o:OEM)
            OPTIONAL MATCH (i:Incident)-[:INVOLVED]->(e)
            OPTIONAL MATCH (wo:WorkOrder)-[:PERFORMED_ON]->(e)
            OPTIONAL MATCH (e)-[:HAS_MANUAL]->(d:Document)
            RETURN e.tag AS tag, e.name AS name,
                   a.name AS area, ac.name AS asset_class, o.name AS oem,
                   collect(DISTINCT {id: i.incident_id, title: i.title, severity: i.severity}) AS incidents,
                   collect(DISTINCT {id: wo.wo_id, title: wo.title, status: wo.status}) AS work_orders,
                   collect(DISTINCT {id: d.doc_id, title: d.title, type: d.type}) AS documents
            """,
            tag=equipment_tag,
        )
        record = result.single()
        if not record or not record["tag"]:
            return None
        data = dict(record)
        # Clean up null entries from OPTIONAL MATCHes
        data["incidents"] = [i for i in data["incidents"] if i.get("id")]
        data["work_orders"] = [w for w in data["work_orders"] if w.get("id")]
        data["documents"] = [d for d in data["documents"] if d.get("id")]
        return data

    @staticmethod
    def _read_plant_hierarchy(tx, plant_id: Optional[str]) -> list[dict]:
        # Neo4j disallows nesting one aggregate function inside another
        # (collect() inside collect()), so equipment must be aggregated per
        # (plant, area) in its own WITH stage before areas are aggregated per
        # plant. Each stage also filters out the placeholder null produced by
        # an OPTIONAL MATCH that found nothing for that row.
        query = """
            MATCH (p:Plant)
        """
        if plant_id:
            query += " WHERE p.plant_id = $plant_id "
        query += """
            OPTIONAL MATCH (p)-[:CONTAINS]->(a:Area)
            OPTIONAL MATCH (a)-[:CONTAINS]->(e:Equipment)
            WITH p, a, collect(DISTINCT CASE WHEN e IS NULL THEN NULL ELSE {tag: e.tag, name: e.name} END) AS equip_raw
            WITH p, a, [x IN equip_raw WHERE x IS NOT NULL] AS equipment
            WITH p, collect(DISTINCT CASE WHEN a IS NULL THEN NULL ELSE {area_id: a.area_id, area_name: a.name, equipment: equipment} END) AS areas_raw
            WITH p, [x IN areas_raw WHERE x IS NOT NULL] AS areas
            RETURN p.plant_id AS plant_id, p.name AS plant_name, p.location AS location, areas
            ORDER BY p.name
        """
        result = tx.run(query, plant_id=plant_id)
        return [dict(r) for r in result]

    @staticmethod
    def _read_all_equipment(tx, plant_id: Optional[str]) -> list[dict]:
        # Guard against tag-less Equipment nodes an LLM extraction may have
        # created (kg_agent's discretionary path); they'd render as blank,
        # unusable options in every equipment dropdown.
        query = """
            MATCH (e:Equipment)
            WHERE e.tag IS NOT NULL AND trim(e.tag) <> ''
        """
        if plant_id:
            query += """
            MATCH (p:Plant {plant_id: $plant_id})-[:CONTAINS]->(a:Area)-[:CONTAINS]->(e)
            """
        else:
            query += """
            OPTIONAL MATCH (a:Area)-[:CONTAINS]->(e)
            """
        query += """
            OPTIONAL MATCH (e)-[:IS_TYPE]->(ac:AssetClass)
            RETURN e.tag AS tag, e.name AS name, a.name AS area,
                   ac.name AS asset_class, toString(e.created_at) AS created_at
            ORDER BY e.name
        """
        result = tx.run(query, plant_id=plant_id)
        return [dict(r) for r in result]

    @staticmethod
    def _read_all_incidents(tx, limit: int, plant_id: Optional[str]) -> list[dict]:
        query = """
            MATCH (i:Incident)
        """
        if plant_id:
            query += """
            MATCH (p:Plant {plant_id: $plant_id})-[:CONTAINS]->(a:Area)-[:CONTAINS]->(e:Equipment)
            MATCH (i)-[:INVOLVED]->(e)
            """
        else:
            query += """
            OPTIONAL MATCH (i)-[:INVOLVED]->(e:Equipment)
            """
            
        query += """
            RETURN i.incident_id AS id, i.title AS title, i.description AS description,
                   i.severity AS severity, COALESCE(i.date, toString(i.created_at)) AS date,
                   e.tag AS equipment_tag, e.name AS equipment_name
            ORDER BY i.created_at DESC
            LIMIT $limit
        """
        result = tx.run(query, limit=limit, plant_id=plant_id)
        return [dict(r) for r in result]

    @staticmethod
    def _read_compliance_gaps(tx, area_id: str) -> list[dict]:
        result = tx.run(
            """
            MATCH (a:Area {area_id: $area_id})-[:CONTAINS]->(e:Equipment)
            OPTIONAL MATCH (i:Incident)-[:INVOLVED]->(e)
            WITH e, count(i) AS incident_count
            WHERE incident_count > 0
            OPTIONAL MATCH (insp:Inspection)-[:INSPECTED]->(e)
            WITH e, incident_count, count(insp) AS inspection_count
            WHERE inspection_count = 0 OR incident_count > inspection_count
            RETURN e.tag AS tag, e.name AS name,
                   incident_count, inspection_count,
                   incident_count - inspection_count AS gap_score
            ORDER BY gap_score DESC
            """,
            area_id=area_id,
        )
        return [dict(r) for r in result]

    @staticmethod
    def _read_graph_stats(tx) -> dict:
        labels = ["Plant", "Area", "Equipment", "Incident", "WorkOrder", "Inspection", "Document", "Operator"]
        stats = {}
        for label in labels:
            result = tx.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            record = result.single()
            stats[label] = record["cnt"] if record else 0
        return stats


# Module-level singleton
industrial_graph = IndustrialGraphStore()
