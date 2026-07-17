"""
Industrial Seed Data — SureFlow Industrial Intelligence Platform.

Populates Neo4j with a realistic demo plant hierarchy (Plant → Areas → Equipment),
incidents, work orders, inspections, and documents, plus pgvector semantic memory
with realistic industrial content (OEM manuals, SOPs, compliance regs, incident reports).

Usage:
    python seed_industrial.py

Requires: Neo4j running (docker-compose), PostgreSQL running.
"""
import sys
import os

# Ensure backend/ is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import create_tables, SessionLocal
from core.memory import MemoryStore
from knowledge_graph.industrial_store import industrial_graph
from knowledge_graph.industrial_schema import setup_industrial_constraints


def seed_neo4j():
    """Populate the Industrial Knowledge Graph with demo data."""
    print("[SEED] Setting up Neo4j industrial constraints...")
    setup_industrial_constraints()

    print("[SEED] Creating plant hierarchy...")

    # ── Plant ──────────────────────────────────────────────────────────────────
    industrial_graph.record_plant("PLANT-001", "Karnataka Plant", "Karnataka, India")
    industrial_graph.record_plant("PLANT-002", "Delhi Plant", "Delhi, India")

    # ── Areas ──────────────────────────────────────────────────────────────────
    areas = [
        ("AREA-001", "Cooling Tower Unit", "PLANT-001"),
        ("AREA-002", "Distillation Column Bay", "PLANT-001"),
        ("AREA-003", "Pump House A", "PLANT-001"),
        ("AREA-004", "Boiler Room", "PLANT-002"),
        ("AREA-005", "Tank Farm", "PLANT-002"),
    ]
    for area_id, name, plant_id in areas:
        industrial_graph.record_area(area_id, name, plant_id)

    # ── Equipment ──────────────────────────────────────────────────────────────
    equipment = [
        # Pump House A
        ("P-101", "Centrifugal Feed Pump", "AREA-003", "Centrifugal Pump", "Grundfos"),
        ("P-102", "Centrifugal Transfer Pump", "AREA-003", "Centrifugal Pump", "Grundfos"),
        ("P-103", "Positive Displacement Pump", "AREA-003", "PD Pump", "Flowserve"),
        # Cooling Tower
        ("CT-201", "Cooling Tower Fan Motor", "AREA-001", "Motor", "Siemens"),
        ("CT-202", "Cooling Water Circulation Pump", "AREA-001", "Centrifugal Pump", "KSB"),
        ("HX-203", "Shell & Tube Heat Exchanger", "AREA-001", "Heat Exchanger", "Alfa Laval"),
        # Distillation
        ("DC-301", "Primary Distillation Column", "AREA-002", "Distillation Column", "Sulzer"),
        ("V-302", "Reflux Drum", "AREA-002", "Pressure Vessel", "Bharat Heavy Electricals"),
        ("CV-303", "Column Feed Control Valve", "AREA-002", "Control Valve", "Fisher"),
        # Boiler Room
        ("BLR-401", "High Pressure Steam Boiler", "AREA-004", "Boiler", "Thermax"),
        ("FD-402", "Forced Draft Fan", "AREA-004", "Fan", "Howden"),
        # Tank Farm
        ("TK-501", "Crude Storage Tank", "AREA-005", "Storage Tank", "CB&I"),
        ("TK-502", "Product Storage Tank", "AREA-005", "Storage Tank", "CB&I"),
    ]
    for tag, name, area_id, asset_class, oem in equipment:
        industrial_graph.record_equipment(tag, name, area_id, asset_class, oem)

    print("[SEED] Creating incidents...")

    # ── Incidents ──────────────────────────────────────────────────────────────
    incidents = [
        (
            "INC-001", "Excessive vibration on P-101",
            "Vibration readings on P-101 exceeded threshold (12mm/s vs 7mm/s limit). "
            "Bearing temperature also elevated to 85°C. Pump was taken offline for inspection. "
            "Root cause: bearing race degradation due to missed lubrication schedule.",
            "P-101", "high", "Rajesh Kumar", "2026-06-15"
        ),
        (
            "INC-002", "Cooling tower fan motor overheating",
            "CT-201 motor temperature reached 110°C, triggering automatic shutdown. "
            "Investigation found blocked air intake filters and worn motor bearings. "
            "Fan was offline for 8 hours during peak load.",
            "CT-201", "critical", "Priya Sharma", "2026-06-20"
        ),
        (
            "INC-003", "Control valve sticking on DC-301 feed",
            "CV-303 failed to respond to DCS commands. Column pressure deviated by 15%. "
            "Maintenance crew found corrosion on valve stem. Temporary bypass installed.",
            "CV-303", "medium", "Amit Patel", "2026-07-01"
        ),
        (
            "INC-004", "Minor oil leak on P-102 mechanical seal",
            "Small oil leak detected during routine walkdown. Seal replacement scheduled. "
            "No environmental impact. Near-miss classification.",
            "P-102", "low", "Vikram Singh", "2026-07-05"
        ),
        (
            "INC-005", "Boiler tube leak detected in BLR-401",
            "Steam leak detected during startup. Boiler taken offline for tube inspection. "
            "Ultrasonic testing revealed wall thinning in superheater section due to erosion. "
            "Three tubes required plugging.",
            "BLR-401", "high", "Suresh Reddy", "2026-07-03"
        ),
    ]
    for inc_id, title, desc, eq_tag, severity, reporter, date in incidents:
        industrial_graph.record_incident(inc_id, title, desc, eq_tag, severity, reporter, date)

    print("[SEED] Creating work orders...")

    # ── Work Orders ────────────────────────────────────────────────────────────
    work_orders = [
        (
            "WO-001", "Replace bearings on P-101",
            "Replace both drive-end and non-drive-end bearings on centrifugal feed pump P-101. "
            "Align pump-motor coupling after bearing replacement. Verify vibration within spec.",
            "P-101", "corrective", "John Doe", "completed", "INC-001"
        ),
        (
            "WO-002", "Clean CT-201 air intake filters",
            "Remove and clean all air intake filters on cooling tower fan motor. "
            "Replace motor bearings. Perform insulation resistance test before restart.",
            "CT-201", "corrective", "Jane Smith", "completed", "INC-002"
        ),
        (
            "WO-003", "Replace control valve CV-303 stem",
            "Replace corroded valve stem on column feed control valve. "
            "Calibrate valve positioner after replacement. Verify full stroke response.",
            "CV-303", "corrective", "Amit Patel", "in_progress", "INC-003"
        ),
        (
            "WO-004", "Quarterly vibration analysis — Pump House A",
            "Perform vibration analysis on all pumps in Pump House A (P-101, P-102, P-103). "
            "Compare readings against baseline. Report any anomalies.",
            "P-101", "preventive", "Rajesh Kumar", "open", None
        ),
        (
            "WO-005", "Annual inspection — Heat Exchanger HX-203",
            "Perform tube bundle inspection on shell & tube heat exchanger. "
            "Check for fouling, corrosion, and tube wall thinning. Hydrotest at 1.5x design pressure.",
            "HX-203", "preventive", "Suresh Reddy", "open", None
        ),
        (
            "WO-006", "Replace mechanical seal on P-102",
            "Replace leaking mechanical seal on transfer pump P-102. "
            "Use upgraded seal material (silicon carbide) for better chemical resistance.",
            "P-102", "corrective", "Vikram Singh", "open", "INC-004"
        ),
    ]
    for wo_id, title, desc, eq_tag, wo_type, assigned, status, inc_id in work_orders:
        industrial_graph.record_work_order(wo_id, title, desc, eq_tag, wo_type, assigned, status, inc_id)

    print("[SEED] Creating inspections...")

    # ── Inspections ────────────────────────────────────────────────────────────
    inspections = [
        ("INSP-001", "Monthly vibration check — P-101", "P-101", "Rajesh Kumar", "fail", "2026-06-10"),
        ("INSP-002", "Weekly cooling tower walkdown", "CT-201", "Priya Sharma", "pass", "2026-06-18"),
        ("INSP-003", "Boiler safety valve test — BLR-401", "BLR-401", "Suresh Reddy", "pass", "2026-06-25"),
        ("INSP-004", "Tank farm corrosion survey", "TK-501", "Vikram Singh", "pass", "2026-07-01"),
        ("INSP-005", "Control valve stroke test — CV-303", "CV-303", "Amit Patel", "fail", "2026-06-28"),
    ]
    for insp_id, title, eq_tag, inspector, result, date in inspections:
        industrial_graph.record_inspection(insp_id, title, eq_tag, inspector, result, date)

    print("[SEED] Creating documents...")

    # ── Documents ──────────────────────────────────────────────────────────────
    documents = [
        ("DOC-001", "Grundfos Centrifugal Pump P-101 — OEM Manual", "manual", "P-101", ""),
        ("DOC-002", "Siemens Motor CT-201 — Installation & Maintenance Guide", "manual", "CT-201", ""),
        ("DOC-003", "OSHA 1910.119 — Process Safety Management", "regulation", "", "AREA-002"),
        ("DOC-004", "SOP-PUMP-001 — Centrifugal Pump Startup Procedure", "sop", "P-101", "AREA-003"),
        ("DOC-005", "ISO 14224 — Reliability and Maintenance Data for Equipment", "regulation", "", ""),
        ("DOC-006", "Fisher Control Valve CV-303 — Calibration Procedure", "manual", "CV-303", ""),
        ("DOC-007", "SOP-BOILER-001 — Steam Boiler Startup Checklist", "sop", "BLR-401", "AREA-004"),
    ]
    for doc_id, title, doc_type, eq_tag, area_id in documents:
        industrial_graph.record_document(doc_id, title, doc_type, eq_tag, area_id)

    print("[SEED] ✅ Neo4j industrial graph seeded successfully!")


