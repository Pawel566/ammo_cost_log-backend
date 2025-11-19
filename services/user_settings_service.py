from sqlmodel import Session, select
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from sqlalchemy import or_
from fastapi import HTTPException
from models.user import UserSettings
from services.user_context import UserContext, UserRole


class UserSettingsService:
    @staticmethod
    async def get_settings(session: Session, user: UserContext) -> UserSettings:
        query = select(UserSettings).where(UserSettings.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(UserSettings.expires_at.is_(None), UserSettings.expires_at > datetime.utcnow()))
        settings = await asyncio.to_thread(lambda: session.exec(query).first())
        if not settings:
            settings = UserSettings(
                user_id=user.user_id,
                ai_mode="off",
                theme="dark",
                distance_unit="m"
            )
            if user.is_guest:
                settings.expires_at = user.expires_at
            session.add(settings)
            await asyncio.to_thread(session.commit)
            await asyncio.to_thread(session.refresh, settings)
        return settings

    @staticmethod
    async def update_settings(session: Session, user: UserContext, data: Dict[str, Any]) -> UserSettings:
        settings = await UserSettingsService.get_settings(session, user)
        if "ai_mode" in data:
            settings.ai_mode = data["ai_mode"]
        if "theme" in data:
            settings.theme = data["theme"]
        if "distance_unit" in data:
            settings.distance_unit = data["distance_unit"]
        if user.is_guest:
            settings.expires_at = user.expires_at
        session.add(settings)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, settings)
        return settings


