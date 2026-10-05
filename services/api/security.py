import jwt
from typing import Set
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from packages.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    "ADMIN": {"cases:read", "cases:write", "review:write", "admin:read", "audit:read"},
    "SUPERVISOR": {"cases:read", "cases:write", "review:write", "audit:read"},
    "RESPONDER": {"cases:read", "cases:write", "review:write"},
    "AUDITOR": {"cases:read", "audit:read"},
}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Validates JWT token and returns decoded user payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(*roles: str):
    """FastAPI dependency factory for role-based access control."""
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role")
        if not user_role or user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required one of: {', '.join(roles)}"
            )
        return user
    return role_checker
