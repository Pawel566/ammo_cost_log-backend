from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ShootingSessionBase(BaseModel):
    date: Optional[date] = None
    cost: Optional[float] = Field(default=None, ge=0, le=1000000)
    notes: Optional[str] = None
    distance_m: Optional[float] = Field(default=None, gt=0, le=10000)
    hits: Optional[int] = Field(default=None, ge=0, le=100000)
    group_cm: Optional[float] = Field(default=None, gt=0, le=10000)
    session_type: Optional[str] = Field(default='standard', max_length=20)

    @model_validator(mode='after')
    def validate_hits_and_date(self):
        shots = getattr(self, 'shots', None)
        if shots is not None and self.hits is not None:
            if self.hits > shots:
                raise ValueError('hits must not exceed shots')
        if self.date is not None and self.date > date.today():
            raise ValueError('date cannot be in the future')
        return self


class ShootingSessionCreate(ShootingSessionBase):
    gun_id: str = Field(min_length=1)
    ammo_id: str = Field(min_length=1)
    shots: int = Field(gt=0, le=100000)


class ShootingSessionUpdate(ShootingSessionBase):
    gun_id: Optional[str] = None
    ammo_id: Optional[str] = None
    shots: Optional[int] = Field(default=None, gt=0, le=100000)


class ShootingSessionRead(BaseModel):
    id: str
    gun_id: str
    ammo_id: str
    date: str
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    distance_m: Optional[float] = Field(default=None, gt=0)
    distance: Optional[float] = Field(default=None, gt=0)
    distance_unit: Optional[str] = Field(default=None, max_length=2)
    hits: Optional[int] = Field(default=None, ge=0)
    group_cm: Optional[float] = Field(default=None, gt=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    final_score: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = None
    session_type: Optional[str] = Field(default='standard', max_length=20)
    target_image_path: Optional[str] = None
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int













