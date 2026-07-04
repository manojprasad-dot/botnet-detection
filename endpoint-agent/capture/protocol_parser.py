"""
KOVIRX Endpoint Agent — Protocol Parser.

Protocol-specific parsers for TCP, UDP, DNS, ICMP, HTTP, and HTTPS.
Extracts structured metadata for flow enrichment and behavior analysis.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.dns import DNS, DNSQR, DNSRR
from scapy.layers.http import HTTPRequest, HTTPResponse
from scapy.layers.tls.record import TLS
from scapy.layers.tls.handshake import TLSClientHello

logger = logging.getLogger("kovirx.agent.capture.protocol_parser")


@dataclass
class ProtocolMetadata:
    """Parsed protocol-specific metadata from a packet."""
    protocol: str = "OTHER"
    src_port: int | None = None
    dst_port: int | None = None
    tcp_flags: str = ""
    tcp_seq: int | None = None
    tcp_ack: int | None = None
    tcp_window: int | None = None

    # DNS fields
    dns_query: str | None = None
    dns_query_type: str | None = None
    dns_response_ips: list[str] = field(default_factory=list)
    dns_is_response: bool = False

    # HTTP fields
    http_method: str | None = None
    http_host: str | None = None
    http_path: str | None = None
    http_user_agent: str | None = None
    http_status: int | None = None

    # TLS/HTTPS fields
    tls_sni: str | None = None
    tls_version: str | None = None
    ja3_fingerprint: str | None = None

    # ICMP fields
    icmp_type: int | None = None
    icmp_code: int | None = None

    # General
    payload_size: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class ProtocolParser:
    """
    Extracts protocol-specific metadata from Scapy packets.

    Supports: TCP, UDP, DNS, ICMP, HTTP, HTTPS/TLS.
    """

    def parse(self, pkt) -> ProtocolMetadata:
        """Parse a packet and return structured protocol metadata."""
        meta = ProtocolMetadata()

        if IP not in pkt:
            return meta

        meta.payload_size = len(pkt)

        # ── TCP ───────────────────────────────────────────────────
        if TCP in pkt:
            meta.protocol = "TCP"
            meta.src_port = pkt[TCP].sport
            meta.dst_port = pkt[TCP].dport
            meta.tcp_flags = str(pkt[TCP].flags)
            meta.tcp_seq = pkt[TCP].seq
            meta.tcp_ack = pkt[TCP].ack
            meta.tcp_window = pkt[TCP].window

            # Check for HTTP
            self._parse_http(pkt, meta)

            # Check for TLS
            self._parse_tls(pkt, meta)

        # ── UDP ───────────────────────────────────────────────────
        elif UDP in pkt:
            meta.protocol = "UDP"
            meta.src_port = pkt[UDP].sport
            meta.dst_port = pkt[UDP].dport

        # ── ICMP ──────────────────────────────────────────────────
        elif ICMP in pkt:
            meta.protocol = "ICMP"
            meta.icmp_type = pkt[ICMP].type
            meta.icmp_code = pkt[ICMP].code

        # ── DNS (can be over TCP or UDP) ──────────────────────────
        if DNS in pkt:
            self._parse_dns(pkt, meta)

        return meta

    def _parse_dns(self, pkt, meta: ProtocolMetadata) -> None:
        """Extract DNS query/response information."""
        dns_layer = pkt[DNS]

        if dns_layer.qr == 0:  # Query
            meta.dns_is_response = False
            if dns_layer.qd:
                meta.dns_query = dns_layer.qd.qname.decode("utf-8", errors="ignore").rstrip(".")
                # Map query type number to name
                qtype = dns_layer.qd.qtype
                type_map = {1: "A", 2: "NS", 5: "CNAME", 15: "MX", 16: "TXT", 28: "AAAA", 33: "SRV"}
                meta.dns_query_type = type_map.get(qtype, str(qtype))
        else:  # Response
            meta.dns_is_response = True
            if dns_layer.qd:
                meta.dns_query = dns_layer.qd.qname.decode("utf-8", errors="ignore").rstrip(".")
            # Extract answer IPs
            for i in range(dns_layer.ancount):
                try:
                    rr = dns_layer.an[i]
                    if hasattr(rr, "rdata"):
                        meta.dns_response_ips.append(str(rr.rdata))
                except Exception:
                    pass

    def _parse_http(self, pkt, meta: ProtocolMetadata) -> None:
        """Extract HTTP request/response fields."""
        try:
            if HTTPRequest in pkt:
                http = pkt[HTTPRequest]
                meta.http_method = http.Method.decode("utf-8", errors="ignore") if http.Method else None
                meta.http_host = http.Host.decode("utf-8", errors="ignore") if http.Host else None
                meta.http_path = http.Path.decode("utf-8", errors="ignore") if http.Path else None
                if http.User_Agent:
                    meta.http_user_agent = http.User_Agent.decode("utf-8", errors="ignore")
            elif HTTPResponse in pkt:
                http = pkt[HTTPResponse]
                meta.http_status = int(http.Status_Code.decode()) if http.Status_Code else None
        except Exception:
            pass

    def _parse_tls(self, pkt, meta: ProtocolMetadata) -> None:
        """Extract TLS/HTTPS metadata including SNI."""
        try:
            if TLS in pkt:
                tls = pkt[TLS]
                # TLS version
                if hasattr(tls, "version"):
                    version_map = {
                        0x0301: "TLS 1.0",
                        0x0302: "TLS 1.1",
                        0x0303: "TLS 1.2",
                        0x0304: "TLS 1.3",
                    }
                    meta.tls_version = version_map.get(tls.version, f"0x{tls.version:04x}")

            if TLSClientHello in pkt:
                client_hello = pkt[TLSClientHello]
                # Extract SNI from extensions
                if hasattr(client_hello, "ext") and client_hello.ext:
                    for ext in client_hello.ext:
                        if hasattr(ext, "servernames"):
                            for sn in ext.servernames:
                                if hasattr(sn, "servername"):
                                    meta.tls_sni = sn.servername.decode("utf-8", errors="ignore")
                                    break
        except Exception:
            pass
