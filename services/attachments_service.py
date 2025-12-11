from sqlmodel import Session, select
from typing import List
from models import Attachment, Gun, AttachmentType
from services.user_context import UserContext, UserRole
from services.gun_service import GunService
from services.exceptions import NotFoundError, BadRequestError


class AttachmentsService:
    @staticmethod
    def _get_allowed_attachment_types(gun_type: str) -> List[AttachmentType]:
        """Zwraca listę dozwolonych typów dodatków dla danego typu broni"""
        if not gun_type:
            return list(AttachmentType)
        
        normalized_type = gun_type.lower().strip()
        
        # Pistolet
        if normalized_type == 'pistol' or normalized_type == 'pistolet' or 'broń krótka' in normalized_type:
            return [
                AttachmentType.red_dot,
                AttachmentType.reflex,
                AttachmentType.compensator,
                AttachmentType.suppressor,
                AttachmentType.tactical_light
            ]
        # Pistolet maszynowy (PCC, PM, PDW)
        elif 'pistolet maszynowy' in normalized_type or 'pcc' in normalized_type or 'pm' in normalized_type or 'pdw' in normalized_type:
            return [
                AttachmentType.red_dot,
                AttachmentType.reflex,
                AttachmentType.lpvo,
                AttachmentType.magnifier,
                AttachmentType.suppressor,
                AttachmentType.compensator,
                AttachmentType.foregrip,
                AttachmentType.angled_grip,
                AttachmentType.tactical_light
            ]
        # Karabinek (AR-15, AK, Grot, SIG MCX)
        elif normalized_type == 'karabinek' or normalized_type == 'carbine' or 'ar-15' in normalized_type or 'ak' in normalized_type or 'grot' in normalized_type or 'mcx' in normalized_type:
            return [
                AttachmentType.red_dot,
                AttachmentType.reflex,
                AttachmentType.lpvo,
                AttachmentType.magnifier,
                AttachmentType.suppressor,
                AttachmentType.compensator,
                AttachmentType.foregrip,
                AttachmentType.angled_grip,
                AttachmentType.bipod,
                AttachmentType.tactical_light
            ]
        # Karabin (długa broń precyzyjna, bolt-action, DMR)
        elif normalized_type == 'rifle' or normalized_type == 'karabin' or 'bolt-action' in normalized_type or 'dmr' in normalized_type or 'precyzyjna' in normalized_type:
            return [
                AttachmentType.lpvo,
                AttachmentType.red_dot,
                AttachmentType.suppressor,
                AttachmentType.compensator,
                AttachmentType.bipod
            ]
        # Strzelba (Shotgun)
        elif normalized_type == 'shotgun' or normalized_type == 'strzelba':
            return [
                AttachmentType.red_dot,
                AttachmentType.reflex,
                AttachmentType.compensator,
                AttachmentType.suppressor,
                AttachmentType.tactical_light
            ]
        # Rewolwer
        elif normalized_type == 'rewolwer' or normalized_type == 'revolver':
            return [
                AttachmentType.red_dot,
                AttachmentType.reflex,
                AttachmentType.compensator,
                AttachmentType.tactical_light
            ]
        # Inna - wszystkie typy dozwolone
        else:
            return list(AttachmentType)
    
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
        gun = GunService._get_single_gun(session, gun_id, user)
        attachment_type = AttachmentType(data.get("type"))
        
        # Walidacja: sprawdź czy typ dodatku jest dozwolony dla typu broni
        allowed_types = AttachmentsService._get_allowed_attachment_types(gun.type or "")
        if attachment_type not in allowed_types:
            gun_type_display = gun.type or "nieokreślony"
            raise BadRequestError(
                f"Typ dodatku '{attachment_type.value}' nie jest dozwolony dla broni typu '{gun_type_display}'. "
                f"Dozwolone typy: {', '.join([t.value for t in allowed_types])}"
            )
        
        # Walidacja wartości dla precision_help, recoil_reduction, ergonomics
        allowed_values = ["none", "low", "medium", "high"]
        precision_help = data.get("precision_help", "none")
        recoil_reduction = data.get("recoil_reduction", "none")
        ergonomics = data.get("ergonomics", "none")
        
        if precision_help not in allowed_values:
            raise BadRequestError(f"precision_help musi być jedną z wartości: {', '.join(allowed_values)}")
        if recoil_reduction not in allowed_values:
            raise BadRequestError(f"recoil_reduction musi być jedną z wartości: {', '.join(allowed_values)}")
        if ergonomics not in allowed_values:
            raise BadRequestError(f"ergonomics musi być jedną z wartości: {', '.join(allowed_values)}")
        
        attachment = Attachment(
            gun_id=gun_id,
            user_id=user.user_id,
            type=attachment_type,
            name=data.get("name"),
            notes=data.get("notes"),
            precision_help=precision_help,
            recoil_reduction=recoil_reduction,
            ergonomics=ergonomics
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
    def get_attachment_by_id(session: Session, user: UserContext, attachment_id: str) -> Attachment:
        return AttachmentsService._get_single_attachment(session, attachment_id, user)

    @staticmethod
    def delete_attachment(session: Session, user: UserContext, attachment_id: str) -> dict:
        attachment = AttachmentsService._get_single_attachment(session, attachment_id, user)
        session.delete(attachment)
        session.commit()
        return {"message": f"Załącznik o ID {attachment_id} został usunięty"}


