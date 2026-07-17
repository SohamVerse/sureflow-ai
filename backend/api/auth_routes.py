"""
Authentication routes — login, current-user, and user provisioning.

Mounted at /api/v1/auth. Login returns a JWT; every other protected route in
the app derives its plant scope from that token (see api/deps.py).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import verify_password, hash_password, create_access_token
from models.auth import User, Location
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class CreateUserRequest(BaseModel):
    email: str
    password: str
    name: str = ""
    role: str = "plant_manager"  # 'plant_manager' | 'operator' | 'cto'
    plant_id: Optional[str] = None


def _user_out(u: User) -> dict:
    return {"email": u.email, "name": u.name, "role": u.role, "plant_id": u.plant_id}


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(
        user_id=user.id, email=user.email, role=user.role, plant_id=user.plant_id
    )
    return {"access_token": token, "token_type": "bearer", "user": _user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Current user plus the plants they can access (CTO → all; plant user → theirs)."""
    if user.role == "cto":
        plants = db.query(Location).order_by(Location.name).all()
    else:
        plants = db.query(Location).filter(Location.plant_id == user.plant_id).all()
    return {
        "user": _user_out(user),
        "plants": [
            {"plant_id": p.plant_id, "name": p.name, "location": p.location}
            for p in plants
        ],
    }


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Provision a user. A CTO may create anyone; a plant_manager may create only
    non-CTO users for their own plant.
    """
    if actor.role != "cto":
        if actor.role != "plant_manager" or body.role == "cto" or body.plant_id != actor.plant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")

    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    # A non-CTO user must belong to a plant.
    if body.role != "cto" and not body.plant_id:
        raise HTTPException(status_code=422, detail="plant_id is required for non-CTO users")

    user = User(
        email=email,
        hashed_password=hash_password(body.password),
        name=body.name,
        role=body.role,
        plant_id=None if body.role == "cto" else body.plant_id,
    )
    db.add(user)
    db.commit()
    return {"status": "created", "user": _user_out(user)}
