from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MaintenanceCreate(BaseModel):
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: Optional[int] = Field(default=0, ge=0)


class MaintenanceUpdate(BaseModel):
    date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: Optional[int] = Field(default=None, ge=0)


class MaintenanceRead(MaintenanceCreate):
    id: str
    gun_id: str
    user_id: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MaintenanceWithGun(MaintenanceRead):
    gun_name: Optional[str] = None



