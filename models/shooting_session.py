from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from typing import Optional
from uuid import uuid4
from datetime import date as Date, datetime


class ShootingSessionBase(SQLModel):
    date: Date
    shots: int = Field(gt=0, le=100000)  # Maksymalna liczba strzałów: 100,000
    cost: Optional[float] = Field(default=None, ge=0, le=1000000)  # Maksymalny koszt: 1,000,000
    notes: Optional[str] = Field(default=None, max_length=500)
    distance_m: Optional[float] = Field(default=None, gt=0, le=10000)  # Maksymalna odległość: 10,000m
    hits: Optional[int] = Field(default=None, ge=0, le=100000)  # Maksymalna liczba trafień: 100,000
    group_cm: Optional[float] = Field(default=None, gt=0, le=10000)  # Maksymalna grupa: 10,000cm
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    final_score: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = Field(default=None, max_length=1000)
    session_type: Optional[str] = Field(default='standard', max_length=20)  # 'standard' or 'advanced'
    target_image_path: Optional[str] = Field(default=None, max_length=500)


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "shooting_sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    gun_id: str = Field(sa_column=Column(ForeignKey("guns.id", ondelete="CASCADE"), nullable=False))
    ammo_id: str = Field(sa_column=Column(ForeignKey("ammo.id", ondelete="CASCADE"), nullable=False))
    user_id: str = Field(index=True, max_length=64)
    gun: Optional["Gun"] = Relationship(back_populates="sessions", passive_deletes=True)
    ammo: Optional["Ammo"] = Relationship(back_populates="sessions", passive_deletes=True)
