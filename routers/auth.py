from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client
import asyncio
from typing import Optional, Iterable, Union
from services.error_handler import ErrorHandler
from services.user_context import UserContext, UserRole, get_user_context_pure, _get_supabase_client
from settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

SUPABASE_URL = settings.supabase_url
SUPABASE_KEY = settings.supabase_anon_key

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "https://your-project-id.supabase.co":
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")
        supabase = None
else:
    print("Warning: Supabase credentials not configured. Authentication endpoints will be disabled.")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    username: str
    role: UserRole


class UserInfo(BaseModel):
    user_id: str
    role: UserRole

class RefreshRequest(BaseModel):
    refresh_token: str

def _resolve_role(metadata: Optional[dict]) -> UserRole:
    if not metadata:
        return UserRole.user
    value = metadata.get("role")
    if not value:
        return UserRole.user
    try:
        return UserRole(value)
    except ValueError:
        return UserRole.user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
    if not credentials:
        raise HTTPException(status_code=401, detail="Brak tokena uwierzytelniającego")
    supabase_client = supabase or _get_supabase_client()
    return await get_user_context_pure(credentials.credentials, supabase_client)


def role_required(allowed_roles: Iterable[Union[UserRole, str]]):
    normalized = set()
    for role in allowed_roles:
        if isinstance(role, UserRole):
            normalized.add(role)
        else:
            normalized.add(UserRole(role))
    async def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
        if not credentials:
            raise HTTPException(status_code=401, detail="Brak tokena uwierzytelniającego")
        supabase_client = supabase or _get_supabase_client()
        user = await get_user_context_pure(credentials.credentials, supabase_client)
        if user.role not in normalized:
            raise HTTPException(status_code=403, detail="Brak uprawnień do wykonania tej operacji")
        return user
    return dependency


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login user with email and password"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = await asyncio.to_thread(
            supabase.auth.sign_in_with_password,
            {
                "email": request.email,
                "password": request.password
            }
        )
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Nieprawidłowe dane logowania")
        user_metadata = response.user.user_metadata or {}
        username = user_metadata.get("username", request.email.split("@")[0])
        role = _resolve_role(user_metadata)
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
            username=username,
            role=role
        )
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.handle_supabase_error(e, "login")

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = await asyncio.to_thread(
            supabase.auth.sign_up,
            {
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "username": request.username,
                        "role": UserRole.user.value
                    }
                }
            }
        )
        if not response.user or not response.session:
            raise HTTPException(status_code=400, detail="Rejestracja nie powiodła się")
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
            username=request.username,
            role=UserRole.user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.handle_supabase_error(e, "register")

@router.post("/logout")
async def logout(current_user: UserContext = Depends(get_current_user)):
    """Logout user"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    try:
        await asyncio.to_thread(supabase.auth.sign_out)
        return {"message": "Wylogowano pomyślnie"}
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.handle_supabase_error(e, "logout")

@router.get("/me", response_model=UserInfo)
async def get_me(current_user: UserContext = Depends(get_current_user)):
    """Get current user info"""
    return UserInfo(
        user_id=current_user.user_id,
        role=current_user.role
    )

@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    """Refresh access token"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    try:
        response = await asyncio.to_thread(supabase.auth.refresh_session, data.refresh_token)
        if not response.session:
            raise HTTPException(status_code=401, detail="Nieprawidłowy refresh token")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.handle_supabase_error(e, "refresh_token")
