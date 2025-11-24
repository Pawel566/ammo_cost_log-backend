from sqlmodel import Session, select
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from sqlalchemy import or_
from fastapi import HTTPException
from models import UserSettings
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
                distance_unit="m",
                maintenance_rounds_limit=500,
                maintenance_days_limit=90,
                maintenance_notifications_enabled=True,
                low_ammo_notifications_enabled=True,
                ai_analysis_intensity="normalna",
                ai_auto_comments=False
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
        if "maintenance_rounds_limit" in data:
            settings.maintenance_rounds_limit = data["maintenance_rounds_limit"]
        if "maintenance_days_limit" in data:
            settings.maintenance_days_limit = data["maintenance_days_limit"]
        if "maintenance_notifications_enabled" in data:
            settings.maintenance_notifications_enabled = data["maintenance_notifications_enabled"]
        if "low_ammo_notifications_enabled" in data:
            settings.low_ammo_notifications_enabled = data["low_ammo_notifications_enabled"]
        if "ai_analysis_intensity" in data:
            settings.ai_analysis_intensity = data["ai_analysis_intensity"]
        if "ai_auto_comments" in data:
            settings.ai_auto_comments = data["ai_auto_comments"]
        if user.is_guest:
            settings.expires_at = user.expires_at
        session.add(settings)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, settings)
        return settings


