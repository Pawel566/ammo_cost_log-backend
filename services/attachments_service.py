from sqlmodel import Session, select
from typing import List
import asyncio
from datetime import datetime
from sqlalchemy import or_
from fastapi import HTTPException
from models import Attachment, Gun, AttachmentType
from services.user_context import UserContext, UserRole
from services.gun_service import GunService


class AttachmentsService:
    @staticmethod
    def _query_for_user(user: UserContext, gun_id: str):
        query = select(Attachment).where(Attachment.gun_id == gun_id)
        if user.role == UserRole.admin:
            return query
        query = query.where(Attachment.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Attachment.expires_at.is_(None), Attachment.expires_at > datetime.utcnow()))
        return query

    @staticmethod
    async def list_for_gun(session: Session, user: UserContext, gun_id: str) -> List[Attachment]:
        await GunService._get_single_gun(session, gun_id, user)
        query = AttachmentsService._query_for_user(user, gun_id)
        attachments = await asyncio.to_thread(lambda: session.exec(query).all())
        return list(attachments)

    @staticmethod
    async def create_attachment(session: Session, user: UserContext, gun_id: str, data: dict) -> Attachment:
        await GunService._get_single_gun(session, gun_id, user)
        attachment = Attachment(
            gun_id=gun_id,
            user_id=user.user_id,
            type=AttachmentType(data.get("type")),
            name=data.get("name"),
            notes=data.get("notes")
        )
        if user.is_guest:
            attachment.expires_at = user.expires_at
        session.add(attachment)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, attachment)
        return attachment

    @staticmethod
    async def _get_single_attachment(session: Session, attachment_id: str, user: UserContext) -> Attachment:
        query = select(Attachment).where(Attachment.id == attachment_id)
        if user.role != UserRole.admin:
            query = query.where(Attachment.user_id == user.user_id)
        if user.is_guest:
            query = query.where(or_(Attachment.expires_at.is_(None), Attachment.expires_at > datetime.utcnow()))
        attachment = await asyncio.to_thread(lambda: session.exec(query).first())
        if not attachment:
            raise HTTPException(status_code=404, detail="Załącznik nie został znaleziony")
        return attachment

    @staticmethod
    async def delete_attachment(session: Session, user: UserContext, attachment_id: str) -> dict:
        attachment = await AttachmentsService._get_single_attachment(session, attachment_id, user)
        await asyncio.to_thread(session.delete, attachment)
        await asyncio.to_thread(session.commit)
        return {"message": f"Załącznik o ID {attachment_id} został usunięty"}


