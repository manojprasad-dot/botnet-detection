import logging
import hashlib
import re
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List, Tuple

from jose import JWTError
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ConflictException, CredentialsException, NotFoundException, PermissionDeniedException
from backend.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    password_needs_rehash,
    validate_password_strength,
)
from database.models.user import User, UserRole
from database.repositories.user import user_repository
from database.models.refresh_token import RefreshToken
from database.models.login_audit import LoginAudit
from database.models.password_history import UserPasswordHistory
from backend.schemas.auth import TokenResponse, UserResponse

logger = logging.getLogger("kovirx.auth")


def hash_token(token: str) -> str:
    """Hash token for database storage using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def parse_user_agent(ua: str) -> Tuple[str, str]:
    """Parse user agent into browser and OS."""
    ua_lower = ua.lower() if ua else ""
    # Browser
    if "chrome" in ua_lower: browser = "Chrome"
    elif "firefox" in ua_lower: browser = "Firefox"
    elif "safari" in ua_lower: browser = "Safari"
    elif "edge" in ua_lower: browser = "Edge"
    else: browser = "Unknown Browser"
    
    # OS
    if "windows" in ua_lower: os = "Windows"
    elif "macintosh" in ua_lower or "mac os" in ua_lower: os = "macOS"
    elif "linux" in ua_lower: os = "Linux"
    elif "android" in ua_lower: os = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower: os = "iOS"
    else: os = "Unknown OS"
    return browser, os


async def check_account_lock(db: AsyncSession, user: User) -> None:
    """Raise CredentialsException if account is locked."""
    if user.locked_until:
        if user.locked_until.tzinfo is None:
            user_locked_until = user.locked_until.replace(tzinfo=timezone.utc)
        else:
            user_locked_until = user.locked_until
            
        if user_locked_until > datetime.now(timezone.utc):
            diff = int((user_locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise CredentialsException(f"Account is locked. Try again after {max(1, diff)} minute(s).")
        else:
            # Lock has expired
            user.locked_until = None
            user.failed_login_attempts = 0
            await db.commit()


async def register_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    role: str = "read_only",
) -> UserResponse:
    """Register a new user account."""
    # Check password strength
    try:
        validate_password_strength(password)
    except ValueError as e:
        raise ConflictException(str(e))

    existing_email = await user_repository.get_by_email(db, email)
    existing_username = await user_repository.get_by_username(db, username)
    if existing_email or existing_username:
        raise ConflictException("User with this email or username already exists")

    user_role = UserRole(role) if role in UserRole.__members__ else UserRole.read_only

    user_data = {
        "email": email,
        "username": username,
        "hashed_password": hash_password(password),
        "role": user_role,
        "is_active": True,
        "last_password_change": datetime.now(timezone.utc),
    }
    user = await user_repository.create(db, obj_in=user_data)
    await db.refresh(user)

    # Record in password history
    hist = UserPasswordHistory(user_id=user.id, password_hash=user.hashed_password)
    db.add(hist)
    await db.commit()

    logger.info("User registered: %s (%s)", username, email)
    return UserResponse.model_validate(user)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: str = "127.0.0.1",
    user_agent: str = "Unknown",
) -> TokenResponse:
    """Authenticate user and return JWT tokens with login auditing and lockout enforcement."""
    browser, os = parse_user_agent(user_agent)
    user = await user_repository.get_by_email(db, email)

    if not user:
        # Audit login failure
        audit = LoginAudit(
            user_id=None,
            login_time=datetime.now(timezone.utc),
            ip_address=ip_address,
            browser=browser,
            operating_system=os,
            status="failed",
            failure_reason="User email not found"
        )
        db.add(audit)
        await db.commit()
        raise CredentialsException("Invalid email or password")

    # Check account lock
    await check_account_lock(db, user)

    if not user.is_active:
        raise CredentialsException("Account is disabled")

    # Verify password
    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            status = "locked"
            reason = "Account locked due to 5 failed attempts"
            logger.warning("User locked out: %s", user.username)
        else:
            status = "failed"
            reason = "Invalid credentials"

        audit = LoginAudit(
            user_id=user.id,
            login_time=datetime.now(timezone.utc),
            ip_address=ip_address,
            browser=browser,
            operating_system=os,
            status=status,
            failure_reason=reason
        )
        db.add(audit)
        await db.commit()
        raise CredentialsException("Invalid email or password")

    # Success: Reset failed attempts, check if rehash needed
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)

    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Save Refresh Token hashed
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        ip_address=ip_address,
        browser=browser,
        device_name=os,
        revoked=False
    )
    db.add(rt)

    # Log successful audit
    audit = LoginAudit(
        user_id=user.id,
        login_time=datetime.now(timezone.utc),
        ip_address=ip_address,
        browser=browser,
        operating_system=os,
        status="success"
    )
    db.add(audit)
    await db.commit()

    logger.info("User logged in: %s", user.username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
    ip_address: str = "127.0.0.1",
    user_agent: str = "Unknown",
) -> TokenResponse:
    """Exchange a valid refresh token for a rotated token pair."""
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

    # Find token in DB
    h = hash_token(refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == h, RefreshToken.revoked == False))
    db_token = result.scalar_one_or_none()

    if not db_token:
        # Potential token reuse attack! Revoke all tokens for user.
        await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
        results = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
        for r in results.scalars():
            r.revoked = True
        await db.commit()
        raise CredentialsException("Token has already been used or revoked. Revoking all sessions.")

    # Revoke current token
    db_token.revoked = True

    # Generate new pair
    token_data = {"sub": str(user.id), "role": user.role.value}
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)

    # Save new refresh token
    browser, os = parse_user_agent(user_agent)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        expires_at=expires_at,
        ip_address=ip_address,
        browser=browser,
        device_name=os,
        revoked=False
    )
    db.add(rt)
    await db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


async def change_user_password(
    db: AsyncSession,
    user_id: UUID,
    current_password: str,
    new_password: str,
) -> None:
    """Change password for user, enforcing password policies and preventing password history reuse."""
    user = await user_repository.get(db, user_id)

    if not user:
        raise NotFoundException("User")

    if not verify_password(current_password, user.hashed_password):
        raise CredentialsException("Current password is incorrect")

    # Validate new password strength
    validate_password_strength(new_password)

    # Check password history (prevent reuse of last 5 passwords)
    result = await db.execute(
        select(UserPasswordHistory)
        .where(UserPasswordHistory.user_id == user_id)
        .order_by(desc(UserPasswordHistory.created_at))
        .limit(5)
    )
    history = result.scalars().all()
    for h in history:
        if verify_password(new_password, h.password_hash):
            raise ConflictException("Password has been used recently. Please choose a different one.")

    # Save new hash
    new_hash = hash_password(new_password)
    user.hashed_password = new_hash
    user.must_change_password = False
    user.last_password_change = datetime.now(timezone.utc)

    # Record history
    hist = UserPasswordHistory(user_id=user_id, password_hash=new_hash)
    db.add(hist)
    await db.commit()

    logger.info("Password changed for user: %s", user.username)


async def forgot_password(db: AsyncSession, email: str) -> str:
    """Generate password reset token."""
    user = await user_repository.get_by_email(db, email)
    if not user:
        logger.warning("Password reset requested for unknown email: %s", email)
        return "If the email exists, a reset token has been generated."

    token = create_password_reset_token(email)
    logger.info("PASSWORD RESET TOKEN for %s: %s", email, token)
    return f"If the email exists, a reset token has been generated. Token: {token}"


async def reset_user_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Reset user password using token."""
    try:
        payload = decode_token(token)
    except JWTError:
        raise CredentialsException("Invalid or expired reset token")

    if payload.get("purpose") != "password_reset":
        raise CredentialsException("Invalid token type")

    email = payload.get("sub")
    user = await user_repository.get_by_email(db, email)
    if not user:
        raise NotFoundException("User")

    # Validate strength
    validate_password_strength(new_password)

    # Update password
    new_hash = hash_password(new_password)
    user.hashed_password = new_hash
    user.must_change_password = False
    user.last_password_change = datetime.now(timezone.utc)

    hist = UserPasswordHistory(user_id=user.id, password_hash=new_hash)
    db.add(hist)
    await db.commit()

    logger.info("Password reset successfully for user: %s", user.username)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> UserResponse:
    """Return user profile by ID."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("User")
    return UserResponse.model_validate(user)


async def get_active_sessions(db: AsyncSession, user_id: UUID) -> List[RefreshToken]:
    """Retrieve active sessions for a user."""
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False, RefreshToken.expires_at > datetime.now(timezone.utc))
        .order_by(desc(RefreshToken.created_at))
    )
    return list(result.scalars().all())


async def revoke_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> None:
    """Revoke a single active session."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.id == session_id, RefreshToken.user_id == user_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("Session")
    session.revoked = True
    await db.commit()


