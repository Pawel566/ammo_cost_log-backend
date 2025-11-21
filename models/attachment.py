from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum, ForeignKey
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
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    gun_id: str = Field(sa_column=Column(ForeignKey("guns.id", ondelete="CASCADE"), nullable=False))
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    type: AttachmentType = Field(sa_column=Column(SQLEnum(AttachmentType, name="attachment_type_enum")))
    gun: Optional["Gun"] = Relationship(back_populates="attachments", passive_deletes=True)

