from sqlmodel import Session, select
from typing import Optional
import asyncio
from datetime import datetime
from sqlalchemy import or_, func
from fastapi import HTTPException
from models import Gun, GunUpdate
from schemas.gun import GunCreate
from services.user_context import UserContext, UserRole


class GunService:
    @staticmethod
    def _query_for_user(user: UserContext):
        query = select(Gun)
        if user.role == UserRole.admin:
            return query
        query = query.where(Gun.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Gun.expires_at.is_(None), Gun.expires_at > datetime.utcnow()))
        return query

    @staticmethod
    def _apply_search(query, search: Optional[str]):
        if not search:
            return query
        pattern = f"%{search.lower()}%"
        return query.where(
            or_(
                func.lower(Gun.name).like(pattern),
                func.lower(func.coalesce(Gun.caliber, "")).like(pattern),
                func.lower(func.coalesce(Gun.type, "")).like(pattern),
                func.lower(func.coalesce(Gun.notes, "")).like(pattern),
            )
        )

    @staticmethod
    async def _get_single_gun(session: Session, gun_id: int, user: UserContext) -> Gun:
        query = GunService._query_for_user(user).where(Gun.id == gun_id)
        gun = await asyncio.to_thread(lambda: session.exec(query).first())
        if not gun:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        return gun

    @staticmethod
    async def get_all_guns(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> dict:
        base_query = GunService._query_for_user(user)
        filtered_query = GunService._apply_search(base_query, search)
        count_query = filtered_query.with_only_columns(func.count(Gun.id)).order_by(None)

        def _run():
            total = session.exec(count_query).one()[0]
            items = session.exec(filtered_query.offset(offset).limit(limit)).all()
            return total, items

        total, items = await asyncio.to_thread(_run)
        return {"total": total, "items": items}

    @staticmethod
    async def get_gun_by_id(session: Session, gun_id: int, user: UserContext) -> Gun:
        return await GunService._get_single_gun(session, gun_id, user)

    @staticmethod
    async def create_gun(session: Session, gun_data: GunCreate, user: UserContext) -> Gun:
        payload = gun_data.model_dump()
        gun = Gun(**payload, user_id=user.user_id)
        if user.is_guest:
            gun.expires_at = user.expires_at
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        return gun

    @staticmethod
    async def update_gun(session: Session, gun_id: int, gun_data: GunUpdate, user: UserContext) -> Gun:
        gun = await GunService._get_single_gun(session, gun_id, user)
        gun_dict = gun_data.model_dump(exclude_unset=True)
        for key, value in gun_dict.items():
            setattr(gun, key, value)
        if user.is_guest:
            gun.expires_at = user.expires_at
        elif gun.expires_at is not None and user.role != UserRole.admin:
            gun.expires_at = None
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        return gun

    @staticmethod
    async def delete_gun(session: Session, gun_id: int, user: UserContext) -> dict:
        gun = await GunService._get_single_gun(session, gun_id, user)
        await asyncio.to_thread(session.delete, gun)
        await asyncio.to_thread(session.commit)
        return {"message": f"Broń o ID {gun_id} została usunięta"}






