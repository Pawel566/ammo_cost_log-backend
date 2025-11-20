from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import or_
import asyncio
from models import ShootingSession
from schemas.session import ShootingSessionRead, ShootingSessionCreate, MonthlySummary
from schemas.pagination import PaginatedResponse
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole
from services.session_service import SessionService
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/shooting-sessions", tags=["Shooting Sessions"])


class ShootingSessionUpdate(BaseModel):
    date: Optional[str] = None
    gun_id: Optional[str] = None
    ammo_id: Optional[str] = None
    shots: Optional[int] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    distance_m: Optional[int] = None
    hits: Optional[int] = None


class MonthlySummaryResponse(PaginatedResponse[MonthlySummary]):
    pass


@router.post("/", response_model=Dict[str, Any])
async def create_shooting_session(
    session_data: ShootingSessionCreate,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    result = await SessionService.create_shooting_session(db, user, session_data)
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
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1),
    gun_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None)
):
    result = await SessionService.get_all_sessions(
        db, user, limit, offset, search, gun_id, date_from, date_to
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


@router.get("/{session_id}", response_model=ShootingSessionRead)
async def get_session(
    session_id: str,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = await asyncio.to_thread(db.get, ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if user.role != UserRole.admin:
        if ss.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if user.is_guest and ss.expires_at and ss.expires_at <= datetime.utcnow():
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


@router.patch("/{session_id}", response_model=ShootingSessionRead)
async def update_session(
    session_id: str,
    session_data: ShootingSessionUpdate,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = await asyncio.to_thread(db.get, ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if user.role != UserRole.admin:
        if ss.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if user.is_guest and ss.expires_at and ss.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=404, detail="Session not found")

    update_data = session_data.model_dump(exclude_unset=True)
    
    if "date" in update_data and update_data["date"]:
        from services.session_service import SessionCalculationService
        update_data["date"] = SessionCalculationService.parse_date(update_data["date"])
    
    # Walidacja przed aktualizacją amunicji
    if "gun_id" in update_data or "ammo_id" in update_data or "shots" in update_data or "hits" in update_data:
        gun_id = update_data.get("gun_id", ss.gun_id)
        ammo_id = update_data.get("ammo_id", ss.ammo_id)
        shots = update_data.get("shots", ss.shots)
        hits = update_data.get("hits", ss.hits)
        
        from services.session_service import SessionValidationService
        from models import Gun, Ammo
        gun = await SessionService._get_gun(db, gun_id, user)
        ammo = await SessionService._get_ammo(db, ammo_id, user)
        SessionValidationService.validate_session_data(gun, ammo, shots, hits)
        
        if "distance_m" in update_data and update_data["distance_m"] is not None and hits is not None and shots > 0:
            from services.session_service import SessionCalculationService
            update_data["accuracy_percent"] = SessionCalculationService.calculate_accuracy(hits, shots)
        elif "hits" in update_data or "shots" in update_data:
            distance_m = update_data.get("distance_m", ss.distance_m)
            if distance_m is not None and hits is not None and shots > 0:
                from services.session_service import SessionCalculationService
                update_data["accuracy_percent"] = SessionCalculationService.calculate_accuracy(hits, shots)
            else:
                update_data["accuracy_percent"] = None
    
    # Aktualizacja amunicji jeśli zmienia się liczba strzałów lub ammo_id (po walidacji)
    if "shots" in update_data or "ammo_id" in update_data:
        old_ammo_id = ss.ammo_id
        new_ammo_id = update_data.get("ammo_id", ss.ammo_id)
        old_shots = ss.shots
        new_shots = update_data.get("shots", ss.shots)
        
        if old_ammo_id != new_ammo_id or old_shots != new_shots:
            if old_ammo_id == new_ammo_id:
                # Ta sama amunicja, tylko zmiana liczby strzałów
                old_ammo = await SessionService._get_ammo(db, old_ammo_id, user)
                if old_ammo and old_ammo.units_in_package is not None:
                    old_ammo.units_in_package += old_shots
                    old_ammo.units_in_package -= new_shots
                    db.add(old_ammo)
            else:
                # Różna amunicja
                old_ammo = await SessionService._get_ammo(db, old_ammo_id, user)
                new_ammo = await SessionService._get_ammo(db, new_ammo_id, user)
                if old_ammo and old_ammo.units_in_package is not None:
                    old_ammo.units_in_package += old_shots
                    db.add(old_ammo)
                if new_ammo and new_ammo.units_in_package is not None:
                    new_ammo.units_in_package -= new_shots
                    db.add(new_ammo)
    
    for key, value in update_data.items():
        setattr(ss, key, value)

    db.add(ss)
    await asyncio.to_thread(db.commit)
    await asyncio.to_thread(db.refresh, ss)
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


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = await asyncio.to_thread(db.get, ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if user.role != UserRole.admin:
        if ss.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        if user.is_guest and ss.expires_at and ss.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=404, detail="Session not found")

    # Przywróć amunicję
    from models import Ammo
    ammo = await SessionService._get_ammo(db, ss.ammo_id, user)
    if ammo:
        if ammo.units_in_package is not None:
            ammo.units_in_package += ss.shots
        db.add(ammo)

    await asyncio.to_thread(db.delete, ss)
    await asyncio.to_thread(db.commit)
    return {"message": "Session deleted"}


@router.get("/summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(12, ge=1, le=120),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    result = await SessionService.get_monthly_summary(db, user, limit, offset, search)
    return {
        "total": result["total"],
        "items": result["items"],
        "limit": limit,
        "offset": offset
    }

