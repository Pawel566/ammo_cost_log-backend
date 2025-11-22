from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session
from models import ShootingSession
from schemas.shooting_sessions import ShootingSessionRead, ShootingSessionCreate, ShootingSessionUpdate, MonthlySummary
from schemas.pagination import PaginatedResponse
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole
from services.shooting_sessions_service import ShootingSessionsService
from datetime import datetime
from typing import Optional, Dict, Any

router = APIRouter(prefix="/shooting-sessions", tags=["Shooting Sessions"])


class MonthlySummaryResponse(PaginatedResponse[MonthlySummary]):
    pass

#
@router.post("/", response_model=Dict[str, Any])
async def create_shooting_session(
    session_data: ShootingSessionCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.create_shooting_session(session, user, session_data)
    return {
        "id": result["session"].id,
        "gun_id": result["session"].gun_id,
        "ammo_id": result["session"].ammo_id,
        "date": result["session"].date.isoformat(),
        "shots": result["session"].shots,
        "cost": result["session"].cost,
        "notes": result["session"].notes,
        "distance_m": result["session"].distance_m,
        "hits": result["session"].hits,
        "accuracy_percent": result["session"].accuracy_percent,
        "remaining_ammo": result["remaining_ammo"]
    }


@router.get("/", response_model=list[ShootingSessionRead])
async def get_all_sessions(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1),
    gun_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None)
):
    result = await ShootingSessionsService.get_all_sessions(
        session, user, limit, offset, search, gun_id, date_from, date_to
    )
    sessions = result["items"]
    return [
        ShootingSessionRead(
            id=s.id,
            gun_id=s.gun_id,
            ammo_id=s.ammo_id,
            date=s.date.isoformat() if hasattr(s.date, 'isoformat') else str(s.date),
            shots=s.shots,
            cost=s.cost,
            notes=s.notes,
            distance_m=s.distance_m,
            hits=s.hits,
            accuracy_percent=s.accuracy_percent,
            ai_comment=s.ai_comment,
            user_id=s.user_id,
            expires_at=s.expires_at
        )
        for s in sessions
    ]

@router.get("/summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(12, ge=1, le=120),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    result = await ShootingSessionsService.get_monthly_summary(session, user, limit, offset, search)
    return {
        "total": result["total"],
        "items": result["items"],
        "limit": limit,
        "offset": offset
    }


@router.get("/{session_id}", response_model=ShootingSessionRead)
async def get_shooting_session(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = session.get(ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if user.role != UserRole.admin:
        if ss.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if user.is_guest:
            if ss.expires_at and ss.expires_at <= datetime.utcnow():
                raise HTTPException(status_code=404, detail="Session not found")
    
    return ShootingSessionRead(
        id=ss.id,
        gun_id=ss.gun_id,
        ammo_id=ss.ammo_id,
        date=ss.date.isoformat() if hasattr(ss.date, 'isoformat') else str(ss.date),
        shots=ss.shots,
        cost=ss.cost,
        notes=ss.notes,
        distance_m=ss.distance_m,
        hits=ss.hits,
        accuracy_percent=ss.accuracy_percent,
        ai_comment=ss.ai_comment,
        user_id=ss.user_id,
        expires_at=ss.expires_at
    )


@router.patch("/{session_id}", response_model=Dict[str, Any])
async def update_session(
    session_id: str,
    session_data: ShootingSessionUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.update_shooting_session(session, session_id, user, session_data)
    ss = result["session"]
    
    return {
        "id": ss.id,
        "gun_id": ss.gun_id,
        "ammo_id": ss.ammo_id,
        "date": ss.date.isoformat() if hasattr(ss.date, 'isoformat') else str(ss.date),
        "shots": ss.shots,
        "cost": ss.cost,
        "notes": ss.notes,
        "distance_m": ss.distance_m,
        "hits": ss.hits,
        "accuracy_percent": ss.accuracy_percent,
        "remaining_ammo": result.get("remaining_ammo")
    }


@router.delete("/{session_id}", response_model=Dict[str, str])
async def delete_session(
    session_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await ShootingSessionsService.delete_shooting_session(session, session_id, user)
    return result