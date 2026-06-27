"""
KOVIRX — Report database model.
"""

import enum
from sqlalchemy import Enum, LargeBinary, String, Text, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class ReportStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Report(Base, UUIDMixin, TimestampMixin):
    """Database record for generated security reports."""

    __tablename__ = "reports"

    report_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # daily, weekly, monthly
    format: Mapped[str] = mapped_column(String(10), nullable=False)       # pdf, csv
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"),
        default=ReportStatus.pending,
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    period_start: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by: Mapped[None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Report type={self.report_type} format={self.format} status={self.status.value}>"
