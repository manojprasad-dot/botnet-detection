"""
KOVIRX Endpoint Agent — Base Collector Interface.
"""

from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """Abstract base class for telemetry data collectors."""

    @abstractmethod
    def collect(self) -> list[dict]:
        """Collect and return telemetry data points."""
        ...
