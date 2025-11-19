from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy import or_
import asyncio
from models import ShootingSession
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
    ss = ShootingSession.model_validate(session_data)
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
    for key, value in update_data.items():
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

