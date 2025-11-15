from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import or_
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole
from services.ai_service import AIService
from services.gun_service import GunService
from services.attachments_service import AttachmentsService
from services.maintenance_service import MaintenanceService
from schemas.ai import AnalyzeRequest
from models import ShootingSession, AccuracySession, User
import asyncio

router = APIRouter()


@router.post("/analyze")
async def analyze(
    data: AnalyzeRequest,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
) -> Dict[str, Any]:
    gun = await GunService._get_single_gun(session, data.gun_id, user)
    attachments = await AttachmentsService.list_for_gun(session, user, data.gun_id)
    maintenance = await MaintenanceService.list_for_gun(session, user, data.gun_id)
    query_cost = select(ShootingSession).where(ShootingSession.gun_id == data.gun_id, ShootingSession.user_id == user.user_id)
    if user.is_guest:
        query_cost = query_cost.where(or_(ShootingSession.expires_at.is_(None), ShootingSession.expires_at > datetime.utcnow()))
    cost_sessions = await asyncio.to_thread(lambda: session.exec(query_cost).all())
    query_accuracy = select(AccuracySession).where(AccuracySession.gun_id == data.gun_id, AccuracySession.user_id == user.user_id)
    if user.is_guest:
        query_accuracy = query_accuracy.where(or_(AccuracySession.expires_at.is_(None), AccuracySession.expires_at > datetime.utcnow()))
    accuracy_sessions = await asyncio.to_thread(lambda: session.exec(query_accuracy).all())
    query_user = select(User).where(User.user_id == user.user_id)
    user_record = await asyncio.to_thread(lambda: session.exec(query_user).first())
    user_skill = user_record.skill_level if user_record else None
    analysis = await AIService.analyze_weapon(
        gun,
        list(attachments),
        list(maintenance),
        list(cost_sessions),
        list(accuracy_sessions),
        user_skill,
        data.openai_api_key
    )
    return {"analysis": analysis}

