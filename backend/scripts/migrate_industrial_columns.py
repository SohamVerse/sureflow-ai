"""One-shot migration: add industrial columns to memory tables."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine
from sqlalchemy import text

STATEMENTS = [
    "ALTER TABLE episodic_memories ADD COLUMN IF NOT EXISTS equipment_tag VARCHAR(100)",
    "ALTER TABLE episodic_memories ADD COLUMN IF NOT EXISTS context_type VARCHAR(50) DEFAULT 'agent_run'",
    "ALTER TABLE reflection_memories ADD COLUMN IF NOT EXISTS equipment_tag VARCHAR(100)",
    "ALTER TABLE reflection_memories ADD COLUMN IF NOT EXISTS incident_id VARCHAR(100)",
    "ALTER TABLE reflection_memories ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'agent_failure'",
    "ALTER TABLE reflection_memories ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'agent'",
    # Indexes
    "CREATE INDEX IF NOT EXISTS ix_episodic_equipment ON episodic_memories(equipment_tag)",
    "CREATE INDEX IF NOT EXISTS ix_reflection_equipment ON reflection_memories(equipment_tag)",
]

with engine.connect() as conn:
    for stmt in STATEMENTS:
        try:
            conn.execute(text(stmt))
            print(f"OK: {stmt[:60]}...")
        except Exception as e:
            print(f"SKIP: {e}")
    conn.commit()
    print("\nMigration complete.")
