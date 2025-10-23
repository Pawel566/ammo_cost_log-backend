from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date as Date
from decimal import Decimal


class GunBase(SQLModel):
    name: str = Field(min_length=1, max_length=100, description="Nazwa broni")
    caliber: Optional[str] = Field(default=None, max_length=20, description="Kaliber")
    notes: Optional[str] = Field(default=None, max_length=500, description="Notatki")


class GunCreate(GunBase):
    pass


class GunRead(GunBase):
    id: int


class GunUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = Field(default=None, max_length=500)


class AmmoBase(SQLModel):
    name: str = Field(min_length=1, max_length=100, description="Nazwa amunicji")
    caliber: Optional[str] = Field(default=None, max_length=20, description="Kaliber")
    price_per_unit: float = Field(gt=0, description="Cena za jednostkę")
    units_in_package: Optional[int] = Field(default=None, ge=0, description="Ilość w opakowaniu")


class AmmoCreate(AmmoBase):
    pass


class AmmoRead(AmmoBase):
    id: int


class AmmoUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    caliber: Optional[str] = Field(default=None, max_length=20)
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    units_in_package: Optional[int] = Field(default=None, ge=0)


class ShootingSessionBase(SQLModel):
    gun_id: int = Field(foreign_key="guns.id", description="ID broni")
    ammo_id: int = Field(foreign_key="ammo.id", description="ID amunicji")
    date: Date = Field(description="Data sesji")
    shots: int = Field(gt=0, description="Liczba strzałów")
    cost: float = Field(ge=0, description="Koszt")
    notes: Optional[str] = Field(default=None, max_length=500, description="Notatki")


class ShootingSessionCreate(ShootingSessionBase):
    pass


class ShootingSessionRead(ShootingSessionBase):
    id: int


class AccuracySessionBase(SQLModel):
    gun_id: int = Field(foreign_key="guns.id", description="ID broni")
    ammo_id: int = Field(foreign_key="ammo.id", description="ID amunicji")
    date: Date = Field(description="Data sesji")
    distance_m: int = Field(gt=0, description="Dystans w metrach")
    hits: int = Field(ge=0, description="Liczba trafień")
    shots: int = Field(gt=0, description="Liczba strzałów")
    accuracy_percent: Optional[float] = Field(default=None, ge=0, le=100, description="Celność w procentach")
    ai_comment: Optional[str] = Field(default=None, max_length=1000, description="Komentarz AI")


class AccuracySessionCreate(AccuracySessionBase):
    pass


class AccuracySessionRead(AccuracySessionBase):
    id: int


class Gun(GunBase, table=True):
    __tablename__ = "guns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    sessions: List["ShootingSession"] = Relationship(back_populates="gun")
    accuracy_sessions: List["AccuracySession"] = Relationship(back_populates="gun")


class Ammo(AmmoBase, table=True):
    __tablename__ = "ammo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    sessions: List["ShootingSession"] = Relationship(back_populates="ammo")
    accuracy_sessions: List["AccuracySession"] = Relationship(back_populates="ammo")


class ShootingSession(ShootingSessionBase, table=True):
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    gun: Optional[Gun] = Relationship(back_populates="sessions")
    ammo: Optional[Ammo] = Relationship(back_populates="sessions")


class AccuracySession(AccuracySessionBase, table=True):
    __tablename__ = "accuracy_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    gun: Optional[Gun] = Relationship(back_populates="accuracy_sessions")
    ammo: Optional[Ammo] = Relationship(back_populates="accuracy_sessions")
