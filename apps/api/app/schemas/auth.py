from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google JWT ID Token


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_locale: Optional[str] = None  # "vi" | "en"
    theme: Optional[str] = None  # "light" | "dark" | "system"
    document_language: Optional[str] = None  # "vi" | "en" | "auto"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    name: str
    avatar: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_locale: str = "vi"
    theme: str = "system"
    document_language: str = "vi"
    plan: str = "pro"
    role: str = "user"
    is_active: bool = True
    google_sub: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
