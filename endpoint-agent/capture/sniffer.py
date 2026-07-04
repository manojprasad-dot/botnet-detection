"""
KOVIRX Endpoint Agent — Packet Sniffer.

Cross-platform packet sniffer utilizing Scapy with configurable interface,
filter, and timeout settings. Runs in a daemon background thread.
"""

import logging
import threading
from typing import Callable

from scapy.all import sniff
from scapy.layers.inet import IP

logger = logging.getLogger("kovirx.agent.capture.sniffer")


class PacketSniffer:
    """
    Cross-platform packet capture engine using Scapy.

    Captures live IP packets in a daemon background thread with
    configurable interface, BPF filter, and batch timeout.
    """

    def __init__(
        self,
        interface: str | None = None,
        filter_str: str = "ip",
        timeout: float = 0.5,
    ):
        self.interface = interface
        self.filter_str = filter_str
        self.timeout = timeout
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.packets_captured: int = 0

    def start(self, callback: Callable[[IP], None]) -> None:
        """Start packet capture in a daemon background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("PacketSniffer is already running.")
            return

        self._stop_event.clear()
        self.packets_captured = 0
        self._thread = threading.Thread(
            target=self._run,
            args=(callback,),
            name="SnifferThread",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "PacketSniffer started (interface=%s, filter='%s', timeout=%.1fs)",
            self.interface or "all", self.filter_str, self.timeout,
        )

    def stop(self) -> None:
        """Stop packet capture and wait for thread to terminate."""
        if not self._thread or not self._thread.is_alive():
            return

        logger.info("Stopping PacketSniffer...")
        self._stop_event.set()
        self._thread.join(timeout=self.timeout + 2.0)
        logger.info(
            "PacketSniffer stopped. Total packets captured: %d",
            self.packets_captured,
        )

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self, callback: Callable[[IP], None]) -> None:
        """Main sniff loop with periodic stop checks."""
        while not self._stop_event.is_set():
            try:
                sniff(
                    iface=self.interface,
                    filter=self.filter_str,
                    prn=lambda pkt: self._handle_packet(pkt, callback),
                    stop_filter=lambda _: self._stop_event.is_set(),
                    store=False,
                    timeout=self.timeout,
                )
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error("Sniffer error: %s", e)

    def _handle_packet(self, pkt, callback: Callable[[IP], None]) -> None:
        """Process a single captured packet."""
        if IP in pkt:
            self.packets_captured += 1
            try:
                callback(pkt)
            except Exception as e:
                logger.error("Packet callback error: %s", e)
