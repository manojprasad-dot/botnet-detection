"""
KOVIRX Models package.

Import all models here so Alembic can discover them via a single import.
"""

from app.models.user import User  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.traffic import TrafficLog, NetworkFlow  # noqa: F401
from app.models.ml import MLPrediction  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.threat import BotnetFamily, ThreatIntelligence  # noqa: F401
from app.models.log import SystemLog, AuditLog  # noqa: F401
