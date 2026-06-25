from typing import Protocol

from ..models import TelemetryEvent


class Collector(Protocol):
    def collect(self) -> list[TelemetryEvent]:
        ...
