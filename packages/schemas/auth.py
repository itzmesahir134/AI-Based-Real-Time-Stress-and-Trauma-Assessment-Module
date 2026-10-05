from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    role: str = Field(..., description="User role (e.g., ADMIN, RESPONDER)")
    expires_in: int = Field(..., description="Token expiration in seconds")

class UserResponse(BaseModel):
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")
