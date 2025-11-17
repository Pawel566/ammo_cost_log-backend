from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date as Date
from uuid import uuid4
from datetime import datetime


class CostSessionBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: Date
    shots: int = Field(gt=0)
    cost: float = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)
    shooting_session_id: Optional[str] = Field(default=None, foreign_key="shootingsession.id")
    shooting_session: Optional["ShootingSession"] = Relationship(back_populates="cost")


class CostSession(CostSessionBase, table=True):
    __tablename__ = "cost_sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

