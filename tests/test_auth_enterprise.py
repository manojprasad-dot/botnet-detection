import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    hash_password,
    verify_password,
    password_needs_rehash,
    validate_password_strength,
)
from database.models.user import User, UserRole
from database.models.refresh_token import RefreshToken
from database.models.login_audit import LoginAudit
from backend.services import auth_service
from backend.core.exceptions import CredentialsException, ConflictException


@pytest.mark.asyncio
async def test_argon2_hashing_and_legacy_fallback():
    """Verify that Argon2 hashing works, and bcrypt hashes are verified as a legacy fallback."""
    # Test Argon2 hashing
    pwd = "SecurePassword123!"
    argon_hash = hash_password(pwd)
    assert argon_hash.startswith("$argon2")
    assert verify_password(pwd, argon_hash) is True
    assert password_needs_rehash(argon_hash) is False

    # Test legacy bcrypt hash verification
    import bcrypt
    salt = bcrypt.gensalt()
    bcrypt_hash = bcrypt.hashpw(pwd.encode("utf-8"), salt).decode("utf-8")
    assert verify_password(pwd, bcrypt_hash) is True
    assert password_needs_rehash(bcrypt_hash) is True


@pytest.mark.asyncio
async def test_password_strength_validator():
    """Verify password strength rules are enforced (12+ characters, upper, lower, digit, special symbol)."""
    # Compliant
    validate_password_strength("SecurePassword123!")

    # Too short
    with pytest.raises(ValueError, match="at least 12 characters"):
        validate_password_strength("Short1!")

    # No uppercase
    with pytest.raises(ValueError, match="uppercase"):
        validate_password_strength("lowercase123!")

    # No lowercase
    with pytest.raises(ValueError, match="lowercase"):
        validate_password_strength("UPPERCASE123!")

    # No number
    with pytest.raises(ValueError, match="number"):
        validate_password_strength("SecurePassword!")

    # No special character
    with pytest.raises(ValueError, match="special character"):
        validate_password_strength("SecurePassword123")


@pytest.mark.asyncio
async def test_account_lockout_policy(db: AsyncSession):
    """Test account lockouts after 5 consecutive failed login attempts."""
    email = f"operator-{uuid4()}@kovirx.com"
    pwd = "SecurePassword123!"
    
    # Register operator
    user_res = await auth_service.register_user(db, email=email, username=email.split("@")[0], password=pwd, role="soc_analyst")
    user_id = user_res.id

    # Find model object
    user = await db.get(User, user_id)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    # Fail 4 times
    for i in range(4):
        with pytest.raises(CredentialsException):
            await auth_service.authenticate_user(db, email=email, password="WrongPassword123!")
        
    await db.refresh(user)
    assert user.failed_login_attempts == 4
    assert user.locked_until is None

    # Fail 5th time -> Account becomes locked
    with pytest.raises(CredentialsException):
        await auth_service.authenticate_user(db, email=email, password="WrongPassword123!")

    await db.refresh(user)
    assert user.failed_login_attempts == 5
    assert user.locked_until is not None

    # Authenticating with correct password fails now
    with pytest.raises(CredentialsException, match="locked"):
        await auth_service.authenticate_user(db, email=email, password=pwd)

    # Unlock the account via service
    await auth_service.admin_unlock_user(db, user.id)
    await db.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    # Login succeeds now
    tokens = await auth_service.authenticate_user(db, email=email, password=pwd)
    assert tokens.access_token is not None


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_sessions(db: AsyncSession):
    """Verify refresh token rotation and active session listing."""
    email = f"analyst-{uuid4()}@kovirx.com"
    pwd = "SecurePassword123!"
    
    # Register
    user_res = await auth_service.register_user(db, email=email, username=email.split("@")[0], password=pwd)
    user_id = user_res.id

    # Authenticate (Session 1)
    tokens1 = await auth_service.authenticate_user(db, email=email, password=pwd, user_agent="Mozilla Chrome")
    
    # Check sessions count
    sessions = await auth_service.get_active_sessions(db, user_id=user_id)
    assert len(sessions) == 1
    assert sessions[0].browser == "Chrome"

    # Rotate Refresh Token
    rotated_tokens = await auth_service.refresh_access_token(
        db, refresh_token=tokens1.refresh_token, user_agent="Mozilla Firefox"
    )
    assert rotated_tokens.access_token is not None
    assert rotated_tokens.refresh_token != tokens1.refresh_token

    # Verify old token is revoked, new token is active
    sessions = await auth_service.get_active_sessions(db, user_id=user_id)
    assert len(sessions) == 1
    assert sessions[0].browser == "Firefox"


@pytest.mark.asyncio
async def test_rbac_endpoint_access(client: AsyncClient, db: AsyncSession):
    """Ensure that API routes require appropriate role permissions."""
    # Create SOC Analyst and Read-Only users
    analyst_email = f"analyst-{uuid4()}@kovirx.com"
    readonly_email = f"read-{uuid4()}@kovirx.com"
    pwd = "SecurePassword123!"

    analyst_res = await auth_service.register_user(db, email=analyst_email, username=analyst_email.split("@")[0], password=pwd, role="soc_analyst")
    readonly_res = await auth_service.register_user(db, email=readonly_email, username=readonly_email.split("@")[0], password=pwd, role="read_only")

    # Get tokens
    analyst_tokens = await auth_service.authenticate_user(db, email=analyst_email, password=pwd)
    readonly_tokens = await auth_service.authenticate_user(db, email=readonly_email, password=pwd)

    analyst_headers = {"Authorization": f"Bearer {analyst_tokens.access_token}"}
    readonly_headers = {"Authorization": f"Bearer {readonly_tokens.access_token}"}

    # Query admin list endpoint (requires super_admin)
    # 1. Analyst (Forbidden)
    res = await client.get("/api/v1/auth/admin/users", headers=analyst_headers)
    assert res.status_code == 403

    # 2. Read-Only (Forbidden)
    res = await client.get("/api/v1/auth/admin/users", headers=readonly_headers)
    assert res.status_code == 403
