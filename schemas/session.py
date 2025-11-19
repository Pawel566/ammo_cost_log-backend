from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional
from schemas.pagination import PaginatedResponse

class ShootingSessionCreate(BaseModel):
    gun_id: str = Field(min_length=1)
    ammo_id: str = Field(min_length=1)
    date: Optional[str] = None
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    distance_m: Optional[int] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)


class ShootingSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    date: date = Field(alias="session_date")  # alias -> z session_date
    gun_id: str
    ammo_id: str
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    distance_m: Optional[int] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = None
    user_id: str
    expires_at: Optional[datetime] = None


class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int


class SessionsListResponse(BaseModel):
    sessions: PaginatedResponse[ShootingSessionRead]

