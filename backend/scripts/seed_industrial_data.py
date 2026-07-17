"""
Seed script for Industrial Intelligence demo data.

Populates Neo4j with a realistic plant hierarchy and event history,
and Reflection Memory with operational lessons.

Usage:
    cd backend
    .venv\\Scripts\\python.exe scripts/seed_industrial_data.py
"""
import sys
import os

# Ensure backend/ is on the Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import create_tables, SessionLocal
from knowledge_graph.industrial_schema import setup_industrial_constraints
from knowledge_graph.industrial_store import industrial_graph
from models.memory import ReflectionMemory


def seed():
    print("[SEED] Starting industrial data seeding...")

    # ── 0. Ensure DB tables + constraints exist ──────────────────────────────
    create_tables()
    print("[SEED] PostgreSQL tables ready.")
    setup_industrial_constraints()
    print("[SEED] Neo4j industrial constraints ready.")

    # ── 1. Plant ─────────────────────────────────────────────────────────────
    industrial_graph.record_plant("PLANT-001", "Karnataka Plant", "Karnataka, India")
    industrial_graph.record_plant("PLANT-002", "Delhi Plant", "Delhi, India")
    print("[SEED] Created Plants: Karnataka, Delhi")

    # ── 2. Areas ─────────────────────────────────────────────────────────────
    areas = [
        ("AREA-100", "Pump House A", "PLANT-001"),
        ("AREA-200", "Distillation Bay", "PLANT-001"),
        ("AREA-300", "Cooling Tower Area", "PLANT-001"),
        ("AREA-400", "Compressor Station", "PLANT-002"),
        ("AREA-500", "Utility & Power", "PLANT-002"),
    ]
    for area_id, name, plant_id in areas:
        industrial_graph.record_area(area_id, name, plant_id)
    print(f"[SEED] Created {len(areas)} Areas")

    # Map area → plant so every downstream entity inherits the correct plant_id
    # (equipment via its area; incidents/WOs/inspections via their equipment).
    area_to_plant = {area_id: plant_id for area_id, _, plant_id in areas}

    # ── 3. Equipment ─────────────────────────────────────────────────────────
    equipment = [
        # Pump House A
        ("P-101", "Centrifugal Feed Pump A", "AREA-100", "Centrifugal Pump", "Flowserve"),
        ("P-102", "Centrifugal Feed Pump B", "AREA-100", "Centrifugal Pump", "Flowserve"),
        ("P-103", "Booster Pump", "AREA-100", "Centrifugal Pump", "Sulzer"),
        # Distillation Bay
        ("V-201", "Distillation Column", "AREA-200", "Pressure Vessel", "Koch-Glitsch"),
        ("V-205", "Safety Relief Valve", "AREA-200", "Safety Valve", "Emerson"),
        ("HX-202", "Column Condenser", "AREA-200", "Heat Exchanger", "Alfa Laval"),
        # Cooling Tower Area
        ("CT-001", "Cooling Tower A", "AREA-300", "Cooling Tower", "SPX Cooling"),
        ("HX-301", "Shell & Tube Heat Exchanger", "AREA-300", "Heat Exchanger", "Alfa Laval"),
        # Compressor Station
        ("C-401", "Reciprocating Compressor", "AREA-400", "Compressor", "Atlas Copco"),
        ("C-402", "Screw Compressor", "AREA-400", "Compressor", "Ingersoll Rand"),
        # Utility & Power
        ("GEN-501", "Diesel Generator", "AREA-500", "Generator", "Cummins"),
        ("TR-502", "Power Transformer", "AREA-500", "Transformer", "ABB"),
    ]
    equip_to_plant = {}
    for tag, name, area, asset_class, oem in equipment:
        pid = area_to_plant.get(area, "")
        equip_to_plant[tag] = pid
        industrial_graph.record_equipment(tag, name, area, asset_class, oem, plant_id=pid)
    print(f"[SEED] Created {len(equipment)} Equipment")

    # ── 4. Incidents ─────────────────────────────────────────────────────────
    incidents = [
        ("INC-001", "Bearing failure on P-101", "High vibration alarm followed by bearing seizure. Pump tripped on high temperature.", "P-101", "high", "Operator Sharma", "2026-03-14"),
        ("INC-002", "Seal leak on P-102", "Mechanical seal leak detected during routine rounds. Minor hydrocarbon release.", "P-102", "medium", "Operator Patel", "2026-04-22"),
        ("INC-003", "Relief valve chattering V-205", "Safety relief valve V-205 chattering during column pressure excursion. PSV did not fully reseat.", "V-205", "high", "Shift Lead Kumar", "2026-05-10"),
        ("INC-004", "Cooling tower fan vibration", "CT-001 fan motor showing elevated vibration. 4.2 mm/s vs 2.5 mm/s baseline.", "CT-001", "medium", "Operator Reddy", "2026-05-28"),
        ("INC-005", "Heat exchanger tube leak HX-301", "Tube bundle leak detected via differential pressure alarm. Cooling capacity reduced 30%.", "HX-301", "high", "Operator Singh", "2026-06-05"),
        ("INC-006", "Compressor surge event C-401", "Reciprocating compressor experienced surge during load change. Anti-surge valve responded but with 3s delay.", "C-401", "critical", "Shift Lead Gupta", "2026-06-20"),
    ]
    for inc_id, title, desc, tag, severity, reporter, date in incidents:
        industrial_graph.record_incident(inc_id, title, desc, tag, severity, reporter, date, plant_id=equip_to_plant.get(tag, ""))
    print(f"[SEED] Created {len(incidents)} Incidents")

    # ── 5. Work Orders ───────────────────────────────────────────────────────
    work_orders = [
        ("WO-1001", "Replace bearing on P-101", "Replace DE and NDE bearings. Realign coupling.", "P-101", "corrective", "Mech. Team A", "completed", "INC-001"),
        ("WO-1002", "Replace mechanical seal P-102", "Replace single mechanical seal with tandem seal upgrade.", "P-102", "corrective", "Mech. Team B", "completed", "INC-002"),
        ("WO-1003", "Overhaul PSV V-205", "Full PSV overhaul, set pressure test, replace soft goods.", "V-205", "corrective", "Instrument Team", "in_progress", "INC-003"),
        ("WO-1004", "PM on P-101 — vibration analysis", "Quarterly vibration analysis and bearing condition monitoring.", "P-101", "preventive", "PdM Team", "completed", None),
        ("WO-1005", "PM on CT-001 — fan balance", "Dynamic balance CT-001 fan, check motor alignment.", "CT-001", "preventive", "Mech. Team C", "planned", "INC-004"),
        ("WO-1006", "Inspect HX-301 tube bundle", "Eddy current inspection of tube bundle. Assess remaining wall thickness.", "HX-301", "corrective", "Inspection Team", "in_progress", "INC-005"),
        ("WO-1007", "Anti-surge valve calibration C-401", "Calibrate anti-surge valve. Verify response time <1s.", "C-401", "corrective", "Instrument Team", "planned", "INC-006"),
        ("WO-1008", "PM on GEN-501 — 500hr service", "Oil change, filter replacement, load bank test.", "GEN-501", "preventive", "Electrical Team", "completed", None),
    ]
    for wo_id, title, desc, tag, wo_type, assigned, status, inc_id in work_orders:
        industrial_graph.record_work_order(wo_id, title, desc, tag, wo_type, assigned, status, inc_id, plant_id=equip_to_plant.get(tag, ""))
    print(f"[SEED] Created {len(work_orders)} Work Orders")

    # ── 6. Inspections ───────────────────────────────────────────────────────
    inspections = [
        ("INSP-001", "API 610 pump inspection P-101", "P-101", "Inspector Joshi", "pass", "2026-01-15"),
        ("INSP-002", "PSV annual test V-205", "V-205", "Inspector Mehta", "fail", "2026-02-20"),
        ("INSP-003", "TEMA heat exchanger inspection HX-301", "HX-301", "Inspector Das", "conditional", "2026-03-10"),
        ("INSP-004", "Electrical safety audit GEN-501", "GEN-501", "Inspector Rao", "pass", "2026-04-05"),
        ("INSP-005", "Compressor performance test C-401", "C-401", "Inspector Nair", "pass", "2026-05-01"),
    ]
    for insp_id, title, tag, inspector, result, date in inspections:
        industrial_graph.record_inspection(insp_id, title, tag, inspector, result, date, plant_id=equip_to_plant.get(tag, ""))
    print(f"[SEED] Created {len(inspections)} Inspections")

    # ── 7. Documents ─────────────────────────────────────────────────────────
    documents = [
        ("DOC-001", "Flowserve Mark III Operation Manual", "oem_manual", "P-101", ""),
        ("DOC-002", "Emerson Type 63EG PSV Manual", "oem_manual", "V-205", ""),
        ("DOC-003", "Pump House A SOP", "sop", "", "AREA-100"),
        ("DOC-004", "OSHA PSM 1910.119", "compliance_regulation", "", ""),
        ("DOC-005", "ISO 55001 Asset Management", "compliance_regulation", "", ""),
    ]
    for doc_id, title, doc_type, eq_tag, area_id in documents:
        doc_plant = equip_to_plant.get(eq_tag) or area_to_plant.get(area_id) or ""
        industrial_graph.record_document(doc_id, title, doc_type, eq_tag, area_id, plant_id=doc_plant)
    print(f"[SEED] Created {len(documents)} Documents")

    # ── 8. Operational Lessons (Reflection Memory) ───────────────────────────
    db = SessionLocal()
    try:
        lessons = [
            ReflectionMemory(
                agent_id="MAINTENANCE",
                task_context="Bearing failure on P-101 — 2026-03-14",
                failure_reason="Bearing ran to failure. Vibration trending was not reviewed for 6 weeks prior.",
                lesson="Implement weekly vibration review dashboard. Escalate any bearing with >3.5 mm/s within 48 hours.",
                equipment_tag="P-101",
                incident_id="INC-001",
                category="operational_failure",
                source="incident_report",
            ),
            ReflectionMemory(
                agent_id="MAINTENANCE",
                task_context="Seal leak on P-102 — 2026-04-22",
                failure_reason="Single mechanical seal failed after 18 months. Design life was 24 months but operating conditions exceeded spec.",
                lesson="Upgrade all single seals to tandem configuration on API 610 pumps handling hydrocarbons.",
                equipment_tag="P-102",
                incident_id="INC-002",
                category="operational_failure",
                source="incident_report",
            ),
            ReflectionMemory(
                agent_id="COMPLIANCE",
                task_context="PSV V-205 failed annual test — 2026-02-20",
                failure_reason="PSV set pressure drifted +8% above nameplate. Soft goods degraded from process fouling.",
                lesson="Reduce PSV test interval from 12 months to 6 months for fouling service. Add inline filter upstream.",
                equipment_tag="V-205",
                incident_id="INC-003",
                category="safety_incident",
                source="capa",
            ),
            ReflectionMemory(
                agent_id="LESSONS_LEARNED",
                task_context="Compressor surge C-401 — 2026-06-20",
                failure_reason="Anti-surge valve response time 3s exceeds 1s requirement. Valve positioner calibration was overdue.",
                lesson="Add anti-surge valve response time to monthly critical instrument checklist. Any >1.5s response triggers immediate work order.",
                equipment_tag="C-401",
                incident_id="INC-006",
                category="safety_incident",
                source="incident_report",
            ),
        ]
        for lesson in lessons:
            # Inherit the plant from the lesson's equipment (falls back to PLANT-001)
            lesson.plant_id = equip_to_plant.get(lesson.equipment_tag) or "PLANT-001"
            db.add(lesson)
        db.commit()
        print(f"[SEED] Created {len(lessons)} Operational Lessons")
    finally:
        db.close()

    print("[SEED] Industrial data seeding complete!")


if __name__ == "__main__":
    seed()
