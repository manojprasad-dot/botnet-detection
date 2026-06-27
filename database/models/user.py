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
    security_analyst = "security_analyst"
    soc_manager = "soc_manager"
    viewer = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.viewer,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role.value}>"
