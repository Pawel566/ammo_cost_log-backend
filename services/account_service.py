from sqlmodel import Session, select
from typing import Dict, Any, Optional
import asyncio
from fastapi import HTTPException
from supabase import Client
from models import Gun, Ammo, ShootingSession, AccuracySession, Attachment, Maintenance, UserSettings, User
from services.user_context import UserContext
from services.error_handler import ErrorHandler


class AccountService:
    @staticmethod
    async def change_password(session: Session, user: UserContext, supabase: Client, access_token: str, old_password: str, new_password: str) -> Dict[str, str]:
        if not supabase:
            raise HTTPException(status_code=503, detail="Authentication service not available")
        try:
            import httpx
            from settings import settings
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{settings.supabase_url}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "apikey": settings.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={"password": new_password}
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
            return {"message": "Hasło zostało zmienione pomyślnie"}
        except HTTPException:
            raise
        except Exception as e:
            raise ErrorHandler.handle_supabase_error(e, "change_password")

    @staticmethod
    async def change_email(session: Session, user: UserContext, supabase: Client, access_token: str, new_email: str) -> Dict[str, str]:
        if not supabase:
            raise HTTPException(status_code=503, detail="Authentication service not available")
        try:
            import httpx
            from settings import settings
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{settings.supabase_url}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "apikey": settings.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={"email": new_email}
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
            return {"message": "Email został zmieniony pomyślnie"}
        except HTTPException:
            raise
        except Exception as e:
            raise ErrorHandler.handle_supabase_error(e, "change_email")

    @staticmethod
    async def update_skill_level(session: Session, user: UserContext, skill_level: str) -> Dict[str, str]:
        def _update_skill_level(db_session: Session):
            query_user = select(User).where(User.user_id == user.user_id)
            user_record = db_session.exec(query_user).first()
            if not user_record:
                user_record = User(user_id=user.user_id, skill_level=skill_level)
                if user.is_guest:
                    from datetime import datetime
                    from services.user_context import calculate_guest_expiration
                    user_record.expires_at = calculate_guest_expiration()
                db_session.add(user_record)
            else:
                user_record.skill_level = skill_level
                if user.is_guest:
                    from datetime import datetime
                    from services.user_context import calculate_guest_expiration
                    user_record.expires_at = calculate_guest_expiration()
            db_session.commit()
        await asyncio.to_thread(_update_skill_level, session)
        return {"message": "Poziom zaawansowania został zaktualizowany", "skill_level": skill_level}

    @staticmethod
    async def delete_account(session: Session, user: UserContext, supabase: Optional[Client] = None) -> Dict[str, str]:
        user_id = user.user_id
        def _delete_user_data(db_session: Session):
            query_guns = select(Gun).where(Gun.user_id == user_id)
            guns = db_session.exec(query_guns).all()
            for gun in guns:
                query_attachments = select(Attachment).where(Attachment.gun_id == gun.id)
                attachments = db_session.exec(query_attachments).all()
                for attachment in attachments:
                    db_session.delete(attachment)
                query_maintenance = select(Maintenance).where(Maintenance.gun_id == gun.id)
                maintenance_list = db_session.exec(query_maintenance).all()
                for maintenance in maintenance_list:
                    db_session.delete(maintenance)
                db_session.delete(gun)
            query_ammo = select(Ammo).where(Ammo.user_id == user_id)
            ammo_list = db_session.exec(query_ammo).all()
            for ammo in ammo_list:
                db_session.delete(ammo)
            query_sessions = select(ShootingSession).where(ShootingSession.user_id == user_id)
            sessions = db_session.exec(query_sessions).all()
            for session_item in sessions:
                db_session.delete(session_item)
            query_accuracy = select(AccuracySession).where(AccuracySession.user_id == user_id)
            accuracy_sessions = db_session.exec(query_accuracy).all()
            for accuracy_session in accuracy_sessions:
                db_session.delete(accuracy_session)
            query_settings = select(UserSettings).where(UserSettings.user_id == user_id)
            settings = db_session.exec(query_settings).first()
            if settings:
                db_session.delete(settings)
            query_user = select(User).where(User.user_id == user_id)
            user_record = db_session.exec(query_user).first()
            if user_record:
                db_session.delete(user_record)
            db_session.commit()
        await asyncio.to_thread(_delete_user_data, session)
        if supabase:
            try:
                await asyncio.to_thread(supabase.auth.admin.delete_user, user_id)
            except Exception as e:
                raise ErrorHandler.handle_supabase_error(e, "delete_account")
        return {"message": "Konto zostało usunięte pomyślnie"}

