from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum, ForeignKey
from typing import Optional
from uuid import uuid4
from datetime import datetime
from enum import Enum


class AttachmentType(str, Enum):
    red_dot = "red_dot"
    reflex = "reflex"
    lpvo = "lpvo"
    magnifier = "magnifier"
    suppressor = "suppressor"
    compensator = "compensator"
    foregrip = "foregrip"
    angled_grip = "angled_grip"
    bipod = "bipod"
    tactical_light = "tactical_light"


class AttachmentBase(SQLModel):
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    precision_help: str = Field(default="none", max_length=20)  # Dozwolone: none, low, medium, high
    recoil_reduction: str = Field(default="none", max_length=20)  # Dozwolone: none, low, medium, high
    ergonomics: str = Field(default="none", max_length=20)  # Dozwolone: none, low, medium, high
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    gun_id: str = Field(sa_column=Column(ForeignKey("guns.id", ondelete="CASCADE"), nullable=False))
    user_id: str = Field(index=True, max_length=64)
    type: AttachmentType = Field(sa_column=Column(SQLEnum(AttachmentType, name="attachment_type_enum")))
    gun: Optional["Gun"] = Relationship(back_populates="attachments", passive_deletes=True)

