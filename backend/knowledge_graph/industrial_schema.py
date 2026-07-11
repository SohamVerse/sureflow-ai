"""
Industrial Knowledge Graph — Neo4j constraint setup.

Extends the strategic constraints (schema.py) with uniqueness constraints
for all industrial ontology node types. Called from main.py at startup.
"""
from __future__ import annotations
import logging

from knowledge_graph.client import get_driver

logger = logging.getLogger("companyos.knowledge_graph.industrial")

# Each tuple: (constraint_name, label, property)
_INDUSTRIAL_CONSTRAINTS = [
    ("plant_id_unique", "Plant", "plant_id"),
    ("area_id_unique", "Area", "area_id"),
    ("equipment_tag_unique", "Equipment", "tag"),
    ("asset_class_name_unique", "AssetClass", "name"),
    ("oem_name_unique", "OEM", "name"),
    ("vendor_name_unique", "Vendor", "name"),
    ("incident_id_unique", "Incident", "incident_id"),
    ("work_order_id_unique", "WorkOrder", "wo_id"),
    ("inspection_id_unique", "Inspection", "inspection_id"),
    ("document_id_unique", "Document", "doc_id"),
    ("operator_name_unique", "Operator", "name"),
    ("engineer_name_unique", "Engineer", "name"),
    ("sensor_id_unique", "Sensor", "sensor_id"),
    ("part_id_unique", "Part", "part_id"),
]


def setup_industrial_constraints() -> None:
    """
    Idempotent — CREATE CONSTRAINT IF NOT EXISTS is safe to run on every startup.
    Never lets a Neo4j outage block app startup; logs a warning and continues.
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            for constraint_name, label, prop in _INDUSTRIAL_CONSTRAINTS:
                session.run(
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
                )
        logger.info("Industrial Neo4j constraints ready (%d constraints).", len(_INDUSTRIAL_CONSTRAINTS))
    except Exception as e:
        logger.warning(f"Neo4j not reachable, skipping industrial constraint setup: {e}")
