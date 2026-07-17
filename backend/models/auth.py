"""
Auth & tenancy models for the multi-location extension.

- Location: the relational mirror of a Neo4j `Plant` node. Source of truth for
  listing plants and assigning users; Neo4j remains the operational graph.
- User: an authenticated identity with a role and (for non-HQ users) a plant.

See MULTI_LOCATION.md for the full design.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid
from datetime import datetime, timezone
import uuid

from core.database import Base


class Location(Base):
    """A plant/site. `plant_id` matches the Neo4j Plant.plant_id (e.g. PLANT-001)."""
    __tablename__ = "locations"

    plant_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), default="")
    timezone = Column(String(64), default="UTC")
    status = Column(String(20), default="active")  # active | onboarding | archived
    created_by = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    """
    An authenticated user.

    role:     'cto' (global/HQ), 'plant_manager', or 'operator'.
    plant_id: the plant a plant-scoped user belongs to; NULL for a global CTO.
    """
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(120), nullable=False, default="")
    role = Column(String(30), nullable=False, default="plant_manager")
    plant_id = Column(String(50), ForeignKey("locations.plant_id"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
