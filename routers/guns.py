from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from models import Gun, GunBase
from database import engine

router = APIRouter()

@router.get("/")
def get_guns():
    with Session(engine) as session:
        guns = session.exec(select(Gun)).all()
        return guns

@router.post("/")
def add_gun(gun_data: GunBase):
    gun = Gun.model_validate(gun_data)
    with Session(engine) as session:
        session.add(gun)
        session.commit()
        session.refresh(gun)
        return gun

@router.delete("/{gun_id}")
def delete_gun(gun_id: int):
    with Session(engine) as session:
        gun = session.get(Gun, gun_id)
        if not gun:
            raise HTTPException(status_code=404, detail="Gun not found")
        session.delete(gun)
        session.commit()
        return {"deleted": gun_id}