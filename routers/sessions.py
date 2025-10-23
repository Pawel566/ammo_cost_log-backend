from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from models import ShootingSession, Ammo, Gun, AccuracySession
from database import get_session
from datetime import date, datetime
from collections import defaultdict
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

try:
    client = OpenAI()
except Exception as e:
    logger.warning(f"Nie można zainicjalizować klienta OpenAI: {e}")
    client = None

router = APIRouter()

class CostSessionInput(BaseModel):
    gun_id: int = Field(description="ID broni")
    ammo_id: int = Field(description="ID amunicji")
    date: Optional[str] = Field(default=None, description="Data w formacie YYYY-MM-DD")
    shots: int = Field(gt=0, description="Liczba strzałów")

class AccuracySessionInput(BaseModel):
    gun_id: int = Field(description="ID broni")
    ammo_id: int = Field(description="ID amunicji")
    date: Optional[str] = Field(default=None, description="Data w formacie YYYY-MM-DD")
    distance_m: int = Field(gt=0, description="Dystans w metrach")
    shots: int = Field(gt=0, description="Liczba strzałów")
    hits: int = Field(ge=0, description="Liczba trafień")

class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int

def _parse_date(date_str: Optional[str]) -> date:
    """Parsuje datę z stringa lub zwraca dzisiejszą datę"""
    if not date_str:
        return date.today()
    
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Data musi być w formacie YYYY-MM-DD (np. 2025-10-23)"
        )

def _validate_ammo_gun_compatibility(ammo: Ammo, gun: Gun) -> bool:
    """Sprawdza czy amunicja pasuje do broni"""
    if not ammo.caliber or not gun.caliber:
        return False
    
    ammo_caliber = ammo.caliber.lower().replace(" ", "").replace(".", "")
    gun_caliber = gun.caliber.lower().replace(" ", "").replace(".", "")
    
    caliber_mappings = {
        "9mm": ["9x19", "9mm", "9mmparabellum", "9mmpara"],
        "9x19": ["9mm", "9x19", "9mmparabellum", "9mmpara"],
        "45acp": ["45acp", "45apc", "45auto", "045", "45APC", "45 APC"],
        "45apc": ["45acp", "45apc", "45auto", "045"],
        "045": ["45acp", "45apc", "45auto", "045"],
        "556": ["556", "556nato", "223", "223rem"],
        "223": ["556", "556nato", "223", "223rem"],
        "762": ["762", "762nato", "762x51", "308", "308win"],
        "308": ["762", "762nato", "762x51", "308", "308win"]
    }
    
    if gun_caliber in ammo_caliber or ammo_caliber in gun_caliber:
        return True
    
    for base_caliber, variants in caliber_mappings.items():
        if gun_caliber in variants and ammo_caliber in variants:
            return True
    
    return False

def _validate_session_data(gun: Gun, ammo: Ammo, shots: int, hits: Optional[int] = None) -> None:
    """Waliduje dane sesji"""
    if not gun:
        raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
    
    if not ammo:
        raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
    
    if not _validate_ammo_gun_compatibility(ammo, gun):
        raise HTTPException(
            status_code=400, 
            detail="Wybrana amunicja nie pasuje do kalibru broni"
        )
    
    if ammo.units_in_package is None or ammo.units_in_package < shots:
        raise HTTPException(
            status_code=400, 
            detail=f"Za mało amunicji. Pozostało tylko {ammo.units_in_package or 0} sztuk."
        )
    
    if hits is not None and (hits < 0 or hits > shots):
        raise HTTPException(
            status_code=400, 
            detail="Liczba trafień musi być między 0 a całkowitą liczbą strzałów"
        )