def seed_reflection_memory():
    """Populate Reflection Memory with operational lessons learned."""
    print("[SEED] Creating industrial lessons learned...")
    memory = MemoryStore()

    lessons = [
        {
            "agent_id": "lessons_learned_agent",
            "task": "RCA for INC-001: Excessive vibration on P-101",
            "failure_reason": "Bearing failure on Pump P-101 due to missed lubrication schedule. "
                             "Weekly lubrication checklist was not signed off for 3 consecutive weeks.",
            "lesson": "Always verify lubrication checklists for centrifugal pumps in Pump House A "
                     "before signing off on weekly inspections. Implement automated reminder system.",
            "equipment_tag": "P-101",
            "incident_id": "INC-001",
            "category": "operational_failure",
            "source": "incident_report",
        },
        {
            "agent_id": "lessons_learned_agent",
            "task": "RCA for INC-002: Cooling tower fan motor overheating",
            "failure_reason": "Motor overheating caused by blocked air intake filters and worn bearings. "
                             "Filter cleaning schedule was quarterly but should be monthly in dusty season.",
            "lesson": "During high-dust months (March-June), increase CT-201 filter cleaning frequency "
                     "from quarterly to monthly. Add bearing temperature to daily operator rounds checklist.",
            "equipment_tag": "CT-201",
            "incident_id": "INC-002",
            "category": "operational_failure",
            "source": "incident_report",
        },
        {
            "agent_id": "lessons_learned_agent",
            "task": "Near-miss analysis: P-102 seal leak",
            "failure_reason": "Mechanical seal degradation on P-102 due to chemical incompatibility. "
                             "Standard EPDM seal material not suitable for the process fluid.",
            "lesson": "For centrifugal pumps handling hydrocarbon-water mixtures, specify silicon carbide "
                     "seal faces instead of standard carbon-ceramic. Update procurement specifications.",
            "equipment_tag": "P-102",
            "incident_id": "INC-004",
            "category": "near_miss",
            "source": "capa",
        },
        {
            "agent_id": "lessons_learned_agent",
            "task": "RCA for INC-005: Boiler tube leak",
            "failure_reason": "Superheater tube wall thinning due to fly ash erosion. "
                             "Erosion rate was higher than predicted because of fuel quality change.",
            "lesson": "When fuel source changes, immediately reassess erosion rates on boiler tubes. "
                     "Schedule UT thickness surveys within 30 days of any fuel specification change.",
            "equipment_tag": "BLR-401",
            "incident_id": "INC-005",
            "category": "safety_incident",
            "source": "incident_report",
        },
    ]

    for l in lessons:
        memory.save_reflection_industrial(**l)

    print("[SEED] ✅ Reflection memory (lessons learned) seeded successfully!")


