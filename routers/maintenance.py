from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import date
from schemas.maintenance import MaintenanceRead
from database import get_session
from routers.auth import role_required
from services.maintenance_service import MaintenanceService
from services.user_context import UserContext, UserRole

router = APIRouter()


@router.get("", response_model=List[MaintenanceRead])
async def get_all_maintenance(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    gun_id: Optional[str] = Query(default=None)
):
    filters = {}
    if gun_id:
        filters["gun_id"] = gun_id
    return await MaintenanceService.list_global(session, user, filters if filters else None)

