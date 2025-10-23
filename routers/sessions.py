from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from models import Session as ShootingSession, Ammo, Gun, AccuracySession
from database import engine
from datetime import date, datetime
from collections import defaultdict
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# --- Ładowanie klucza API ---
load_dotenv()
try:
    client = OpenAI()  # automatycznie czyta OPENAI_API_KEY z .env
except Exception:
    client = None

router = APIRouter()

# --- Modele wejściowe (walidacja danych z requesta) ---
class CostSessionInput(BaseModel):
    gun_id: int
    ammo_id: int
    date: Optional[str] = None
    shots: int

class AccuracySessionInput(BaseModel):
    gun_id: int
    ammo_id: int
    date: Optional[str] = None
    distance_m: int
    shots: int
    hits: int

# --- Dopasowanie amunicji do broni ---
def ammo_matches_gun(ammo: Ammo, gun: Gun) -> bool:
    if not ammo.caliber or not gun.caliber:
        return False
    
    a = ammo.caliber.lower().replace(" ", "").replace(".", "")
    g = gun.caliber.lower().replace(" ", "").replace(".", "")
    
    # Specjalne przypadki dla popularnych kalibrów
    caliber_mappings = {
        "9mm": ["9x19", "9mm", "9mmparabellum", "9mmpara"],
        "9x19": ["9mm", "9x19", "9mmparabellum", "9mmpara"],
        "45acp": ["45acp", "45apc", "45auto", "045"],
        "45apc": ["45acp", "45apc", "45auto", "045"],
        "045": ["45acp", "45apc", "45auto", "045"],
        "556": ["556", "556nato", "223", "223rem"],
        "223": ["556", "556nato", "223", "223rem"],
        "762": ["762", "762nato", "762x51", "308", "308win"],
        "308": ["762", "762nato", "762x51", "308", "308win"]
    }
    
    # Sprawdź bezpośrednie dopasowanie
    if g in a or a in g:
        return True
    
    # Sprawdź mapowania kalibrów
    for base_caliber, variants in caliber_mappings.items():
        if g in variants and a in variants:
            return True
    
    return False


# --- GET wszystkich sesji ---
@router.get("/")
def get_all_sessions():
    with Session(engine) as db:
        cost_sessions = db.exec(select(ShootingSession)).all()
        acc_sessions = db.exec(select(AccuracySession)).all()
        return {
            "cost_sessions": cost_sessions,
            "accuracy_sessions": acc_sessions
        }


# --- POST: sesja kosztowa ---
@router.post("/cost")
def add_cost_session(data: CostSessionInput):
    data = data.dict()
    if not data.get("date"):
        data["date"] = date.today()
    elif isinstance(data.get("date"), str):
        try:
            data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Date must be in format YYYY-MM-DD (e.g. 2025-10-23)")

    with Session(engine) as db:
        gun = db.get(Gun, data["gun_id"])
        ammo = db.get(Ammo, data["ammo_id"])

        if not gun:
            raise HTTPException(status_code=404, detail="Gun not found")
        if not ammo:
            raise HTTPException(status_code=404, detail="Ammo not found")
        if not ammo_matches_gun(ammo, gun):
            raise HTTPException(status_code=400, detail="Selected ammo doesn't match gun caliber")
        if ammo.units_in_package is None or ammo.units_in_package < data["shots"]:
            raise HTTPException(status_code=400, detail=f"Not enough ammo. Only {ammo.units_in_package or 0} left.")
        if data["shots"] <= 0:
            raise HTTPException(status_code=400, detail="Shots must be > 0")

        data["cost"] = round(ammo.price_per_unit * data["shots"], 2)
        ammo.units_in_package -= data["shots"]

        new_session = ShootingSession(**data)
        db.add(new_session)
        db.add(ammo)
        db.commit()
        db.refresh(new_session)

        return {"session": new_session, "remaining_ammo": ammo.units_in_package}


# --- POST: sesja celnościowa (z AI) ---
@router.post("/accuracy")
def add_accuracy_session(data: AccuracySessionInput):
    data = data.dict()
    
    if not data.get("date"):
        data["date"] = date.today()
    elif isinstance(data.get("date"), str):
        try:
            data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Date must be in format YYYY-MM-DD (e.g. 2025-10-23)")

    with Session(engine) as db:
        gun = db.get(Gun, data["gun_id"])
        ammo = db.get(Ammo, data["ammo_id"])

        if not gun:
            raise HTTPException(status_code=404, detail="Gun not found")
        if not ammo:
            raise HTTPException(status_code=404, detail="Ammo not found")
        if not ammo_matches_gun(ammo, gun):
            raise HTTPException(status_code=400, detail="Selected ammo doesn't match gun caliber")
        if ammo.units_in_package is None or ammo.units_in_package < data["shots"]:
            raise HTTPException(status_code=400, detail=f"Not enough ammo. Only {ammo.units_in_package or 0} left.")
        if data["shots"] <= 0:
            raise HTTPException(status_code=400, detail="Shots must be > 0")
        if data["hits"] < 0 or data["hits"] > data["shots"]:
            raise HTTPException(status_code=400, detail="Hits must be between 0 and total shots")

        # Oblicz koszt i odlicz amunicję (tylko raz)
        cost = round(ammo.price_per_unit * data["shots"], 2)
        ammo.units_in_package -= data["shots"]

        accuracy = round((data["hits"] / data["shots"]) * 100, 2)

        ai_comment = None
        try:
            if client:
                prompt = (
                    f"Ocena wyników strzeleckich:\n"
                    f"Broń: {gun.name}, kaliber {gun.caliber}\n"
                    f"Dystans: {data['distance_m']} m\n"
                    f"Trafienia: {data['hits']} z {data['shots']} strzałów\n"
                    f"Celność: {accuracy}%\n"
                    f"Napisz krótki komentarz po polsku — maks 2 zdania z oceną i sugestią poprawy."
                )

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Jesteś instruktorem strzelectwa."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=80
                )
                ai_comment = response.choices[0].message.content.strip()
            else:
                ai_comment = "Brak klucza API — użyj pliku .env z OPENAI_API_KEY."
        except Exception as e:
            ai_comment = f"Błąd AI: {e}"

        # Utwórz sesję kosztową
        cost_session = ShootingSession(
            gun_id=data["gun_id"],
            ammo_id=data["ammo_id"],
            date=data["date"],
            shots=data["shots"],
            cost=cost,
            notes=f"Sesja celnościowa - {data['hits']}/{data['shots']} trafień ({accuracy}%)"
        )

        # Utwórz sesję celnościową
        new_session = AccuracySession(
            gun_id=data["gun_id"],
            ammo_id=data["ammo_id"],
            date=data["date"],
            distance_m=data["distance_m"],
            hits=data["hits"],
            shots=data["shots"],
            accuracy_percent=accuracy,
            ai_comment=ai_comment
        )

        db.add(cost_session)
        db.add(new_session)
        db.add(ammo)
        db.commit()
        db.refresh(cost_session)
        db.refresh(new_session)

        return {
            "accuracy_session": new_session, 
            "cost_session": cost_session,
            "remaining_ammo": ammo.units_in_package
        }


# --- GET: podsumowanie miesięczne ---
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

        return [
            {
                "month": month,
                "total_cost": round(cost_summary[month], 2),
                "total_shots": shot_summary[month]
            }
            for month in sorted(cost_summary.keys())
        ]
