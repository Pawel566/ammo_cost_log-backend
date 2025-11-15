from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional, List
from schemas.gun import GunCreate, GunRead
from schemas.pagination import PaginatedResponse
from schemas.attachment import AttachmentCreate, AttachmentRead
from schemas.maintenance import MaintenanceCreate, MaintenanceRead
from models import GunUpdate
from database import get_session
from routers.auth import role_required
from services.gun_service import GunService
from services.attachments_service import AttachmentsService
from services.maintenance_service import MaintenanceService
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
    gun_id: str,
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
    gun_id: str,
    gun_data: GunUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.update_gun(session, gun_id, gun_data, user)

@router.delete("/{gun_id}")
async def delete_gun(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.delete_gun(session, gun_id, user)


@router.get("/{gun_id}/attachments", response_model=List[AttachmentRead])
async def get_gun_attachments(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.list_for_gun(session, user, gun_id)


@router.post("/{gun_id}/attachments", response_model=AttachmentRead)
async def add_attachment(
    gun_id: str,
    attachment_data: AttachmentCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.create_attachment(session, user, gun_id, attachment_data.model_dump())


@router.delete("/{gun_id}/attachments/{attachment_id}")
async def delete_attachment(
    gun_id: str,
    attachment_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.delete_attachment(session, user, attachment_id)


@router.get("/{gun_id}/maintenance", response_model=List[MaintenanceRead])
async def get_gun_maintenance(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.list_for_gun(session, user, gun_id)


@router.post("/{gun_id}/maintenance", response_model=MaintenanceRead)
async def add_maintenance(
    gun_id: str,
    maintenance_data: MaintenanceCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.create_maintenance(session, user, gun_id, maintenance_data.model_dump())


@router.delete("/{gun_id}/maintenance/{maintenance_id}")
async def delete_maintenance(
    gun_id: str,
    maintenance_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.delete_maintenance(session, user, maintenance_id)