from sqlmodel import Session, select
from typing import Optional
from sqlalchemy import or_, func
from models import Ammo, AmmoUpdate
from schemas.ammo import AmmoCreate
from services.user_context import UserContext, UserRole
from services.exceptions import NotFoundError, BadRequestError


class AmmoService:
    @staticmethod
    def _query_for_user(user: UserContext):
        query = select(Ammo)
        if user.role == UserRole.admin:
            return query
        query = query.where(Ammo.user_id == user.user_id)
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
    def _get_single_ammo(session: Session, ammo_id: str, user: UserContext) -> Ammo:
        query = AmmoService._query_for_user(user).where(Ammo.id == ammo_id)
        ammo = session.exec(query).first()
        if not ammo:
            raise NotFoundError("Amunicja nie została znaleziona")
        return ammo

    @staticmethod
    def get_all_ammo(session: Session, user: UserContext, limit: int, offset: int, search: Optional[str]) -> dict:
        base_query = AmmoService._query_for_user(user)
        filtered_query = AmmoService._apply_search(base_query, search)
        count_query = filtered_query.with_only_columns(func.count(Ammo.id)).order_by(None)

        total = session.exec(count_query).one()
        items = session.exec(filtered_query.offset(offset).limit(limit)).all()
        return {"total": total, "items": items}

    @staticmethod
    def get_ammo_by_id(session: Session, ammo_id: str, user: UserContext) -> Ammo:
        return AmmoService._get_single_ammo(session, ammo_id, user)

    @staticmethod
    def create_ammo(session: Session, ammo_data: AmmoCreate, user: UserContext) -> Ammo:
        payload = ammo_data.model_dump()
        ammo = Ammo(**payload, user_id=user.user_id)
        session.add(ammo)
        session.commit()
        session.refresh(ammo)
        return ammo

    @staticmethod
    def update_ammo(session: Session, ammo_id: str, ammo_data: AmmoUpdate, user: UserContext) -> Ammo:
        ammo = AmmoService._get_single_ammo(session, ammo_id, user)
        ammo_dict = ammo_data.model_dump(exclude_unset=True)
        for key, value in ammo_dict.items():
            setattr(ammo, key, value)
        session.add(ammo)
        session.commit()
        session.refresh(ammo)
        return ammo

    @staticmethod
    def delete_ammo(session: Session, ammo_id: str, user: UserContext) -> dict:
        ammo = AmmoService._get_single_ammo(session, ammo_id, user)
        try:
            session.delete(ammo)
            session.commit()
            return {"message": f"Amunicja o ID {ammo_id} została usunięta"}
        except Exception as e:
            session.rollback()
            error_msg = str(e).lower()
            if "foreign key" in error_msg or "integrity" in error_msg:
                raise BadRequestError(
                    "Nie można usunąć amunicji, ponieważ jest powiązana z sesjami strzeleckimi. Najpierw usuń powiązane sesje."
                )
            raise BadRequestError(f"Błąd podczas usuwania amunicji: {str(e)}")

    @staticmethod
    def add_ammo_quantity(session: Session, ammo_id: str, amount: int, user: UserContext) -> Ammo:
        ammo = AmmoService._get_single_ammo(session, ammo_id, user)
        current = ammo.units_in_package or 0
        ammo.units_in_package = current + amount
        session.add(ammo)
        session.commit()
        session.refresh(ammo)
        return ammo






