from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlmodel import Session
from typing import Optional, Dict
from schemas.gun import GunCreate, GunRead
from schemas.pagination import PaginatedResponse
from models import GunUpdate
from database import get_session
from routers.auth import role_required
from services.gun_service import GunService
from services.user_context import UserContext, UserRole
from services.exceptions import BadRequestError
import asyncio

# Import Supabase service functions only when needed to avoid import errors
try:
    from services.supabase_service import upload_weapon_image, get_signed_image_url, delete_weapon_image
except ImportError:
    # If Supabase is not available, define stub functions
    def upload_weapon_image(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")
    
    def get_signed_image_url(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")
    
    def delete_weapon_image(*args, **kwargs):
        raise ValueError("Supabase storage is not configured")

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

@router.get("/{gun_id}", response_model=GunRead)
async def get_gun(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.get_gun_by_id(session, gun_id, user)

@router.post("", response_model=GunRead)
async def add_gun(
    gun_data: GunCreate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.create_gun(session, gun_data, user)

@router.put("/{gun_id}", response_model=GunRead)
async def update_gun(
    gun_id: str,
    gun_data: GunUpdate,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.update_gun(session, gun_id, gun_data, user)

@router.delete("/{gun_id}", response_model=Dict[str, str])
async def delete_gun(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    return await GunService.delete_gun(session, gun_id, user)

@router.post("/{gun_id}/image")
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
        raise BadRequestError("Plik musi być obrazem")
    
    gun = await GunService._get_single_gun(session, gun_id, user)
    
    if gun.user_id != user.user_id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień do tej broni")
    
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:
        raise BadRequestError("Plik jest zbyt duży (max 10MB)")
    
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
    except ValueError as e:
        # Jeśli Supabase nie jest skonfigurowane
        raise HTTPException(status_code=503, detail="Usługa przechowywania zdjęć nie jest dostępna. Skonfiguruj Supabase Storage.")

@router.get("/{gun_id}/image")
async def get_weapon_image(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.guest, UserRole.user, UserRole.admin]))
):
    """
    Get signed URL for weapon image.
    Returns null if no image is uploaded or if Supabase is not configured.
    """
    try:
        gun = await GunService._get_single_gun(session, gun_id, user)
        
        if not gun.image_path:
            return {"url": None}
        
        try:
            signed_url = await asyncio.to_thread(get_signed_image_url, gun.image_path)
            return {"url": signed_url}
        except (ValueError, Exception) as e:
            # Jeśli Supabase nie jest skonfigurowane lub wystąpił błąd, zwróć null zamiast błędu
            print(f"Warning: Could not generate signed URL: {e}")
            return {"url": None}
    except Exception as e:
        # Jeśli nie można pobrać broni, zwróć null zamiast błędu
        print(f"Warning: Could not get weapon image: {e}")
        return {"url": None}

@router.delete("/{gun_id}/image")
async def delete_weapon_image_endpoint(
    gun_id: str,
    session: Session = Depends(get_session),
    user: UserContext = Depends(role_required([UserRole.user, UserRole.admin]))
):
    """
    Delete weapon image from Supabase Storage.
    Only authenticated users (not guests) can delete images.
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Goście nie mogą usuwać zdjęć")
    
    gun = await GunService._get_single_gun(session, gun_id, user)
    
    if gun.user_id != user.user_id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Brak uprawnień do tej broni")
    
    if not gun.image_path:
        return {"message": "Brak zdjęcia do usunięcia"}
    
    try:
        await asyncio.to_thread(delete_weapon_image, gun.image_path)
        
        gun.image_path = None
        session.add(gun)
        await asyncio.to_thread(session.commit)
        await asyncio.to_thread(session.refresh, gun)
        
        return {"message": "Zdjęcie zostało usunięte"}
    except ValueError as e:
        # Jeśli Supabase nie jest skonfigurowane
        raise HTTPException(status_code=503, detail="Usługa przechowywania zdjęć nie jest dostępna")