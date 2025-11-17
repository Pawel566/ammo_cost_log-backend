from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from models.shooting_session import (
    ShootingSession, ShootingSessionRead, ShootingSessionCreate, ShootingSessionUpdate
)
from models.cost_session import CostSession
from models.accuracy_session import AccuracySession
from database import get_session

router = APIRouter(prefix="/shooting-sessions", tags=["Shooting Sessions"])


@router.post("/", response_model=ShootingSessionRead)
def create_shooting_session(
    session_data: ShootingSessionCreate,
    db: Session = Depends(get_session)
):
    ss = ShootingSession.model_validate(session_data)
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss


@router.get("/", response_model=list[ShootingSessionRead])
def get_all_sessions(db: Session = Depends(get_session)):
    return db.exec(select(ShootingSession)).all()


@router.get("/{session_id}", response_model=ShootingSessionRead)
def get_session(session_id: str, db: Session = Depends(get_session)):
    ss = db.get(ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")
    return ss


@router.patch("/{session_id}", response_model=ShootingSessionRead)
def update_session(
    session_id: str,
    session_data: ShootingSessionUpdate,
    db: Session = Depends(get_session)
):
    ss = db.get(ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = session_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ss, key, value)

    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_session)):
    ss = db.get(ShootingSession, session_id)
    if not ss:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(ss)
    db.commit()
    return {"message": "Session deleted"}

