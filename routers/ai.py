from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Dict, Any
from database import get_session
from routers.auth import role_required
from services.user_context import UserContext, UserRole

router = APIRouter()


@router.post("/analyze")
async def analyze(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
) -> Dict[str, Any]:
    return {"message": "AI analysis endpoint - to be implemented in 0.4.0"}

