import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_device_crud_flow(client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
    """Test device registration, detail lookup, listing, update, and deletion."""
    # 1. Register a new device
    device_data = {
        "hostname": "workstation-01.kovirx.local",
        "operating_system": "Windows 11 Pro",
        "mac_address": "00:11:22:33:44:55",
        "ip_address": "192.168.1.105",
        "agent_version": "1.0.2",
        "os_version": "23H2",
        "architecture": "x86_64",
        "tags": ["finance", "endpoint"],
    }
    response = await client.post(
        "/api/v1/devices/register",
        json=device_data,
        headers=auth_headers,
    )
    assert response.status_code == 201
    device = response.json()
    assert device["hostname"] == device_data["hostname"]
    assert device["operating_system"] == device_data["operating_system"]
    assert device["status"] == "online"
    assert device["risk_score"] == 0.0
    device_id = device["id"]

    # 2. List devices and verify pagination
    response = await client.get("/api/v1/devices", headers=auth_headers)
    assert response.status_code == 200
    listing = response.json()
    assert listing["total"] >= 1
    assert any(d["id"] == device_id for d in listing["devices"])

    # 3. Retrieve specific device details
    response = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["hostname"] == device_data["hostname"]

    # 4. Update device properties (analyst/admin role allowed)
    update_data = {
        "hostname": "workstation-01-modified.kovirx.local",
        "status": "quarantined",
    }
    response = await client.put(
        f"/api/v1/devices/{device_id}",
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["hostname"] == update_data["hostname"]
    assert updated["status"] == "quarantined"

    # 5. Delete device using analyst headers (should be forbidden)
    response = await client.delete(
        f"/api/v1/devices/{device_id}",
        headers=auth_headers,
    )
    assert response.status_code == 403

    # 6. Delete device using admin headers (should succeed)
    response = await client.delete(
        f"/api/v1/devices/{device_id}",
        headers=admin_auth_headers,
    )
    assert response.status_code == 204

    # 7. Check if device is indeed deleted (should return 404)
    response = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert response.status_code == 404
