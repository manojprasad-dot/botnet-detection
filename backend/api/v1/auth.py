from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.api.deps import get_current_user, require_admin, require_any_auth
from database.session import get_db
from database.models.user import User
from backend.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
    ResetPasswordRequest,
    UserUpdateRequest,
    SessionResponse,
    LoginAuditResponse,
    UserCreateRequest,
    UserEditRequest,
)
from backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await auth_service.register_user(
        db, email=data.email, username=data.username,
        password=data.password, role=data.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    user_agent: str = Header("Unknown", alias="User-Agent"),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and receive access and refresh JWT tokens."""
    ip_address = request.client.host if request.client else "127.0.0.1"
    return await auth_service.authenticate_user(
        db, email=data.email, password=data.password,
        ip_address=ip_address, user_agent=user_agent
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshTokenRequest,
    request: Request,
    user_agent: str = Header("Unknown", alias="User-Agent"),
    db: AsyncSession = Depends(get_db)
):
    """Exchange a refresh token for a new access and rotated refresh token."""
    ip_address = request.client.host if request.client else "127.0.0.1"
    return await auth_service.refresh_access_token(
        db, refresh_token=data.refresh_token,
        ip_address=ip_address, user_agent=user_agent
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log out of the current session."""
    # Try to extract the refresh token from request header if possible to revoke it
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Since access token is stateless, we revoke all/current active refresh tokens for safety
        await auth_service.revoke_all_sessions(db, user_id=current_user.id)
    return MessageResponse(message="Logged out successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    await auth_service.change_user_password(
        db, user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link."""
    msg = await auth_service.forgot_password(db, email=data.email)
    return MessageResponse(message=msg)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token."""
    await auth_service.reset_user_password(db, token=data.token, new_password=data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile details."""
    return await auth_service.get_user_by_id(db, user_id=current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile parameters: full name, phone, department, avatar."""
    updated = await auth_service.update_profile(
        db, user_id=current_user.id,
        full_name=data.full_name, phone=data.phone,
        department=data.department, avatar_url=data.avatar_url
    )
    return updated


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active login sessions."""
    tokens = await auth_service.get_active_sessions(db, user_id=current_user.id)
    return tokens


@router.delete("/sessions/{id}", response_model=MessageResponse)
async def revoke_session(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a single active login session."""
    from uuid import UUID
    await auth_service.revoke_session(db, user_id=current_user.id, session_id=UUID(id))
    return MessageResponse(message="Session revoked successfully")


@router.delete("/sessions", response_model=MessageResponse)
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all active sessions (force logout of all devices)."""
    await auth_service.revoke_all_sessions(db, user_id=current_user.id)
    return MessageResponse(message="All sessions revoked successfully")


# ── Super Admin Panel Endpoints ────────────────────────────────────

@router.get("/admin/users", response_model=List[UserResponse])
async def admin_get_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin: list all registered users."""
    return await auth_service.admin_list_users(db)


@router.post("/admin/users", response_model=UserResponse, status_code=201)
async def admin_create_user(
    data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin: provision a new user with role assignments."""
    return await auth_service.admin_create_user(
        db, username=data.username, email=data.email,
        password=data.password, role=data.role,
        department=data.department, full_name=data.full_name
    )


@router.put("/admin/users/{id}", response_model=UserResponse)
async def admin_edit_user(
    id: str,
    data: UserEditRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin: edit a user's details or deactivate account."""
    from uuid import UUID
    return await auth_service.admin_edit_user(
        db, user_id=UUID(id), username=data.username,
        email=data.email, role=data.role,
        department=data.department, full_name=data.full_name,
        phone=data.phone, is_active=data.is_active
    )


@router.post("/admin/users/{id}/unlock", response_model=UserResponse)
async def admin_unlock_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin: unlock a locked-out account."""
    from uuid import UUID
    return await auth_service.admin_unlock_user(db, user_id=UUID(id))


@router.get("/admin/audit-logs", response_model=List[LoginAuditResponse])
async def admin_get_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Admin: view all user login histories."""
    return await auth_service.admin_view_login_history(db)
