from sqlmodel import Session, select
from typing import Optional
from sqlalchemy import or_, func
from models import Gun, GunUpdate
from schemas.gun import GunCreate
from services.user_context import UserContext, UserRole
from services.exceptions import NotFoundError, BadRequestError


class GunService:
    @staticmethod
    def _query_for_user(user: UserContext):
        query = select(Gun).where(Gun.user_id == user.user_id)
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
    def _get_single_gun(session: Session, gun_id: str, user: UserContext) -> Gun:
        query = GunService._query_for_user(user).where(Gun.id == gun_id)
        gun = session.exec(query).first()
        if not gun:
            raise NotFoundError("Broń nie została znaleziona")
        return gun

    @staticmethod
    def get_all_guns(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> dict:
        base_query = GunService._query_for_user(user)
        filtered_query = GunService._apply_search(base_query, search)
        count_query = filtered_query.with_only_columns(func.count(Gun.id)).order_by(None)

        total = session.exec(count_query).one()
        items = session.exec(filtered_query.offset(offset).limit(limit)).all()
        return {"total": total, "items": items}

    @staticmethod
    def get_gun_by_id(session: Session, gun_id: str, user: UserContext) -> Gun:
        return GunService._get_single_gun(session, gun_id, user)

    @staticmethod
    def create_gun(session: Session, gun_data: GunCreate, user: UserContext) -> Gun:
        from datetime import date
        from services.exceptions import BadRequestError
        payload = gun_data.model_dump(exclude_unset=True)
        payload.pop('user_id', None)
        # Jeśli created_at nie jest podane, użyj dzisiejszej daty
        if 'created_at' not in payload or payload['created_at'] is None:
            payload['created_at'] = date.today()
        else:
            # Walidacja: data utworzenia nie może być w przyszłości
            created_at = payload['created_at']
            if isinstance(created_at, str):
                from datetime import datetime
                created_at = datetime.strptime(created_at, "%Y-%m-%d").date()
            if created_at > date.today():
                raise BadRequestError("Data utworzenia broni nie może być w przyszłości")
        gun = Gun(**payload, user_id=user.user_id)
        session.add(gun)
        session.commit()
        session.refresh(gun)
        return gun

    @staticmethod
    def update_gun(session: Session, gun_id: str, gun_data: GunUpdate, user: UserContext) -> Gun:
        gun = GunService._get_single_gun(session, gun_id, user)
        gun_dict = gun_data.model_dump(exclude_unset=True)
        gun_dict.pop('user_id', None)
        for key, value in gun_dict.items():
            setattr(gun, key, value)
        session.add(gun)
        session.commit()
        session.refresh(gun)
        return gun

    @staticmethod
    async def delete_gun(session: Session, gun_id: str, user: UserContext) -> dict:
        gun = GunService._get_single_gun(session, gun_id, user)
        
        # Usuń zdjęcie broni z Supabase jeśli istnieje
        if gun.image_path:
            try:
                from services.supabase_service import delete_weapon_image
                import asyncio
                await asyncio.to_thread(delete_weapon_image, gun.image_path)
            except Exception as e:
                # Nie blokuj usuwania broni, jeśli usunięcie zdjęcia się nie powiodło
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Nie udało się usunąć zdjęcia broni z Supabase: {str(e)}")
        
        try:
            session.delete(gun)
            session.commit()
            return {"message": f"Broń o ID {gun_id} została usunięta"}
        except Exception as e:
            session.rollback()
            error_msg = str(e).lower()
            if "foreign key" in error_msg or "integrity" in error_msg:
                raise BadRequestError(
                    "Nie można usunąć broni, ponieważ jest powiązana z sesjami strzeleckimi, konserwacją lub wyposażeniem. Najpierw usuń powiązane rekordy."
                )
            raise BadRequestError(f"Błąd podczas usuwania broni: {str(e)}")






