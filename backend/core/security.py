"""
KOVIRX Platform — Security utilities.

Handles JWT token creation / validation and password hashing via bcrypt.
"""

import re
from datetime import datetime, timedelta, timezone

import bcrypt
from argon2 import PasswordHasher
from jose import JWTError, jwt

from .config import settings

# ── Password Hashing & Validation ─────────────────────────────────
ph = PasswordHasher()


def hash_password(plain: str) -> str:
    """Hash a plaintext password with Argon2."""
    return ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against an Argon2 or bcrypt hash."""
    try:
        if hashed.startswith("$argon2"):
            try:
                return ph.verify(hashed, plain)
            except Exception:
                return False
        else:
            # Fallback to bcrypt for backward compatibility
            pw_bytes = plain.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception:
        return False


def password_needs_rehash(hashed: str) -> bool:
    """Check if the password hash is using the legacy bcrypt scheme."""
    return not hashed.startswith("$argon2")


def validate_password_strength(password: str) -> None:
    """
    Validate password strength.
    Enforces minimum 12 characters, uppercase, lowercase, numbers, and special characters.
    """
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character.")


# ── JWT Tokens ────────────────────────────────────────────────────
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a long-lived refresh JWT."""
    import uuid
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises ``JWTError`` on invalid / expired tokens.
    Returns the payload dict on success.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise


def create_password_reset_token(email: str) -> str:
    """Create a short-lived token for password resets (15 min)."""
    return create_access_token(
        data={"sub": email, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=15),
    )
