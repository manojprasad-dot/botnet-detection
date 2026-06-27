import logging
import threading
from typing import Callable
from scapy.all import sniff
from scapy.layers.inet import IP

logger = logging.getLogger("kovirx.agent.capture.sniffer")


class PacketSniffer:
    """
    Cross-platform packet sniffer daemon utilizing Scapy.
    Captures live IP packets in the background.
    """

    def __init__(self, interface: str | None = None, filter_str: str = "ip"):
        self.interface = interface
        self.filter_str = filter_str
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, callback: Callable[[IP], None]) -> None:
        """Start packet capture in a daemon background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("PacketSniffer is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(callback,),
            name="SnifferThread",
            daemon=True
        )
        self._thread.start()
        logger.info("PacketSniffer background service started.")

    def stop(self) -> None:
        """Stop packet capture and wait for thread to terminate."""
        if not self._thread or not self._thread.is_alive():
            return

        logger.info("Stopping PacketSniffer background service...")
        self._stop_event.set()
        # Wake up Scapy's sniff loop by sending a dummy packet if necessary, or rely on timeout.
        self._thread.join(timeout=3.0)
        logger.info("PacketSniffer background service stopped.")

    def _run(self, callback: Callable[[IP], None]) -> None:
        """Sniff loop execution block."""
        try:
            sniff(
                iface=self.interface,
                filter=self.filter_str,
                prn=lambda pkt: callback(pkt) if IP in pkt else None,
                stop_filter=lambda pkt: self._stop_event.is_set(),
                store=False,
                timeout=2,  # check stop_filter periodically
            )
        except Exception as e:
            logger.error("Error in Scapy sniff thread: %s", e)
