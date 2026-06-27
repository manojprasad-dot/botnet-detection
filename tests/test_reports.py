import pytest
from uuid import UUID
from httpx import AsyncClient
from backend.core.celery_app import celery_app

# Make celery tasks execute synchronously for the test suite
celery_app.conf.update(task_always_eager=True)


@pytest.mark.asyncio
async def test_report_generation_pipeline(client: AsyncClient, auth_headers: dict):
    """Test report request, background compilation, and download lifecycle."""
    # 1. Register a test device to generate telemetry and database records
    device_response = await client.post(
        "/api/v1/devices/register",
        json={"hostname": "report-test-host.kovirx.local"},
        headers=auth_headers,
    )
    assert device_response.status_code == 201
    device_id = device_response.json()["id"]

    # 2. Trigger report generation
    generate_payload = {
        "report_type": "daily",
        "format": "csv"
    }
    response = await client.post(
        "/api/v1/reports/generate",
        json=generate_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    report_data = response.json()
    assert report_data["report_type"] == "daily"
    assert report_data["format"] == "csv"
    assert "id" in report_data
    report_id = report_data["id"]

    # 3. Yield to the event loop to let the background task complete
    import asyncio
    await asyncio.sleep(0.1)

    # 3. List reports and verify it is there and completed (via task_always_eager)
    list_response = await client.get(
        "/api/v1/reports",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    reports = list_response.json()
    assert len(reports) >= 1
    
    matched_report = None
    for r in reports:
        if r["id"] == report_id:
            matched_report = r
            break
            
    assert matched_report is not None
    assert matched_report["status"] == "completed"

    # 4. Download report and verify content
    download_response = await client.get(
        f"/api/v1/reports/{report_id}/download",
        headers=auth_headers,
    )
    assert download_response.status_code == 200
    assert "text/csv" in download_response.headers["content-type"]
    assert b"KOVIRX Security Report" in download_response.content
    assert b"Total Devices" in download_response.content
