from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from collections import defaultdict
from fastapi import HTTPException
from models import ShootingSession, Ammo, Gun, AccuracySession
import asyncio
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class SessionValidationService:
    @staticmethod
    def validate_ammo_gun_compatibility(ammo: Ammo, gun: Gun) -> bool:
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

    @staticmethod
    def validate_session_data(gun: Gun, ammo: Ammo, shots: int, hits: Optional[int] = None) -> None:
        if not gun:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
        
        if not SessionValidationService.validate_ammo_gun_compatibility(ammo, gun):
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


class SessionCalculationService:
    @staticmethod
    def calculate_cost(price_per_unit: float, shots: int) -> float:
        return round(price_per_unit * shots, 2)

    @staticmethod
    def calculate_accuracy(hits: int, shots: int) -> float:
        return round((hits / shots) * 100, 2)

    @staticmethod
    def parse_date(date_str: Optional[str]) -> date:
        if not date_str:
            return date.today()
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Data musi być w formacie YYYY-MM-DD (np. 2025-10-23)"
            )


class AIService:
    @staticmethod
    async def generate_comment(gun: Gun, distance: int, hits: int, shots: int, accuracy: float, api_key: Optional[str] = None) -> str:
        logger.info(f"Generowanie komentarza AI dla {gun.name}, celność: {accuracy}%")
        
        if not api_key:
            logger.warning("Brak klucza API OpenAI od użytkownika")
            return "Brak klucza API OpenAI — dodaj klucz w formularzu aby otrzymać komentarz AI."
        
        try:
            client_with_key = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Błąd inicjalizacji klienta OpenAI z podanym kluczem: {e}")
            return f"Nieprawidłowy klucz API OpenAI: {e}"
        
        try:
            prompt = (
                f"Ocena wyników strzeleckich:\n"
                f"Broń: {gun.name}, kaliber {gun.caliber}\n"
                f"Dystans: {distance} m\n"
                f"Trafienia: {hits} z {shots} strzałów\n"
                f"Celność: {accuracy}%\n"
                f"Napisz krótki komentarz po polsku — maks 2 zdania z oceną i sugestią poprawy."
            )

            messages = [
                {"role": "system", "content": "Jesteś instruktorem strzelectwa."},
                {"role": "user", "content": prompt}
            ]

            logger.info(f"Wysyłanie zapytania do OpenAI: {prompt[:100]}...")
            
            def _create_completion():
                return client_with_key.chat.completions.create(
                    model="gpt-5-mini",
                    messages=messages
                )
            
            response = await asyncio.to_thread(_create_completion)
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Otrzymano odpowiedź AI: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania komentarza AI: {e}")
            return f"Błąd AI: {e}"


class SessionService:
    @staticmethod
    async def get_all_sessions(session: Session) -> Dict[str, List]:
        cost_sessions = await asyncio.to_thread(lambda: session.exec(select(ShootingSession)).all())
        accuracy_sessions = await asyncio.to_thread(lambda: session.exec(select(AccuracySession)).all())
        
        return {
            "cost_sessions": cost_sessions,
            "accuracy_sessions": accuracy_sessions
        }

    @staticmethod
    async def create_cost_session(
        session: Session, 
        gun_id: int, 
        ammo_id: int, 
        date_str: Optional[str],
        shots: int
    ) -> Dict[str, Any]:
        parsed_date = SessionCalculationService.parse_date(date_str)
        
        gun = await asyncio.to_thread(session.get, Gun, gun_id)
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        
        SessionValidationService.validate_session_data(gun, ammo, shots)
        
        cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, shots)
        ammo.units_in_package -= shots
        
        new_session = ShootingSession(
            gun_id=gun_id,
            ammo_id=ammo_id,
            date=parsed_date,
            shots=shots,
            cost=cost
        )
        
        session.add(new_session)
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, new_session)
        
        return {
            "session": new_session, 
            "remaining_ammo": ammo.units_in_package
        }

    @staticmethod
    async def create_accuracy_session(
        session: Session,
        gun_id: int,
        ammo_id: int,
        date_str: Optional[str],
        distance_m: int,
        shots: int,
        hits: int,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        parsed_date = SessionCalculationService.parse_date(date_str)
        
        gun = await asyncio.to_thread(session.get, Gun, gun_id)
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        
        SessionValidationService.validate_session_data(gun, ammo, shots, hits)
        
        cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, shots)
        ammo.units_in_package -= shots
        accuracy = SessionCalculationService.calculate_accuracy(hits, shots)
        
        ai_comment = await AIService.generate_comment(gun, distance_m, hits, shots, accuracy, api_key)
        
        cost_session = ShootingSession(
            gun_id=gun_id,
            ammo_id=ammo_id,
            date=parsed_date,
            shots=shots,
            cost=cost,
            notes=f"Sesja celnościowa - {hits}/{shots} trafień ({accuracy}%)"
        )
        
        accuracy_session = AccuracySession(
            gun_id=gun_id,
            ammo_id=ammo_id,
            date=parsed_date,
            distance_m=distance_m,
            hits=hits,
            shots=shots,
            accuracy_percent=accuracy,
            ai_comment=ai_comment
        )
        
        session.add(cost_session)
        session.add(accuracy_session)
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, cost_session)
        await asyncio.to_thread(session.refresh, accuracy_session)
        
        return {
            "accuracy_session": accuracy_session,
            "cost_session": cost_session,
            "remaining_ammo": ammo.units_in_package
        }

    @staticmethod
    async def get_monthly_summary(session: Session) -> List[Dict[str, Any]]:
        sessions = await asyncio.to_thread(lambda: session.exec(select(ShootingSession)).all())
        if not sessions:
            return []

        cost_summary = defaultdict(float)
        shot_summary = defaultdict(int)

        for session_data in sessions:
            month_key = session_data.date.strftime("%Y-%m")
            cost_summary[month_key] += float(session_data.cost)
            shot_summary[month_key] += session_data.shots

        return [
            {
                "month": month,
                "total_cost": round(cost_summary[month], 2),
                "total_shots": shot_summary[month]
            }
            for month in sorted(cost_summary.keys())
        ]

