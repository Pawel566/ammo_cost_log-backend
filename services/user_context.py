from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Any
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

    def model_post_init(self, __context: Any) -> None:
        if self.is_guest and self.expires_at is None:
            self.expires_at = calculate_guest_expiration()


def calculate_guest_expiration() -> datetime:
    ttl_hours = settings.guest_session_ttl_hours or 24
    return datetime.utcnow() + timedelta(hours=ttl_hours)

