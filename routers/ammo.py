from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from models import Ammo, AmmoBase
from database import engine

router = APIRouter()

@router.get("/")
def get_ammo():
    with Session(engine) as session:
        ammo_list = session.exec(select(Ammo)).all()
        return ammo_list

@router.post("/")
def add_ammo(ammo_data: AmmoBase):
    if ammo_data.price_per_unit < 0:
        raise HTTPException(status_code=400, detail="Price per unit must be >= 0")

    ammo = Ammo.from_orm(ammo_data)
    with Session(engine) as session:
        session.add(ammo)
        session.commit()
        session.refresh(ammo)
        return ammo

@router.delete("/{ammo_id}")
def delete_ammo(ammo_id: int):
    with Session(engine) as session:
        ammo = session.get(Ammo, ammo_id)
        if not ammo:
            raise HTTPException(status_code=404, detail="Ammo not found")
        session.delete(ammo)
        session.commit()
        return {"deleted": ammo_id}