def seed_episodic_memory():
    """Populate Episodic Memory with historical maintenance episodes."""
    print("[SEED] Creating industrial episodic memory...")
    memory = MemoryStore()

    episodes = [
        {
            "agent_id": "maintenance_agent",
            "task": "Analyze vibration trend for P-101",
            "output": {
                "recommendation": "Immediate bearing replacement required. Vibration trend shows exponential "
                                "increase over last 30 days. Predicted time to failure: 5-7 days.",
                "confidence": 85,
                "risk_level": "high",
            },
            "equipment_tag": "P-101",
            "context_type": "maintenance",
        },
        {
            "agent_id": "maintenance_agent",
            "task": "Root Cause Analysis for CT-201 motor overheating",
            "output": {
                "recommendation": "Two contributing factors: (1) blocked air filters reducing cooling, "
                                "(2) worn bearings increasing friction heat. Both must be addressed.",
                "confidence": 78,
                "risk_level": "critical",
            },
            "equipment_tag": "CT-201",
            "context_type": "incident_rca",
        },
        {
            "agent_id": "compliance_agent",
            "task": "Quarterly compliance check — OSHA 1910.119 for Distillation Column Bay",
            "output": {
                "recommendation": "Area AREA-002 is 90% compliant with OSHA 1910.119. "
                                "Missing: updated P&ID for CV-303 bypass configuration.",
                "confidence": 72,
                "risk_level": "medium",
            },
            "equipment_tag": "CV-303",
            "context_type": "inspection",
        },
    ]

    for ep in episodes:
        memory.save_episodic_industrial(**ep)

    print("[SEED] ✅ Episodic memory (industrial) seeded successfully!")


def main():
    print("=" * 60)
    print("  SureFlow Industrial Intelligence — Seed Data")
    print("=" * 60)

    # Ensure tables exist
    print("\n[SEED] Ensuring database tables exist...")
    create_tables()

    # Seed all stores
    seed_neo4j()
    print()
    seed_reflection_memory()
    print()
    seed_episodic_memory()

    print("\n" + "=" * 60)
    print("  ✅ All industrial seed data loaded successfully!")
    print("=" * 60)
    print("\nGraph summary:")
    print(industrial_graph.get_industrial_overview())


if __name__ == "__main__":
    main()
