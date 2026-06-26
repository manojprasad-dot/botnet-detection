import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ml_prediction_endpoints(client: AsyncClient, auth_headers: dict):
    """Test running predictions on ingested flows and querying model status."""
    # 1. Register a test device
    device_response = await client.post(
        "/api/v1/devices/register",
        json={"hostname": "ml-test-host.kovirx.local"},
        headers=auth_headers,
    )
    device_id = device_response.json()["id"]

    # 2. Ingest a flow
    ingest_payload = {
        "device_id": device_id,
        "flows": [
            {
                "device_id": device_id,
                "source_ip": "192.168.1.50",
                "dest_ip": "203.0.113.5",
                "protocol": "TCP",
                "packet_count": 100,
                "byte_count": 50000,
                "flow_duration": 1.0,
                "tcp_flags": "S",
            }
        ]
    }
    await client.post("/api/v1/traffic/ingest", json=ingest_payload, headers=auth_headers)

    # 3. Retrieve the ingested flow ID
    flows_response = await client.get(f"/api/v1/traffic/flows?device_id={device_id}", headers=auth_headers)
    flow_id = flows_response.json()["flows"][0]["id"]

    # 4. Trigger explicit prediction
    predict_response = await client.post(
        "/api/v1/ml/predict",
        json={"flow_ids": [flow_id]},
        headers=auth_headers,
    )
    assert predict_response.status_code == 200
    predictions = predict_response.json()
    assert len(predictions) >= 1
    pred = predictions[0]
    assert "model_name" in pred
    assert "confidence_score" in pred
    assert "explanation" in pred  # SHAP explanations
    prediction_id = pred["id"]

    # 5. List predictions
    list_response = await client.get(
        f"/api/v1/ml/predictions?device_id={device_id}",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 1
    assert any(p["id"] == prediction_id for p in list_data["predictions"])

    # 6. Retrieve detailed prediction by ID
    detail_response = await client.get(
        f"/api/v1/ml/predictions/{prediction_id}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == prediction_id

    # 7. Query model status
    status_response = await client.get(
        "/api/v1/ml/model-status",
        headers=auth_headers,
    )
    assert status_response.status_code == 200
    status = status_response.json()
    assert "models" in status
    assert len(status["models"]) >= 2
    assert any(m["name"] == "xgboost" for m in status["models"])
    assert any(m["name"] == "isolation_forest" for m in status["models"])
