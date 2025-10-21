from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date


class GunBase(SQLModel):
    name: str
    caliber: Optional[str] = None
    notes: Optional[str] = None



class AmmoBase(SQLModel):
    name: str
    caliber: Optional[str] = None
    price_per_unit: float
    units_in_package: Optional[int] = None


class SessionBase(SQLModel):
    gun_id: int = Field(foreign_key="gun.id")
    ammo_id: int = Field(foreign_key="ammo.id")
    date: date
    shots: int
    cost: float
    notes: Optional[str] = None


class Gun(GunBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Ammo(AmmoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Session(SessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
