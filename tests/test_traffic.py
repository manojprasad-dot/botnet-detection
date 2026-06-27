import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_traffic_ingestion_flow(client: AsyncClient, auth_headers: dict):
    """Test registering a device, ingesting network flows, and querying them."""
    # 1. Register a test device
    device_response = await client.post(
        "/api/v1/devices/register",
        json={
            "hostname": "traffic-test-pc.kovirx.local",
            "operating_system": "Linux Ubuntu 22.04",
        },
        headers=auth_headers,
    )
    assert device_response.status_code == 201
    device = device_response.json()
    device_id = device["id"]

    # 2. Ingest a batch of network flows (some regular, some simulating botnet DNS queries)
    ingest_payload = {
        "device_id": device_id,
        "flows": [
            {
                "device_id": device_id,
                "source_ip": "192.168.1.100",
                "source_port": 49152,
                "dest_ip": "8.8.8.8",
                "dest_port": 53,
                "protocol": "UDP",
                "packet_count": 2,
                "byte_count": 150,
                "flow_duration": 0.05,
                "dns_query": "google.com",
            },
            {
                "device_id": device_id,
                "source_ip": "192.168.1.100",
                "source_port": 51234,
                "dest_ip": "104.244.42.1",
                "dest_port": 443,
                "protocol": "TCP",
                "packet_count": 25,
                "byte_count": 12000,
                "flow_duration": 4.5,
                "tcp_flags": "PA",
            },
            # Malicious looking C2 connection (regular beaconing, high DNS entropy)
            {
                "device_id": device_id,
                "source_ip": "192.168.1.100",
                "source_port": 61111,
                "dest_ip": "198.51.100.42",
                "dest_port": 8080,
                "protocol": "TCP",
                "packet_count": 500,
                "byte_count": 200000,
                "flow_duration": 120.0,
                "tcp_flags": "A",
                "dns_query": "wxzpqmkljhasdfuytw.info", # high entropy
            }
        ]
    }

    response = await client.post(
        "/api/v1/traffic/ingest",
        json=ingest_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    ingest_res = response.json()
    assert ingest_res["ingested_flows"] == 3
    # depending on whether stubs are loaded, we might see alerts generated
    assert "generated_alerts" in ingest_res

    # 3. Retrieve flows and filter by device_id
    response = await client.get(
        f"/api/v1/traffic/flows?device_id={device_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    flows_list = response.json()
    assert flows_list["total"] == 3
    assert len(flows_list["flows"]) == 3
    
    # Check details of first retrieved flow
    flow = flows_list["flows"][0]
    assert "source_ip" in flow
    assert "dest_ip" in flow
    assert "dns_entropy" in flow

    # 4. Get individual flow by ID
    flow_id = flows_list["flows"][0]["id"]
    response = await client.get(
        f"/api/v1/traffic/flows/{flow_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == flow_id
