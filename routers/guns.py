from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from models import GunCreate, GunRead, GunUpdate
from database import get_session
from services.gun_service import GunService

router = APIRouter()

@router.get("/", response_model=List[GunRead])
async def get_guns(session: Session = Depends(get_session)):
    return await GunService.get_all_guns(session)

@router.get("/{gun_id}", response_model=GunRead)
async def get_gun(gun_id: int, session: Session = Depends(get_session)):
    return await GunService.get_gun_by_id(session, gun_id)

@router.post("/", response_model=GunRead)
async def add_gun(gun_data: GunCreate, session: Session = Depends(get_session)):
    return await GunService.create_gun(session, gun_data)

@router.put("/{gun_id}", response_model=GunRead)
async def update_gun(gun_id: int, gun_data: GunUpdate, session: Session = Depends(get_session)):
    return await GunService.update_gun(session, gun_id, gun_data)

@router.delete("/{gun_id}")
async def delete_gun(gun_id: int, session: Session = Depends(get_session)):
    return await GunService.delete_gun(session, gun_id)