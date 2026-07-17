"""
Auth dependencies — the enforcement layer for multi-location.

Every protected route depends on `get_current_user` (decodes the Bearer JWT).
`resolve_scope` turns the verified identity into an *effective plant_id*:
plant users are hard-locked to their own plant; a CTO may target one plant or
go global (None). Scope is NEVER taken from a client-supplied body field.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_access_token
from models.auth import User

# auto_error=False so we can return a clean 401 instead of FastAPI's default.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == payload.get("email")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def require_cto(user: User = Depends(get_current_user)) -> User:
    if user.role != "cto":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires global (CTO) access")
    return user


def resolve_scope(user: User, target_plant_id: Optional[str] = None) -> Optional[str]:
    """
    Effective plant_id for this request.

    - CTO: `target_plant_id` if given (scoped to one plant), else None (global).
    - Plant user: forced to their own plant; requesting another plant → 403.
    """
    if user.role == "cto":
        return (target_plant_id or None)
    if not user.plant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no plant assignment")
    if target_plant_id and target_plant_id != user.plant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another plant's data")
    return user.plant_id
