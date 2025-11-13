from sqlmodel import Session, select
from typing import Optional
import asyncio
from datetime import datetime
from sqlalchemy import or_, func
from fastapi import HTTPException
from models import Ammo, AmmoUpdate
from schemas.ammo import AmmoCreate
from services.user_context import UserContext, UserRole


class AmmoService:
    @staticmethod
    def _query_for_user(user: UserContext):
        query = select(Ammo)
        if user.role == UserRole.admin:
            return query
        query = query.where(Ammo.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Ammo.expires_at.is_(None), Ammo.expires_at > datetime.utcnow()))
        return query

    @staticmethod
    def _apply_search(query, search: Optional[str]):
        if not search:
            return query
        pattern = f"%{search.lower()}%"
        return query.where(
            or_(
                func.lower(Ammo.name).like(pattern),
                func.lower(func.coalesce(Ammo.caliber, "")).like(pattern)
            )
        )

    @staticmethod
    async def _get_single_ammo(session: Session, ammo_id: int, user: UserContext) -> Ammo:
        query = AmmoService._query_for_user(user).where(Ammo.id == ammo_id)
        ammo = await asyncio.to_thread(lambda: session.exec(query).first())
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
        return ammo

    @staticmethod
    async def get_all_ammo(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> dict:
        base_query = AmmoService._query_for_user(user)
        filtered_query = AmmoService._apply_search(base_query, search)
        count_query = filtered_query.with_only_columns(func.count(Ammo.id)).order_by(None)

        def _run():
            total = session.exec(count_query).one()[0]
            items = session.exec(filtered_query.offset(offset).limit(limit)).all()
            return total, items

        total, items = await asyncio.to_thread(_run)
        return {"total": total, "items": items}

    @staticmethod
    async def get_ammo_by_id(session: Session, ammo_id: int, user: UserContext) -> Ammo:
        return await AmmoService._get_single_ammo(session, ammo_id, user)

    @staticmethod
    async def create_ammo(session: Session, ammo_data: AmmoCreate, user: UserContext) -> Ammo:
        payload = ammo_data.model_dump()
        ammo = Ammo(**payload, user_id=user.user_id)
        if user.is_guest:
            ammo.expires_at = user.expires_at
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo

    @staticmethod
    async def update_ammo(session: Session, ammo_id: int, ammo_data: AmmoUpdate, user: UserContext) -> Ammo:
        ammo = await AmmoService._get_single_ammo(session, ammo_id, user)
        ammo_dict = ammo_data.model_dump(exclude_unset=True)
        for key, value in ammo_dict.items():
            setattr(ammo, key, value)
        if user.is_guest:
            ammo.expires_at = user.expires_at
        elif ammo.expires_at is not None and user.role != UserRole.admin:
            ammo.expires_at = None
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo

    @staticmethod
    async def delete_ammo(session: Session, ammo_id: int, user: UserContext) -> dict:
        ammo = await AmmoService._get_single_ammo(session, ammo_id, user)
        await asyncio.to_thread(session.delete, ammo)
        await asyncio.to_thread(session.commit)
        return {"message": f"Amunicja o ID {ammo_id} została usunięta"}

    @staticmethod
    async def add_ammo_quantity(session: Session, ammo_id: int, amount: int, user: UserContext) -> Ammo:
        ammo = await AmmoService._get_single_ammo(session, ammo_id, user)
        current = ammo.units_in_package or 0
        ammo.units_in_package = current + amount
        if user.is_guest:
            ammo.expires_at = user.expires_at
        elif ammo.expires_at is not None and user.role != UserRole.admin:
            ammo.expires_at = None
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo






