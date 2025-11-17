from typing import Optional, List
from uuid import uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

from datetime import date


class ShootingSessionBase(SQLModel):
    date: date
    weapon_id: str = Field(foreign_key="guns.id")
    notes: Optional[str] = None
    total_shots: Optional[int] = None


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "shootingsession"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    # relacje do opcjonalnych modułów
    cost: Optional["CostSession"] = Relationship(
        back_populates="shooting_session"
    )
    accuracy: Optional["AccuracySession"] = Relationship(
        back_populates="shooting_session"
    )


class ShootingSessionRead(ShootingSessionBase):
    id: str


class ShootingSessionCreate(ShootingSessionBase):
    pass


class ShootingSessionUpdate(SQLModel):
    date: Optional[date] = None
    weapon_id: Optional[str] = None
    notes: Optional[str] = None
    total_shots: Optional[int] = None

