from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "operator"


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QRSessionResponse(BaseModel):
    session_id: str
    qr_payload: str
    expires_in_seconds: int = 120


class QRStatusResponse(BaseModel):
    session_id: str
    status: str  # pending, scanned, approved, expired
    token: Optional[Token] = None


class QRAuthorizeRequest(BaseModel):
    session_id: str
