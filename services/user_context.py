from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from settings import settings


class UserRole(str, Enum):
    guest = "guest"
    user = "user"
    admin = "admin"


class UserContext(BaseModel):
    user_id: str
    role: UserRole
    is_guest: bool = False
    guest_session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    email: Optional[str] = None
    username: Optional[str] = None


def calculate_guest_expiration() -> datetime:
    ttl_hours = settings.guest_session_ttl_hours or 24
    return datetime.utcnow() + timedelta(hours=ttl_hours)

