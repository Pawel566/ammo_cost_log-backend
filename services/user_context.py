from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException
from supabase import Client, create_client
import asyncio
from uuid import uuid4
import base64
import json
from settings import settings


class UserRole(str, Enum):
    guest = "guest"
    user = "user"
    admin = "admin"


class UserContext(BaseModel):
    user_id: str
    role: UserRole
    is_guest: bool = False
    expires_at: Optional[datetime] = None


_supabase_client: Optional[Client] = None

def _get_supabase_client() -> Optional[Client]:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    if settings.supabase_url == "https://your-project-id.supabase.co":
        return None
    try:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)
        return _supabase_client
    except Exception:
        return None


def calculate_guest_expiration() -> datetime:
    ttl_hours = settings.guest_session_ttl_hours or 24
    return datetime.utcnow() + timedelta(hours=ttl_hours)


def _resolve_role_for_auth_only(metadata: Optional[dict]) -> UserRole:
    if not metadata:
        return UserRole.user
    value = metadata.get("role")
    if not value:
        return UserRole.user
    try:
        return UserRole(value)
    except ValueError:
        return UserRole.user


def _decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload_part = parts[1]
        padding = len(payload_part) % 4
        if padding:
            payload_part += '=' * (4 - padding)
        decoded = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")


def _extract_role_from_jwt(token: str) -> UserRole:
    payload = _decode_jwt_payload(token)
    role_value = payload.get("role")
    if not role_value:
        raise HTTPException(status_code=403, detail="Role claim missing from token")
    try:
        return UserRole(role_value)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Invalid role claim: {role_value}")


async def _validate_jwt_and_get_user(token: str, supabase: Optional[Client]) -> UserContext:
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    try:
        role = _extract_role_from_jwt(token)
        response = await asyncio.to_thread(supabase.auth.get_user, token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return UserContext(
            user_id=response.user.id,
            role=role,
            is_guest=False,
            expires_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        from services.error_handler import ErrorHandler
        raise ErrorHandler.handle_supabase_error(e, "get_user_context")


async def get_user_context_pure(
    token: Optional[str],
    supabase: Optional[Client] = None
) -> UserContext:
    if token:
        supabase_client = supabase or _get_supabase_client()
        return await _validate_jwt_and_get_user(token, supabase_client)
    
    guest_id = str(uuid4())
    expires_at = calculate_guest_expiration()
    return UserContext(
        user_id=guest_id,
        role=UserRole.guest,
        is_guest=True,
        expires_at=expires_at
    )

