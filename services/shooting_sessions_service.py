from sqlmodel import Session, select
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import or_, func, cast, String, not_
from fastapi import HTTPException
from models import ShootingSession, Ammo, Gun
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
    def calculate_cost(price_per_unit: float, shots: int, fixed_cost: float = 0.0) -> float:
        return round(fixed_cost + (price_per_unit * shots), 2)

    @staticmethod
    def calculate_accuracy(hits: int, shots: int) -> float:
        return round((hits / shots) * 100, 2)

    @staticmethod
    def calculate_final_score(group_cm: Optional[float], distance_m: Optional[float], hits: Optional[int], shots: int) -> Optional[float]:
        if not hits or not shots or shots <= 0:
            return None
        
        accuracy = hits / shots
        
        if group_cm and distance_m and distance_m > 0:
            moa = (group_cm / distance_m) * 34.38
            effective_moa = moa * distance_m / 100
            precision = max(0, 1 - (effective_moa / 10))
            final = (accuracy * 0.4) + (precision * 0.6)
            return round(final * 100, 2)
        
        return round(accuracy * 100, 2)

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


class ShootingSessionsService:
    @staticmethod
    def _query_for_user(model, user: UserContext):
        query = select(model)
        if user.role == UserRole.admin:
            return query
        query = query.where(model.user_id == user.user_id)
        return query

    @staticmethod
    def _apply_session_search(query, model, search: Optional[str]):
        if not search:
            return query
        try:
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
        except Exception as e:
            logger.error(f"Błąd podczas aplikowania search: {e}", exc_info=True)
            # Fallback: zwróć query bez search
            return query

    @staticmethod
    def _get_gun(session: Session, gun_id: str, user: UserContext) -> Optional[Gun]:
        query = select(Gun).where(Gun.id == gun_id)
        if user.role != UserRole.admin:
            query = query.where(Gun.user_id == user.user_id)
        return session.exec(query).first()

    @staticmethod
    def _get_ammo(session: Session, ammo_id: str, user: UserContext) -> Optional[Ammo]:
        query = select(Ammo).where(Ammo.id == ammo_id)
        if user.role != UserRole.admin:
            query = query.where(Ammo.user_id == user.user_id)
        return session.exec(query).first()

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
        base_query = ShootingSessionsService._query_for_user(ShootingSession, user)
        
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
        
        query = ShootingSessionsService._apply_session_search(base_query, ShootingSession, search)
        
        # Dla SQLite, gdy mamy join (search), liczymy przez wykonanie query
        if search:
            # Gdy jest search, query ma join - wykonaj query i policz w Pythonie
            try:
                all_items = session.exec(query).all()
                total = len(all_items)
                items = sorted(all_items, key=lambda x: x.date, reverse=True)[offset:offset + limit]
            except Exception as e:
                logger.error(f"Błąd podczas wykonywania zapytania z search: {e}", exc_info=True)
                return {"total": 0, "items": []}
        else:
            # Gdy nie ma search, użyj prostego count (dla kompatybilności z SQLite)
            count_query = select(func.count(ShootingSession.id))
            if user.role != UserRole.admin:
                count_query = count_query.where(ShootingSession.user_id == user.user_id)
            if gun_id:
                count_query = count_query.where(ShootingSession.gun_id == gun_id)
            if date_from:
                try:
                    date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
                    count_query = count_query.where(ShootingSession.date >= date_from_parsed)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
                    count_query = count_query.where(ShootingSession.date <= date_to_parsed)
                except ValueError:
                    pass
            try:
                total = session.exec(count_query).one()
            except Exception as e:
                logger.error(f"Błąd podczas liczenia sesji: {e}", exc_info=True)
                total = 0
            
            items = session.exec(
                query.order_by(ShootingSession.date.desc())
                     .offset(offset)
                     .limit(limit)
            ).all()

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
        parsed_date = SessionCalculationService.parse_date(data.date)
        gun = ShootingSessionsService._get_gun(session, data.gun_id, user)
        ammo = ShootingSessionsService._get_ammo(session, data.ammo_id, user)
        
        hits = data.hits if data.hits is not None else None
        SessionValidationService.validate_session_data(gun, ammo, data.shots, hits)
        
        cost = data.cost
        if cost is None:
            cost = SessionCalculationService.calculate_cost(ammo.price_per_unit, data.shots)
        
        accuracy_percent = None
        if hits is not None and data.shots > 0:
            accuracy_percent = SessionCalculationService.calculate_accuracy(hits, data.shots)
        
        group_cm = data.group_cm if hasattr(data, 'group_cm') and data.group_cm is not None else None
        final_score = SessionCalculationService.calculate_final_score(
            group_cm, 
            data.distance_m if data.distance_m is not None else None,
            hits,
            data.shots
        )
        
        ammo.units_in_package -= data.shots
        
        new_session = ShootingSession(
            gun_id=data.gun_id,
            ammo_id=data.ammo_id,
            date=parsed_date,
            shots=data.shots,
            cost=cost,
            notes=data.notes,
            distance_m=data.distance_m if data.distance_m is not None else None,
            hits=data.hits if data.hits is not None else None,
            group_cm=group_cm,
            accuracy_percent=accuracy_percent,
            final_score=final_score,
            ai_comment=None,
            session_type=data.session_type if hasattr(data, 'session_type') and data.session_type else 'standard',
            user_id=gun.user_id
        )
        
        session.add(new_session)
        session.add(ammo)
        session.add(gun)
        session.commit()
        session.refresh(new_session)
        MaintenanceService.update_last_maintenance_rounds(session, user, data.gun_id)
        
        return {
            "session": new_session,
            "remaining_ammo": ammo.units_in_package
        }

    @staticmethod
    async def get_monthly_summary(
        session: Session,
        user: UserContext,
        limit: int,
        offset: int,
        search: Optional[str]
    ) -> Dict[str, Any]:
        query = ShootingSessionsService._query_for_user(ShootingSession, user)

        sessions = session.exec(query).all()
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

    @staticmethod
    async def update_shooting_session(
        session: Session,
        session_id: str,
        user: UserContext,
        data: Any
    ) -> Dict[str, Any]:
        ss = session.get(ShootingSession, session_id)
        if not ss:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if user.role != UserRole.admin:
            if ss.user_id != user.user_id:
                raise HTTPException(status_code=404, detail="Session not found")

        update_dict = data.model_dump(exclude_unset=True)
        
        if not update_dict:
            return {"session": ss, "remaining_ammo": None}

        old_shots = ss.shots
        old_ammo_id = ss.ammo_id
        old_gun_id = ss.gun_id

        if "date" in update_dict:
            if isinstance(update_dict["date"], str):
                update_dict["date"] = SessionCalculationService.parse_date(update_dict["date"])
            elif update_dict["date"] is None:
                del update_dict["date"]

        if "gun_id" in update_dict:
            if update_dict["gun_id"] == "" or update_dict["gun_id"] is None:
                del update_dict["gun_id"]
        
        if "ammo_id" in update_dict:
            if update_dict["ammo_id"] == "" or update_dict["ammo_id"] is None:
                del update_dict["ammo_id"]

        if "notes" in update_dict:
            if update_dict["notes"] == "":
                update_dict["notes"] = None
            elif update_dict["notes"] is None:
                del update_dict["notes"]

        new_gun_id = update_dict.get("gun_id", old_gun_id)
        new_ammo_id = update_dict.get("ammo_id", old_ammo_id)
        new_shots = update_dict.get("shots", old_shots)
        new_hits = update_dict.get("hits", ss.hits)

        if "gun_id" in update_dict or "ammo_id" in update_dict or "shots" in update_dict or "hits" in update_dict:
            gun = ShootingSessionsService._get_gun(session, new_gun_id, user)
            ammo = ShootingSessionsService._get_ammo(session, new_ammo_id, user)
            
            if not gun:
                raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
            if not ammo:
                raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
            if gun.user_id != ammo.user_id:
                raise HTTPException(status_code=400, detail="Wybrana broń i amunicja należą do różnych użytkowników")
            
            if new_hits is not None and (new_hits < 0 or new_hits > new_shots):
                raise HTTPException(
                    status_code=400,
                    detail="Liczba trafień musi być między 0 a całkowitą liczbą strzałów"
                )

            shots_diff = new_shots - old_shots
            ammo_changed = old_ammo_id != new_ammo_id
            old_ammo = None

            if shots_diff > 0 or ammo_changed:
                if not SessionValidationService.validate_ammo_gun_compatibility(ammo, gun):
                    raise HTTPException(
                        status_code=400,
                        detail="Wybrana amunicja nie pasuje do kalibru broni"
                    )
                
                if ammo_changed:
                    old_ammo = ShootingSessionsService._get_ammo(session, old_ammo_id, user)
                    if old_ammo and old_ammo.units_in_package is not None:
                        old_ammo.units_in_package += old_shots
                        session.add(old_ammo)
                
                if ammo.units_in_package is None or ammo.units_in_package < new_shots:
                    if old_ammo and old_ammo.units_in_package is not None:
                        old_ammo.units_in_package -= old_shots
                        session.add(old_ammo)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Za mało amunicji. Pozostało tylko {ammo.units_in_package or 0} sztuk."
                    )
                
                if ammo.units_in_package is not None:
                    if ammo_changed:
                        ammo.units_in_package -= new_shots
                    else:
                        ammo.units_in_package -= shots_diff
                    session.add(ammo)

            if shots_diff < 0:
                if ammo.units_in_package is not None:
                    ammo.units_in_package += abs(shots_diff)
                    session.add(ammo)

        if "distance_m" in update_dict:
            if update_dict["distance_m"] is None:
                del update_dict["distance_m"]

        if "hits" in update_dict:
            if update_dict["hits"] is None:
                del update_dict["hits"]

        if "group_cm" in update_dict:
            if update_dict["group_cm"] is None:
                del update_dict["group_cm"]

        if "shots" in update_dict:
            if update_dict["shots"] is None:
                del update_dict["shots"]

        if "cost" in update_dict:
            if update_dict["cost"] is None:
                del update_dict["cost"]

        final_distance_m = update_dict.get("distance_m", ss.distance_m)
        final_hits = update_dict.get("hits", ss.hits)
        final_shots = update_dict.get("shots", ss.shots)
        final_group_cm = update_dict.get("group_cm", ss.group_cm if hasattr(ss, 'group_cm') else None)

        if final_distance_m is not None and final_hits is not None and final_shots and final_shots > 0:
            update_dict["accuracy_percent"] = SessionCalculationService.calculate_accuracy(final_hits, final_shots)
            update_dict["final_score"] = SessionCalculationService.calculate_final_score(
                final_group_cm,
                final_distance_m,
                final_hits,
                final_shots
            )
        elif "distance_m" in update_dict or "hits" in update_dict or "group_cm" in update_dict:
            if final_distance_m is None or final_hits is None:
                update_dict["accuracy_percent"] = None
                update_dict["final_score"] = None

        if "cost" not in update_dict and ("shots" in update_dict or "ammo_id" in update_dict):
            if "ammo_id" in update_dict:
                ammo = ShootingSessionsService._get_ammo(session, update_dict["ammo_id"], user)
            else:
                ammo = ShootingSessionsService._get_ammo(session, new_ammo_id, user)
            if ammo:
                final_shots = update_dict.get("shots", ss.shots)
                old_cost = ss.cost if ss.cost else 0.0
                old_ammo_cost = 0.0
                if ss.ammo_id and ss.shots:
                    old_ammo = ShootingSessionsService._get_ammo(session, ss.ammo_id, user)
                    if old_ammo:
                        old_ammo_cost = old_ammo.price_per_unit * ss.shots
                fixed_cost = max(0.0, old_cost - old_ammo_cost)
                new_ammo_cost = ammo.price_per_unit * final_shots
                update_dict["cost"] = round(fixed_cost + new_ammo_cost, 2)

        for key, value in update_dict.items():
            setattr(ss, key, value)

        session.add(ss)
        session.commit()
        session.refresh(ss)

        remaining_ammo = None
        if new_ammo_id != old_ammo_id or new_shots != old_shots:
            final_ammo = ShootingSessionsService._get_ammo(session, new_ammo_id, user)
            if final_ammo:
                remaining_ammo = final_ammo.units_in_package

        return {
            "session": ss,
            "remaining_ammo": remaining_ammo
        }

    @staticmethod
    async def delete_shooting_session(session: Session, session_id: str, user: UserContext) -> Dict[str, str]:
        ss = session.get(ShootingSession, session_id)
        if not ss:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if user.role != UserRole.admin:
            if ss.user_id != user.user_id:
                raise HTTPException(status_code=404, detail="Session not found")

        # Usuń zdjęcie tarczy z Supabase jeśli istnieje
        if ss.target_image_path:
            try:
                from services.supabase_service import delete_target_image
                import asyncio
                await asyncio.to_thread(delete_target_image, ss.target_image_path)
            except Exception as e:
                # Nie blokuj usuwania sesji, jeśli usunięcie zdjęcia się nie powiodło
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Nie udało się usunąć zdjęcia tarczy z Supabase: {str(e)}")

        session.delete(ss)
        session.commit()

        return {"message": "Session deleted"}

