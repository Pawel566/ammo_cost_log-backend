from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MaintenanceCreate(BaseModel):
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: Optional[int] = Field(default=0, ge=0)
    activities: Optional[List[str]] = Field(default=None)


class MaintenanceUpdate(BaseModel):
    maintenance_date: Optional[date] = Field(default=None, alias="date")
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: Optional[int] = Field(default=None, ge=0)
    activities: Optional[List[str]] = Field(default=None)
    
    model_config = ConfigDict(populate_by_name=True)


class MaintenanceRead(MaintenanceCreate):
    id: str
    gun_id: str
    user_id: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MaintenanceWithGun(MaintenanceRead):
    gun_name: Optional[str] = None



