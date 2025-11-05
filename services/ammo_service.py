from sqlmodel import Session, select
from typing import List
import asyncio
from fastapi import HTTPException
from models import Ammo, AmmoCreate, AmmoRead, AmmoUpdate


class AmmoService:
    @staticmethod
    async def get_all_ammo(session: Session) -> List[Ammo]:
        ammo_list = await asyncio.to_thread(lambda: session.exec(select(Ammo)).all())
        return ammo_list

    @staticmethod
    async def get_ammo_by_id(session: Session, ammo_id: int) -> Ammo:
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
        return ammo

    @staticmethod
    async def create_ammo(session: Session, ammo_data: AmmoCreate) -> Ammo:
        ammo = Ammo.model_validate(ammo_data)
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo

    @staticmethod
    async def update_ammo(session: Session, ammo_id: int, ammo_data: AmmoUpdate) -> Ammo:
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
        
        ammo_dict = ammo_data.model_dump(exclude_unset=True)
        for key, value in ammo_dict.items():
            setattr(ammo, key, value)
        
        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo

    @staticmethod
    async def delete_ammo(session: Session, ammo_id: int) -> dict:
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")
        
        session.delete(ammo)
        await asyncio.to_thread(session.commit)
        return {"message": f"Amunicja o ID {ammo_id} została usunięta"}

    @staticmethod
    async def add_ammo_quantity(session: Session, ammo_id: int, amount: int) -> Ammo:
        ammo = await asyncio.to_thread(session.get, Ammo, ammo_id)
        if not ammo:
            raise HTTPException(status_code=404, detail="Amunicja nie została znaleziona")

        current = ammo.units_in_package or 0
        ammo.units_in_package = current + amount

        session.add(ammo)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, ammo)
        return ammo





