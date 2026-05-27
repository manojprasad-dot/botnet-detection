from collections import defaultdict

from .schemas import Alert, RegisteredDevice, TelemetryEvent


class InMemoryStore:
    def __init__(self) -> None:
        self.devices: dict[str, RegisteredDevice] = {}
        self.telemetry: dict[str, list[TelemetryEvent]] = defaultdict(list)
        self.alerts: list[Alert] = []


store = InMemoryStore()
