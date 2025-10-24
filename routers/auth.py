from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase client only if credentials are provided
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

class UserInfo(BaseModel):
    user_id: str
    email: str
    username: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Verify JWT token and return user info"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        token = credentials.credentials
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user metadata for username
        user_metadata = response.user.user_metadata or {}
        username = user_metadata.get('username', response.user.email.split('@')[0])
        
        return UserInfo(
            user_id=response.user.id,
            email=response.user.email,
            username=username
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login user with email and password"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get username from user metadata
        user_metadata = response.user.user_metadata or {}
        username = user_metadata.get('username', request.email.split('@')[0])
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
            username=username
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username
                }
            }
        })
        
        if not response.user or not response.session:
            raise HTTPException(status_code=400, detail="Registration failed")
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
            username=request.username
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Registration failed")

@router.post("/logout")
async def logout():
    """Logout user"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Logout failed")

@router.get("/me", response_model=UserInfo)
async def get_me(current_user: UserInfo = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = supabase.auth.refresh_session(refresh_token)
        
        if not response.session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
