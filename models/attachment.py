from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum
from typing import Optional
from uuid import uuid4
from datetime import datetime
from enum import Enum


class AttachmentType(str, Enum):
    optic = "optic"
    light = "light"
    laser = "laser"
    suppressor = "suppressor"
    bipod = "bipod"
    compensator = "compensator"
    grip = "grip"
    trigger = "trigger"
    other = "other"


class AttachmentBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    type: AttachmentType = Field(sa_column=Column(SQLEnum(AttachmentType, name="attachment_type_enum")))
    gun: Optional["Gun"] = Relationship(back_populates="attachments")

