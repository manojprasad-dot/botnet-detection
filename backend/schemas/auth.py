"""
KOVIRX — Auth schemas.

Request / response models for authentication endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Requests ───────────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    role: str = "viewer"  # default role for self-registration


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Responses ──────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    
    # ── Extended Profile Fields ──
    full_name: str | None = None
    department: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    is_verified: bool = False
    must_change_password: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_password_change: datetime | None = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    avatar_url: str | None = None


class SessionResponse(BaseModel):
    id: UUID
    ip_address: str | None = None
    device_name: str | None = None
    browser: str | None = None
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class LoginAuditResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    login_time: datetime
    logout_time: datetime | None = None
    ip_address: str
    country: str | None = None
    city: str | None = None
    browser: str | None = None
    operating_system: str | None = None
    status: str
    failure_reason: str | None = None

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=128)
    role: str
    department: str | None = None
    full_name: str | None = None
    is_active: bool = True


class UserEditRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=64)
    role: str | None = None
    department: str | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None

