from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MaintenanceCreate(BaseModel):
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)


class MaintenanceRead(MaintenanceCreate):
    id: str
    gun_id: str
    user_id: str
    rounds_since_last: int
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


