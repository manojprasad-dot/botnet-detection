from sqlalchemy import ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, TimestampMixin, UUIDMixin

class UserPasswordHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_password_histories"

    user_id: Mapped[None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
