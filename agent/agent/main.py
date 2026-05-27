import argparse
import hashlib
import platform
import socket
import time
import uuid

from .client import PlatformApiClient
from .collectors.simulated import SimulatedBotnetCollector
from .collectors.system import SystemTelemetryCollector
from .config import settings
from .models import DeviceRegistration, TelemetryBatch, TelemetryEvent


def build_registration(simulate_botnet: bool = False) -> DeviceRegistration:
    tags = ["mvp", "cross-platform-agent"]
    if simulate_botnet:
        tags.append("simulation")

    return DeviceRegistration(
        device_fingerprint=build_device_fingerprint(),
        hostname=socket.gethostname(),
        ip_address=resolve_ip_address(),
        operating_system=normalize_os_name(),
        os_version=platform.version(),
        agent_version=settings.agent_version,
        architecture=platform.machine(),
        tags=tags,
    )


def normalize_os_name() -> str:
    mapping = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}
    return mapping.get(platform.system(), "unknown")


def resolve_ip_address() -> str | None:
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return None


def build_device_fingerprint() -> str:
    components = [
        socket.gethostname(),
        platform.system(),
        platform.machine(),
        str(uuid.getnode()),
    ]
    digest = hashlib.sha256("|".join(components).encode("utf-8")).hexdigest()
    return digest


def collect_events(simulate_botnet: bool) -> list[TelemetryEvent]:
    events = SystemTelemetryCollector().collect()
    if simulate_botnet:
        events.extend(SimulatedBotnetCollector().collect())
    return events


def print_alerts(alerts: list[dict]) -> None:
    for alert in alerts:
        print(
            f"[{alert['severity'].upper()}] {alert['title']} "
            f"confidence={alert['confidence_score']}"
        )


def run_once(server_url: str, simulate_botnet: bool) -> None:
    client = PlatformApiClient(server_url=server_url)
    registration = build_registration(simulate_botnet=simulate_botnet)
    registered_device = client.register_device(registration)
    batch = TelemetryBatch(
        device_id=registered_device["device_id"],
        events=collect_events(simulate_botnet),
    )
    result = client.send_telemetry(batch)
    print(f"Registered device: {registered_device['device_id']}")
    print(f"Ingested events: {result['ingested_events']}")
    print(f"Generated alerts: {len(result['generated_alerts'])}")
    print_alerts(result["generated_alerts"])


def run_loop(server_url: str, interval_seconds: int, simulate_botnet: bool) -> None:
    client = PlatformApiClient(server_url=server_url)
    registration = build_registration(simulate_botnet=simulate_botnet)
    registered_device = client.register_device(registration)

    print(f"Agent registered as device {registered_device['device_id']}")
    while True:
        batch = TelemetryBatch(
            device_id=registered_device["device_id"],
            events=collect_events(simulate_botnet),
        )
        result = client.send_telemetry(batch)
        print(
            f"Sent {result['ingested_events']} events, "
            f"alerts={len(result['generated_alerts'])}"
        )
        print_alerts(result["generated_alerts"])
        time.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-platform endpoint telemetry agent")
    parser.add_argument("--server", default=settings.server_url, help="Backend API base URL")
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.interval_seconds,
        help="Telemetry send interval in seconds",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Register and send a single telemetry batch",
    )
    parser.add_argument(
        "--simulate-botnet",
        action="store_true",
        help="Inject suspicious events so the detection pipeline can be demoed safely",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.once:
        run_once(args.server, args.simulate_botnet)
        return

    run_loop(args.server, args.interval, args.simulate_botnet)


if __name__ == "__main__":
    main()
