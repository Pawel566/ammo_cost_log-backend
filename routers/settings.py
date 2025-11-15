from fastapi import APIRouter, Depends
from sqlmodel import Session
from schemas.settings import UserSettingsRead, UserSettingsUpdate
from database import get_session
from routers.auth import role_required
from services.user_settings_service import UserSettingsService
from services.user_context import UserContext, UserRole

router = APIRouter()


@router.get("", response_model=UserSettingsRead)
async def get_settings(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await UserSettingsService.get_settings(session, user)


@router.post("", response_model=UserSettingsRead)
async def update_settings(
    settings_data: UserSettingsUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await UserSettingsService.update_settings(session, user, settings_data.model_dump(exclude_unset=True))


@router.put("", response_model=UserSettingsRead)
async def update_settings_put(
    settings_data: UserSettingsUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await UserSettingsService.update_settings(session, user, settings_data.model_dump(exclude_unset=True))

