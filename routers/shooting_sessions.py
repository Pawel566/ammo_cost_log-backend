from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy import or_
import asyncio
from models.shooting_session import ShootingSession
from models.ammo import Ammo
from schemas.session import ShootingSessionRead, ShootingSessionCreate
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from datetime import date as DtDate

router = APIRouter(prefix="/shooting-sessions", tags=["Shooting Sessions"])


class ShootingSessionUpdate(BaseModel):
    date: Optional[DtDate] = None
    gun_id: Optional[str] = None
    ammo_id: Optional[str] = None
    shots: Optional[int] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    distance_m: Optional[int] = None
    hits: Optional[int] = None
    accuracy_percent: Optional[float] = None
    ai_comment: Optional[str] = None


@router.post("/", response_model=ShootingSessionRead)
async def create_shooting_session(
    session_data: ShootingSessionCreate,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    data_dict = session_data.model_dump()
    # Mapowanie 'date' z schematu na 'session_date' w modelu
    if 'date' in data_dict:
        data_dict['session_date'] = data_dict.pop('date')
    ss = ShootingSession(**data_dict)
    ss.user_id = user.user_id
    if user.is_guest:
        ss.expires_at = user.expires_at
    db.add(ss)
    await asyncio.to_thread(db.commit)
    await asyncio.to_thread(db.refresh, ss)
    return ss


@router.get("/", response_model=list[ShootingSessionRead])
async def get_all_sessions(
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    query = select(ShootingSession)
    if user.role != UserRole.admin:
        query = query.where(ShootingSession.user_id == user.user_id)
        if user.is_guest:
            query = query.where(
                or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow())
            )
    return await asyncio.to_thread(lambda: db.exec(query).all())


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
    
    return ss


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
    
    # Obsługa aliasu daty i przeliczanie kosztu
    shots_changed = 'shots' in update_data
    ammo_changed = 'ammo_id' in update_data
    cost_provided = 'cost' in update_data
    
    # Jeśli zmieniono shots lub ammo_id, a cost nie jest podane, przelicz koszt
    if (shots_changed or ammo_changed) and not cost_provided:
        # Użyj nowego ammo_id jeśli jest podane, w przeciwnym razie użyj istniejącego
        ammo_id = update_data.get('ammo_id', ss.ammo_id)
        ammo = await asyncio.to_thread(db.get, Ammo, ammo_id)
        if ammo:
            # Użyj nowej liczby strzałów jeśli jest podana, w przeciwnym razie użyj istniejącej
            shots = update_data.get('shots', ss.shots)
            cost = round(ammo.price_per_unit * shots, 2)
            update_data['cost'] = cost
    
    # Aktualizuj pola, obsługując alias daty
    for key, value in update_data.items():
        # Obsłuż alias daty
        if key == 'date':
            setattr(ss, 'session_date', value)
        else:
            setattr(ss, key, value)

    db.add(ss)
    await asyncio.to_thread(db.commit)
    await asyncio.to_thread(db.refresh, ss)
    return ss


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

    await asyncio.to_thread(db.delete, ss)
    await asyncio.to_thread(db.commit)
    return {"message": "Session deleted"}

