from __future__ import annotations

from typing import Any

import requests

from .models import DeviceRegistration, TelemetryBatch


class PlatformApiClient:
    def __init__(self, server_url: str, timeout: int = 10) -> None:
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    def register_device(self, payload: DeviceRegistration) -> dict[str, Any]:
        response = requests.post(
            f"{self.server_url}/api/v1/devices/register",
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def send_telemetry(self, payload: TelemetryBatch) -> dict[str, Any]:
        response = requests.post(
            f"{self.server_url}/api/v1/telemetry/ingest",
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
