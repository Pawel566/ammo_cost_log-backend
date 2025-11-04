from sqlmodel import Session, select
from typing import List
import asyncio
from fastapi import HTTPException
from models import Gun, GunCreate, GunRead, GunUpdate


class GunService:
    @staticmethod
    async def get_all_guns(session: Session) -> List[Gun]:
        guns = await asyncio.to_thread(lambda: session.exec(select(Gun)).all())
        return guns

    @staticmethod
    async def get_gun_by_id(session: Session, gun_id: int) -> Gun:
        gun = await asyncio.to_thread(session.get, Gun, gun_id)
        if not gun:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        return gun

    @staticmethod
    async def create_gun(session: Session, gun_data: GunCreate) -> Gun:
        gun = Gun.model_validate(gun_data)
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        return gun

    @staticmethod
    async def update_gun(session: Session, gun_id: int, gun_data: GunUpdate) -> Gun:
        gun = await asyncio.to_thread(session.get, Gun, gun_id)
        if not gun:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        
        gun_dict = gun_data.model_dump(exclude_unset=True)
        for key, value in gun_dict.items():
            setattr(gun, key, value)
        
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        return gun

    @staticmethod
    async def delete_gun(session: Session, gun_id: int) -> dict:
        gun = await asyncio.to_thread(session.get, Gun, gun_id)
        if not gun:
            raise HTTPException(status_code=404, detail="Broń nie została znaleziona")
        
        session.delete(gun)
        await asyncio.to_thread(session.commit)
        return {"message": f"Broń o ID {gun_id} została usunięta"}

