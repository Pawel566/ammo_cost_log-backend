from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from models import Session as ShootingSession, Ammo, Gun, SessionBase
from database import engine
from datetime import date,datetime

router = APIRouter()

@router.get("/")
def get_sessions():
    with Session(engine) as db:
        sessions = db.exec(select(ShootingSession)).all()
        return sessions

@router.post("/")
def add_session(session_data: SessionBase):
    if isinstance(session_data.date, str):
        session_data.date = datetime.strptime(session_data.date, "%Y-%m-%d").date()

    if session_data.shots <= 0:
        raise HTTPException(status_code=400, detail="Shots must be > 0")
    if session_data.date > date.today():
        raise HTTPException(status_code=400, detail="Date cannot be in the future")

    with Session(engine) as db:
        gun = db.get(Gun, session_data.gun_id)
        ammo = db.get(Ammo, session_data.ammo_id)

        if not gun:
            raise HTTPException(status_code=404, detail="Gun not found")
        if not ammo:
            raise HTTPException(status_code=404, detail="Ammo not found")


        session_data.cost = session_data.shots * ammo.price_per_unit

        db.add(session_data)
        db.commit()
        db.refresh(session_data)
        return session_data

from collections import defaultdict

@router.get("/summary")
def get_monthly_summary():

    with Session(engine) as db:
        sessions = db.exec(select(ShootingSession)).all()

        if not sessions:
            return []

        summary = defaultdict(float)

        for s in sessions:
            month_key = s.date.strftime("%Y-%m")
            summary[month_key] += float(s.cost)

        result = [{"month": k, "total_cost": round(v, 2)} for k, v in sorted(summary.items())]
        return result
