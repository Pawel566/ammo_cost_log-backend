from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlmodel import Session
from typing import Optional
from schemas.gun import GunCreate, GunRead
from schemas.pagination import PaginatedResponse
from models import GunUpdate
from database import get_session
from routers.auth import role_required
from services.gun_service import GunService
from services.user_context import UserContext, UserRole
from services.supabase_service import upload_weapon_image, get_signed_image_url
import asyncio

router = APIRouter()

@router.get("", response_model=PaginatedResponse[GunRead])
async def get_guns(
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin])),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1)
):
    return await GunService.get_all_guns(session, user, limit, offset, search)

@router.post("", response_model=GunRead)
async def add_gun(
    gun_data: GunCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.create_gun(session, gun_data, user)

@router.post("/{gun_id}/upload-image")
async def upload_weapon_image_endpoint(
    gun_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.user, UserRole.admin]))
):
    """
    Upload weapon image to Supabase Storage.
    Only authenticated users (not guests) can upload images.
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Goście nie mogą dodawać zdjęć")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Plik musi być obrazem")
    
    gun = await GunService._get_single_gun(session, gun_id, user)
    
    if gun.user_id != user.user_id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień do tej broni")
    
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Plik jest zbyt duży (max 10MB)")
    
    filename = file.filename or f"image_{gun_id}.jpg"
    
    try:
        image_path = await asyncio.to_thread(
            upload_weapon_image,
            user.user_id,
            gun_id,
            filename,
            file_bytes
        )
        
        gun.image_path = image_path
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        
        return {"image_path": image_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas przesyłania zdjęcia: {str(e)}")

@router.get("/{gun_id}/image")
async def get_weapon_image(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    """
    Get signed URL for weapon image.
    Returns null if no image is uploaded.
    """
    gun = await GunService._get_single_gun(session, gun_id, user)
    
    if not gun.image_path:
        return {"url": None}
    
    try:
        signed_url = await asyncio.to_thread(get_signed_image_url, gun.image_path)
        return {"url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania URL: {str(e)}")

@router.get("/{gun_id}", response_model=GunRead)
async def get_gun(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.get_gun_by_id(session, gun_id, user)

@router.put("/{gun_id}", response_model=GunRead)
async def update_gun(
    gun_id: str,
    gun_data: GunUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.update_gun(session, gun_id, gun_data, user)

@router.delete("/{gun_id}")
async def delete_gun(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.delete_gun(session, gun_id, user)