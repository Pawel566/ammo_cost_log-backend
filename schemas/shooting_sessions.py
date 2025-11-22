from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ShootingSessionCreate(BaseModel):
    gun_id: str = Field(min_length=1)
    ammo_id: str = Field(min_length=1)
    date: Optional[str] = None
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    distance_m: Optional[float] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)


class ShootingSessionUpdate(BaseModel):
    date: Optional[str] = None
    gun_id: Optional[str] = None
    ammo_id: Optional[str] = None
    shots: Optional[int] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)
    distance_m: Optional[float] = Field(default=None, gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None


class ShootingSessionRead(BaseModel):
    id: str
    gun_id: str
    ammo_id: str
    date: str
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    distance_m: Optional[float] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int


