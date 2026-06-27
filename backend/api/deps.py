"""
KOVIRX — FastAPI dependency injection.

Provides get_db, get_current_user, and role-based access control.
"""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import CredentialsException, PermissionDeniedException
from backend.core.security import decode_token
from database.session import get_db
from database.models.user import User, UserRole

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from the Authorization header.
    Returns the authenticated User object.
    """
    if credentials is None:
        raise CredentialsException("Missing authentication token")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise CredentialsException("Invalid or expired token")

    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException("Token missing user identifier")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise CredentialsException("User not found")
    if not user.is_active:
        raise CredentialsException("Account is disabled")

    return user


def require_role(*roles: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("super_admin"))])
    """
    async def _check_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.value not in roles:
            raise PermissionDeniedException(
                f"Role '{current_user.role.value}' does not have access. "
                f"Required: {', '.join(roles)}"
            )
        return current_user

    return _check_role


# Convenience dependencies for common role combinations
require_admin = require_role("super_admin")
require_analyst = require_role("super_admin", "security_analyst")
require_manager = require_role("super_admin", "soc_manager")
require_any_auth = require_role("super_admin", "security_analyst", "soc_manager", "viewer")
