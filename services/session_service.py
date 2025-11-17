from sqlmodel import Session, select
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import or_, func, cast, String, not_
from fastapi import HTTPException
from models import ShootingSession, Ammo, Gun
import asyncio
import logging
from services.user_context import UserContext, UserRole
from services.maintenance_service import MaintenanceService

logger = logging.getLogger(__name__)


class SessionValidationService:
    @staticmethod
    def validate_ammo_gun_compatibility(ammo: Ammo, gun: Gun) -> bool:
        if not ammo.caliber or not gun.caliber:
            return True
        
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
    async def _get_gun(session: Session, gun_id: str, user: UserContext) -> Optional[Gun]:
        query = select(Gun).where(Gun.id == gun_id)
        if user.role != UserRole.admin:
            query = query.where(Gun.user_id == user.user_id)
            if user.is_guest:
                query = query.where(or_(Gun.expires_at.is_(None), Gun.expires_at > datetime.utcnow()))
        return await asyncio.to_thread(lambda: session.exec(query).first())

    @staticmethod
    async def _get_ammo(session: Session, ammo_id: str, user: UserContext) -> Optional[Ammo]:
        query = select(Ammo).where(Ammo.id == ammo_id)
        if user.role != UserRole.admin:
            query = query.where(Ammo.user_id == user.user_id)
            if user.is_guest:
                query = query.where(or_(Ammo.expires_at.is_(None), Ammo.expires_at > datetime.utcnow()))
        return await asyncio.to_thread(lambda: session.exec(query).first())

    @staticmethod
    async def get_all_sessions(
        session: Session, 
        user: UserContext, 
        limit: int, 
        offset: int, 
        search: Optional[str],
        gun_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        base_query = SessionService._query_for_user(ShootingSession, user)
        
        if gun_id:
            base_query = base_query.where(ShootingSession.gun_id == gun_id)
        
        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
                base_query = base_query.where(ShootingSession.date >= date_from_parsed)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
                base_query = base_query.where(ShootingSession.date <= date_to_parsed)
            except ValueError:
                pass
        
        query = SessionService._apply_session_search(base_query, ShootingSession, search)
        count_query = query.with_only_columns(func.count(ShootingSession.id)).order_by(None)

        def _run():
            total = session.exec(count_query).one()
            items = session.exec(query.order_by(ShootingSession.date.desc()).offset(offset).limit(limit)).all()
            return total, items

        total, items = await asyncio.to_thread(_run)

        return {
            "total": total,
            "items": items
        }

    @staticmethod
    async def create_shooting_session(
        session: Session,
        user: UserContext,
        data: Any
    ) -> Dict[str, Any]:
        """
        Tworzy jedną sesję strzelecką z opcjonalnymi polami kosztu i celności.
        
        - Waliduje zgodność broni i amunicji
        - Oblicza koszt na podstawie price_per_unit i shots
        - Jeśli distance_m i hits są podane, oblicza celność i zapisuje ją w tej samej sesji
        - W przeciwnym razie zostawia pola celności puste
        - Aktualizuje magazyn amunicji
        - Zwraca strukturę z informacją o sesji i pozostałej liczbie sztuk
        """
        parsed_date = SessionCalculationService.parse_date(data.date)
        gun = await SessionService._get_gun(session, data.gun_id, user)
        ammo = await SessionService._get_ammo(session, data.ammo_id, user)
        
        # Walidacja zgodności broni i amunicji
        hits = data.hits if data.hits is not None else None
        SessionValidationService.validate_session_data(gun, ammo, data.shots, hits)
        
        # Obliczanie kosztu na podstawie price_per_unit i shots
        cost = data.cost
        if cost is None:
            cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, data.shots)
        
        # Obliczanie celności tylko jeśli distance_m i hits są podane
        accuracy_percent = None
        if data.distance_m is not None and hits is not None and data.shots > 0:
            accuracy_percent = SessionCalculationService.calculate_accuracy(hits, data.shots)
        
        # Aktualizacja magazynu amunicji
        ammo.units_in_package -= data.shots
        target_expiration = user.expires_at if user.is_guest else gun.expires_at
        
        if user.is_guest:
            ammo.expires_at = target_expiration
            gun.expires_at = target_expiration
        elif user.role != UserRole.admin:
            ammo.expires_at = None
            gun.expires_at = None
        
        # Tworzenie sesji z opcjonalnymi polami celności
        new_session = ShootingSession(
            gun_id=data.gun_id,
            ammo_id=data.ammo_id,
            date=parsed_date,
            shots=data.shots,
            cost=cost,
            notes=data.notes,
            distance_m=data.distance_m if data.distance_m is not None else None,
            hits=data.hits if data.hits is not None else None,
            accuracy_percent=accuracy_percent,
            ai_comment=None,
            user_id=gun.user_id,
            expires_at=target_expiration
        )
        
        session.add(new_session)
        session.add(ammo)
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, new_session)
        await MaintenanceService.update_last_maintenance_rounds(session, user, data.gun_id)
        
        # Zwracanie struktury z informacją o sesji i pozostałej liczbie sztuk
        return {
            "session": new_session,
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
            if session_data.cost:
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




