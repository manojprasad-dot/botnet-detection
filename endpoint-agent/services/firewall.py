"""
KOVIRX Endpoint Agent — Cross-Platform Firewall Manager.

Provides IP blocking and unblocking across Windows (netsh),
Linux (iptables), and macOS (pfctl) using subprocess commands.
"""

import logging
import platform
import subprocess

logger = logging.getLogger("kovirx.agent.firewall")


class FirewallManager:
    """
    Cross-platform firewall management for automated threat response.

    Supports:
        - Windows: netsh advfirewall
        - Linux: iptables
        - macOS: pfctl
    """

    def __init__(self):
        self._os = platform.system()
        self._blocked_ips: set[str] = set()

    def block_ip(self, ip: str, rule_name: str | None = None) -> bool:
        """
        Block inbound and outbound traffic for an IP address.

        Args:
            ip: IP address to block
            rule_name: Optional rule name (auto-generated if None)

        Returns:
            True if the rule was applied successfully
        """
        if ip in self._blocked_ips:
            logger.debug("IP %s is already blocked.", ip)
            return True

        rule_name = rule_name or f"KOVIRX_BLOCK_{ip.replace('.', '_')}"

        try:
            if self._os == "Windows":
                success = self._block_windows(ip, rule_name)
            elif self._os == "Linux":
                success = self._block_linux(ip)
            elif self._os == "Darwin":
                success = self._block_macos(ip)
            else:
                logger.warning("Unsupported OS for firewall management: %s", self._os)
                return False

            if success:
                self._blocked_ips.add(ip)
                logger.info("Blocked IP: %s (rule: %s)", ip, rule_name)
            return success

        except Exception as e:
            logger.error("Failed to block IP %s: %s", ip, e)
            return False

    def unblock_ip(self, ip: str, rule_name: str | None = None) -> bool:
        """
        Remove block rule for an IP address.

        Args:
            ip: IP address to unblock
            rule_name: Rule name used when blocking

        Returns:
            True if the rule was removed successfully
        """
        rule_name = rule_name or f"KOVIRX_BLOCK_{ip.replace('.', '_')}"

        try:
            if self._os == "Windows":
                success = self._unblock_windows(rule_name)
            elif self._os == "Linux":
                success = self._unblock_linux(ip)
            elif self._os == "Darwin":
                success = self._unblock_macos(ip)
            else:
                return False

            if success:
                self._blocked_ips.discard(ip)
                logger.info("Unblocked IP: %s", ip)
            return success

        except Exception as e:
            logger.error("Failed to unblock IP %s: %s", ip, e)
            return False

    @property
    def blocked_ips(self) -> list[str]:
        """Return list of currently blocked IPs."""
        return sorted(self._blocked_ips)

    # ── Windows ───────────────────────────────────────────────────

    def _block_windows(self, ip: str, rule_name: str) -> bool:
        # Block inbound
        result_in = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_IN",
                "dir=in", "action=block",
                f"remoteip={ip}",
                "protocol=any",
            ],
            capture_output=True, text=True, timeout=10,
        )
        # Block outbound
        result_out = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_OUT",
                "dir=out", "action=block",
                f"remoteip={ip}",
                "protocol=any",
            ],
            capture_output=True, text=True, timeout=10,
        )
        return result_in.returncode == 0 and result_out.returncode == 0

    def _unblock_windows(self, rule_name: str) -> bool:
        result_in = subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}_IN"],
            capture_output=True, text=True, timeout=10,
        )
        result_out = subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}_OUT"],
            capture_output=True, text=True, timeout=10,
        )
        return result_in.returncode == 0 or result_out.returncode == 0

    # ── Linux ─────────────────────────────────────────────────────

    def _block_linux(self, ip: str) -> bool:
        result_in = subprocess.run(
            ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True, text=True, timeout=10,
        )
        result_out = subprocess.run(
            ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"],
            capture_output=True, text=True, timeout=10,
        )
        return result_in.returncode == 0 and result_out.returncode == 0

    def _unblock_linux(self, ip: str) -> bool:
        result_in = subprocess.run(
            ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True, text=True, timeout=10,
        )
        result_out = subprocess.run(
            ["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"],
            capture_output=True, text=True, timeout=10,
        )
        return result_in.returncode == 0 or result_out.returncode == 0

    # ── macOS ─────────────────────────────────────────────────────

    def _block_macos(self, ip: str) -> bool:
        # Add to pf table
        result = subprocess.run(
            ["pfctl", "-t", "kovirx_blocked", "-T", "add", ip],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0

    def _unblock_macos(self, ip: str) -> bool:
        result = subprocess.run(
            ["pfctl", "-t", "kovirx_blocked", "-T", "delete", ip],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
