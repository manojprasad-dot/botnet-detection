"""
KOVIRX — Authentication service.

Handles user registration, login, token lifecycle, and password management.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from datetime import datetime, timezone
from uuid import UUID

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException, CredentialsException, NotFoundException
from backend.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from database.models.user import User, UserRole
from database.repositories.user import user_repository
from backend.schemas.auth import TokenResponse, UserResponse

logger = logging.getLogger("kovirx.auth")


async def register_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    role: str = "viewer",
) -> UserResponse:
    """Register a new user account."""
    # Check for existing email / username
    existing_email = await user_repository.get_by_email(db, email)
    existing_username = await user_repository.get_by_username(db, username)
    if existing_email or existing_username:
        raise ConflictException("User with this email or username already exists")

    user_data = {
        "email": email,
        "username": username,
        "hashed_password": hash_password(password),
        "role": UserRole(role) if role in UserRole.__members__ else UserRole.viewer,
    }
    user = await user_repository.create(db, obj_in=user_data)
    await db.refresh(user)
    logger.info("User registered: %s (%s)", username, email)
    return UserResponse.model_validate(user)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    user = await user_repository.get_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        raise CredentialsException("Invalid email or password")

    if not user.is_active:
        raise CredentialsException("Account is disabled")

    # Update last login
    await user_repository.update(db, db_obj=user, obj_in={"last_login_at": datetime.now(timezone.utc)})

    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    logger.info("User logged in: %s", user.username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise CredentialsException("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise CredentialsException("Token is not a refresh token")

    user_id = payload.get("sub")
    user = await user_repository.get(db, UUID(user_id))

    if not user or not user.is_active:
        raise CredentialsException("User not found or disabled")

    token_data = {"sub": str(user.id), "role": user.role.value}
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


async def change_user_password(
    db: AsyncSession,
    user_id: UUID,
    current_password: str,
    new_password: str,
) -> None:
    """Change password for the authenticated user."""
    user = await user_repository.get(db, user_id)

    if not user:
        raise NotFoundException("User")

    if not verify_password(current_password, user.hashed_password):
        raise CredentialsException("Current password is incorrect")

    await user_repository.update(db, db_obj=user, obj_in={"hashed_password": hash_password(new_password)})
    logger.info("Password changed for user: %s", user.username)


async def forgot_password(db: AsyncSession, email: str) -> str:
    """
    Generate a password-reset token.
    In development, the token is returned directly (logged to console).
    In production, this would send an email.
    """
    user = await user_repository.get_by_email(db, email)

    # Always return success to prevent email enumeration
    if not user:
        logger.warning("Password reset requested for unknown email: %s", email)
        return "If the email exists, a reset link has been sent."

    token = create_password_reset_token(email)
    # DEV: Log token to console instead of sending email
    logger.info("PASSWORD RESET TOKEN for %s: %s", email, token)
    return "If the email exists, a reset link has been sent."


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> UserResponse:
    """Return a user profile by ID."""
    user = await user_repository.get(db, user_id)
    if not user:
        raise NotFoundException("User")
    return UserResponse.model_validate(user)


async def seed_superadmin(db: AsyncSession, email: str, password: str) -> None:
    """Create the first super-admin if no users exist."""
    users = await user_repository.get_multi(db, limit=1)
    if users:
        return  # Users already exist, skip seeding

    admin_data = {
        "email": email,
        "username": "admin",
        "hashed_password": hash_password(password),
        "role": UserRole.super_admin,
        "is_active": True,
    }
    await user_repository.create(db, obj_in=admin_data)
    logger.info("Seeded super-admin: %s", email)
