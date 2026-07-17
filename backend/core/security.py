"""
Password hashing (bcrypt) and JWT issuance/verification for multi-location auth.

Kept dependency-light on purpose: `bcrypt` directly (no passlib version-detection
quirks) and `pyjwt`. The token carries the identity + role + plant scope that
every protected route derives its access from.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt

from core.config import settings

# bcrypt hard-limits passwords to 72 bytes; truncate defensively so long inputs
# don't raise on newer bcrypt releases.
_MAX_PW_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:_MAX_PW_BYTES], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:_MAX_PW_BYTES], hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(*, user_id, email: str, role: str, plant_id: Optional[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "plant_id": plant_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None
