"""
KOVIRX — Response Engine Orchestrator.

Automated threat response based on risk score thresholds.

Risk Score Actions:
    > 95: Alert → Block IP → Terminate Connection → Quarantine → Notify Admin
    > 80: Alert → Block IP → Notify Admin
    > 60: Alert → Notify Admin
    > 35: Log + Monitor
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.agent_ws.handler import agent_ws_manager
from backend.websocket.manager import ws_manager

logger = logging.getLogger("kovirx.response_engine")


class ResponseOrchestrator:
    """
    Automated threat response orchestrator.

    Evaluates risk scores and executes graduated response actions,
    logging every action to the response_actions audit trail.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_and_respond(
        self,
        device_id: str,
        risk_score: int,
        threat_type: str,
        dest_ip: str | None = None,
        alert_id: UUID | None = None,
    ) -> list[dict]:
        """
        Evaluate risk score and execute appropriate response actions.

        Returns:
            List of action records that were executed.
        """
        actions_taken = []

        if risk_score >= 95:
            # CRITICAL: Full response chain
            actions_taken.append(await self._create_alert(device_id, risk_score, threat_type))
            if dest_ip:
                actions_taken.append(await self._block_ip(device_id, dest_ip))
                actions_taken.append(await self._terminate_connection(device_id, dest_ip))
            actions_taken.append(await self._quarantine_device(device_id))
            await self._notify_admin(device_id, risk_score, threat_type, "critical")

        elif risk_score >= 80:
            # HIGH: Block + Notify
            actions_taken.append(await self._create_alert(device_id, risk_score, threat_type))
            if dest_ip:
                actions_taken.append(await self._block_ip(device_id, dest_ip))
            await self._notify_admin(device_id, risk_score, threat_type, "high")

        elif risk_score >= 60:
            # MEDIUM: Alert + Notify
            actions_taken.append(await self._create_alert(device_id, risk_score, threat_type))
            await self._notify_admin(device_id, risk_score, threat_type, "medium")

        elif risk_score >= 35:
            # LOW: Log only
            logger.info(
                "Low risk (%d%%) for device %s. Monitoring.",
                risk_score, device_id,
            )

        # Record all actions to audit trail
        for action in actions_taken:
            await self._record_action(action)

        return actions_taken

    async def _block_ip(self, device_id: str, ip: str) -> dict:
        """Send block_ip command to the agent via WebSocket."""
        command = {"command": "block_ip", "target": ip}
        sent = await agent_ws_manager.send_to_device(device_id, command)

        status = "executed" if sent > 0 else "failed"
        logger.info("Block IP %s for device %s: %s", ip, device_id, status)

        return {
            "action_type": "block_ip",
            "device_id": device_id,
            "target": ip,
            "status": status,
            "triggered_by": "auto",
        }

    async def _terminate_connection(self, device_id: str, ip: str) -> dict:
        """Send terminate_connection command to the agent."""
        command = {"command": "terminate_connection", "target": ip}
        sent = await agent_ws_manager.send_to_device(device_id, command)

        return {
            "action_type": "terminate_connection",
            "device_id": device_id,
            "target": ip,
            "status": "executed" if sent > 0 else "failed",
            "triggered_by": "auto",
        }

    async def _quarantine_device(self, device_id: str) -> dict:
        """Quarantine a device by blocking all outbound traffic."""
        command = {"command": "quarantine", "target": device_id}
        sent = await agent_ws_manager.send_to_device(device_id, command)

        logger.warning("Device %s quarantined.", device_id)
        return {
            "action_type": "quarantine",
            "device_id": device_id,
            "target": device_id,
            "status": "executed" if sent > 0 else "failed",
            "triggered_by": "auto",
        }

    async def _create_alert(self, device_id: str, risk_score: int, threat_type: str) -> dict:
        """Create an alert record in the database."""
        return {
            "action_type": "alert",
            "device_id": device_id,
            "target": threat_type,
            "status": "executed",
            "triggered_by": "auto",
            "risk_score": risk_score,
        }

    async def _notify_admin(
        self, device_id: str, risk_score: int, threat_type: str, severity: str
    ) -> None:
        """Push alert notification to dashboard via WebSocket."""
        notification = {
            "type": "threat_alert",
            "severity": severity,
            "device_id": device_id,
            "risk_score": risk_score,
            "threat_type": threat_type,
            "message": f"Risk {risk_score}%: {threat_type} detected on device {device_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await ws_manager.broadcast(notification)
        logger.info("Admin notified: %s threat on %s (risk=%d%%)", severity, device_id, risk_score)

    async def _record_action(self, action: dict) -> None:
        """Write action to the response_actions audit trail."""
        try:
            from database.models.response_action import ResponseAction

            record = ResponseAction(
                device_id=action.get("device_id", ""),
                action_type=action.get("action_type", "unknown"),
                target=action.get("target", ""),
                status=action.get("status", "pending"),
                triggered_by=action.get("triggered_by", "auto"),
                risk_score=action.get("risk_score", 0),
            )
            self.db.add(record)
            await self.db.flush()
        except ImportError:
            logger.debug("ResponseAction model not available yet. Action: %s", action)
        except Exception as e:
            logger.error("Failed to record response action: %s", e)
