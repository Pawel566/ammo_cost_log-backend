from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from schemas.pagination import PaginatedResponse


class SessionCreate(BaseModel):
    gun_id: str = Field(min_length=1)
    ammo_id: str = Field(min_length=1)
    date: Optional[str] = None
    shots: int = Field(gt=0)


class AccuracySessionCreate(SessionCreate):
    distance_m: int = Field(gt=0)
    hits: int = Field(ge=0)
    openai_api_key: Optional[str] = None


class ShootingSessionRead(BaseModel):
    id: str
    gun_id: str
    ammo_id: str
    date: date
    shots: int = Field(gt=0)
    cost: float = Field(ge=0)
    notes: Optional[str] = None
    user_id: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AccuracySessionRead(BaseModel):
    id: str
    gun_id: str
    ammo_id: str
    date: date
    distance_m: int = Field(gt=0)
    hits: int = Field(ge=0)
    shots: int = Field(gt=0)
    accuracy_percent: Optional[float] = None
    ai_comment: Optional[str] = None
    user_id: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int


class SessionsListResponse(BaseModel):
    cost_sessions: PaginatedResponse[ShootingSessionRead]
    accuracy_sessions: PaginatedResponse[AccuracySessionRead]

