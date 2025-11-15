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
    async def list_for_gun(session: Session, user: UserContext, gun_id: str) -> List[Maintenance]:
        await GunService._get_single_gun(session, gun_id, user)
        query = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date))
        maintenance_list = await asyncio.to_thread(lambda: session.exec(query).all())
        if not maintenance_list:
            return []
        maintenance_list_sorted = sorted(maintenance_list, key=lambda x: x.date)
        result = []
        for i, maint in enumerate(maintenance_list_sorted):
            if i == len(maintenance_list_sorted) - 1:
                rounds = await MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, maint.date, None
                )
                maint.rounds_since_last = rounds
            elif i > 0:
                prev_maint = maintenance_list_sorted[i - 1]
                rounds = await MaintenanceService._calculate_rounds_since_last(
                    session, user, gun_id, prev_maint.date, maint.date
                )
                maint.rounds_since_last = rounds
            else:
                query_all_sessions = select(ShootingSession).where(
                    ShootingSession.gun_id == gun_id,
                    ShootingSession.user_id == user.user_id,
                    ShootingSession.date <= maint.date
                )
                if user.is_guest:
                    query_all_sessions = query_all_sessions.where(
                        or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow())
                    )
                sessions = await asyncio.to_thread(lambda: session.exec(query_all_sessions).all())
                cost_rounds = sum(session_item.shots for session_item in sessions)
                query_all_accuracy = select(AccuracySession).where(
                    AccuracySession.gun_id == gun_id,
                    AccuracySession.user_id == user.user_id,
                    AccuracySession.date <= maint.date
                )
                if user.is_guest:
                    query_all_accuracy = query_all_accuracy.where(
                        or_(AccuracySession.expires_at.is_(None), AccuracySession.expires_at > datetime.utcnow())
                    )
                accuracy_sessions = await asyncio.to_thread(lambda: session.exec(query_all_accuracy).all())
                accuracy_rounds = sum(acc_session.shots for acc_session in accuracy_sessions)
                maint.rounds_since_last = cost_rounds + accuracy_rounds
            result.append(maint)
        result.reverse()
        return result

    @staticmethod
    async def list_global(session: Session, user: UserContext, filters: Optional[Dict[str, Any]] = None) -> List[Maintenance]:
        query = MaintenanceService._query_for_user(user)
        if filters:
            if filters.get("gun_id"):
                query = query.where(Maintenance.gun_id == filters["gun_id"])
            if filters.get("date_from"):
                query = query.where(Maintenance.date >= filters["date_from"])
            if filters.get("date_to"):
                query = query.where(Maintenance.date <= filters["date_to"])
        query = query.order_by(desc(Maintenance.date))
        maintenance_list = await asyncio.to_thread(lambda: session.exec(query).all())
        result = []
        maintenance_by_gun = {}
        for maint in maintenance_list:
            if maint.gun_id not in maintenance_by_gun:
                maintenance_by_gun[maint.gun_id] = []
            maintenance_by_gun[maint.gun_id].append(maint)
        for gun_id, gun_maintenance in maintenance_by_gun.items():
            gun_maintenance.sort(key=lambda x: x.date)
            for i, maint in enumerate(gun_maintenance):
                if i == len(gun_maintenance) - 1:
                    rounds = await MaintenanceService._calculate_rounds_since_last(
                        session, user, gun_id, maint.date, None
                    )
                    maint.rounds_since_last = rounds
                elif i > 0:
                    prev_maint = gun_maintenance[i - 1]
                    rounds = await MaintenanceService._calculate_rounds_since_last(
                        session, user, gun_id, prev_maint.date, maint.date
                    )
                    maint.rounds_since_last = rounds
                else:
                    query_all_sessions = select(ShootingSession).where(
                        ShootingSession.gun_id == gun_id,
                        ShootingSession.user_id == user.user_id,
                        ShootingSession.date <= maint.date
                    )
                    if user.is_guest:
                        query_all_sessions = query_all_sessions.where(
                            or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow())
                        )
                    sessions = await asyncio.to_thread(lambda: session.exec(query_all_sessions).all())
                    cost_rounds = sum(session_item.shots for session_item in sessions)
                    query_all_accuracy = select(AccuracySession).where(
                        AccuracySession.gun_id == gun_id,
                        AccuracySession.user_id == user.user_id,
                        AccuracySession.date <= maint.date
                    )
                    if user.is_guest:
                        query_all_accuracy = query_all_accuracy.where(
                            or_(AccuracySession.expires_at.is_(None), AccuracySession.expires_at > datetime.utcnow())
                        )
                    accuracy_sessions = await asyncio.to_thread(lambda: session.exec(query_all_accuracy).all())
                    accuracy_rounds = sum(acc_session.shots for acc_session in accuracy_sessions)
                    maint.rounds_since_last = cost_rounds + accuracy_rounds
                result.append(maint)
        result.sort(key=lambda x: x.date, reverse=True)
        return result

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
    async def create_maintenance(session: Session, user: UserContext, gun_id: str, data: dict) -> Maintenance:
        await GunService._get_single_gun(session, gun_id, user)
        maintenance_date = data.get("date")
        if isinstance(maintenance_date, str):
            maintenance_date = datetime.strptime(maintenance_date, "%Y-%m-%d").date()
        query_last = MaintenanceService._query_for_user(user, gun_id).order_by(desc(Maintenance.date)).limit(1)
        last_maintenance = await asyncio.to_thread(lambda: session.exec(query_last).first())
        if last_maintenance:
            rounds_since_last = await MaintenanceService._calculate_rounds_since_last(
                session, user, gun_id, last_maintenance.date, maintenance_date
            )
        else:
            query_all_sessions = select(ShootingSession).where(
                ShootingSession.gun_id == gun_id,
                ShootingSession.user_id == user.user_id,
                ShootingSession.date <= maintenance_date
            )
            if user.is_guest:
                query_all_sessions = query_all_sessions.where(
                    or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow())
                )
            sessions = await asyncio.to_thread(lambda: session.exec(query_all_sessions).all())
            cost_rounds = sum(session_item.shots for session_item in sessions)
            query_all_accuracy = select(AccuracySession).where(
                AccuracySession.gun_id == gun_id,
                AccuracySession.user_id == user.user_id,
                AccuracySession.date <= maintenance_date
            )
            if user.is_guest:
                query_all_accuracy = query_all_accuracy.where(
                    or_(AccuracySession.expires_at.is_(None), AccuracySession.expires_at > datetime.utcnow())
                )
            accuracy_sessions = await asyncio.to_thread(lambda: session.exec(query_all_accuracy).all())
            accuracy_rounds = sum(acc_session.shots for acc_session in accuracy_sessions)
            rounds_since_last = cost_rounds + accuracy_rounds
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
    async def delete_maintenance(session: Session, user: UserContext, maintenance_id: str) -> dict:
        maintenance = await MaintenanceService._get_single_maintenance(session, maintenance_id, user)
        await asyncio.to_thread(session.delete, maintenance)
        await asyncio.to_thread(session.commit)
        return {"message": f"Konserwacja o ID {maintenance_id} została usunięta"}

