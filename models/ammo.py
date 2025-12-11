from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Enum as SQLEnum
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
from enum import Enum


class AmmoType(str, Enum):
    FMJ = "FMJ"
    HP = "HP"
    SP = "SP"
    MATCH = "Match"
    TRAINING = "Training"
    SUBSONIC = "Subsonic"
    MAGNUM = "Magnum"
    BIRDSHOT = "Birdshot"
    BUCKSHOT = "Buckshot"
    SLUG = "Slug"


class AmmoCategory(str, Enum):
    PISTOL = "pistol"
    REVOLVER = "revolver"
    RIFLE = "rifle"
    SHOTGUN = "shotgun"
    OTHER = "other"


class AmmoBase(SQLModel):
    name: str = Field(min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=50)
    type: Optional[AmmoType] = Field(default=None)
    category: Optional[AmmoCategory] = Field(default=None)
    price_per_unit: float = Field(gt=0, le=1000000)  # Maksymalna cena: 1,000,000
    units_in_package: Optional[int] = Field(default=None, ge=0, le=1000000)  # Maksymalna ilość: 1,000,000


class AmmoUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=50)
    type: Optional[AmmoType] = Field(default=None)
    category: Optional[AmmoCategory] = Field(default=None)
    price_per_unit: Optional[float] = Field(default=None, gt=0, le=1000000)  # Maksymalna cena: 1,000,000
    units_in_package: Optional[int] = Field(default=None, ge=0, le=1000000)  # Maksymalna ilość: 1,000,000


class Ammo(AmmoBase, table=True):
    __tablename__ = "ammo"
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True, max_length=64)
    type: Optional[AmmoType] = Field(default=None, sa_column=Column(SQLEnum(AmmoType, name="ammo_type_enum"), nullable=True))
    category: Optional[AmmoCategory] = Field(default=None, sa_column=Column(SQLEnum(AmmoCategory, name="ammo_category_enum"), nullable=True))
    sessions: List["ShootingSession"] = Relationship(back_populates="ammo", passive_deletes=True)

