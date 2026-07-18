"""
Seed auth data for the multi-location extension.

Creates the Locations that mirror the seeded Neo4j plants and the demo users
(one global CTO + one plant manager) that match the frontend's demo accounts.

Usage:
    cd backend
    .venv\\Scripts\\python.exe scripts/seed_users.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import create_tables, SessionLocal
from core.security import hash_password
from models.auth import User, Location


# (plant_id, name, location) — must match the plants in seed_industrial_data.py
LOCATIONS = [
    ("PLANT-001", "Karnataka Plant", "Karnataka, India"),
    ("PLANT-002", "Delhi Plant", "Delhi, India"),
]

# (email, password, name, role, plant_id)
USERS = [
    ("cto@sureflow.ai", "Sureflow_CTO_2026!", "CTO (Global)", "cto", None),
    ("karnataka@sureflow.ai", "Sureflow_Plant_2026!", "Karnataka Manager", "plant_manager", "PLANT-001"),
    ("delhi@sureflow.ai", "Sureflow_Plant_2026!", "Delhi Manager", "plant_manager", "PLANT-002"),
]


def seed():
    print("[SEED] Ensuring auth tables exist...")
    create_tables()

    db = SessionLocal()
    try:
        for plant_id, name, location in LOCATIONS:
            existing = db.query(Location).filter(Location.plant_id == plant_id).first()
            if existing:
                existing.name = name
                existing.location = location
            else:
                db.add(Location(plant_id=plant_id, name=name, location=location, created_by="seed"))
        db.commit()
        print(f"[SEED] {len(LOCATIONS)} location(s) ready.")

        for email, password, name, role, plant_id in USERS:
            email = email.lower().strip()
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Reset password/role so the demo credentials always work.
                user.hashed_password = hash_password(password)
                user.name = name
                user.role = role
                user.plant_id = plant_id
            else:
                db.add(User(
                    email=email,
                    hashed_password=hash_password(password),
                    name=name,
                    role=role,
                    plant_id=plant_id,
                ))
        db.commit()
        print(f"[SEED] {len(USERS)} user(s) ready:")
        for email, password, _, role, plant_id in USERS:
            print(f"        {email} / {password}  ({role}{', ' + plant_id if plant_id else ', global'})")
    finally:
        db.close()

    print("[SEED] Auth seeding complete!")


if __name__ == "__main__":
    seed()
