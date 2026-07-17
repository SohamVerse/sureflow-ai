"""
Location (plant) routes — list, provision, and inspect plants.

Mounted at /api/v1/plants. Listing is scoped to the caller (CTO sees all,
plant users see only theirs). Creating a location is CTO-only and provisions
both the relational Location row and the Neo4j Plant node (+ optional areas).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import hash_password
from models.auth import Location, User
from api.deps import get_current_user, require_cto, resolve_scope
from knowledge_graph.industrial_store import industrial_graph

router = APIRouter(prefix="/plants", tags=["plants"])


class AreaSpec(BaseModel):
    area_id: str
    name: str


class ManagerSpec(BaseModel):
    email: str
    password: str
    name: str = ""


class CreatePlantRequest(BaseModel):
    plant_id: str = ""          # optional; auto-generated if blank
    name: str
    location: str = ""
    areas: list[AreaSpec] = []  # optional initial area skeleton
    manager: Optional[ManagerSpec] = None  # optional first plant-manager to invite


def _plant_out(p: Location, with_stats: bool = True) -> dict:
    out = {
        "plant_id": p.plant_id,
        "name": p.name,
        "location": p.location,
        "status": p.status,
    }
    if with_stats:
        out["stats"] = industrial_graph.get_graph_stats(plant_id=p.plant_id)
    return out


@router.get("")
def list_plants(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List plants visible to the caller (CTO → all; plant user → only theirs)."""
    q = db.query(Location).order_by(Location.name)
    if user.role != "cto":
        q = q.filter(Location.plant_id == user.plant_id)
    return {"plants": [_plant_out(p) for p in q.all()]}


@router.post("")
def create_plant(
    body: CreatePlantRequest,
    actor: User = Depends(require_cto),
    db: Session = Depends(get_db),
):
    """
    Onboard a new location (CTO only) in one shot: relational Location row +
    Neo4j Plant/Area skeleton + (optionally) the first plant-manager user.
    """
    plant_id = body.plant_id.strip() or f"PLANT-{uuid.uuid4().hex[:6].upper()}"
    if db.query(Location).filter(Location.plant_id == plant_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plant already exists")

    # Validate the manager (if provided) BEFORE writing anything.
    manager_email = None
    if body.manager and body.manager.email:
        manager_email = body.manager.email.lower().strip()
        if db.query(User).filter(User.email == manager_email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Manager email already exists")

    loc = Location(plant_id=plant_id, name=body.name, location=body.location, created_by=actor.email)
    db.add(loc)

    # Mirror into the operational graph (Plant + Area skeleton, stamped plant_id).
    industrial_graph.record_plant(plant_id, body.name, body.location)
    for area in body.areas:
        if area.area_id and area.name:
            industrial_graph.record_area(area.area_id, area.name, plant_id)
    industrial_graph._stats_cache_dict = {}

    # Invite the first plant manager, if one was supplied.
    manager_out = None
    if manager_email:
        mgr = User(
            email=manager_email,
            hashed_password=hash_password(body.manager.password),
            name=body.manager.name or f"{body.name} Manager",
            role="plant_manager",
            plant_id=plant_id,
        )
        db.add(mgr)
        manager_out = {"email": mgr.email, "name": mgr.name}

    db.commit()

    return {
        "status": "created",
        "plant_id": plant_id,
        "name": body.name,
        "areas_created": len(body.areas),
        "manager": manager_out,
    }


@router.get("/{plant_id}")
def get_plant(
    plant_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Plant profile + graph stats + hierarchy (scope-checked)."""
    resolve_scope(user, plant_id)  # 403 if a plant user requests another plant
    p = db.query(Location).filter(Location.plant_id == plant_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return {
        **_plant_out(p),
        "hierarchy": industrial_graph.get_plant_hierarchy(plant_id=plant_id),
    }
