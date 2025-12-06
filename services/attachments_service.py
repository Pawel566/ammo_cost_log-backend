from sqlmodel import Session, select
from typing import List
from models import Attachment, Gun, AttachmentType
from services.user_context import UserContext, UserRole
from services.gun_service import GunService
from services.exceptions import NotFoundError


class AttachmentsService:
    @staticmethod
    def _query_for_user(user: UserContext, gun_id: str):
        query = select(Attachment).where(Attachment.gun_id == gun_id)
        if user.role == UserRole.admin:
            return query
        query = query.where(Attachment.user_id == user.user_id)
        return query

    @staticmethod
    def list_for_gun(session: Session, user: UserContext, gun_id: str) -> List[Attachment]:
        GunService._get_single_gun(session, gun_id, user)
        query = AttachmentsService._query_for_user(user, gun_id)
        attachments = session.exec(query).all()
        return list(attachments)

    @staticmethod
    def create_attachment(session: Session, user: UserContext, gun_id: str, data: dict) -> Attachment:
        GunService._get_single_gun(session, gun_id, user)
        attachment = Attachment(
            gun_id=gun_id,
            user_id=user.user_id,
            type=AttachmentType(data.get("type")),
            name=data.get("name"),
            notes=data.get("notes")
        )
        session.add(attachment)
        session.commit()
        session.refresh(attachment)
        return attachment

    @staticmethod
    def _get_single_attachment(session: Session, attachment_id: str, user: UserContext) -> Attachment:
        query = select(Attachment).where(Attachment.id == attachment_id)
        if user.role != UserRole.admin:
            query = query.where(Attachment.user_id == user.user_id)
        attachment = session.exec(query).first()
        if not attachment:
            raise NotFoundError("Załącznik nie został znaleziony")
        return attachment

    @staticmethod
    def delete_attachment(session: Session, user: UserContext, attachment_id: str) -> dict:
        attachment = AttachmentsService._get_single_attachment(session, attachment_id, user)
        session.delete(attachment)
        session.commit()
        return {"message": f"Załącznik o ID {attachment_id} został usunięty"}


