from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional
from schemas.gun import GunCreate, GunRead
from schemas.pagination import PaginatedResponse
from models import GunUpdate
from database import get_session
from routers.auth import role_required
from services.gun_service import GunService
from services.user_context import UserContext, UserRole

router = APIRouter()

@router.get("", response_model=PaginatedResponse[GunRead])
async def get_guns(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    return await GunService.get_all_guns(session, user, limit, offset, search)

@router.get("/{gun_id}", response_model=GunRead)
async def get_gun(
    gun_id: int,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.get_gun_by_id(session, gun_id, user)

@router.post("", response_model=GunRead)
async def add_gun(
    gun_data: GunCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.create_gun(session, gun_data, user)

@router.put("/{gun_id}", response_model=GunRead)
async def update_gun(
    gun_id: int,
    gun_data: GunUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.update_gun(session, gun_id, gun_data, user)

@router.delete("/{gun_id}")
async def delete_gun(
    gun_id: int,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.delete_gun(session, gun_id, user)