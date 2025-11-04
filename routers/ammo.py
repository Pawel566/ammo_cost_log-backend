from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from pydantic import BaseModel, Field
from models import AmmoCreate, AmmoRead, AmmoUpdate
from database import get_session
from services.ammo_service import AmmoService

router = APIRouter()

class QuantityPayload(BaseModel):
    amount: int = Field(gt=0)

@router.get("/", response_model=List[AmmoRead])
async def get_ammo(session: Session = Depends(get_session)):
    return await AmmoService.get_all_ammo(session)

@router.get("/{ammo_id}", response_model=AmmoRead)
async def get_ammo_by_id(ammo_id: int, session: Session = Depends(get_session)):
    return await AmmoService.get_ammo_by_id(session, ammo_id)

@router.post("/", response_model=AmmoRead)
async def add_ammo(ammo_data: AmmoCreate, session: Session = Depends(get_session)):
    return await AmmoService.create_ammo(session, ammo_data)

@router.put("/{ammo_id}", response_model=AmmoRead)
async def update_ammo(ammo_id: int, ammo_data: AmmoUpdate, session: Session = Depends(get_session)):
    return await AmmoService.update_ammo(session, ammo_id, ammo_data)

@router.delete("/{ammo_id}")
async def delete_ammo(ammo_id: int, session: Session = Depends(get_session)):
    return await AmmoService.delete_ammo(session, ammo_id)

@router.post("/{ammo_id}/add", response_model=AmmoRead)
async def add_ammo_quantity(ammo_id: int, payload: QuantityPayload, session: Session = Depends(get_session)):
    return await AmmoService.add_ammo_quantity(session, ammo_id, payload.amount)