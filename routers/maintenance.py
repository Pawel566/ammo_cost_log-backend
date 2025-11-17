from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from schemas.maintenance import MaintenanceCreate, MaintenanceUpdate, MaintenanceRead
from database import get_session
from routers.auth import role_required
from services.maintenance_service import MaintenanceService
from services.user_context import UserContext, UserRole

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_all_maintenance(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    gun_id: Optional[str] = Query(default=None)
):
    return await MaintenanceService.list_all(session, user, gun_id)

@router.get("/guns/{gun_id}/maintenance", response_model=List[MaintenanceRead])
async def get_gun_maintenance(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.list_for_gun(session, user, gun_id)

@router.get("/statistics", response_model=Dict[str, Any])
async def get_maintenance_statistics(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.get_statistics(session, user)

@router.post("/guns/{gun_id}/maintenance", response_model=MaintenanceRead)
async def add_maintenance(
    gun_id: str,
    maintenance_data: MaintenanceCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.create_maintenance(session, user, gun_id, maintenance_data.model_dump())

@router.put("/maintenance/{maintenance_id}", response_model=MaintenanceRead)
async def update_maintenance(
    maintenance_id: str,
    maintenance_data: MaintenanceUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    data_dict = maintenance_data.model_dump(exclude_none=True, by_alias=True)
    return await MaintenanceService.update_maintenance(session, user, maintenance_id, data_dict)

@router.delete("/maintenance/{maintenance_id}")
async def delete_maintenance(
    maintenance_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await MaintenanceService.delete_maintenance(session, user, maintenance_id)



