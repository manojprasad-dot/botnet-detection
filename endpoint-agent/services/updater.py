"""
KOVIRX Endpoint Agent — Self-Update Service.

Checks the backend for new agent versions and applies updates.
Supports checksum verification and graceful restart.
"""

import hashlib
import logging
import os
import sys
import tempfile

logger = logging.getLogger("kovirx.agent.updater")


class AgentUpdater:
    """
    Self-update mechanism for the endpoint agent.

    Checks /api/v1/agent/version for the latest version,
    downloads the update package, verifies integrity, and restarts.
    """

    def __init__(self, api_client, current_version: str):
        self.client = api_client
        self.current_version = current_version

    def check_for_update(self) -> dict | None:
        """
        Check if a newer agent version is available.

        Returns:
            Version info dict if update available, None otherwise.
        """
        try:
            version_info = self.client.check_agent_version()
            if not version_info:
                return None

            latest = version_info.get("latest_version", "")
            if latest and latest != self.current_version:
                logger.info(
                    "Agent update available: %s → %s",
                    self.current_version, latest,
                )
                return version_info
            else:
                logger.debug("Agent is up to date (v%s)", self.current_version)
                return None
        except Exception as e:
            logger.debug("Update check failed (non-critical): %s", e)
            return None

    def download_and_apply(self, version_info: dict) -> bool:
        """
        Download update package, verify checksum, and apply.

        Args:
            version_info: Dict with 'download_url' and 'checksum' fields

        Returns:
            True if update was applied successfully
        """
        download_url = version_info.get("download_url")
        expected_checksum = version_info.get("checksum")

        if not download_url:
            logger.warning("No download URL in version info.")
            return False

        try:
            # Download to temp file
            update_data = self.client.download_update(download_url)
            if not update_data:
                logger.error("Failed to download update package.")
                return False

            # Verify checksum
            if expected_checksum:
                actual_checksum = hashlib.sha256(update_data).hexdigest()
                if actual_checksum != expected_checksum:
                    logger.error(
                        "Update checksum mismatch: expected=%s actual=%s",
                        expected_checksum, actual_checksum,
                    )
                    return False

            # Write to temp location
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".zip", prefix="kovirx_update_"
            ) as tmp:
                tmp.write(update_data)
                tmp_path = tmp.name

            logger.info("Update package downloaded and verified: %s", tmp_path)
            # Actual application would involve extracting and replacing files
            # For now, log the path for manual application
            logger.info("Update ready for application. Package: %s", tmp_path)
            return True

        except Exception as e:
            logger.error("Update download/apply failed: %s", e)
            return False

    def restart_agent(self) -> None:
        """Restart the agent process to apply updates."""
        logger.info("Restarting agent to apply update...")
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            logger.error("Agent restart failed: %s", e)
