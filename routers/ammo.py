from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.ammo import AmmoCreate, AmmoRead
from schemas.pagination import PaginatedResponse
from models import AmmoUpdate
from database import get_session
from routers.auth import role_required
from services.ammo_service import AmmoService
from services.user_context import UserContext, UserRole

router = APIRouter()

class QuantityPayload(BaseModel):
    amount: int = Field(gt=0)

@router.get("", response_model=PaginatedResponse[AmmoRead])
async def get_ammo(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    return await AmmoService.get_all_ammo(session, user, limit, offset, search)

@router.get("/{ammo_id}", response_model=AmmoRead)
async def get_ammo_by_id(
    ammo_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AmmoService.get_ammo_by_id(session, ammo_id, user)

@router.post("", response_model=AmmoRead)
async def add_ammo(
    ammo_data: AmmoCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AmmoService.create_ammo(session, ammo_data, user)

@router.put("/{ammo_id}", response_model=AmmoRead)
async def update_ammo(
    ammo_id: str,
    ammo_data: AmmoUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AmmoService.update_ammo(session, ammo_id, ammo_data, user)

@router.delete("/{ammo_id}")
async def delete_ammo(
    ammo_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AmmoService.delete_ammo(session, ammo_id, user)

@router.post("/{ammo_id}/add", response_model=AmmoRead)
async def add_ammo_quantity(
    ammo_id: str,
    payload: QuantityPayload,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AmmoService.add_ammo_quantity(session, ammo_id, payload.amount, user)