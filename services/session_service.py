from sqlmodel import Session, select
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import or_, func, cast, String
from fastapi import HTTPException
from models import ShootingSession, Ammo, Gun, AccuracySession
import asyncio
import logging
from openai import OpenAI
from services.error_handler import ErrorHandler
from services.user_context import UserContext, UserRole

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
        if gun.user_id != ammo.user_id:
            raise HTTPException(status_code=400, detail="Wybrana broń i amunicja należą do różnych użytkowników")
        current_time = datetime.utcnow()
        if gun.expires_at and gun.expires_at <= current_time:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        if ammo.expires_at and ammo.expires_at <= current_time:
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
    def parse_date(date_value: Optional[Union[str, date]]) -> date:
        if not date_value:
            return date.today()
        if isinstance(date_value, date):
            return date_value
        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
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
            return ErrorHandler.handle_openai_error(e, "openai_client_init")
        
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
                    model="gpt-4o-mini",
                    messages=messages
                )
            
            response = await asyncio.to_thread(_create_completion)
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Otrzymano odpowiedź AI: {result}")
            return result
            
        except Exception as e:
            return ErrorHandler.handle_openai_error(e, "generate_ai_comment")


class SessionService:
    @staticmethod
    def _query_for_user(model, user: UserContext):
        query = select(model)
        if user.role == UserRole.admin:
            return query
        query = query.where(model.user_id == user.user_id)
        if user.is_guest and hasattr(model, "expires_at"):
            query = query.where(or_(model.expires_at.is_(None), model.expires_at > datetime.utcnow()))
        return query

    @staticmethod
    def _apply_session_search(query, model, search: Optional[str]):
        if not search:
            return query
        pattern = f"%{search.lower()}%"
        query = query.join(Gun, model.gun_id == Gun.id).join(Ammo, model.ammo_id == Ammo.id)
        conditions = [
            func.lower(Gun.name).like(pattern),
            func.lower(Ammo.name).like(pattern),
            cast(model.date, String).like(pattern)
        ]
        if hasattr(model, "notes"):
            conditions.append(func.lower(func.coalesce(model.notes, "")).like(pattern))
        if hasattr(model, "ai_comment"):
            conditions.append(func.lower(func.coalesce(model.ai_comment, "")).like(pattern))
        return query.where(or_(*conditions))

    @staticmethod
    async def _get_gun(session: Session, gun_id: int, user: UserContext) -> Optional[Gun]:
        query = select(Gun).where(Gun.id == gun_id)
        if user.role != UserRole.admin:
            query = query.where(Gun.user_id == user.user_id)
            if user.is_guest:
                query = query.where(or_(Gun.expires_at.is_(None), Gun.expires_at > datetime.utcnow()))
        return await asyncio.to_thread(lambda: session.exec(query).first())

    @staticmethod
    async def _get_ammo(session: Session, ammo_id: int, user: UserContext) -> Optional[Ammo]:
        query = select(Ammo).where(Ammo.id == ammo_id)
        if user.role != UserRole.admin:
            query = query.where(Ammo.user_id == user.user_id)
            if user.is_guest:
                query = query.where(or_(Ammo.expires_at.is_(None), Ammo.expires_at > datetime.utcnow()))
        return await asyncio.to_thread(lambda: session.exec(query).first())

    @staticmethod
    async def get_all_sessions(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> Dict[str, Dict[str, Any]]:
        cost_base = SessionService._query_for_user(ShootingSession, user)
        cost_query = SessionService._apply_session_search(cost_base, ShootingSession, search)
        cost_count_query = cost_query.with_only_columns(func.count(ShootingSession.id)).order_by(None)

        accuracy_base = SessionService._query_for_user(AccuracySession, user)
        accuracy_query = SessionService._apply_session_search(accuracy_base, AccuracySession, search)
        accuracy_count_query = accuracy_query.with_only_columns(func.count(AccuracySession.id)).order_by(None)

        def _run_cost():
            total = session.exec(cost_count_query).one()[0]
            items = session.exec(cost_query.offset(offset).limit(limit)).all()
            return total, items

        def _run_accuracy():
            total = session.exec(accuracy_count_query).one()[0]
            items = session.exec(accuracy_query.offset(offset).limit(limit)).all()
            return total, items

        cost_total, cost_items = await asyncio.to_thread(_run_cost)
        accuracy_total, accuracy_items = await asyncio.to_thread(_run_accuracy)

        return {
            "cost_sessions": {"total": cost_total, "items": cost_items},
            "accuracy_sessions": {"total": accuracy_total, "items": accuracy_items}
        }

    @staticmethod
    async def create_cost_session(
        session: Session,
        user: UserContext,
        gun_id: int,
        ammo_id: int,
        date_value: Optional[Union[str, date]],
        shots: int
    ) -> Dict[str, Any]:
        parsed_date = SessionCalculationService.parse_date(date_value)
        gun = await SessionService._get_gun(session, gun_id, user)
        ammo = await SessionService._get_ammo(session, ammo_id, user)
        SessionValidationService.validate_session_data(gun, ammo, shots)
        cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, shots)
        ammo.units_in_package -= shots
        target_expiration = user.expires_at if user.is_guest else gun.expires_at
        if user.is_guest:
            ammo.expires_at = target_expiration
            gun.expires_at = target_expiration
        elif user.role != UserRole.admin:
            ammo.expires_at = None
            gun.expires_at = None
        new_session = ShootingSession(
            gun_id=gun_id,
            ammo_id=ammo_id,
            date=parsed_date,
            shots=shots,
            cost=cost,
            user_id=gun.user_id,
            expires_at=target_expiration
        )
        session.add(new_session)
        session.add(ammo)
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, new_session)
        return {
            "session": new_session,
            "remaining_ammo": ammo.units_in_package
        }

    @staticmethod
    async def create_accuracy_session(
        session: Session,
        user: UserContext,
        gun_id: int,
        ammo_id: int,
        date_value: Optional[Union[str, date]],
        distance_m: int,
        shots: int,
        hits: int,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        parsed_date = SessionCalculationService.parse_date(date_value)
        gun = await SessionService._get_gun(session, gun_id, user)
        ammo = await SessionService._get_ammo(session, ammo_id, user)
        SessionValidationService.validate_session_data(gun, ammo, shots, hits)
        cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, shots)
        ammo.units_in_package -= shots
        accuracy = SessionCalculationService.calculate_accuracy(hits, shots)
        ai_comment = await AIService.generate_comment(gun, distance_m, hits, shots, accuracy, api_key)
        target_expiration = user.expires_at if user.is_guest else gun.expires_at
        if user.is_guest:
            ammo.expires_at = target_expiration
            gun.expires_at = target_expiration
        elif user.role != UserRole.admin:
            ammo.expires_at = None
            gun.expires_at = None
        cost_session = ShootingSession(
            gun_id=gun_id,
            ammo_id=ammo_id,
            date=parsed_date,
            shots=shots,
            cost=cost,
            user_id=gun.user_id,
            expires_at=target_expiration,
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
            ai_comment=ai_comment,
            user_id=gun.user_id,
            expires_at=target_expiration
        )
        session.add(cost_session)
        session.add(accuracy_session)
        session.add(ammo)
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, cost_session)
        await asyncio.to_thread(session.refresh, accuracy_session)
        return {
            "accuracy_session": accuracy_session,
            "cost_session": cost_session,
            "remaining_ammo": ammo.units_in_package
        }

    @staticmethod
    async def get_monthly_summary(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> Dict[str, Any]:
        query = SessionService._query_for_user(ShootingSession, user)

        def _fetch_sessions():
            return session.exec(query).all()

        sessions = await asyncio.to_thread(_fetch_sessions)
        if not sessions:
            return {"total": 0, "items": []}

        cost_summary = defaultdict(float)
        shot_summary = defaultdict(int)

        for session_data in sessions:
            month_key = session_data.date.strftime("%Y-%m")
            cost_summary[month_key] += float(session_data.cost)
            shot_summary[month_key] += session_data.shots

        summary = [
            {
                "month": month,
                "total_cost": round(cost_summary[month], 2),
                "total_shots": shot_summary[month]
            }
            for month in sorted(cost_summary.keys())
        ]

        if search:
            lowered = search.lower()
            summary = [item for item in summary if lowered in item["month"].lower()]

        total = len(summary)
        items = summary[offset:offset + limit]
        return {"total": total, "items": items}




