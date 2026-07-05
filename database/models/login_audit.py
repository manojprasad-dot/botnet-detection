from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, UUIDMixin

class LoginAudit(Base, UUIDMixin):
    __tablename__ = "login_audits"

    user_id: Mapped[None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    login_time: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed, locked
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
