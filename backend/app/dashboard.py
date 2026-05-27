def render_command_center() -> str:
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>KOVIRX Threat Command Center</title>
        <style>
            :root {
                color-scheme: dark;
                --bg: #07111f;
                --bg-soft: #0c1830;
                --panel: rgba(10, 21, 40, 0.88);
                --panel-border: rgba(113, 151, 204, 0.18);
                --ink: #eef5ff;
                --muted: #8ea5c5;
                --safe: #46d6e5;
                --warning: #f0b24f;
                --threat: #f26363;
                --critical: #c71f37;
                --accent: #7df2d4;
                --grid: rgba(105, 136, 180, 0.08);
                --shadow: 0 18px 40px rgba(2, 10, 20, 0.45);
                --font-ui: "Segoe UI", "Trebuchet MS", sans-serif;
                --font-display: "Bahnschrift", "Segoe UI", sans-serif;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                color: var(--ink);
                font-family: var(--font-ui);
                background:
                    radial-gradient(circle at top left, rgba(47, 92, 163, 0.25), transparent 28%),
                    radial-gradient(circle at bottom right, rgba(125, 242, 212, 0.12), transparent 24%),
                    linear-gradient(180deg, #06101c 0%, #07111f 52%, #091426 100%);
            }

            body::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background-image:
                    linear-gradient(var(--grid) 1px, transparent 1px),
                    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
                background-size: 28px 28px;
                opacity: 0.42;
            }

            .app-shell {
                position: relative;
                z-index: 1;
                max-width: 1540px;
                margin: 0 auto;
                padding: 24px;
            }

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 18px;
                margin-bottom: 20px;
            }

            .brand {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .brand-cluster {
                display: flex;
                align-items: center;
                gap: 20px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }

            .brandmark-frame {
                width: 330px;
                height: 170px;
                overflow: hidden;
                border-radius: 26px;
                border: 1px solid rgba(113, 151, 204, 0.2);
                background:
                    radial-gradient(circle at 30% 30%, rgba(125, 242, 212, 0.1), transparent 28%),
                    rgba(8, 19, 36, 0.94);
                box-shadow:
                    inset 0 1px 0 rgba(255, 255, 255, 0.04),
                    0 22px 44px rgba(2, 10, 20, 0.45);
                position: relative;
            }

            .brandmark-frame::after {
                content: "";
                position: absolute;
                inset: 0;
                pointer-events: none;
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.04), transparent 46%);
            }

            .brandmark-frame img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                object-position: 76% 13%;
                transform: scale(1.02);
                filter: saturate(1.08) brightness(1.02);
            }

            .brand-copy {
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-width: 360px;
            }

            .eyebrow {
                display: inline-flex;
                width: fit-content;
                gap: 10px;
                align-items: center;
                padding: 7px 12px;
                border-radius: 999px;
                border: 1px solid rgba(125, 242, 212, 0.28);
                background: rgba(17, 37, 59, 0.8);
                color: var(--accent);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }

            .dot {
                width: 8px;
                height: 8px;
                border-radius: 999px;
                background: var(--accent);
                box-shadow: 0 0 10px rgba(125, 242, 212, 0.8);
                animation: pulseDot 1.8s infinite;
            }

            h1 {
                margin: 0;
                font-family: var(--font-display);
                font-size: clamp(34px, 4vw, 54px);
                letter-spacing: 0.04em;
            }

            .subtitle {
                margin: 0;
                max-width: 720px;
                color: var(--muted);
                font-size: 15px;
                line-height: 1.6;
            }

            .status-strip {
                display: flex;
                gap: 14px;
                flex-wrap: wrap;
                justify-content: flex-end;
            }

            .status-card,
            .panel {
                backdrop-filter: blur(18px);
                background: var(--panel);
                border: 1px solid var(--panel-border);
                border-radius: 22px;
                box-shadow: var(--shadow);
            }

            .status-card {
                min-width: 150px;
                padding: 16px 18px;
            }

            .status-label {
                color: var(--muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }

            .status-value {
                margin-top: 10px;
                font-size: 30px;
                font-weight: 700;
            }

            .layout {
                display: grid;
                grid-template-columns: 280px 1fr 360px;
                gap: 18px;
                align-items: start;
            }

            .panel {
                padding: 18px;
            }

            .panel h2 {
                margin: 0 0 14px;
                font-size: 18px;
                letter-spacing: 0.03em;
            }

            .panel-title-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 16px;
            }

            .tiny {
                font-size: 12px;
                color: var(--muted);
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .legend {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                font-size: 12px;
                color: var(--muted);
            }

            .legend span {
                display: inline-flex;
                gap: 6px;
                align-items: center;
            }

            .swatch {
                width: 10px;
                height: 10px;
                border-radius: 999px;
                display: inline-block;
            }

            .command-stage {
                min-height: 760px;
            }

            .map-shell {
                position: relative;
                overflow: hidden;
                border-radius: 24px;
                min-height: 520px;
                background:
                    radial-gradient(circle at center, rgba(53, 93, 163, 0.22), transparent 35%),
                    linear-gradient(180deg, rgba(6, 15, 29, 0.9), rgba(4, 12, 22, 0.96));
                border: 1px solid rgba(99, 140, 196, 0.14);
            }

            .map-shell::before {
                content: "";
                position: absolute;
                inset: 0;
                background:
                    radial-gradient(circle at center, rgba(125, 242, 212, 0.09), transparent 26%),
                    radial-gradient(circle, rgba(70, 214, 229, 0.07) 1px, transparent 1px);
                background-size: 100% 100%, 26px 26px;
                pointer-events: none;
            }

            .topology-svg {
                display: block;
                width: 100%;
                height: 520px;
            }

            .ai-brain-overlay {
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: 220px;
                height: 220px;
                pointer-events: none;
                display: grid;
                place-items: center;
            }

            .brain-ring {
                position: absolute;
                inset: 0;
                border-radius: 50%;
                border: 1px solid rgba(125, 242, 212, 0.2);
                animation: spinSlow 14s linear infinite;
            }

            .brain-ring::before,
            .brain-ring::after {
                content: "";
                position: absolute;
                inset: 18px;
                border-radius: 50%;
                border: 1px dashed rgba(70, 214, 229, 0.18);
            }

            .brain-core {
                position: relative;
                width: 144px;
                height: 144px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                background:
                    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.12), transparent 26%),
                    radial-gradient(circle, rgba(70, 214, 229, 0.25), rgba(8, 16, 28, 0.96));
                box-shadow:
                    0 0 0 12px rgba(70, 214, 229, 0.05),
                    0 0 48px rgba(70, 214, 229, 0.25);
                text-align: center;
                padding: 18px;
                animation: brainPulse 2.4s ease-in-out infinite;
            }

            .brain-core strong {
                display: block;
                font-size: 13px;
                color: var(--accent);
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .brain-score {
                font-size: 40px;
                font-weight: 700;
                line-height: 1;
            }

            .brain-level {
                margin-top: 8px;
                font-size: 12px;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }

            .battle-grid {
                display: grid;
                grid-template-columns: 1.6fr 1fr;
                gap: 18px;
                margin-top: 18px;
            }

            .device-list {
                display: grid;
                gap: 12px;
            }

            .device-card {
                display: grid;
                grid-template-columns: auto 1fr auto;
                gap: 12px;
                align-items: center;
                padding: 14px;
                border-radius: 16px;
                background: rgba(13, 25, 44, 0.86);
                border: 1px solid rgba(105, 136, 180, 0.12);
                cursor: pointer;
                transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
            }

            .device-card:hover,
            .device-card.is-selected {
                transform: translateY(-2px);
                border-color: rgba(125, 242, 212, 0.32);
                background: rgba(16, 32, 56, 0.96);
            }

            .health-ring {
                --ring-color: var(--safe);
                --ring-value: 50;
                width: 56px;
                height: 56px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                background:
                    radial-gradient(circle at center, #081324 58%, transparent 60%),
                    conic-gradient(var(--ring-color) calc(var(--ring-value) * 1%), rgba(255, 255, 255, 0.08) 0);
                box-shadow: inset 0 0 18px rgba(255, 255, 255, 0.02);
            }

            .health-ring span {
                font-size: 12px;
                color: var(--ink);
                font-weight: 600;
            }

            .device-meta strong {
                display: block;
                font-size: 14px;
                letter-spacing: 0.04em;
            }

            .device-meta small,
            .device-reason,
            .feed-subline,
            .timeline-description,
            .alert-meta,
            .analysis-copy,
            .metric-note {
                color: var(--muted);
            }

            .device-tags {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-top: 8px;
            }

            .tag {
                display: inline-flex;
                align-items: center;
                padding: 4px 8px;
                border-radius: 999px;
                background: rgba(99, 140, 196, 0.12);
                font-size: 11px;
                color: #c5d6ee;
            }

            .status-pill {
                padding: 7px 10px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                border: 1px solid transparent;
            }

            .status-safe { background: rgba(70, 214, 229, 0.1); color: var(--safe); border-color: rgba(70, 214, 229, 0.25); }
            .status-warning { background: rgba(240, 178, 79, 0.12); color: var(--warning); border-color: rgba(240, 178, 79, 0.28); }
            .status-threat { background: rgba(242, 99, 99, 0.12); color: var(--threat); border-color: rgba(242, 99, 99, 0.28); }
            .status-critical { background: rgba(199, 31, 55, 0.12); color: var(--critical); border-color: rgba(199, 31, 55, 0.28); }
            .status-isolated { background: rgba(158, 171, 193, 0.12); color: #d2dceb; border-color: rgba(158, 171, 193, 0.24); }

            .brain-explanations,
            .timeline-list,
            .alerts-list,
            .feed-list {
                display: grid;
                gap: 12px;
            }

            .brain-point,
            .timeline-card,
            .alert-card,
            .feed-card,
            .dna-line {
                padding: 14px;
                border-radius: 16px;
                background: rgba(12, 24, 41, 0.82);
                border: 1px solid rgba(105, 136, 180, 0.12);
            }

            .analysis-score {
                display: flex;
                gap: 12px;
                align-items: center;
                margin-bottom: 16px;
            }

            .analysis-radar {
                width: 72px;
                height: 72px;
                border-radius: 50%;
                background:
                    radial-gradient(circle at center, rgba(8, 16, 28, 0.96) 0 38%, transparent 40%),
                    conic-gradient(var(--accent) calc(var(--radar-value) * 1%), rgba(255, 255, 255, 0.08) 0);
                display: grid;
                place-items: center;
                box-shadow: 0 0 0 1px rgba(125, 242, 212, 0.18);
            }

            .analysis-radar strong {
                font-size: 14px;
            }

            .timeline-card,
            .alert-card,
            .feed-card {
                position: relative;
                overflow: hidden;
            }

            .timeline-stage,
            .feed-event {
                display: inline-flex;
                width: fit-content;
                padding: 5px 8px;
                border-radius: 999px;
                background: rgba(99, 140, 196, 0.12);
                color: #d3e2f4;
                font-size: 11px;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }

            .alert-card::before,
            .timeline-card::before,
            .feed-card::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 3px;
                background: rgba(125, 242, 212, 0.8);
            }

            .alert-card.severity-medium::before,
            .timeline-card.severity-medium::before { background: var(--warning); }
            .alert-card.severity-high::before,
            .timeline-card.severity-high::before { background: var(--threat); }
            .alert-card.severity-critical::before,
            .timeline-card.severity-critical::before { background: var(--critical); }
            .feed-card.event-dns_query::before { background: var(--warning); }
            .feed-card.event-network_summary::before { background: var(--threat); }
            .feed-card.event-socket_snapshot::before { background: var(--critical); }

            .alert-actions {
                display: flex;
                gap: 10px;
                margin-top: 14px;
            }

            button {
                border: 0;
                border-radius: 12px;
                padding: 10px 14px;
                font: inherit;
                font-size: 13px;
                cursor: pointer;
                transition: transform 0.18s ease, opacity 0.18s ease;
            }

            button:hover {
                transform: translateY(-1px);
            }

            .btn-primary {
                background: linear-gradient(135deg, rgba(125, 242, 212, 0.88), rgba(70, 214, 229, 0.82));
                color: #06101c;
                font-weight: 700;
            }

            .btn-secondary {
                background: rgba(255, 255, 255, 0.08);
                color: var(--ink);
            }

            .bottom-row {
                display: grid;
                grid-template-columns: 1.2fr 1fr;
                gap: 18px;
                margin-top: 18px;
            }

            .empty-state {
                color: var(--muted);
                text-align: center;
                padding: 26px;
                border: 1px dashed rgba(113, 151, 204, 0.18);
                border-radius: 18px;
            }

            .footer-line {
                margin-top: 18px;
                display: flex;
                justify-content: space-between;
                gap: 16px;
                flex-wrap: wrap;
                color: var(--muted);
                font-size: 12px;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }

            .node-circle {
                cursor: pointer;
                transition: transform 0.18s ease;
            }

            .node-circle:hover {
                transform: scale(1.04);
            }

            .node-pulse {
                animation: nodePulse 2.2s infinite;
            }

            .is-isolated {
                opacity: 0.55;
                filter: grayscale(0.15);
            }

            @keyframes spinSlow {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            @keyframes pulseDot {
                0%, 100% { transform: scale(1); opacity: 0.85; }
                50% { transform: scale(1.35); opacity: 1; }
            }

            @keyframes brainPulse {
                0%, 100% { box-shadow: 0 0 0 12px rgba(70, 214, 229, 0.05), 0 0 42px rgba(70, 214, 229, 0.22); }
                50% { box-shadow: 0 0 0 18px rgba(70, 214, 229, 0.07), 0 0 64px rgba(70, 214, 229, 0.3); }
            }

            @keyframes nodePulse {
                0% { opacity: 0.3; transform: scale(1); }
                60% { opacity: 0; transform: scale(1.8); }
                100% { opacity: 0; transform: scale(1.8); }
            }

            @media (max-width: 1320px) {
                .layout {
                    grid-template-columns: 1fr;
                }

                .command-stage {
                    min-height: 0;
                }
            }

            @media (max-width: 880px) {
                .topbar {
                    flex-direction: column;
                }

                .brand-cluster {
                    align-items: flex-start;
                }

                .brandmark-frame {
                    width: min(100%, 360px);
                }

                .status-strip {
                    justify-content: flex-start;
                }

                .battle-grid,
                .bottom-row {
                    grid-template-columns: 1fr;
                }

                .app-shell {
                    padding: 18px;
                }
            }
        </style>
    </head>
    <body>
        <div class="app-shell">
            <div class="topbar">
                <div class="brand">
                    <div class="eyebrow"><span class="dot"></span>KOVIRX Threat Command Center</div>
                    <div class="brand-cluster">
                        <div class="brandmark-frame">
                            <img src="/static/kovirx-logo-reference.png" alt="KOVIRX logo" />
                        </div>
                        <div class="brand-copy">
                            <h1>Detect. Analyze. Defend.</h1>
                            <p class="subtitle">
                                Live tactical view of endpoint telemetry, botnet behavior, AI explanations,
                                and network-wide threat spread. This screen turns your project into a security operations story,
                                not just a list of logs.
                            </p>
                        </div>
                    </div>
                </div>
                <div id="status-strip" class="status-strip"></div>
            </div>

            <div class="layout">
                <section class="panel">
                    <div class="panel-title-row">
                        <div>
                            <div class="tiny">Device readiness</div>
                            <h2>Fleet Health</h2>
                        </div>
                        <div class="tiny" id="fleet-count">0 nodes</div>
                    </div>
                    <div id="device-list" class="device-list"></div>
                </section>

                <section class="panel command-stage">
                    <div class="panel-title-row">
                        <div>
                            <div class="tiny">Battlefield view</div>
                            <h2>Interactive Network Topology</h2>
                        </div>
                        <div class="legend">
                            <span><i class="swatch" style="background: var(--safe)"></i>Safe</span>
                            <span><i class="swatch" style="background: var(--warning)"></i>Warning</span>
                            <span><i class="swatch" style="background: var(--threat)"></i>Threat</span>
                            <span><i class="swatch" style="background: var(--critical)"></i>Critical</span>
                        </div>
                    </div>

                    <div class="map-shell">
                        <svg id="topology-svg" class="topology-svg" viewBox="0 0 920 520" preserveAspectRatio="xMidYMid meet"></svg>
                        <div class="ai-brain-overlay">
                            <div class="brain-ring"></div>
                            <div class="brain-core">
                                <div>
                                    <strong>AI Engine</strong>
                                    <div id="brain-score" class="brain-score">0%</div>
                                    <div id="brain-level" class="brain-level">Calibrating</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="battle-grid">
                        <div class="panel" style="padding: 16px;">
                            <div class="panel-title-row">
                                <div>
                                    <div class="tiny">Threat replay</div>
                                    <h2>Attack Progression</h2>
                                </div>
                                <div id="timeline-count" class="tiny">0 events</div>
                            </div>
                            <div id="timeline-list" class="timeline-list"></div>
                        </div>
                        <div class="panel" style="padding: 16px;">
                            <div class="panel-title-row">
                                <div>
                                    <div class="tiny">Threat DNA</div>
                                    <h2>AI Explanation</h2>
                                </div>
                                <div id="analysis-status" class="tiny">Awaiting telemetry</div>
                            </div>
                            <div id="analysis-root"></div>
                        </div>
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-title-row">
                        <div>
                            <div class="tiny">Tactical response</div>
                            <h2>Alerts and Forensics</h2>
                        </div>
                        <div id="last-refresh" class="tiny">Syncing...</div>
                    </div>
                    <div id="alerts-list" class="alerts-list"></div>
                </section>
            </div>

            <div class="bottom-row">
                <section class="panel">
                    <div class="panel-title-row">
                        <div>
                            <div class="tiny">Live wire data</div>
                            <h2>Traffic Stream</h2>
                        </div>
                        <div id="feed-count" class="tiny">0 packets of context</div>
                    </div>
                    <div id="feed-list" class="feed-list"></div>
                </section>
                <section class="panel">
                    <div class="panel-title-row">
                        <div>
                            <div class="tiny">AI threat feed</div>
                            <h2>Threat Brain</h2>
                        </div>
                        <div id="brain-headline" class="tiny">Model online</div>
                    </div>
                    <div id="brain-explanations" class="brain-explanations"></div>
                </section>
            </div>

            <div class="footer-line">
                <span>Command center refreshes every 5 seconds</span>
                <span>Click any node to inspect it</span>
                <span>Isolation mode is visual-only in this MVP</span>
            </div>
        </div>

        <script>
            const STATUS_COLORS = {
                safe: getComputedStyle(document.documentElement).getPropertyValue("--safe").trim(),
                warning: getComputedStyle(document.documentElement).getPropertyValue("--warning").trim(),
                threat: getComputedStyle(document.documentElement).getPropertyValue("--threat").trim(),
                critical: getComputedStyle(document.documentElement).getPropertyValue("--critical").trim(),
                isolated: "#95a9c7"
            };

            const isolatedDevices = new Set();
            let selectedDeviceId = null;
            let lastSnapshot = null;

            function escapeHtml(value) {
                return String(value)
                    .replaceAll("&", "&amp;")
                    .replaceAll("<", "&lt;")
                    .replaceAll(">", "&gt;")
                    .replaceAll('"', "&quot;")
                    .replaceAll("'", "&#39;");
            }

            function formatTime(value) {
                try {
                    return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
                } catch {
                    return value;
                }
            }

            function formatDateTime(value) {
                try {
                    return new Date(value).toLocaleString();
                } catch {
                    return value;
                }
            }

            function severityClass(status) {
                return "status-" + status;
            }

            function chooseSelectedNode(snapshot) {
                if (selectedDeviceId && snapshot.nodes.some((node) => node.device_id === selectedDeviceId)) {
                    return snapshot.nodes.find((node) => node.device_id === selectedDeviceId);
                }

                const ranked = [...snapshot.nodes].sort((a, b) => b.risk_score - a.risk_score);
                selectedDeviceId = ranked[0]?.device_id || null;
                return ranked[0] || null;
            }

            function renderStatusStrip(snapshot) {
                const strip = document.getElementById("status-strip");
                const items = [
                    ["Devices", snapshot.summary.total_devices],
                    ["Active", snapshot.summary.active_devices_24h],
                    ["Events", snapshot.summary.total_events],
                    ["Alerts", snapshot.summary.total_alerts]
                ];
                strip.innerHTML = items.map(([label, value]) => `
                    <div class="status-card">
                        <div class="status-label">${escapeHtml(label)}</div>
                        <div class="status-value">${escapeHtml(value)}</div>
                    </div>
                `).join("");
            }

            function ringColor(status) {
                return STATUS_COLORS[status] || STATUS_COLORS.safe;
            }

            function renderDeviceList(snapshot) {
                const container = document.getElementById("device-list");
                document.getElementById("fleet-count").textContent = `${snapshot.nodes.length} nodes`;
                if (!snapshot.nodes.length) {
                    container.innerHTML = '<div class="empty-state">Run the agent to populate the network map.</div>';
                    return;
                }

                container.innerHTML = snapshot.nodes.map((node) => {
                    const isolated = isolatedDevices.has(node.device_id);
                    const status = isolated ? "isolated" : node.status;
                    const selected = selectedDeviceId === node.device_id ? "is-selected" : "";
                    return `
                        <div class="device-card ${selected}" data-device-id="${escapeHtml(node.device_id)}">
                            <div class="health-ring" style="--ring-color:${ringColor(status)}; --ring-value:${node.health_score};">
                                <span>${node.health_score}</span>
                            </div>
                            <div class="device-meta">
                                <strong>${escapeHtml(node.label)}</strong>
                                <small>${escapeHtml(node.operating_system)} • risk ${node.risk_score}% • seen ${formatTime(node.last_seen_at)}</small>
                                <div class="device-tags">
                                    ${(node.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
                                </div>
                            </div>
                            <span class="status-pill ${severityClass(status)}">${escapeHtml(status)}</span>
                        </div>
                    `;
                }).join("");

                container.querySelectorAll(".device-card").forEach((card) => {
                    card.addEventListener("click", () => {
                        selectedDeviceId = card.dataset.deviceId;
                        renderSnapshot(lastSnapshot);
                    });
                });
            }

            function renderTopology(snapshot) {
                const svg = document.getElementById("topology-svg");
                const width = 920;
                const height = 520;
                const centerX = width / 2;
                const centerY = height / 2;
                const radiusX = 308;
                const radiusY = 176;
                const nodes = snapshot.nodes;

                if (!nodes.length) {
                    svg.innerHTML = "";
                    return;
                }

                const count = nodes.length;
                const markup = nodes.map((node, index) => {
                    const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
                    const x = centerX + Math.cos(angle) * radiusX;
                    const y = centerY + Math.sin(angle) * radiusY;
                    const isolated = isolatedDevices.has(node.device_id);
                    const status = isolated ? "isolated" : node.status;
                    const color = ringColor(status);
                    const active = node.status === "threat" || node.status === "critical";
                    const selected = selectedDeviceId === node.device_id;
                    const lineDash = isolated ? "7 6" : active ? "3 6" : "0";
                    const lineOpacity = isolated ? 0.35 : active ? 0.82 : 0.48;
                    const nodeRadius = selected ? 18 : 14;
                    const pulseRadius = selected ? 26 : 22;
                    return `
                        <g data-device-id="${escapeHtml(node.device_id)}" class="node-group ${isolated ? "is-isolated" : ""}">
                            <line x1="${centerX}" y1="${centerY}" x2="${x}" y2="${y}"
                                  stroke="${color}" stroke-width="${selected ? 2.4 : 1.5}"
                                  stroke-dasharray="${lineDash}" opacity="${lineOpacity}" />
                            ${active && !isolated ? `<circle class="node-pulse" cx="${x}" cy="${y}" r="${pulseRadius}" fill="${color}" opacity="0.24"></circle>` : ""}
                            <circle cx="${x}" cy="${y}" r="${pulseRadius}" fill="${color}" opacity="${selected ? 0.18 : 0.1}"></circle>
                            <circle class="node-circle" cx="${x}" cy="${y}" r="${nodeRadius}" fill="${color}" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"></circle>
                            <text x="${x}" y="${y + 4}" text-anchor="middle" fill="#05101d" font-size="9" font-weight="700">${escapeHtml(node.operating_system.slice(0, 3).toUpperCase())}</text>
                            <text x="${x}" y="${y + 36}" text-anchor="middle" fill="#d7e6fb" font-size="12" font-family="Segoe UI">${escapeHtml(node.label)}</text>
                            <text x="${x}" y="${y + 52}" text-anchor="middle" fill="rgba(215,230,251,0.72)" font-size="10">${escapeHtml(isolated ? "isolated" : node.status)}</text>
                        </g>
                    `;
                }).join("");

                svg.innerHTML = `
                    <defs>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="4" result="coloredBlur"></feGaussianBlur>
                            <feMerge>
                                <feMergeNode in="coloredBlur"></feMergeNode>
                                <feMergeNode in="SourceGraphic"></feMergeNode>
                            </feMerge>
                        </filter>
                    </defs>
                    <circle cx="${centerX}" cy="${centerY}" r="104" fill="rgba(70,214,229,0.05)" stroke="rgba(70,214,229,0.12)" stroke-width="1.2"></circle>
                    <circle cx="${centerX}" cy="${centerY}" r="154" fill="none" stroke="rgba(125,242,212,0.08)" stroke-dasharray="4 8"></circle>
                    <circle cx="${centerX}" cy="${centerY}" r="204" fill="none" stroke="rgba(125,242,212,0.05)" stroke-dasharray="2 10"></circle>
                    ${markup}
                `;

                svg.querySelectorAll(".node-group").forEach((group) => {
                    group.addEventListener("click", () => {
                        selectedDeviceId = group.dataset.deviceId;
                        renderSnapshot(lastSnapshot);
                    });
                });
            }

            function renderTimeline(snapshot) {
                const container = document.getElementById("timeline-list");
                document.getElementById("timeline-count").textContent = `${snapshot.timeline.length} events`;
                if (!snapshot.timeline.length) {
                    container.innerHTML = '<div class="empty-state">Replay data appears when telemetry and alerts arrive.</div>';
                    return;
                }

                container.innerHTML = snapshot.timeline.map((item) => `
                    <div class="timeline-card severity-${escapeHtml(item.severity)}">
                        <div class="timeline-stage">${escapeHtml(item.stage)}</div>
                        <strong>${escapeHtml(item.title)}</strong>
                        <div class="alert-meta">${escapeHtml(item.device_id)} • ${formatDateTime(item.occurred_at)}</div>
                        <div class="timeline-description">${escapeHtml(item.description)}</div>
                    </div>
                `).join("");
            }

            function renderAnalysis(snapshot) {
                const selected = chooseSelectedNode(snapshot);
                const root = document.getElementById("analysis-root");
                const status = document.getElementById("analysis-status");
                if (!selected) {
                    root.innerHTML = '<div class="empty-state">Select a node to inspect its threat DNA.</div>';
                    status.textContent = "No nodes online";
                    return;
                }

                const isolated = isolatedDevices.has(selected.device_id);
                const statusValue = isolated ? "isolated" : selected.status;
                status.textContent = `${selected.label} • ${statusValue}`;

                root.innerHTML = `
                    <div class="analysis-score">
                        <div class="analysis-radar" style="--radar-value:${selected.confidence_score};">
                            <strong>${selected.confidence_score}%</strong>
                        </div>
                        <div>
                            <div class="tiny">Selected node</div>
                            <h2 style="margin: 4px 0 6px;">${escapeHtml(selected.label)}</h2>
                            <div class="analysis-copy">${escapeHtml(selected.operating_system)} • risk ${selected.risk_score}% • health ${selected.health_score}%</div>
                        </div>
                    </div>
                    <div class="dna-line">
                        <div class="tiny">Threat fingerprint</div>
                        <strong>${escapeHtml(selected.latest_alert_title || "Baseline telemetry profile")}</strong>
                        <div class="analysis-copy">Why the AI cares about this endpoint right now.</div>
                    </div>
                    ${(selected.reasons || []).map((reason) => `
                        <div class="dna-line">
                            <div class="tiny">Signal</div>
                            <strong>${escapeHtml(reason)}</strong>
                        </div>
                    `).join("")}
                    <div class="alert-actions">
                        <button class="btn-primary" id="isolate-button">${isolated ? "Reconnect Node" : "Isolate Device"}</button>
                        <button class="btn-secondary" id="focus-button">Focus in Topology</button>
                    </div>
                `;

                document.getElementById("isolate-button").addEventListener("click", () => {
                    if (isolatedDevices.has(selected.device_id)) {
                        isolatedDevices.delete(selected.device_id);
                    } else {
                        isolatedDevices.add(selected.device_id);
                    }
                    renderSnapshot(lastSnapshot);
                });

                document.getElementById("focus-button").addEventListener("click", () => {
                    selectedDeviceId = selected.device_id;
                    document.getElementById("topology-svg").scrollIntoView({ behavior: "smooth", block: "center" });
                    renderSnapshot(lastSnapshot);
                });
            }

            function renderAlerts(snapshot) {
                const container = document.getElementById("alerts-list");
                if (!snapshot.alerts.length) {
                    container.innerHTML = '<div class="empty-state">No active threats yet. Run the simulation mode to exercise the system.</div>';
                    return;
                }

                container.innerHTML = snapshot.alerts.map((alert) => `
                    <div class="alert-card severity-${escapeHtml(alert.severity)}">
                        <div class="status-pill ${severityClass(alert.severity)}" style="width: fit-content;">${escapeHtml(alert.severity)}</div>
                        <h2 style="margin: 12px 0 6px; font-size: 17px;">${escapeHtml(alert.title)}</h2>
                        <div class="alert-meta">${escapeHtml(alert.device_id)} • confidence ${(alert.confidence_score * 100).toFixed(0)}%</div>
                        <p class="analysis-copy">${escapeHtml(alert.description)}</p>
                        <div class="feed-subline">Detected ${formatDateTime(alert.created_at)}</div>
                    </div>
                `).join("");
            }

            function renderFeed(snapshot) {
                const container = document.getElementById("feed-list");
                document.getElementById("feed-count").textContent = `${snapshot.traffic_feed.length} recent events`;
                if (!snapshot.traffic_feed.length) {
                    container.innerHTML = '<div class="empty-state">Telemetry feed is empty. Start the agent to begin streaming.</div>';
                    return;
                }

                container.innerHTML = snapshot.traffic_feed.map((item) => `
                    <div class="feed-card event-${escapeHtml(item.event_type)}">
                        <div class="feed-event">${escapeHtml(item.event_type.replaceAll("_", " "))}</div>
                        <strong>${escapeHtml(item.summary)}</strong>
                        <div class="feed-subline">${escapeHtml(item.device_id)} • ${escapeHtml(item.source)} • ${formatDateTime(item.observed_at)}</div>
                    </div>
                `).join("");
            }

            function renderBrain(snapshot) {
                document.getElementById("brain-score").textContent = `${snapshot.ai_brain.confidence_score}%`;
                document.getElementById("brain-level").textContent = snapshot.ai_brain.threat_level;
                document.getElementById("brain-headline").textContent = snapshot.ai_brain.headline;
                const container = document.getElementById("brain-explanations");
                container.innerHTML = `
                    <div class="brain-point">
                        <div class="tiny">Global risk score</div>
                        <div class="status-value">${snapshot.ai_brain.global_risk_score}%</div>
                        <div class="metric-note">${escapeHtml(snapshot.ai_brain.headline)}</div>
                    </div>
                    ${snapshot.ai_brain.explanations.map((point) => `
                        <div class="brain-point">${escapeHtml(point)}</div>
                    `).join("")}
                `;
            }

            function renderSnapshot(snapshot) {
                if (!snapshot) {
                    return;
                }

                lastSnapshot = snapshot;
                renderStatusStrip(snapshot);
                renderDeviceList(snapshot);
                renderTopology(snapshot);
                renderTimeline(snapshot);
                renderAnalysis(snapshot);
                renderAlerts(snapshot);
                renderFeed(snapshot);
                renderBrain(snapshot);
                document.getElementById("last-refresh").textContent = `Refreshed ${formatTime(snapshot.generated_at)}`;
            }

            async function fetchSnapshot() {
                try {
                    const response = await fetch("/api/v1/command-center");
                    if (!response.ok) {
                        throw new Error("Request failed");
                    }
                    const snapshot = await response.json();
                    renderSnapshot(snapshot);
                } catch (error) {
                    document.getElementById("last-refresh").textContent = "Refresh failed";
                    console.error(error);
                }
            }

            fetchSnapshot();
            setInterval(fetchSnapshot, 5000);
        </script>
    </body>
    </html>
    """
