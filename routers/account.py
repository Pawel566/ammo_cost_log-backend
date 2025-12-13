from fastapi import APIRouter, Depends, Header
from sqlmodel import Session, select
from schemas.account import ChangePasswordRequest, ChangeEmailRequest, UpdateSkillLevelRequest, DeleteAccountRequest
from database import get_session
from routers.auth import get_current_user
from services.account_service import AccountService
from services.user_context import UserContext
from routers.auth import supabase
from models import User
from fastapi.security import HTTPAuthorizationCredentials
from routers.auth import security
from services.rank_service import get_rank_info, update_user_rank
import asyncio

router = APIRouter()


@router.get("/skill-level")
async def get_skill_level(
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user)
):
    # Zapewnij, że użytkownik istnieje w bazie (automatycznie tworzy, jeśli nie istnieje)
    user_record = await asyncio.to_thread(lambda: AccountService.ensure_user_exists(session, user))
    return {"skill_level": user_record.skill_level if user_record else "beginner"}


@router.post("/skill-level")
async def update_skill_level(
    data: UpdateSkillLevelRequest,
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user)
):
    return await AccountService.update_skill_level(session, user, data.skill_level)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Brak tokena uwierzytelniającego")
    return await AccountService.change_password(session, user, supabase, credentials.credentials, data.old_password, data.new_password)


@router.post("/change-email")
async def change_email(
    data: ChangeEmailRequest,
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Brak tokena uwierzytelniającego")
    return await AccountService.change_email(session, user, supabase, credentials.credentials, data.new_email)


@router.get("/rank")
async def get_rank(
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user)
):
    # Zapewnij, że użytkownik istnieje w bazie (automatycznie tworzy, jeśli nie istnieje)
    user_record = await asyncio.to_thread(lambda: AccountService.ensure_user_exists(session, user))
    
    if not hasattr(user_record, 'rank') or user_record.rank is None:
        user_record.rank = "Nowicjusz"
        session.add(user_record)
        await asyncio.to_thread(lambda: session.commit())
        await asyncio.to_thread(lambda: session.refresh(user_record))
    
    updated_rank = await asyncio.to_thread(lambda: update_user_rank(user_record, session))
    await asyncio.to_thread(lambda: session.refresh(user_record))
    rank_info = await asyncio.to_thread(lambda: get_rank_info(user_record, session))
    rank_info["rank"] = updated_rank
    return rank_info


@router.delete("")
async def delete_account(
    data: DeleteAccountRequest,
    session: Session = Depends(get_session),
    user: UserContext = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not credentials:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Brak tokena uwierzytelniającego")
    return await AccountService.delete_account(session, user, supabase, credentials.credentials, data.password)

