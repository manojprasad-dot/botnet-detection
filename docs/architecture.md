# Cross-Platform Platform Architecture

## Vision

This project is organized as a distributed detection platform with a thin endpoint agent and centralized analysis services.

## MVP Components

- `agent/`: cross-platform telemetry collector and secure API client
- `backend/`: registration, telemetry ingestion, alert generation
- `docs/`: architecture, rollout, and evolution guidance

## Target Enterprise Shape

```text
Endpoint Agents -> API Gateway -> Telemetry Ingestion -> Feature Extraction
               -> Threat Detection -> Alerting -> Dashboard / SOC
```

## Planned Deployment Layers

### Edge / Endpoint

- Windows native service
- Linux daemon
- macOS background agent
- Android VPN telemetry app
- IoT lightweight collector

### Control Plane

- API gateway
- Device identity and registration
- Policy distribution
- Threat intelligence updates

### Data Plane

- Telemetry ingestion
- Queue or stream layer
- Feature extraction workers
- Detection services
- Alerting services

## Detection Strategy

### Layer 1: Edge Detection

- Fast signatures
- Connection-rate thresholds
- IOC lookups
- Low-cost heuristics

### Layer 2: Cloud Detection

- Aggregated telemetry correlation
- Sequence and anomaly models
- Threat intelligence enrichment
- Multi-device campaign analysis

## OS-Specific Roadmap

### Windows

- ETW providers
- Windows Filtering Platform integration
- Service installation via NSSM or native service wrapper during MVP

### Linux

- `psutil` and `/proc` during MVP
- eBPF and audit integration in advanced phase

### macOS

- `psutil` and system metadata during MVP
- NetworkExtension and launchd integration later

### Android

- Separate client using `VPNService`
- Metadata-only traffic extraction without root

## Security Model

- TLS for all agent-server communication
- Device registration token or certificate
- Signed configuration updates
- Rotating agent credentials
- Auditable alert history

## Suggested Near-Term Milestones

1. Persist devices, telemetry, and alerts in PostgreSQL.
2. Add authentication and enrollment flow.
3. Introduce message queueing for ingestion decoupling.
4. Add a web dashboard.
5. Add OS-specific collectors and feature extraction workers.
