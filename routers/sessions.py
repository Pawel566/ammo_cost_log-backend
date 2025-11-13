from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Dict, Any, Optional
from database import get_session
from routers.auth import role_required
from services.session_service import SessionService
from services.user_context import UserContext, UserRole
from schemas.session import (
    SessionCreate,
    AccuracySessionCreate,
    SessionsListResponse,
    MonthlySummary,
)
from schemas.pagination import PaginatedResponse

router = APIRouter()


class MonthlySummaryResponse(PaginatedResponse[MonthlySummary]):
    pass


@router.get("", response_model=SessionsListResponse)
async def get_all_sessions(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    return await SessionService.get_all_sessions(session, user, limit, offset, search)


@router.post("/cost", response_model=Dict[str, Any])
async def add_cost_session(
    data: SessionCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await SessionService.create_cost_session(
        session,
        user,
        data.gun_id,
        data.ammo_id,
        data.date,
        data.shots
    )


@router.post("/accuracy", response_model=Dict[str, Any])
async def add_accuracy_session(
    data: AccuracySessionCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await SessionService.create_accuracy_session(
        session,
        user,
        data.gun_id,
        data.ammo_id,
        data.date,
        data.distance_m,
        data.shots,
        data.hits,
        data.openai_api_key
    )


@router.get("/summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(12, ge=1, le=120),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    return await SessionService.get_monthly_summary(session, user, limit, offset, search)
