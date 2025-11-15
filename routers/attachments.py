from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from schemas.attachment import AttachmentCreate, AttachmentRead
from database import get_session
from routers.auth import role_required
from services.attachments_service import AttachmentsService
from services.user_context import UserContext, UserRole

router = APIRouter()

@router.get("/guns/{gun_id}/attachments", response_model=List[AttachmentRead])
async def get_gun_attachments(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.list_for_gun(session, user, gun_id)

@router.post("/guns/{gun_id}/attachments", response_model=AttachmentRead)
async def add_attachment(
    gun_id: str,
    attachment_data: AttachmentCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.create_attachment(session, user, gun_id, attachment_data.model_dump())

@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await AttachmentsService.delete_attachment(session, user, attachment_id)

