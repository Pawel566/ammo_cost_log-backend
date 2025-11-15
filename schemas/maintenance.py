from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MaintenanceCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)


class MaintenanceUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    date: Optional[date] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=500)


class MaintenanceRead(MaintenanceCreate):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    id: str
    gun_id: str
    user_id: str
    rounds_since_last: int
    expires_at: Optional[datetime] = Field(default=None)


