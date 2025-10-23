from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Gun, GunCreate, GunRead, GunUpdate
from database import get_session

router = APIRouter()

@router.get("/", response_model=List[GunRead])
def get_guns(session: Session = Depends(get_session)):
    """Pobiera listę wszystkich broni"""
    guns = session.exec(select(Gun)).all()
    return guns

@router.get("/{gun_id}", response_model=GunRead)
def get_gun(gun_id: int, session: Session = Depends(get_session)):
    """Pobiera konkretną broń po ID"""
    gun = session.get(Gun, gun_id)
    if not gun:
        raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
    return gun

@router.post("/", response_model=GunRead)
def add_gun(gun_data: GunCreate, session: Session = Depends(get_session)):
    """Dodaje nową broń"""
    gun = Gun.model_validate(gun_data)
    session.add(gun)
    session.commit()
    session.refresh(gun)
    return gun

@router.put("/{gun_id}", response_model=GunRead)
def update_gun(gun_id: int, gun_data: GunUpdate, session: Session = Depends(get_session)):
    """Aktualizuje istniejącą broń"""
    gun = session.get(Gun, gun_id)
    if not gun:
        raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
    
    gun_dict = gun_data.model_dump(exclude_unset=True)
    for key, value in gun_dict.items():
        setattr(gun, key, value)
    
    session.add(gun)
    session.commit()
    session.refresh(gun)
    return gun

@router.delete("/{gun_id}")
def delete_gun(gun_id: int, session: Session = Depends(get_session)):
    """Usuwa broń"""
    gun = session.get(Gun, gun_id)
    if not gun:
        raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
    
    session.delete(gun)
    session.commit()
    return {"message": f"Broń o ID {gun_id} została usunięta"}