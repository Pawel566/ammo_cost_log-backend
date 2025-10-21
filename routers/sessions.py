from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from models import Session as ShootingSession, Ammo, Gun, SessionBase
from database import engine
from datetime import date,datetime
from collections import defaultdict

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

        if ammo.units_in_package is None:
            raise HTTPException(status_code=400, detail="Ammo quantity not set")
        if ammo.units_in_package < session_data.shots:
            raise HTTPException(status_code=400, detail=f"Not enough ammo. Only {ammo.units_in_package} left.")

        ammo.units_in_package -= session_data.shots

        session_data.cost = session_data.shots * ammo.price_per_unit

        new_session = ShootingSession.model_validate(session_data)
        db.add(new_session)
        db.add(ammo)
        db.commit()
        db.refresh(new_session)

        return {
            "session": new_session,
            "remaining_ammo": ammo.units_in_package
        }



@router.get("/summary")
def get_monthly_summary():
    with Session(engine) as db:
        sessions = db.exec(select(ShootingSession)).all()

        if not sessions:
            return []

        cost_summary = defaultdict(float)
        shot_summary = defaultdict(int)

        for s in sessions:
            month_key = s.date.strftime("%Y-%m")
            cost_summary[month_key] += float(s.cost)
            shot_summary[month_key] += s.shots

        result = [
            {
                "month": month,
                "total_cost": round(cost_summary[month], 2),
                "total_shots": shot_summary[month]
            }
            for month in sorted(cost_summary.keys())
        ]
        return result
