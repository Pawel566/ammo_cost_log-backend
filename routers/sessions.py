from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from database import get_session
from services.session_service import SessionService

router = APIRouter()

class CostSessionInput(BaseModel):
    gun_id: int
    ammo_id: int
    date: Optional[str] = Field(default=None)
    shots: int = Field(gt=0)
    openai_api_key: Optional[str] = Field(default=None)

class AccuracySessionInput(BaseModel):
    gun_id: int
    ammo_id: int
    date: Optional[str] = Field(default=None)
    distance_m: int = Field(gt=0)
    shots: int = Field(gt=0)
    hits: int = Field(ge=0)
    openai_api_key: Optional[str] = Field(default=None)

class MonthlySummary(BaseModel):
    month: str
    total_cost: float
    total_shots: int

@router.get("/", response_model=Dict[str, List])
async def get_all_sessions(session: Session = Depends(get_session)):
    return await SessionService.get_all_sessions(session)

@router.post("/cost", response_model=Dict[str, Any])
async def add_cost_session(data: CostSessionInput, session: Session = Depends(get_session)):
    return await SessionService.create_cost_session(
        session,
        data.gun_id,
        data.ammo_id,
        data.date,
        data.shots
    )

@router.post("/accuracy", response_model=Dict[str, Any])
async def add_accuracy_session(data: AccuracySessionInput, session: Session = Depends(get_session)):
    return await SessionService.create_accuracy_session(
        session,
        data.gun_id,
        data.ammo_id,
        data.date,
        data.distance_m,
        data.shots,
        data.hits,
        data.openai_api_key
    )

@router.get("/summary", response_model=List[MonthlySummary])
async def get_monthly_summary(session: Session = Depends(get_session)):
    return await SessionService.get_monthly_summary(session)
