from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import uuid4
from datetime import date, datetime
from enum import Enum
from pydantic import ConfigDict
from sqlalchemy.orm import Mapped


class GunBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = Field(min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class GunUpdate(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class AmmoBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = Field(min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    price_per_unit: float = Field(gt=0)
    units_in_package: Optional[int] = Field(default=None, ge=0)


class AmmoUpdate(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    units_in_package: Optional[int] = Field(default=None, ge=0)


class ShootingSessionBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: date
    shots: int = Field(gt=0)
    cost: float = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)


class AccuracySessionBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: date
    distance_m: int = Field(gt=0)
    hits: int = Field(ge=0)
    shots: int = Field(gt=0)
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100)
    ai_comment: Optional[str] = Field(default=None, max_length=1000)


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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gun_id: str = Field(foreign_key="guns.id")
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class MaintenanceBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    gun_id: str = Field(foreign_key="guns.id")
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)
    rounds_since_last: int = Field(ge=0)


class UserSettingsBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ai_mode: str = Field(default="off", max_length=20)
    theme: str = Field(default="dark", max_length=20)
    distance_unit: str = Field(default="m", max_length=2)


class UserBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    skill_level: str = Field(default="beginner", max_length=20)


class Gun(GunBase, table=True):
    __tablename__ = "guns"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    sessions: Mapped[List["ShootingSession"]] = Relationship(back_populates="gun")
    accuracy_sessions: Mapped[List["AccuracySession"]] = Relationship(back_populates="gun")
    attachments: Mapped[List["Attachment"]] = Relationship(back_populates="gun")
    maintenance: Mapped[List["Maintenance"]] = Relationship(back_populates="gun")


class Ammo(AmmoBase, table=True):
    __tablename__ = "ammo"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    sessions: Mapped[List["ShootingSession"]] = Relationship(back_populates="ammo")
    accuracy_sessions: Mapped[List["AccuracySession"]] = Relationship(back_populates="ammo")


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "sessions"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    gun: Mapped[Optional["Gun"]] = Relationship(back_populates="sessions")
    ammo: Mapped[Optional["Ammo"]] = Relationship(back_populates="sessions")


class AccuracySession(AccuracySessionBase, table=True):
    __tablename__ = "accuracy_sessions"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    gun: Mapped[Optional["Gun"]] = Relationship(back_populates="accuracy_sessions")
    ammo: Mapped[Optional["Ammo"]] = Relationship(back_populates="accuracy_sessions")


class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    gun: Mapped[Optional["Gun"]] = Relationship(back_populates="attachments")


class Maintenance(MaintenanceBase, table=True):
    __tablename__ = "maintenance"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    gun: Mapped[Optional["Gun"]] = Relationship(back_populates="maintenance")


class UserSettings(UserSettingsBase, table=True):
    __tablename__ = "user_settings"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)


class User(UserBase, table=True):
    __tablename__ = "users"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
