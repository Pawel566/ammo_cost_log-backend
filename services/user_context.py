from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, field_validator
from settings import settings


class UserRole(str, Enum):
    guest = "guest"
    user = "user"
    admin = "admin"


class UserContext(BaseModel):
    user_id: str
    role: UserRole
    is_guest: bool = False
    expires_at: Optional[datetime] = None

    @field_validator('expires_at', mode='before')
    @classmethod
    def ensure_guest_expires_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """If is_guest=True, always generate expires_at"""
        if info.data.get('is_guest', False) and v is None:
            return calculate_guest_expiration()
        return v


def calculate_guest_expiration() -> datetime:
    ttl_hours = settings.guest_session_ttl_hours or 24
    return datetime.utcnow() + timedelta(hours=ttl_hours)

