from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import uuid4
from datetime import date as Date, datetime


class MaintenanceBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    date: Date
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: int = Field(ge=0, default=0)


class Maintenance(MaintenanceBase, table=True):
    __tablename__ = "maintenance"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    gun: Optional["Gun"] = Relationship(back_populates="maintenance")

