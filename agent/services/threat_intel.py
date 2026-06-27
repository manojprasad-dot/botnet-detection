import logging

logger = logging.getLogger("kovirx.agent.services.threat_intel")


class LocalThreatIntel:
    """
    Lightweight Client-side interface to verify remote target destinations 
    against known malicious threat indicators.
    """

    def __init__(self):
        # Local cached blocklist of known C2 / malicious IPs and domains.
        # Updated dynamically or loaded on agent startup.
        self.malicious_ips = {
            "185.220.101.1",  # Tor exit nodes
            "45.227.254.10", # Known botnet controller
            "103.20.192.5",
        }
        self.malicious_domains = {
            "c2-panel.kovirx.local",
            "botnet-command.xyz",
            "malware-dns.net",
            "exfiltration-target.org"
        }

    def check_destination(self, ip: str, domain: str | None = None) -> tuple[bool, float]:
        """
        Check destination IP and DNS query domain.
        Returns:
            - matched: bool (true if IOC matched)
            - score: float (reputation penalty score from 0.0 to 1.0)
        """
        if ip in self.malicious_ips:
            logger.warning("Threat Intel Match: Malicious IP detected: %s", ip)
            return True, 0.95

        if domain and domain in self.malicious_domains:
            logger.warning("Threat Intel Match: Malicious Domain detected: %s", domain)
            return True, 0.98

        return False, 0.0
