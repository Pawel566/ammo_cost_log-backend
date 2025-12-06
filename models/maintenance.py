from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey, JSON
from typing import Optional, List
from uuid import uuid4
from datetime import date as Date, datetime


class MaintenanceBase(SQLModel):
    date: Date
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: int = Field(ge=0, default=0)
    activities: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))


class Maintenance(MaintenanceBase, table=True):
    __tablename__ = "maintenance"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    gun_id: str = Field(sa_column=Column(ForeignKey("guns.id", ondelete="CASCADE"), nullable=False))
    user_id: str = Field(index=True, max_length=64)
    gun: Optional["Gun"] = Relationship(back_populates="maintenance", passive_deletes=True)

