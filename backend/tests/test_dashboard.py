import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(client: AsyncClient, auth_headers: dict):
    """Test retrieving aggregated statistics for the SOC Dashboard."""
    response = await client.get(
        "/api/v1/dashboard/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    summary = response.json()

    # Verify that the expected aggregate keys are present
    assert "protected_devices" in summary
    assert "active_threats" in summary
    assert "today_alerts" in summary
    assert "botnet_attempts_24h" in summary
    assert "traffic_stats" in summary
    assert "top_threat_types" in summary
    assert "severity_breakdown" in summary

    traffic = summary["traffic_stats"]
    assert "total_flows" in traffic
    assert "suspicious_flows" in traffic
    assert "blocked_flows" in traffic
