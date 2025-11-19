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
    from datetime import datetime as dt
    parsed_date = None
    if session_data.date:
        if isinstance(session_data.date, str):
            parsed_date = dt.strptime(session_data.date, "%Y-%m-%d").date()
        else:
            parsed_date = session_data.date
    else:
        parsed_date = dt.now().date()
    
    ss = ShootingSession(
        gun_id=session_data.gun_id,
        ammo_id=session_data.ammo_id,
        session_date=parsed_date,
        shots=session_data.shots,
        cost=session_data.cost,
        notes=session_data.notes,
        distance_m=session_data.distance_m,
        hits=session_data.hits,
        accuracy_percent=session_data.accuracy_percent,
        ai_comment=session_data.ai_comment,
        user_id=user.user_id,
        expires_at=user.expires_at if user.is_guest else None
    )

    db.add(ss)
    await asyncio.to_thread(db.commit)
    await asyncio.to_thread(db.refresh, ss)

    return ShootingSessionRead.model_validate(ss)


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
    sessions = await asyncio.to_thread(lambda: db.exec(query).all())
    return [ShootingSessionRead.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=ShootingSessionRead)
async def get_session(
    session_id: str,
    db: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    ss = await asyncio.to_thread(db.get, ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")

    if user.role != UserRole.admin and ss.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    return ShootingSessionRead.model_validate(ss)


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

    update_data = session_data.model_dump(exclude_unset=True)

    if "date" in update_data:
        setattr(ss, "session_date", update_data.pop("date"))

    for key, value in update_data.items():
        setattr(ss, key, value)

    db.add(ss)
    await asyncio.to_thread(db.commit)
    await asyncio.to_thread(db.refresh, ss)

    return ShootingSessionRead.model_validate(ss)


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

