"""
KOVIRX — Report generation service.

Generates daily / weekly / monthly reports in PDF and CSV formats.
"""

import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException
from database.models.alert import Alert
from database.models.device import Device
from database.models.ml import MLPrediction
from database.models.report import Report, ReportStatus
from database.repositories.report import report_repository
from backend.schemas.report import ReportResponse
from backend.core.celery_app import celery_app

logger = logging.getLogger("kovirx.reports")


def _get_period(report_type: str) -> tuple[datetime, datetime]:
    """Calculate period start/end for report type."""
    now = datetime.now(timezone.utc)
    if report_type == "daily":
        start = now - timedelta(days=1)
    elif report_type == "weekly":
        start = now - timedelta(weeks=1)
    elif report_type == "monthly":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=1)
    return start, now


@celery_app.task(name="backend.services.report_service.compile_report_task")
def compile_report_task(report_id_str: str, report_type: str, fmt: str) -> None:
    """Synchronous Celery wrapper that runs the async compiler."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(async_compile_report(report_id_str, report_type, fmt))
    except RuntimeError:
        asyncio.run(async_compile_report(report_id_str, report_type, fmt))


async def async_compile_report(report_id_str: str, report_type: str, fmt: str) -> None:
    from database.session import async_session_factory
    from database.repositories.report import report_repository
    from database.models.report import ReportStatus

    report_id = UUID(report_id_str)
    async with async_session_factory() as db:
        try:
            period_start, period_end = _get_period(report_type)

            # Gather data
            alerts_result = await db.execute(
                select(Alert).where(
                    Alert.created_at >= period_start,
                    Alert.created_at <= period_end,
                ).order_by(Alert.created_at.desc())
            )
            alerts = list(alerts_result.scalars().all())

            predictions_result = await db.execute(
                select(MLPrediction).where(
                    MLPrediction.created_at >= period_start,
                    MLPrediction.created_at <= period_end,
                )
            )
            predictions = list(predictions_result.scalars().all())

            device_count = (await db.execute(select(func.count(Device.id)))).scalar() or 0

            if fmt == "csv":
                content = _generate_csv(alerts, predictions, device_count, period_start, period_end)
            else:
                content = _generate_pdf_content(alerts, predictions, device_count, period_start, period_end)

            await report_repository.update_status(
                db,
                report_id=report_id,
                status=ReportStatus.completed,
                content=content,
            )
            await db.commit()
            logger.info("Report %s compiled successfully", report_id_str)
        except Exception as e:
            logger.exception("Report %s compilation failed: %s", report_id_str, e)
            await report_repository.update_status(
                db,
                report_id=report_id,
                status=ReportStatus.failed,
                error_message=str(e),
            )
            await db.commit()


async def generate_report(
    db: AsyncSession,
    report_type: str = "daily",
    fmt: str = "csv",
    generated_by: UUID | None = None,
) -> ReportResponse:
    """Generate a daily/weekly/monthly report in PDF or CSV."""
    period_start, period_end = _get_period(report_type)
    report_id = uuid.uuid4()

    filename = f"kovirx_report_{report_type}_{report_id.hex[:8]}.{fmt.lower()}"

    report_in = {
        "id": report_id,
        "report_type": report_type,
        "format": fmt.lower(),
        "filename": filename,
        "status": ReportStatus.pending,
        "period_start": period_start,
        "period_end": period_end,
        "generated_by": generated_by,
    }

    await report_repository.create(db, obj_in=report_in)
    await db.commit()

    # Trigger background compilation
    compile_report_task.delay(str(report_id), report_type, fmt.lower())

    return ReportResponse(
        id=report_id,
        report_type=report_type,
        format=fmt.lower(),
        filename=filename,
        generated_at=datetime.now(timezone.utc),
        period_start=period_start,
        period_end=period_end,
        status="pending",
    )


def _generate_csv(alerts, predictions, device_count, start, end) -> bytes:
    """Generate a CSV report."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["KOVIRX Security Report"])
    writer.writerow([f"Period: {start.isoformat()} to {end.isoformat()}"])
    writer.writerow([f"Total Devices: {device_count}"])
    writer.writerow([f"Total Alerts: {len(alerts)}"])
    writer.writerow([f"Total Predictions: {len(predictions)}"])
    writer.writerow([])

    # Alerts section
    writer.writerow(["=== ALERTS ==="])
    writer.writerow(["Severity", "Title", "Status", "Device ID", "Created At"])
    for alert in alerts:
        writer.writerow([
            alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
            alert.title,
            alert.status.value if hasattr(alert.status, 'value') else alert.status,
            str(alert.device_id),
            alert.created_at.isoformat(),
        ])
    writer.writerow([])

    # Predictions section
    writer.writerow(["=== ML PREDICTIONS ==="])
    writer.writerow(["Model", "Threat Type", "Confidence", "Risk Level", "Device ID", "Created At"])
    for pred in predictions:
        writer.writerow([
            pred.model_name,
            pred.threat_type,
            f"{pred.confidence_score:.2%}",
            pred.risk_level.value if hasattr(pred.risk_level, 'value') else pred.risk_level,
            str(pred.device_id),
            pred.created_at.isoformat(),
        ])

    return output.getvalue().encode("utf-8")


def _generate_pdf_content(alerts, predictions, device_count, start, end) -> bytes:
    """
    Generate a PDF report using reportlab.
    Falls back to a text-based summary if reportlab is not available.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("KOVIRX Security Report", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"Period: {start.strftime('%Y-%m-%d %H:%M')} — {end.strftime('%Y-%m-%d %H:%M')} UTC",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 12))

        # Summary table
        summary_data = [
            ["Metric", "Value"],
            ["Total Devices", str(device_count)],
            ["Total Alerts", str(len(alerts))],
            ["Total Predictions", str(len(predictions))],
        ]
        t = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0C1426")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # Alert details
        if alerts:
            elements.append(Paragraph("Alerts", styles["Heading2"]))
            alert_data = [["Severity", "Title", "Status", "Created"]]
            for a in alerts[:50]:  # Limit to 50 for PDF size
                alert_data.append([
                    a.severity.value if hasattr(a.severity, 'value') else str(a.severity),
                    a.title[:60],
                    a.status.value if hasattr(a.status, 'value') else str(a.status),
                    a.created_at.strftime("%Y-%m-%d %H:%M"),
                ])
            at = Table(alert_data)
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            elements.append(at)

        doc.build(elements)
        return buffer.getvalue()

    except ImportError:
        # Fallback: plain text pseudo-PDF
        logger.warning("reportlab not installed, generating text report")
        return _generate_csv(alerts, predictions, device_count, start, end)


async def get_report_content(db: AsyncSession, report_id: UUID) -> Report | None:
    """Retrieve stored report content by ID."""
    return await report_repository.get(db, report_id)


async def list_reports(db: AsyncSession) -> list[ReportResponse]:
    """List all generated reports (metadata only)."""
    reports = await report_repository.list_reports(db)
    return [
        ReportResponse(
            id=r.id,
            report_type=r.report_type,
            format=r.format,
            filename=r.filename,
            generated_at=r.created_at or datetime.now(timezone.utc),
            period_start=r.period_start,
            period_end=r.period_end,
            status=r.status.value,
        )
        for r in reports
    ]
