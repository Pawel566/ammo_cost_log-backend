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

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str  # Recovery token from URL (hash token from Supabase email)
    password: str

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

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Supabase automatically sends password reset email
        response = await asyncio.to_thread(
            supabase.auth.reset_password_for_email,
            request.email,
            {
                "redirect_to": f"{settings.frontend_url or 'http://localhost:5173'}/reset-password"
            }
        )
        # Supabase doesn't return error if email doesn't exist (security)
        return {"message": "Jeśli podany adres email istnieje w systemie, otrzymasz wiadomość z linkiem do resetowania hasła."}
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.handle_supabase_error(e, "forgot_password")

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using recovery token from URL"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Supabase recovery tokens are in the format: access_token#refresh_token
        # We need to extract the access_token and verify it
        # The token from URL hash is the full recovery token
        
        # Try to verify the token by exchanging it for a session
        # Supabase recovery tokens need to be exchanged for a session first
        temp_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Parse the token - Supabase recovery tokens can be in format: access_token#refresh_token
        # or just access_token
        token_parts = request.token.split('#')
        access_token = token_parts[0]
        refresh_token = token_parts[1] if len(token_parts) > 1 else None
        
        # Try to set session with the recovery token
        session_data = {"access_token": access_token}
        if refresh_token:
            session_data["refresh_token"] = refresh_token
        
        try:
            session_response = await asyncio.to_thread(
                temp_client.auth.set_session,
                session_data
            )
            
            if not session_response.session:
                raise HTTPException(status_code=401, detail="Nieprawidłowy token resetowania hasła")
            
            # Get user from session
            user_id = session_response.session.user.id
            
            # Use service_role_key if available for admin operations (preferred)
            if settings.supabase_service_role_key:
                admin_client = create_client(SUPABASE_URL, settings.supabase_service_role_key)
                admin_response = await asyncio.to_thread(
                    admin_client.auth.admin.update_user_by_id,
                    user_id,
                    {"password": request.password}
                )
                if admin_response.user:
                    return {"message": "Hasło zostało pomyślnie zresetowane"}
                else:
                    raise HTTPException(status_code=400, detail="Nie udało się zresetować hasła")
            else:
                # Fallback: use the session to update password
                update_response = await asyncio.to_thread(
                    temp_client.auth.update_user,
                    {"password": request.password}
                )
                
                if update_response.user:
                    return {"message": "Hasło zostało pomyślnie zresetowane"}
                else:
                    raise HTTPException(status_code=400, detail="Nie udało się zresetować hasła")
        except Exception as session_error:
            # If setting session fails, the token is invalid
            raise HTTPException(
                status_code=401,
                detail="Nieprawidłowy lub wygasły token resetowania hasła. Poproś o nowy link."
            )
    except HTTPException:
        raise
    except Exception as e:
        # Check if it's a session/token error
        error_msg = str(e).lower()
        if "session" in error_msg or "token" in error_msg or "invalid" in error_msg or "expired" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Nieprawidłowy lub wygasły token resetowania hasła. Poproś o nowy link."
            )
        raise ErrorHandler.handle_supabase_error(e, "reset_password")
