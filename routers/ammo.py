from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel, Field
from models import Ammo, AmmoCreate, AmmoRead, AmmoUpdate
from database import get_session

router = APIRouter()

class QuantityPayload(BaseModel):
    amount: int = Field(gt=0, description="Ilość do dodania")

@router.get("/", response_model=List[AmmoRead])
def get_ammo(session: Session = Depends(get_session)):
    """Pobiera listę wszystkich amunicji"""
    ammo_list = session.exec(select(Ammo)).all()
    return ammo_list

@router.get("/{ammo_id}", response_model=AmmoRead)
def get_ammo_by_id(ammo_id: int, session: Session = Depends(get_session)):
    """Pobiera konkretną amunicję po ID"""
    ammo = session.get(Ammo, ammo_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
    return ammo

@router.post("/", response_model=AmmoRead)
def add_ammo(ammo_data: AmmoCreate, session: Session = Depends(get_session)):
    """Dodaje nową amunicję"""
    ammo = Ammo.model_validate(ammo_data)
    session.add(ammo)
    session.commit()
    session.refresh(ammo)
    return ammo

@router.put("/{ammo_id}", response_model=AmmoRead)
def update_ammo(ammo_id: int, ammo_data: AmmoUpdate, session: Session = Depends(get_session)):
    """Aktualizuje istniejącą amunicję"""
    ammo = session.get(Ammo, ammo_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
    
    ammo_dict = ammo_data.model_dump(exclude_unset=True)
    for key, value in ammo_dict.items():
        setattr(ammo, key, value)
    
    session.add(ammo)
    session.commit()
    session.refresh(ammo)
    return ammo

@router.delete("/{ammo_id}")
def delete_ammo(ammo_id: int, session: Session = Depends(get_session)):
    """Usuwa amunicję"""
    ammo = session.get(Ammo, ammo_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
    
    session.delete(ammo)
    session.commit()
    return {"message": f"Amunicja o ID {ammo_id} została usunięta"}

@router.post("/{ammo_id}/add", response_model=AmmoRead)
def add_ammo_quantity(ammo_id: int, payload: QuantityPayload, session: Session = Depends(get_session)):
    """Dodaje ilość do istniejącej amunicji"""
    ammo = session.get(Ammo, ammo_id)
    if not ammo:
        raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")

    current = ammo.units_in_package or 0
    ammo.units_in_package = current + payload.amount

    session.add(ammo)
    session.commit()
    session.refresh(ammo)
    return ammo