def _generate_ai_comment(gun: Gun, distance: int, hits: int, shots: int, accuracy: float) -> str:
    """Generuje komentarz AI dla sesji celnościowej"""
    if not client:
        return "Brak klucza API — użyj pliku .env z OPENAI_API_KEY."
    
    try:
        prompt = (
            f"Ocena wyników strzeleckich:\n"
            f"Broń: {gun.name}, kaliber {gun.caliber}\n"
            f"Dystans: {distance} m\n"
            f"Trafienia: {hits} z {shots} strzałów\n"
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
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Błąd podczas generowania komentarza AI: {e}")
        return f"Błąd AI: {e}"

@router.get("/", response_model=Dict[str, List])
def get_all_sessions(session: Session = Depends(get_session)):
    """Pobiera wszystkie sesje"""
    cost_sessions = session.exec(select(ShootingSession)).all()
    accuracy_sessions = session.exec(select(AccuracySession)).all()
    
    return {
        "cost_sessions": cost_sessions,
        "accuracy_sessions": accuracy_sessions
    }

@router.post("/cost", response_model=Dict[str, Any])
def add_cost_session(data: CostSessionInput, session: Session = Depends(get_session)):
    """Dodaje sesję kosztową"""
    parsed_date = _parse_date(data.date)
    
    gun = session.get(Gun, data.gun_id)
    ammo = session.get(Ammo, data.ammo_id)
    
    _validate_session_data(gun, ammo, data.shots)
    
    cost = round(ammo.price_per_unit * data.shots, 2)
    ammo.units_in_package -= data.shots
    
    new_session = ShootingSession(
        gun_id=data.gun_id,
        ammo_id=data.ammo_id,
        date=parsed_date,
        shots=data.shots,
        cost=cost
    )
    
    session.add(new_session)
    session.add(ammo)
    session.commit()
    session.refresh(new_session)
    
    return {
        "session": new_session, 
        "remaining_ammo": ammo.units_in_package
    }

@router.post("/accuracy", response_model=Dict[str, Any])
def add_accuracy_session(data: AccuracySessionInput, session: Session = Depends(get_session)):
    """Dodaje sesję celnościową z komentarzem AI"""
    parsed_date = _parse_date(data.date)
    
    gun = session.get(Gun, data.gun_id)
    ammo = session.get(Ammo, data.ammo_id)
    
    _validate_session_data(gun, ammo, data.shots, data.hits)
    
    cost = round(ammo.price_per_unit * data.shots, 2)
    ammo.units_in_package -= data.shots
    accuracy = round((data.hits / data.shots) * 100, 2)
    
    ai_comment = _generate_ai_comment(gun, data.distance_m, data.hits, data.shots, accuracy)
    
    cost_session = ShootingSession(
        gun_id=data.gun_id,
        ammo_id=data.ammo_id,
        date=parsed_date,
        shots=data.shots,
        cost=cost,
        notes=f"Sesja celnościowa - {data.hits}/{data.shots} trafień ({accuracy}%)"
    )
    
    accuracy_session = AccuracySession(
        gun_id=data.gun_id,
        ammo_id=data.ammo_id,
        date=parsed_date,
        distance_m=data.distance_m,
        hits=data.hits,
        shots=data.shots,
        accuracy_percent=accuracy,
        ai_comment=ai_comment
    )
    
    session.add(cost_session)
    session.add(accuracy_session)
    session.add(ammo)
    session.commit()
    session.refresh(cost_session)
    session.refresh(accuracy_session)
    
    return {
        "accuracy_session": accuracy_session,
        "cost_session": cost_session,
        "remaining_ammo": ammo.units_in_package
    }

@router.get("/summary", response_model=List[MonthlySummary])
def get_monthly_summary(session: Session = Depends(get_session)):
    """Pobiera podsumowanie miesięczne"""
    sessions = session.exec(select(ShootingSession)).all()
    if not sessions:
        return []

    cost_summary = defaultdict(float)
    shot_summary = defaultdict(int)

    for session_data in sessions:
        month_key = session_data.date.strftime("%Y-%m")
        cost_summary[month_key] += float(session_data.cost)
        shot_summary[month_key] += session_data.shots

    return [
        MonthlySummary(
            month=month,
            total_cost=round(cost_summary[month], 2),
            total_shots=shot_summary[month]
        )
        for month in sorted(cost_summary.keys())
    ]
