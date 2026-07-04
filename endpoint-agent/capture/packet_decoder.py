"""
KOVIRX Endpoint Agent — Packet Decoder.

Low-level frame decoding for VLAN tags, tunneling protocols,
IPv4/IPv6 dual-stack, and fragmentation tracking.
"""

import logging
from dataclasses import dataclass

from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Dot1Q, GRE

logger = logging.getLogger("kovirx.agent.capture.packet_decoder")


@dataclass
class DecodedFrame:
    """Result of frame-level packet decoding."""
    has_vlan: bool = False
    vlan_id: int | None = None
    has_tunnel: bool = False
    tunnel_type: str | None = None
    is_ipv6: bool = False
    is_fragment: bool = False
    fragment_offset: int = 0
    inner_ip_src: str | None = None
    inner_ip_dst: str | None = None
    raw_length: int = 0


class PacketDecoder:
    """
    Low-level frame decoder for advanced packet analysis.

    Supports:
        - VLAN tag (802.1Q) stripping
        - GRE tunnel detection
        - IPv4/IPv6 dual-stack identification
        - IP fragmentation tracking
    """

    def decode(self, pkt) -> DecodedFrame:
        """Decode a raw packet and extract frame-level metadata."""
        frame = DecodedFrame(raw_length=len(pkt))

        # ── VLAN Detection ────────────────────────────────────────
        if Dot1Q in pkt:
            frame.has_vlan = True
            frame.vlan_id = pkt[Dot1Q].vlan

        # ── GRE Tunnel Detection ──────────────────────────────────
        if GRE in pkt:
            frame.has_tunnel = True
            frame.tunnel_type = "GRE"
            # Try to extract inner IP
            gre_layer = pkt[GRE]
            if IP in gre_layer:
                inner = gre_layer[IP]
                frame.inner_ip_src = inner.src
                frame.inner_ip_dst = inner.dst

        # ── IPv6 Detection ────────────────────────────────────────
        if IPv6 in pkt:
            frame.is_ipv6 = True

        # ── Fragmentation Detection ───────────────────────────────
        if IP in pkt:
            ip_layer = pkt[IP]
            # Check MF (More Fragments) flag or non-zero fragment offset
            if ip_layer.flags.MF or ip_layer.frag > 0:
                frame.is_fragment = True
                frame.fragment_offset = ip_layer.frag

        return frame
