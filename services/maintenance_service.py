from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import or_, func, desc
from models import Maintenance, Gun, ShootingSession
from services.user_context import UserContext, UserRole
from services.gun_service import GunService
from services.exceptions import NotFoundError, BadRequestError
import logging

logger = logging.getLogger(__name__)


class MaintenanceService:
    @staticmethod
    def _query_for_user(user: UserContext, gun_id: Optional[str] = None):
        query = select(Maintenance)
        if gun_id:
            query = query.where(Maintenance.gun_id == gun_id)
        if user.role == UserRole.admin:
            return query
        query = query.where(Maintenance.user_id == user.user_id)
        return query

    @staticmethod
    def _calculate_rounds_since_last(session: Session, user: UserContext, gun_id: str, last_maintenance_date: date, until_date: Optional[date] = None) -> int:
        try:
            query_sessions = select(ShootingSession).where(
                ShootingSession.gun_id == gun_id,
                ShootingSession.user_id == user.user_id,
                ShootingSession.date > last_maintenance_date
            )
            if until_date:
                query_sessions = query_sessions.where(ShootingSession.date <= until_date)
            sessions = session.exec(query_sessions).all()
            rounds = sum(session_item.shots for session_item in sessions)
            return rounds
        except Exception as e:
            logger.warning(f"Błąd podczas obliczania rounds_since_last dla {gun_id}: {e}")
            return 0

    @staticmethod
    def list_all(session: Session, user: UserContext, gun_id: Optional[str] = None) -> List[Maintenance]:
        try:
            query = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date))
            maintenance_list = session.exec(query).all()
            
            result = []
            processed_guns = set()
            
            for maint in maintenance_list:
                try:
                    maint_dict = {
                        "id": maint.id,
                        "gun_id": maint.gun_id,
                        "user_id": maint.user_id,
                        "date": maint.date,
                        "notes": maint.notes,
                        "rounds_since_last": maint.rounds_since_last,
                        "activities": maint.activities
                    }
                    
                    gun_query = select(Gun).where(Gun.id == maint.gun_id)
                    if user.role != UserRole.admin:
                        gun_query = gun_query.where(Gun.user_id == user.user_id)
                    gun = session.exec(gun_query).first()
                    if gun:
                        maint_dict["gun_name"] = gun.name
                    
                    if maint.gun_id not in processed_guns:
                        try:
                            query_last = MaintenanceService._query_for_user(user, maint.gun_id).order_by(desc(Maintenance.date)).limit(1)
                            last_maintenance = session.exec(query_last).first()
                            if last_maintenance and last_maintenance.id == maint.id:
                                rounds_since_last = MaintenanceService._calculate_rounds_since_last(
                                    session, user, maint.gun_id, maint.date, None
                                )
                                maint_dict["rounds_since_last"] = rounds_since_last
                                maint.rounds_since_last = rounds_since_last
                                session.add(maint)
                                session.commit()
                        except Exception as e:
                            logger.warning(f"Błąd podczas obliczania rounds_since_last dla {maint.gun_id}: {e}")
                        processed_guns.add(maint.gun_id)
                    
                    result.append(maint_dict)
                except Exception as e:
                    logger.error(f"Błąd podczas przetwarzania konserwacji {maint.id}: {e}", exc_info=True)
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy konserwacji: {e}", exc_info=True)
            return []

    @staticmethod
    def list_for_gun(session: Session, user: UserContext, gun_id: str) -> List[Maintenance]:
        GunService._get_single_gun(session, gun_id, user)
        query = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date))
        maintenance_list = session.exec(query).all()
        
        if maintenance_list:
            last_maintenance = maintenance_list[0]
            rounds_since_last = MaintenanceService._calculate_rounds_since_last(
                session, user, gun_id, last_maintenance.date, None
            )
            if last_maintenance.rounds_since_last != rounds_since_last:
                last_maintenance.rounds_since_last = rounds_since_last
                session.add(last_maintenance)
                session.commit()
        
        return list(maintenance_list)

    @staticmethod
    def create_maintenance(session: Session, user: UserContext, gun_id: str, data: dict) -> Maintenance:
        GunService._get_single_gun(session, gun_id, user)
        maintenance_date = data.get("date")
        if isinstance(maintenance_date, str):
            maintenance_date = datetime.strptime(maintenance_date, "%Y-%m-%d").date()
        
        # Walidacja: data konserwacji nie może być w przyszłości
        if maintenance_date > date.today():
            raise BadRequestError("Data konserwacji nie może być w przyszłości")
        
        rounds_since_last = data.get("rounds_since_last", 0)
        if rounds_since_last == 0:
            query_last = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date)).limit(1)
            last_maintenance = session.exec(query_last).first()
            if last_maintenance:
                rounds_since_last = MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, last_maintenance.date, maintenance_date
                )
            else:
                rounds_since_last = MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, date(1900, 1, 1), maintenance_date
                )
        
        maintenance = Maintenance(
            gun_id=gun_id,
            user_id=user.user_id,
            date=maintenance_date,
            notes=data.get("notes"),
            rounds_since_last=rounds_since_last,
            activities=data.get("activities")
        )
        session.add(maintenance)
        session.commit()
        session.refresh(maintenance)
        return maintenance

    @staticmethod
    def _get_single_maintenance(session: Session, maintenance_id: str, user: UserContext) -> Maintenance:
        query = select(Maintenance).where(Maintenance.id == maintenance_id)
        if user.role != UserRole.admin:
            query = query.where(Maintenance.user_id == user.user_id)
        maintenance = session.exec(query).first()
        if not maintenance:
            raise NotFoundError("Konserwacja nie została znaleziona")
        return maintenance

    @staticmethod
    def update_maintenance(session: Session, user: UserContext, maintenance_id: str, data: dict) -> Maintenance:
        maintenance = MaintenanceService._get_single_maintenance(session, maintenance_id, user)
        if "date" in data and data["date"] is not None:
            new_date = data["date"]
            if isinstance(new_date, str):
                new_date = datetime.strptime(new_date, "%Y-%m-%d").date()
            elif isinstance(new_date, date):
                pass
            else:
                new_date = None
            
            if new_date and new_date > date.today():
                raise BadRequestError("Data konserwacji nie może być w przyszłości")
            
            if new_date:
                maintenance.date = new_date
        if "notes" in data:
            maintenance.notes = data.get("notes")
        if "activities" in data:
            maintenance.activities = data.get("activities")
        if "rounds_since_last" in data and data["rounds_since_last"] is not None:
            maintenance.rounds_since_last = data["rounds_since_last"]
        session.add(maintenance)
        session.commit()
        session.refresh(maintenance)
        return maintenance

    @staticmethod
    def delete_maintenance(session: Session, user: UserContext, maintenance_id: str) -> dict:
        maintenance = MaintenanceService._get_single_maintenance(session, maintenance_id, user)
        session.delete(maintenance)
        session.commit()
        return {"message": f"Konserwacja o ID {maintenance_id} została usunięta"}

    @staticmethod
    def update_last_maintenance_rounds(session: Session, user: UserContext, gun_id: str) -> None:
        query_last = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date)).limit(1)
        last_maintenance = session.exec(query_last).first()
        if last_maintenance:
            rounds_since_last = MaintenanceService._calculate_rounds_since_last(
                session, user, gun_id, last_maintenance.date, None
            )
            last_maintenance.rounds_since_last = rounds_since_last
            session.add(last_maintenance)
            session.commit()

    @staticmethod
    def get_statistics(session: Session, user: UserContext) -> Dict[str, Any]:
        try:
            query_guns = select(Gun)
            if user.role != UserRole.admin:
                query_guns = query_guns.where(Gun.user_id == user.user_id)
            guns = session.exec(query_guns).all()
            
            today = date.today()
            gun_stats = []
            longest_without = None
            max_days = 0
            
            for gun in guns:
                try:
                    query_last = MaintenanceService._query_for_user(user, gun.id).order_by(desc(Maintenance.date)).limit(1)
                    last_maintenance = session.exec(query_last).first()
                    
                    if last_maintenance:
                        days_since = (today - last_maintenance.date).days
                    else:
                        query_first_session = select(ShootingSession).where(
                            ShootingSession.gun_id == gun.id,
                            ShootingSession.user_id == user.user_id
                        ).order_by(ShootingSession.date).limit(1)
                        first_session = session.exec(query_first_session).first()
                        
                        if first_session:
                            days_since = (today - first_session.date).days
                        else:
                            # Użyj daty utworzenia broni jako fallback
                            if gun.created_at:
                                days_since = (today - gun.created_at).days
                            else:
                                days_since = 0
                    
                    gun_stats.append({
                        "gun_id": gun.id,
                        "gun_name": gun.name,
                        "days_since_last": days_since
                    })
                    
                    if days_since is not None and days_since > max_days:
                        max_days = days_since
                        longest_without = {
                            "gun_id": gun.id,
                            "gun_name": gun.name,
                            "days_since": days_since
                        }
                except Exception as e:
                    logger.warning(f"Błąd podczas przetwarzania statystyk dla broni {gun.id}: {e}")
                    continue
            
            return {
                "longest_without_maintenance": longest_without,
                "guns_status": gun_stats
            }
        except Exception as e:
            logger.error(f"Błąd podczas pobierania statystyk konserwacji: {e}", exc_info=True)
            return {
                "longest_without_maintenance": None,
                "guns_status": []
            }



