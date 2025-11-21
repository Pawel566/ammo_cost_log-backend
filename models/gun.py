from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import uuid4
from datetime import datetime


class GunBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class GunUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class Gun(GunBase, table=True):
    __tablename__ = "guns"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    sessions: List["ShootingSession"] = Relationship(back_populates="gun", passive_deletes=True)
    attachments: List["Attachment"] = Relationship(back_populates="gun", passive_deletes=True)
    maintenance: List["Maintenance"] = Relationship(back_populates="gun", passive_deletes=True)

