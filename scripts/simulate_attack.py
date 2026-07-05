"""
KOVIRX — Attack Simulation Script.

Sends crafted malicious telemetry to the backend to test the full pipeline:
    Telemetry → ML Prediction → Alert → WebSocket → Dashboard

Usage:
    python scripts/simulate_attack.py

    # Or with custom backend URL:
    python scripts/simulate_attack.py --url https://your-backend.up.railway.app
"""

import argparse
import json
import random
import time
import requests

# ── Configuration ────────────────────────────────────────────────

DEFAULT_URL = "https://captivating-inspiration-production-730c.up.railway.app"
EMAIL = "admin@kovirx.com"
PASSWORD = "admin123"


def get_token(base_url: str, email: str = EMAIL, password: str = PASSWORD) -> str:
    """Authenticate and get JWT token."""
    print(f"\n[Auth] Authenticating with {base_url}...")
    resp = requests.post(
        f"{base_url}/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    if resp.status_code != 200:
        print(f"[ERROR] Login failed: {resp.status_code} - {resp.text}")
        raise SystemExit(1)

    token = resp.json().get("access_token")
    print(f"[SUCCESS] Authenticated. Token: {token[:20]}...")
    return token


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ── Attack Scenarios ─────────────────────────────────────────────

def dns_tunneling_attack() -> dict:
    """Simulate DNS tunneling / DGA domain — high entropy DNS queries."""
    dga_domains = [
        "x7k9m2p4q8r1.evil-botnet.xyz",
        "a3f8j2k5n9p1.malware-c2.top",
        "h4k7m2q9r3t6.data-exfil.cc",
        "z8x3c7v2b5n1.ransomware.io",
    ]
    domain = random.choice(dga_domains)
    return {
        "flow": {
            "source_ip": "192.168.1.105",
            "source_port": random.randint(40000, 65000),
            "dest_ip": "185.220.101.42",
            "dest_port": 53,
            "protocol": "UDP",
            "packet_count": random.randint(50, 200),
            "byte_count": random.randint(5000, 25000),
            "packets_sent": random.randint(30, 100),
            "packets_recv": random.randint(20, 100),
            "bytes_sent": random.randint(3000, 15000),
            "bytes_recv": random.randint(2000, 10000),
            "flow_duration": round(random.uniform(0.5, 3.0), 3),
            "tcp_flags": None,
            "dns_query": domain,
            "dns_entropy": round(random.uniform(4.2, 4.8), 4),
            "beacon_interval": round(random.uniform(0.01, 0.05), 4),
            "failed_connections": 0,
            "start_time": "2026-07-04T08:15:03Z",
            "end_time": "2026-07-04T08:15:06Z",
        },
        "prediction": {
            "xgb_score": round(random.uniform(0.85, 0.97), 4),
            "is_anomaly": True,
            "threat_type": "DNS Abuse",
            "features_used": {
                "max_dns_entropy": 4.5,
                "dns_query_count": 10.0,
            }
        },
        "risk": {
            "risk_score": random.randint(78, 95),
            "severity": "critical",
            "recommendation": "Quarantine device immediately and run offline malware scan.",
        },
        "collected_at": "2026-07-04T08:15:06Z"
    }


def c2_beaconing_attack() -> dict:
    """Simulate C2 beaconing — regular interval connections to suspicious IP."""
    c2_ips = ["45.33.32.156", "198.51.100.23", "203.0.113.42", "91.219.236.18"]
    return {
        "flow": {
            "source_ip": "192.168.1.42",
            "source_port": random.randint(40000, 65000),
            "dest_ip": random.choice(c2_ips),
            "dest_port": 443,
            "protocol": "TCP",
            "packet_count": random.randint(10, 40),
            "byte_count": random.randint(2000, 8000),
            "packets_sent": random.randint(5, 20),
            "packets_recv": random.randint(5, 20),
            "bytes_sent": random.randint(1000, 4000),
            "bytes_recv": random.randint(1000, 4000),
            "flow_duration": round(random.uniform(28.0, 32.0), 3),
            "tcp_flags": "S,A",
            "dns_query": None,
            "dns_entropy": 0.0,
            "beacon_interval": round(random.uniform(0.001, 0.01), 4),
            "failed_connections": 0,
            "start_time": "2026-07-04T08:16:00Z",
            "end_time": "2026-07-04T08:16:30Z",
        },
        "prediction": {
            "xgb_score": round(random.uniform(0.88, 0.96), 4),
            "is_anomaly": True,
            "threat_type": "Beaconing",
            "features_used": {
                "beacon_interval_score": 0.9,
                "connection_count": 5.0,
            }
        },
        "risk": {
            "risk_score": random.randint(82, 96),
            "severity": "critical",
            "recommendation": "Block C2 destination IP and investigate endpoint registry.",
        },
        "collected_at": "2026-07-04T08:16:30Z"
    }


def port_scan_attack() -> dict:
    """Simulate port scanning — connections to many destination ports."""
    return {
        "flow": {
            "source_ip": "192.168.1.200",
            "source_port": random.randint(40000, 65000),
            "dest_ip": "10.0.0.50",
            "dest_port": random.randint(1, 1024),
            "protocol": "TCP",
            "packet_count": random.randint(3, 8),
            "byte_count": random.randint(200, 600),
            "packets_sent": random.randint(2, 5),
            "packets_recv": random.randint(1, 3),
            "bytes_sent": random.randint(100, 300),
            "bytes_recv": random.randint(100, 300),
            "flow_duration": round(random.uniform(0.01, 0.5), 3),
            "tcp_flags": "S,R",
            "dns_query": None,
            "dns_entropy": 0.0,
            "beacon_interval": 0.0,
            "failed_connections": random.randint(3, 8),
            "start_time": "2026-07-04T08:17:00Z",
            "end_time": "2026-07-04T08:17:01Z",
        },
        "prediction": {
            "xgb_score": round(random.uniform(0.72, 0.85), 4),
            "is_anomaly": True,
            "threat_type": "Port Scan",
            "features_used": {
                "failed_connection_ratio": 0.8,
                "tcp_flag_score": 0.5,
            }
        },
        "risk": {
            "risk_score": random.randint(65, 80),
            "severity": "high",
            "recommendation": "Block port scan source host and review internal network map.",
        },
        "collected_at": "2026-07-04T08:17:01Z"
    }


def data_exfiltration_attack() -> dict:
    """Simulate data exfiltration — high outbound byte ratio."""
    return {
        "flow": {
            "source_ip": "192.168.1.77",
            "source_port": random.randint(40000, 65000),
            "dest_ip": "104.21.45.12",
            "dest_port": 443,
            "protocol": "TCP",
            "packet_count": random.randint(500, 2000),
            "byte_count": random.randint(500000, 2000000),
            "packets_sent": random.randint(400, 1800),
            "packets_recv": random.randint(50, 200),
            "bytes_sent": random.randint(450000, 1800000),
            "bytes_recv": random.randint(10000, 50000),
            "flow_duration": round(random.uniform(30.0, 120.0), 3),
            "tcp_flags": "S,A,P,F",
            "dns_query": None,
            "dns_entropy": 0.0,
            "beacon_interval": 0.0,
            "failed_connections": 0,
            "start_time": "2026-07-04T08:18:00Z",
            "end_time": "2026-07-04T08:20:00Z",
        },
        "prediction": {
            "xgb_score": round(random.uniform(0.80, 0.92), 4),
            "is_anomaly": True,
            "threat_type": "Command & Control",
            "features_used": {
                "bytes_sent": 1500000.0,
                "outbound_frequency": 15.0,
            }
        },
        "risk": {
            "risk_score": random.randint(75, 90),
            "severity": "high",
            "recommendation": "Quarantine exfiltration target and isolate host from internet.",
        },
        "collected_at": "2026-07-04T08:20:00Z"
    }


# ── Attack Sequences ─────────────────────────────────────────────

ATTACK_SCENARIOS = [
    ("DNS Tunneling / DGA", dns_tunneling_attack),
    ("C2 Beaconing", c2_beaconing_attack),
    ("Port Scan", port_scan_attack),
    ("Data Exfiltration", data_exfiltration_attack),
]


def run_attack_sequence(base_url: str, token: str, rounds: int = 2, delay: float = 2.0):
    """Run the full attack simulation."""
    url = f"{base_url}/api/v1/telemetry/ingest"
    total_sent = 0
    total_alerts = 0

    print(f"\n{'='*60}")
    print(f"  [ATTACK] KOVIRX ATTACK SIMULATION - {rounds} round(s)")
    print(f"  Target: {base_url}")
    print(f"{'='*60}\n")

    import uuid
    from datetime import datetime, timezone
    device_id = str(uuid.uuid4())

    for round_num in range(1, rounds + 1):
        print(f"--- Round {round_num}/{rounds} -----------------------------")

        for name, generator in ATTACK_SCENARIOS:
            event = generator()
            event["collected_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            payload = {
                "device_id": device_id,
                "events": [event],
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            try:
                resp = requests.post(url, json=payload, headers=headers(token), timeout=10)
                total_sent += 1

                if resp.status_code == 200:
                    result = resp.json()
                    alerts_created = result.get("alerts_created", 0)
                    total_alerts += alerts_created
                    risk = event["risk"]["risk_score"]
                    severity = event["risk"]["severity"].upper()

                    alert_icon = "[ALERT]" if alerts_created > 0 else "[INFO]"
                    print(f"  {alert_icon} {name:<28} Risk={risk:>3}% [{severity:<8}] "
                          f"Alerts={alerts_created}")
                else:
                    print(f"  [FAIL] {name:<28} HTTP {resp.status_code}: {resp.text[:80]}")

            except Exception as e:
                print(f"  [ERROR] {name:<28} Error: {e}")

            time.sleep(delay)

        print()

    print(f"{'='*60}")
    print(f"  RESULTS: {total_sent} payloads sent, {total_alerts} alerts generated")
    print(f"  Check your dashboard for real-time alerts!")
    print(f"{'='*60}\n")


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KOVIRX Attack Simulation")
    parser.add_argument("--url", default=DEFAULT_URL, help="Backend URL")
    parser.add_argument("--email", default=EMAIL, help="Login email")
    parser.add_argument("--password", default=PASSWORD, help="Login password")
    parser.add_argument("--rounds", type=int, default=2, help="Number of attack rounds")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between attacks (seconds)")
    args = parser.parse_args()

    # Pass the custom email and password down by modifying the module-level values dynamically
    # or updating the get_token function to accept credentials. Let's update get_token call.
    token = get_token(args.url, args.email, args.password)
    run_attack_sequence(args.url, token, rounds=args.rounds, delay=args.delay)


if __name__ == "__main__":
    main()
