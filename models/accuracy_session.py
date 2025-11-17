from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date as Date
from uuid import uuid4
from datetime import datetime


class AccuracySessionBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: Date
    distance_m: int = Field(gt=0)
    hits: int = Field(ge=0)
    shots: int = Field(gt=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = Field(default=None, max_length=1000)
    shooting_session_id: Optional[int] = Field(default=None, foreign_key="shootingsession.id")
    shooting_session: Optional["ShootingSession"] = Relationship(back_populates="accuracy")


class AccuracySession(AccuracySessionBase, table=True):
    __tablename__ = "accuracy_sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

