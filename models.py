from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

class GunBase(SQLModel):
    name: str
    caliber: Optional[str] = None
    notes: Optional[str] = None



class AmmoBase(SQLModel):
    name: str
    caliber: Optional[str] = None
    price_per_unit: Decimal
    units_in_package: Optional[int] = None


class SessionBase(SQLModel):
    gun_id: int
    ammo_id: int
    date: date
    shots: int
    cost: Decimal
    notes: Optional[str] = None


class Gun(GunBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Ammo(AmmoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Session(SessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
