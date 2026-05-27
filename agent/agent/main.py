import argparse
import platform
import socket
import time

from .client import PlatformApiClient
from .collectors.system import SystemTelemetryCollector
from .config import settings
from .models import DeviceRegistration, TelemetryBatch


def build_registration() -> DeviceRegistration:
    return DeviceRegistration(
        hostname=socket.gethostname(),
        ip_address=resolve_ip_address(),
        operating_system=normalize_os_name(),
        os_version=platform.version(),
        agent_version=settings.agent_version,
        architecture=platform.machine(),
        tags=["mvp", "cross-platform-agent"],
    )


def normalize_os_name() -> str:
    mapping = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}
    return mapping.get(platform.system(), "unknown")


def resolve_ip_address() -> str | None:
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return None


def run_once(server_url: str) -> None:
    client = PlatformApiClient(server_url=server_url)
    registration = build_registration()
    registered_device = client.register_device(registration)
    collector = SystemTelemetryCollector()
    batch = TelemetryBatch(
        device_id=registered_device["device_id"],
        events=collector.collect(),
    )
    result = client.send_telemetry(batch)
    print(f"Registered device: {registered_device['device_id']}")
    print(f"Ingested events: {result['ingested_events']}")
    print(f"Generated alerts: {len(result['generated_alerts'])}")


def run_loop(server_url: str, interval_seconds: int) -> None:
    client = PlatformApiClient(server_url=server_url)
    registration = build_registration()
    registered_device = client.register_device(registration)
    collector = SystemTelemetryCollector()

    print(f"Agent registered as device {registered_device['device_id']}")
    while True:
        batch = TelemetryBatch(
            device_id=registered_device["device_id"],
            events=collector.collect(),
        )
        result = client.send_telemetry(batch)
        print(
            f"Sent {result['ingested_events']} events, "
            f"alerts={len(result['generated_alerts'])}"
        )
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.once:
        run_once(args.server)
        return

    run_loop(args.server, args.interval)


if __name__ == "__main__":
    main()
