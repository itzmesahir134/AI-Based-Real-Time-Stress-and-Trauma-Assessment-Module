from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from packages.config import get_settings
from packages.schemas import TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# Hardcoded users for SIH demo prototype
DEMO_USERS = {
    "admin": {"password": "saathi-admin-2026", "role": "ADMIN"},
    "responder": {"password": "saathi-resp-2026", "role": "RESPONDER"},
    "supervisor": {"password": "saathi-super-2026", "role": "SUPERVISOR"},
    "auditor": {"password": "saathi-audit-2026", "role": "AUDITOR"},
}

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    settings = get_settings()
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DEMO_USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": form_data.username, "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
