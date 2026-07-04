# KOVIRX Endpoint Agent

Enterprise cross-platform botnet detection agent for Windows, Linux, and macOS.

## Architecture

```
endpoint-agent/
├── main.py               # Entry point — full agent lifecycle
├── config.py             # Pydantic settings (env vars / .env)
├── models.py             # Data models
│
├── capture/              # Packet Capture Engine
│   ├── sniffer.py        # Scapy-based packet sniffer
│   ├── flow_engine.py    # Stateful flow aggregator
│   ├── protocol_parser.py # TCP/UDP/DNS/ICMP/HTTP/TLS parser
│   └── packet_decoder.py # VLAN/GRE/IPv6 decoder
│
├── services/             # Independent Service Modules
│   ├── scheduler.py      # Background task orchestrator
│   ├── heartbeat.py      # 30s heartbeat with system metrics
│   ├── queue.py          # SQLite-backed priority queue
│   ├── compression.py    # gzip payload compression
│   ├── encryption.py     # AES-256-GCM encryption layer
│   ├── retry.py          # Exponential backoff retry engine
│   ├── updater.py        # Self-update mechanism
│   ├── firewall.py       # Cross-platform IP block/unblock
│   ├── health_monitor.py # System health monitoring
│   ├── risk_engine.py    # Multi-source risk scorer
│   ├── threat_intel.py   # Local IOC database with sync
│   └── logger.py         # Structured JSON logging
│
├── client/               # Backend Communication
│   ├── api_client.py     # REST API client (JWT auth)
│   └── websocket_client.py # WebSocket command listener
│
├── ml/                   # Local ML Inference
│   ├── detection_engine.py  # XGBoost + Isolation Forest
│   └── feature_extractor.py # 22-dim feature extraction
│
├── behavior/             # Behavior Analysis Engine
│   ├── analyzer.py       # DNS beaconing, DGA, exfiltration
│   ├── patterns.py       # Port scan, lateral movement
│   └── session_tracker.py # Long-lived session monitoring
│
└── collectors/           # System Telemetry Collectors
    ├── base.py           # Abstract collector interface
    └── system.py         # CPU/RAM/network metrics
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure (optional — uses defaults)
export KOVIRX_AGENT_SERVER_URL=http://127.0.0.1:8000

# Run the agent (requires admin/root for packet capture)
sudo python main.py
```

## Detection Pipeline

```
Packets → Flows → Features → ML → Behavior → Risk Score → Alert
                                    ↑              ↑
                              IOC Database    History Score
```

### Risk Score Composition

| Source          | Weight | Description                      |
|-----------------|--------|----------------------------------|
| ML Score        | 40%    | XGBoost + Isolation Forest       |
| IOC Match       | 25%    | Threat intelligence database     |
| Behavior Score  | 25%    | Temporal pattern analysis        |
| History Score   | 10%    | Device risk history (server-side)|

## Configuration

All settings via environment variables with `KOVIRX_AGENT_` prefix:

| Variable                      | Default             | Description                    |
|-------------------------------|---------------------|--------------------------------|
| `KOVIRX_AGENT_SERVER_URL`     | `http://127.0.0.1:8000` | Backend API URL           |
| `KOVIRX_AGENT_HEARTBEAT_INTERVAL` | `30`           | Heartbeat interval (seconds)   |
| `KOVIRX_AGENT_CAPTURE_INTERFACE` | `None` (all)     | Network interface to sniff     |
| `KOVIRX_AGENT_LOG_LEVEL`     | `INFO`               | Log level                      |
| `KOVIRX_AGENT_COMPRESSION_ENABLED` | `true`         | gzip compress payloads        |
| `KOVIRX_AGENT_AUTO_UPDATE_ENABLED` | `false`        | Enable self-updates           |
