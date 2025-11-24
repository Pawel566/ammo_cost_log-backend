import os
from supabase import create_client, Client
from settings import settings
from typing import Optional

SUPABASE_URL = settings.supabase_url
SUPABASE_SERVICE_ROLE_KEY = settings.supabase_service_role_key

BUCKET = "weapon-images"

supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase storage client: {e}")
        supabase = None
else:
    print("Warning: Supabase storage credentials not configured. Image upload will be disabled.")


def upload_weapon_image(user_uid: str, weapon_id: str, filename: str, file_bytes: bytes) -> str:
    """
    Upload weapon image to Supabase Storage.
    
    Args:
        user_uid: User UID from Supabase Auth
        weapon_id: Weapon ID
        filename: Original filename
        file_bytes: File content as bytes
    
    Returns:
        Storage path of uploaded image
    """
    if not supabase:
        raise ValueError("Supabase storage client not initialized")
    
    path = f"{user_uid}/weapons/{weapon_id}/{filename}"
    
    try:
        supabase.storage.from_(BUCKET).upload(path, file_bytes, file_options={"content-type": "image/jpeg"})
        return path
    except Exception as e:
        if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
            supabase.storage.from_(BUCKET).update(path, file_bytes, file_options={"content-type": "image/jpeg"})
            return path
        raise


def get_signed_image_url(path: str, expires: int = 3600) -> str:
    """
    Generate signed URL for weapon image.
    
    Args:
        path: Storage path of the image
        expires: Expiration time in seconds (default: 3600 = 1 hour)
    
    Returns:
        Signed URL string
    """
    if not supabase:
        raise ValueError("Supabase storage client not initialized")
    
    try:
        response = supabase.storage.from_(BUCKET).create_signed_url(path, expires)
        return response["signedURL"]
    except Exception as e:
        raise ValueError(f"Failed to generate signed URL: {str(e)}")




