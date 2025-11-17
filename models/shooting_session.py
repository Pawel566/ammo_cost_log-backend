from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import uuid4
from datetime import date as Date, datetime


class ShootingSessionBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: Date
    shots: int = Field(gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)
    distance_m: Optional[int] = Field(default=None, gt=0)
    hits: Optional[int] = Field(default=None, ge=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = Field(default=None, max_length=1000)


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    gun: Optional["Gun"] = Relationship(back_populates="sessions")
    ammo: Optional["Ammo"] = Relationship(back_populates="sessions")