async def revoke_all_sessions(db: AsyncSession, user_id: UUID) -> None:
    """Revoke all sessions for a user."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked == False))
    for session in result.scalars().all():
        session.revoked = True
    await db.commit()


async def update_profile(db: AsyncSession, user_id: UUID, full_name: str | None, phone: str | None, department: str | None, avatar_url: str | None) -> User:
    """Update profile details."""
    user = await user_repository.get(db, user_id)
    if not user:
        raise NotFoundException("User")

    if full_name is not None: user.full_name = full_name
    if phone is not None: user.phone = phone
    if department is not None: user.department = department
    if avatar_url is not None: user.avatar_url = avatar_url

    await db.commit()
    await db.refresh(user)
    return user


async def admin_list_users(db: AsyncSession) -> List[User]:
    """Admin: list all active registered users."""
    result = await db.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


async def admin_create_user(db: AsyncSession, username: str, email: str, password: str, role: str, department: str | None, full_name: str | None) -> User:
    """Admin: create a new user account with custom role assignments."""
    validate_password_strength(password)
    
    existing_email = await user_repository.get_by_email(db, email)
    existing_username = await user_repository.get_by_username(db, username)
    if existing_email or existing_username:
        raise ConflictException("User with this email or username already exists")

    user_data = {
        "email": email,
        "username": username,
        "hashed_password": hash_password(password),
        "role": UserRole(role) if role in UserRole.__members__ else UserRole.read_only,
        "department": department,
        "full_name": full_name,
        "is_active": True,
        "is_verified": True,
        "must_change_password": True,
        "last_password_change": datetime.now(timezone.utc),
    }
    user = await user_repository.create(db, obj_in=user_data)
    await db.refresh(user)

    hist = UserPasswordHistory(user_id=user.id, password_hash=user.hashed_password)
    db.add(hist)
    await db.commit()
    return user


async def admin_edit_user(db: AsyncSession, user_id: UUID, username: str | None, email: str | None, role: str | None, department: str | None, full_name: str | None, phone: str | None, is_active: bool | None) -> User:
    """Admin: edit registry details of a user."""
    user = await user_repository.get(db, user_id)
    if not user:
        raise NotFoundException("User")

    if username is not None: user.username = username
    if email is not None: user.email = email
    if role is not None: user.role = UserRole(role) if role in UserRole.__members__ else user.role
    if department is not None: user.department = department
    if full_name is not None: user.full_name = full_name
    if phone is not None: user.phone = phone
    if is_active is not None: user.is_active = is_active

    await db.commit()
    await db.refresh(user)
    return user


async def admin_view_login_history(db: AsyncSession, user_id: UUID | None = None) -> List[LoginAudit]:
    """Admin: retrieve historical login logs."""
    stmt = select(LoginAudit).order_by(desc(LoginAudit.login_time))
    if user_id:
        stmt = stmt.where(LoginAudit.user_id == user_id)
    result = await db.execute(stmt.limit(100))
    return list(result.scalars().all())


async def admin_unlock_user(db: AsyncSession, user_id: UUID) -> User:
    """Admin: unlock locked-out account."""
    user = await user_repository.get(db, user_id)
    if not user:
        raise NotFoundException("User")
    user.locked_until = None
    user.failed_login_attempts = 0
    await db.commit()
    await db.refresh(user)
    return user


async def seed_superadmin(db: AsyncSession, email: str, password: str) -> None:
    """Create the first super-admin if no users exist."""
    users = await user_repository.get_multi(db, limit=1)
    if users:
        return

    admin_data = {
        "email": email,
        "username": "admin",
        "hashed_password": hash_password(password),
        "role": UserRole.super_admin,
        "is_active": True,
        "is_verified": True,
        "last_password_change": datetime.now(timezone.utc),
    }
    user = await user_repository.create(db, obj_in=admin_data)
    
    # Record history
    hist = UserPasswordHistory(user_id=user.id, password_hash=user.hashed_password)
    db.add(hist)
    await db.commit()
    logger.info("Seeded super-admin: %s", email)
