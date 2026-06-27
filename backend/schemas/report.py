"""
KOVIRX — Report schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    report_type: str = "daily"  # daily, weekly, monthly
    format: str = "pdf"         # pdf, csv


class ReportResponse(BaseModel):
    id: UUID
    report_type: str
    format: str
    filename: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    status: str

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    total: int
    reports: list[ReportResponse]
