"""
KOVIRX — User model with RBAC roles.

Roles: super_admin, security_analyst, soc_manager, viewer.
"""

import enum

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """Role-Based Access Control roles."""
    super_admin = "super_admin"
    soc_manager = "soc_manager"
    soc_analyst = "soc_analyst"
    incident_responder = "incident_responder"
    read_only = "read_only"
    # Legacy roles (backwards compatibility)
    security_analyst = "security_analyst"
    viewer = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.read_only,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Enterprise EDR Fields ──
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_password_change: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role.value}>"
