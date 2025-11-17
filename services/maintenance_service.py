from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import asyncio
from sqlalchemy import or_, func, desc
from fastapi import HTTPException
from models import Maintenance, Gun, ShootingSession, AccuracySession
from services.user_context import UserContext, UserRole
from services.gun_service import GunService


class MaintenanceService:
    @staticmethod
    def _query_for_user(user: UserContext, gun_id: Optional[str] = None):
        query = select(Maintenance)
        if gun_id:
            query = query.where(Maintenance.gun_id == gun_id)
        if user.role == UserRole.admin:
            return query
        query = query.where(Maintenance.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Maintenance.expires_at.is_(None), Maintenance.expires_at > datetime.utcnow()))
        return query

    @staticmethod
    async def _calculate_rounds_since_last(session: Session, user: UserContext, gun_id: str, last_maintenance_date: date, until_date: Optional[date] = None) -> int:
        query_sessions = select(ShootingSession).where(
            ShootingSession.gun_id == gun_id,
            ShootingSession.user_id == user.user_id,
            ShootingSession.date > last_maintenance_date
        )
        if until_date:
            query_sessions = query_sessions.where(ShootingSession.date <= until_date)
        if user.is_guest:
            query_sessions = query_sessions.where(
                or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow())
            )
        sessions = await asyncio.to_thread(lambda: session.exec(query_sessions).all())
        cost_rounds = sum(session_item.shots for session_item in sessions)
        
        query_accuracy = select(AccuracySession).where(
            AccuracySession.gun_id == gun_id,
            AccuracySession.user_id == user.user_id,
            AccuracySession.date > last_maintenance_date
        )
        if until_date:
            query_accuracy = query_accuracy.where(AccuracySession.date <= until_date)
        if user.is_guest:
            query_accuracy = query_accuracy.where(
                or_(AccuracySession.expires_at.is_(None), AccuracySession.expires_at > datetime.utcnow())
            )
        accuracy_sessions = await asyncio.to_thread(lambda: session.exec(query_accuracy).all())
        accuracy_rounds = sum(acc_session.shots for acc_session in accuracy_sessions)
        return cost_rounds + accuracy_rounds

    @staticmethod
    async def list_all(session: Session, user: UserContext, gun_id: Optional[str] = None) -> List[Maintenance]:
        query = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date))
        maintenance_list = await asyncio.to_thread(lambda: session.exec(query).all())
        
        result = []
        for maint in maintenance_list:
            maint_dict = {
                "id": maint.id,
                "gun_id": maint.gun_id,
                "user_id": maint.user_id,
                "date": maint.date,
                "notes": maint.notes,
                "rounds_since_last": maint.rounds_since_last,
                "expires_at": maint.expires_at
            }
            
            gun_query = select(Gun).where(Gun.id == maint.gun_id)
            if user.role != UserRole.admin:
                gun_query = gun_query.where(Gun.user_id == user.user_id)
            gun = await asyncio.to_thread(lambda: session.exec(gun_query).first())
            if gun:
                maint_dict["gun_name"] = gun.name
            
            result.append(maint_dict)
        
        return result

    @staticmethod
    async def list_for_gun(session: Session, user: UserContext, gun_id: str) -> List[Maintenance]:
        await GunService._get_single_gun(session, gun_id, user)
        query = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date))
        maintenance_list = await asyncio.to_thread(lambda: session.exec(query).all())
        return list(maintenance_list)

    @staticmethod
    async def create_maintenance(session: Session, user: UserContext, gun_id: str, data: dict) -> Maintenance:
        await GunService._get_single_gun(session, gun_id, user)
        maintenance_date = data.get("date")
        if isinstance(maintenance_date, str):
            maintenance_date = datetime.strptime(maintenance_date, "%Y-%m-%d").date()
        
        rounds_since_last = data.get("rounds_since_last", 0)
        if rounds_since_last == 0:
            query_last = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date)).limit(1)
            last_maintenance = await asyncio.to_thread(lambda: session.exec(query_last).first())
            if last_maintenance:
                rounds_since_last = await MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, last_maintenance.date, maintenance_date
                )
            else:
                rounds_since_last = await MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, date(1900, 1, 1), maintenance_date
                )
        
        maintenance = Maintenance(
            gun_id=gun_id,
            user_id=user.user_id,
            date=maintenance_date,
            notes=data.get("notes"),
            rounds_since_last=rounds_since_last
        )
        if user.is_guest:
            maintenance.expires_at = user.expires_at
        session.add(maintenance)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, maintenance)
        return maintenance

    @staticmethod
    async def _get_single_maintenance(session: Session, maintenance_id: str, user: UserContext) -> Maintenance:
        query = select(Maintenance).where(Maintenance.id == maintenance_id)
        if user.role != UserRole.admin:
            query = query.where(Maintenance.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Maintenance.expires_at.is_(None), Maintenance.expires_at > datetime.utcnow()))
        maintenance = await asyncio.to_thread(lambda: session.exec(query).first())
        if not maintenance:
            raise HTTPException(status_code=404, detail="Konserwacja nie została znaleziona")
        return maintenance

    @staticmethod
    async def update_maintenance(session: Session, user: UserContext, maintenance_id: str, data: dict) -> Maintenance:
        maintenance = await MaintenanceService._get_single_maintenance(session, maintenance_id, user)
        if "date" in data and data["date"]:
            if isinstance(data["date"], str):
                maintenance.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            else:
                maintenance.date = data["date"]
        if "notes" in data:
            maintenance.notes = data.get("notes")
        if "rounds_since_last" in data and data["rounds_since_last"] is not None:
            maintenance.rounds_since_last = data["rounds_since_last"]
        if user.is_guest:
            maintenance.expires_at = user.expires_at
        session.add(maintenance)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, maintenance)
        return maintenance

    @staticmethod
    async def delete_maintenance(session: Session, user: UserContext, maintenance_id: str) -> dict:
        maintenance = await MaintenanceService._get_single_maintenance(session, maintenance_id, user)
        await asyncio.to_thread(session.delete, maintenance)
        await asyncio.to_thread(session.commit)
        return {"message": f"Konserwacja o ID {maintenance_id} została usunięta"}

    @staticmethod
    async def get_statistics(session: Session, user: UserContext) -> Dict[str, Any]:
        query_guns = select(Gun)
        if user.role != UserRole.admin:
            query_guns = query_guns.where(Gun.user_id == user.user_id)
        if user.is_guest:
            query_guns = query_guns.where(or_(Gun.expires_at.is_(None), Gun.expires_at > datetime.utcnow()))
        guns = await asyncio.to_thread(lambda: session.exec(query_guns).all())
        
        today = date.today()
        gun_stats = []
        longest_without = None
        max_days = 0
        
        for gun in guns:
            query_last = MaintenanceService._query_for_user(user, gun.id).order_by(desc(Maintenance.date)).limit(1)
            last_maintenance = await asyncio.to_thread(lambda: session.exec(query_last).first())
            
            if last_maintenance:
                days_since = (today - last_maintenance.date).days
            else:
                days_since = None
            
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
        
        return {
            "longest_without_maintenance": longest_without,
            "guns_status": gun_stats
        }

