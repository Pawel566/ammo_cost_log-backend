from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import uuid4
from datetime import date as Date, datetime
from enum import Enum


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


class AmmoBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    price_per_unit: float = Field(gt=0)
    units_in_package: Optional[int] = Field(default=None, ge=0)


class AmmoUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    units_in_package: Optional[int] = Field(default=None, ge=0)


class ShootingSessionBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: Date
    shots: int = Field(gt=0)
    cost: float = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=500)


class AccuracySessionBase(SQLModel):
    gun_id: str = Field(foreign_key="guns.id")
    ammo_id: str = Field(foreign_key="ammo.id")
    date: Date
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
    gun_id: str = Field(foreign_key="guns.id")
    type: AttachmentType
    name: str = Field(min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class UserSettingsBase(SQLModel):
    ai_mode: str = Field(default="off", max_length=20)
    theme: str = Field(default="dark", max_length=20)
    distance_unit: str = Field(default="m", max_length=2)


class UserBase(SQLModel):
    skill_level: str = Field(default="beginner", max_length=20)


class Gun(GunBase, table=True):
    __tablename__ = "guns"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    sessions: List["ShootingSession"] = Relationship(back_populates="gun")
    accuracy_sessions: List["AccuracySession"] = Relationship(back_populates="gun")
    attachments: List["Attachment"] = Relationship(back_populates="gun")


class Ammo(AmmoBase, table=True):
    __tablename__ = "ammo"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    sessions: List["ShootingSession"] = Relationship(back_populates="ammo")
    accuracy_sessions: List["AccuracySession"] = Relationship(back_populates="ammo")


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    gun: Optional[Gun] = Relationship(back_populates="sessions")
    ammo: Optional[Ammo] = Relationship(back_populates="sessions")


class AccuracySession(AccuracySessionBase, table=True):
    __tablename__ = "accuracy_sessions"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    gun: Optional[Gun] = Relationship(back_populates="accuracy_sessions")
    ammo: Optional[Ammo] = Relationship(back_populates="accuracy_sessions")


class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    gun: Optional[Gun] = Relationship(back_populates="attachments")


class UserSettings(UserSettingsBase, table=True):
    __tablename__ = "user_settings"
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)


class User(UserBase, table=True):
    __tablename__ = "users"
    user_id: str = Field(primary_key=True, max_length=64)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
