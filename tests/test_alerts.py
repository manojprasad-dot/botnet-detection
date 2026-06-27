import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.alert import Alert, AlertSeverity, AlertStatus
from database.models.device import Device
from database.models.user import User


@pytest_asyncio.fixture
async def seeded_device_and_alert(db: AsyncSession, test_user: User) -> tuple[Device, Alert]:
    """Helper fixture to seed a device and an associated alert in the database."""
    device = Device(
        hostname="alert-test-pc.kovirx.local",
        operating_system="Windows 11 Enterprise",
        registered_by=test_user.id,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    alert = Alert(
        device_id=device.id,
        severity=AlertSeverity.high,
        title="Suspicious Beaconing Detected",
        description="Machine learning detected regular connection bursts to 198.51.100.42.",
        status=AlertStatus.new,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return device, alert


@pytest.mark.asyncio
async def test_alert_management_flow(
    client: AsyncClient,
    auth_headers: dict,
    admin_auth_headers: dict,
    test_user: User,
    seeded_device_and_alert: tuple[Device, Alert],
):
    """Test retrieving, updating status, and assigning alerts to analysts."""
    device, alert = seeded_device_and_alert
    alert_id = alert.id

    # 1. List alerts and filter by severity
    response = await client.get(
        "/api/v1/alerts?severity=high",
        headers=auth_headers,
    )
    assert response.status_code == 200
    listing = response.json()
    assert listing["total"] >= 1
    assert any(a["id"] == str(alert_id) for a in listing["alerts"])

    # 2. Get specific alert detail
    response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Suspicious Beaconing Detected"

    # 3. Update alert status to 'investigating' (analyst role allowed)
    response = await client.put(
        f"/api/v1/alerts/{alert_id}",
        json={"status": "investigating"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "investigating"

    # 4. Try to assign alert using analyst headers (should fail, only manager or admin allowed)
    response = await client.post(
        f"/api/v1/alerts/{alert_id}/assign",
        json={"assigned_to": str(test_user.id)},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # 5. Assign alert using admin headers (should succeed)
    response = await client.post(
        f"/api/v1/alerts/{alert_id}/assign",
        json={"assigned_to": str(test_user.id)},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == str(test_user.id)
