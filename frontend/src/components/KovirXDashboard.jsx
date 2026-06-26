import { useState, useEffect, useRef } from "react";
import logoImg from "../assets/logo.jpg";
import {
  getDashboardSummary,
  getAlerts,
  getDevices,
  updateAlertStatus,
  logout,
  getWebSocketUrl
} from "../services/api";

// ── Color Palette ──────────────────────────────────────────────
const COLORS = {
  bg: "#060B18",
  panel: "#0C1426",
  panelBorder: "#1E293B",
  text: "#C5D0E6",
  textDim: "#5A7090",
  cyan: "#00D4FF",
  amber: "#FFB400",
  red: "#FF355E",
  purple: "#9B59FF",
  safe: "#00E676",
};

const NODE_COLORS = {
  monitoring: COLORS.cyan,
  safe: COLORS.safe,
  warning: COLORS.amber,
  critical: COLORS.red,
};

// ── Custom Hook: useAnimationFrame ─────────────────────────────
function useAnimationFrame(callback) {
  const cbRef = useRef(callback);
  const frameRef = useRef();
  const prevRef = useRef(performance.now());

  useEffect(() => {
    cbRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const loop = (now) => {
      const delta = now - prevRef.current;
      prevRef.current = now;
      cbRef.current(delta);
      frameRef.current = requestAnimationFrame(loop);
    };
    frameRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameRef.current);
  }, []);
}

// ── Network Mesh Canvas ────────────────────────────────────────
function NetworkMesh({ threatLevel }) {
  const canvasRef = useRef(null);
  const nodesRef = useRef([]);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W;
    canvas.height = H;

    const cx = W / 2, cy = H / 2;
    const nodes = [{ x: cx, y: cy, r: 18, state: "monitoring", pulse: 0, fixed: true, label: "AI CORE" }];

    const rings = [
      { count: 6, radius: 80, states: ["safe","safe","warning","safe","monitoring","safe"] },
      { count: 8, radius: 155, states: ["safe","warning","critical","safe","safe","warning","safe","safe"] },
      { count: 10, radius: 230, states: ["safe","safe","safe","warning","safe","critical","safe","safe","safe","monitoring"] },
    ];

    rings.forEach(ring => {
      for (let i = 0; i < ring.count; i++) {
        const angle = (i / ring.count) * Math.PI * 2 - Math.PI / 2;
        nodes.push({
          x: cx + Math.cos(angle) * ring.radius,
          y: cy + Math.sin(angle) * ring.radius,
          r: ring.radius === 80 ? 10 : ring.radius === 155 ? 8 : 7,
          state: ring.states[i],
          pulse: Math.random() * Math.PI * 2,
          fixed: false,
          label: null,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          ox: cx + Math.cos(angle) * ring.radius,
          oy: cy + Math.sin(angle) * ring.radius,
        });
      }
    });

    nodesRef.current = nodes;
  }, []);

  useAnimationFrame((delta) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    timeRef.current += delta * 0.001;
    const t = timeRef.current;

    ctx.clearRect(0, 0, W, H);

    const nodes = nodesRef.current;

    // Adjust node states based on threatLevel dynamically
    if (threatLevel === "critical" && nodes.length > 5) {
      nodes[2].state = "critical";
      nodes[5].state = "critical";
    }

    // drift non-fixed nodes gently
    nodes.forEach(n => {
      if (n.fixed) return;
      n.x += n.vx;
      n.y += n.vy;
      const dx = n.x - n.ox, dy = n.y - n.oy;
      const dist = Math.sqrt(dx*dx+dy*dy);
      if (dist > 18) { n.vx -= dx * 0.002; n.vy -= dy * 0.002; }
    });

    // Draw edges
    nodes.forEach((a, i) => {
      nodes.forEach((b, j) => {
        if (j <= i) return;
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx*dx+dy*dy);
        if (dist > 195) return;
        const alpha = (1 - dist / 195) * 0.22;
        const isActive = (a.state === "critical" || b.state === "critical") ? true :
                         (a.state === "warning" || b.state === "warning");
        const edgeColor = isActive ? COLORS.amber : COLORS.cyan;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = edgeColor + Math.floor(alpha * 255).toString(16).padStart(2,"0");
        ctx.lineWidth = isActive ? 0.8 : 0.5;
        ctx.stroke();

        // Traveling packet on some edges
        if (dist < 140 && Math.sin(t * 1.5 + i * 0.7 + j * 0.4) > 0.85) {
          const progress = (Math.sin(t * 2 + i + j) * 0.5 + 0.5);
          const px = a.x + (b.x - a.x) * progress;
          const py = a.y + (b.y - a.y) * progress;
          ctx.beginPath();
          ctx.arc(px, py, 2, 0, Math.PI * 2);
          ctx.fillStyle = edgeColor;
          ctx.fill();
        }
      });
    });

    // Draw nodes
    nodes.forEach(n => {
      const color = NODE_COLORS[n.state];
      const pulseScale = 1 + Math.sin(t * 2.5 + n.pulse) * 0.15;
      const glowR = n.r * (n.fixed ? 3.5 : 2.8) * pulseScale;

      // outer glow
      const grad = ctx.createRadialGradient(n.x, n.y, n.r * 0.5, n.x, n.y, glowR);
      grad.addColorStop(0, color + "55");
      grad.addColorStop(1, color + "00");
      ctx.beginPath();
      ctx.arc(n.x, n.y, glowR, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // node body
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * pulseScale, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.panel;
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = n.fixed ? 2.5 : 1.5;
      ctx.stroke();

      // inner dot
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // AI Core rotating rings
      if (n.fixed) {
        [28, 38].forEach((rr, idx) => {
          ctx.beginPath();
          ctx.arc(n.x, n.y, rr, t * (idx === 0 ? 1.2 : -0.8), t * (idx === 0 ? 1.2 : -0.8) + Math.PI * 1.4);
          ctx.strokeStyle = COLORS.purple + "88";
          ctx.lineWidth = 1;
          ctx.stroke();
        });
      }
    });
  });

  return (
    <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />
  );
}

// ── Replay Steps ───────────────────────────────────────────────
const REPLAY_STEPS = [
  { ts: "08:15:03", label: "Device Connected", icon: "◉" },
  { ts: "08:15:47", label: "Suspicious DNS Query", icon: "⚠" },
  { ts: "08:16:22", label: "Botnet Beacon Sent", icon: "⬆" },
  { ts: "08:17:01", label: "C2 Handshake", icon: "⚡" },
  { ts: "08:18:00", label: "Threat Detected", icon: "✕" },
];

// ── Sub-Components ─────────────────────────────────────────────
function SeverityBadge({ sev }) {
  const map = {
    Critical: { bg: COLORS.red + "22", border: COLORS.red, text: COLORS.red },
    High: { bg: COLORS.amber + "22", border: COLORS.amber, text: COLORS.amber },
    Medium: { bg: "#9B59FF22", border: COLORS.purple, text: COLORS.purple },
    Low: { bg: COLORS.cyan + "22", border: COLORS.cyan, text: COLORS.cyan },
    Resolved: { bg: COLORS.cyan + "22", border: COLORS.cyan, text: COLORS.cyan },
  };
  const s = map[sev] || map.Medium;
  return (
    <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", fontWeight: 700,
      background: s.bg, border: `1px solid ${s.border}`, color: s.text,
      padding: "2px 6px", borderRadius: 3, letterSpacing: 1 }}>
      {sev.toUpperCase()}
    </span>
  );
}

function StatCard({ label, value, delta, color }) {
  return (
    <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
      borderRadius: 8, padding: "10px 14px", flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 9, color: COLORS.textDim, fontFamily: "Orbitron, monospace",
        letterSpacing: 2, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontFamily: "Orbitron, monospace", fontWeight: 700, color: color || COLORS.cyan }}>
        {value}
      </div>
      {delta && <div style={{ fontSize: 9, color: COLORS.amber, marginTop: 2 }}>▲ {delta} / 24h</div>}
    </div>
  );
}

// Helper to format ISO dates into human readable hours
const formatTime = (dateStr) => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch (e) {
    return "00:00";
  }
};

// Helper to format relative time
const formatRelativeTime = (dateStr) => {
  try {
    const diffMs = new Date() - new Date(dateStr);
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return new Date(dateStr).toLocaleDateString();
  } catch (e) {
    return "recent";
  }
};

// ── Main Dashboard ─────────────────────────────────────────────
export default function KovirXDashboard() {
  const [threatLevel, setThreatLevel] = useState("high");
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [replaying, setReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState(-1);
  const [pulseCore, setPulseCore] = useState(false);

  // Live State from Backend API
  const [summary, setSummary] = useState({
    protected_devices: 0,
    active_threats: 0,
    today_alerts: 0,
    detection_accuracy: 0.0,
    botnet_attempts_24h: 0,
    traffic_stats: { total_flows: 0, suspicious_flows: 0, blocked_flows: 0 },
    top_threat_types: []
  });
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch all dashboard data
  const loadDashboardData = async () => {
    try {
      const [sumData, alertsData, devicesData] = await Promise.all([
        getDashboardSummary(),
        getAlerts(),
        getDevices(),
      ]);
      setSummary(sumData);
      setAlerts(alertsData);
      setDevices(devicesData);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Set threat level based on active alerts severity
  useEffect(() => {
    if (alerts.some(a => a.status === 'new' && a.severity.toLowerCase() === 'critical')) {
      setThreatLevel("critical");
    } else if (alerts.some(a => a.status === 'new' && a.severity.toLowerCase() === 'high')) {
      setThreatLevel("high");
    } else if (alerts.some(a => a.status === 'new' && a.severity.toLowerCase() === 'medium')) {
      setThreatLevel("warning");
    } else {
      setThreatLevel("safe");
    }
  }, [alerts]);

  // WebSocket Live Stream Listener
  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let isMounted = true;

    const connectWS = () => {
      const wsUrl = getWebSocketUrl();
      if (!wsUrl) return;

      console.log("Connecting WebSocket to alert stream:", wsUrl);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isMounted) setWsConnected(true);
        console.log("WebSocket connected.");
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          console.log("WebSocket broadcast received:", payload);
          if (payload.channel === "alerts" && payload.event === "new") {
            const newAlert = payload.data;
            if (isMounted) {
              setAlerts((prev) => [newAlert, ...prev]);
              setPulseCore(true);
              setTimeout(() => setPulseCore(false), 800);
              setSummary((prev) => ({
                ...prev,
                today_alerts: (prev.today_alerts || 0) + 1,
                active_threats: (prev.active_threats || 0) + 1,
              }));
            }
          } else if (payload.channel === "traffic" && payload.event === "ingested") {
            if (isMounted) {
              setSummary((prev) => ({
                ...prev,
                traffic_stats: {
                  ...prev.traffic_stats,
                  total_flows: (prev.traffic_stats?.total_flows || 0) + (payload.data.flow_count || 0),
                }
              }));
            }
          }
        } catch (err) {
          console.error("Error parsing WS payload:", err);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          setWsConnected(false);
          console.log("WebSocket connection closed. Reconnecting in 3s...");
          reconnectTimeout = setTimeout(connectWS, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket encountered an error:", err);
        ws.close();
      };
    };

    connectWS();

    return () => {
      isMounted = false;
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  // Replay animation
  useEffect(() => {
    if (!replaying) return;
    setReplayStep(0);
    const steps = REPLAY_STEPS.length;
    let i = 0;
    const iv = setInterval(() => {
      i++;
      setReplayStep(i);
      if (i >= steps - 1) {
        clearInterval(iv);
        setTimeout(() => {
          setReplaying(false);
          setReplayStep(-1);
        }, 1800);
      }
    }, 900);
    return () => clearInterval(iv);
  }, [replaying]);

  // Random core pulse
  useEffect(() => {
    const iv = setInterval(() => {
      setPulseCore(true);
      setTimeout(() => setPulseCore(false), 600);
    }, 5000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div style={{ background: COLORS.bg, minHeight: "100vh", color: COLORS.text,
      fontFamily: "Inter, system-ui, sans-serif", display: "flex", flexDirection: "column",
      overflow: "hidden", userSelect: "none" }}>

      {/* TOP NAV */}
      <div style={{ display: "flex", alignItems: "stretch", height: 68,
        background: `linear-gradient(90deg, #080D1C 0%, ${COLORS.panel} 30%, ${COLORS.panel} 70%, #080D1C 100%)`,
        borderBottom: `1px solid ${COLORS.panelBorder}`, flexShrink: 0, position: "relative" }}>

        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 1,
          background: `linear-gradient(90deg, transparent 0%, #00D4FF66 30%, #9B59FF88 50%, #00D4FF66 70%, transparent 100%)` }} />

        {/* BRAND ZONE */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 24px",
          borderRight: `1px solid ${COLORS.panelBorder}`, minWidth: 240,
          background: "linear-gradient(90deg, #050A16, #0C1426)" }}>

          <div style={{ position: "relative", flexShrink: 0 }}>
            <div style={{ position: "absolute", inset: -8, borderRadius: "50%",
              background: "radial-gradient(circle, #00D4FF14 0%, transparent 70%)",
              pointerEvents: "none" }} />
            <div style={{ position: "absolute", inset: -4, borderRadius: "50%",
              border: "1px solid #00D4FF33", pointerEvents: "none" }} />
            <img
              src={logoImg}
              alt="KovirX Logo"
              style={{ height: 50, width: 50, objectFit: "contain", display: "block",
                filter: "drop-shadow(0 0 12px #00D4FFCC) drop-shadow(0 0 24px #9B59FF88)" }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <span style={{ fontFamily: "Orbitron, monospace", fontWeight: 900,
              fontSize: 18, letterSpacing: 4, lineHeight: 1,
              background: "linear-gradient(90deg, #ffffff, #00D4FF)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              KOVIRX
            </span>
            <span style={{ fontFamily: "Orbitron, monospace", fontSize: 7,
              letterSpacing: 3, color: "#5A7090" }}>
              DETECT · ANALYZE · DEFEND
            </span>
          </div>
        </div>

        {/* NAV STATUS */}
        <div style={{ display: "flex", alignItems: "center", padding: "0 24px", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 8, height: 8, borderRadius: "50%",
              background: wsConnected ? COLORS.safe : COLORS.red,
              boxShadow: `0 0 8px ${wsConnected ? COLORS.safe : COLORS.red}`,
              animation: wsConnected ? "none" : "threatBlink 1.2s infinite"
            }} />
            <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: wsConnected ? COLORS.safe : COLORS.red, letterSpacing: 2, fontWeight: 700 }}>
              {wsConnected ? "NEXUS ONLINE" : "NEXUS OFFLINE"}
            </span>
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {/* RIGHT STATUS */}
        <div style={{ display: "flex", alignItems: "stretch", borderLeft: `1px solid ${COLORS.panelBorder}` }}>
          {/* System Level */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 24px", borderRight: `1px solid ${COLORS.panelBorder}` }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%",
              background: threatLevel === 'critical' || threatLevel === 'high' ? COLORS.red : COLORS.safe,
              boxShadow: `0 0 8px ${threatLevel === 'critical' || threatLevel === 'high' ? COLORS.red : COLORS.safe}`, flexShrink: 0,
              animation: threatLevel === 'critical' || threatLevel === 'high' ? "threatBlink 1.2s infinite" : "none" }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace",
                color: threatLevel === 'critical' || threatLevel === 'high' ? COLORS.red : COLORS.safe,
                letterSpacing: 2, fontWeight: 700 }}>SYSTEM LEVEL</span>
              <span style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace",
                letterSpacing: 1 }}>{threatLevel.toUpperCase()}</span>
            </div>
          </div>

          {/* Time & Logout */}
          <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "0 24px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 2, alignItems: "flex-end" }}>
              <span style={{ fontSize: 12, fontFamily: "Orbitron, monospace", color: COLORS.text, letterSpacing: 1 }}>
                {new Date().toLocaleTimeString("en-US", { hour12: false })}
              </span>
              <span style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace", letterSpacing: 2 }}>UTC · LIVE</span>
            </div>

            <button onClick={logout} style={{
              background: 'rgba(255, 53, 94, 0.1)',
              border: `1px solid ${COLORS.red}`,
              color: COLORS.red,
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontFamily: 'Orbitron, monospace',
              fontSize: '9px',
              fontWeight: 700,
              letterSpacing: '1.5px',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => e.target.style.background = 'rgba(255, 53, 94, 0.25)'}
            onMouseOut={(e) => e.target.style.background = 'rgba(255, 53, 94, 0.1)'}
            >
              LOGOUT
            </button>
          </div>
        </div>
      </div>

      {/* STAT BAR */}
      <div style={{ display: "flex", gap: 8, padding: "8px 16px", flexShrink: 0 }}>
        <StatCard label="ACTIVE THREATS" value={summary.active_threats} />
        <StatCard label="TOTAL FLOWS" value={summary.traffic_stats?.total_flows?.toLocaleString() || "0"} color={COLORS.amber} />
        <StatCard label="SUSPICIOUS FLOWS" value={summary.traffic_stats?.suspicious_flows?.toLocaleString() || "0"} color={COLORS.red} />
        <StatCard label="AI ACCURACY" value={`${(summary.detection_accuracy * 100).toFixed(1)}%`} color={COLORS.purple} />
        <StatCard label="NODES MONITORED" value={summary.protected_devices?.toLocaleString() || "0"} color={COLORS.cyan} />
        <StatCard label="TODAY'S ALERTS" value={summary.today_alerts} color={COLORS.safe} />
      </div>

      {/* MAIN BODY */}
      <div style={{ flex: 1, display: "flex", gap: 8, padding: "0 16px 12px", minHeight: 0, overflow: "hidden" }}>

        {/* LEFT COLUMN */}
        <div style={{ width: 240, display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>

          {/* Threat Timeline */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px", flex: 1, display: 'flex', flexDirection: 'column', overflow: "hidden" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 10 }}>THREAT TIMELINE</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 0, overflowY: 'auto', flex: 1 }}>
              {alerts && alerts.length > 0 ? (
                alerts.slice(0, 8).map((item, i) => (
                  <div key={item.id || i} style={{ display: "flex", gap: 10, position: "relative",
                    animation: `slideIn 0.4s ease ${i * 0.1}s both` }}>
                    {/* connector */}
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 16 }}>
                      <div style={{ width: 10, height: 10, borderRadius: "50%", flexShrink: 0,
                        background: item.severity === "critical" ? COLORS.red :
                                    item.severity === "high" ? COLORS.amber : COLORS.cyan,
                        border: `2px solid ${COLORS.panel}`,
                        boxShadow: `0 0 8px ${item.severity === "critical" ? COLORS.red :
                                    item.severity === "high" ? COLORS.amber : COLORS.cyan}` }} />
                      {i < alerts.slice(0, 8).length - 1 && (
                        <div style={{ width: 1, flex: 1, minHeight: 24,
                          background: `linear-gradient(${COLORS.panelBorder}, transparent)` }} />
                      )}
                    </div>
                    <div style={{ paddingBottom: 14, flex: 1 }}>
                      <div style={{ fontSize: 9, color: COLORS.textDim, fontFamily: "Orbitron, monospace" }}>
                        {formatTime(item.created_at)}
                      </div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.text, marginTop: 1 }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 2, lineHeight: 1.4 }}>
                        {item.description}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 10, color: COLORS.textDim }}>No timeline events recorded.</div>
              )}
            </div>
          </div>

          {/* Threat DNA */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 8 }}>THREAT DNA</div>
            <div style={{ fontSize: 10, color: COLORS.red, fontFamily: "Orbitron, monospace",
              marginBottom: 8, fontWeight: 700 }}>REAL-TIME CLASSIFICATIONS</div>
            {summary.top_threat_types && summary.top_threat_types.length > 0 ? (
              summary.top_threat_types.map((d, i) => {
                const total = summary.top_threat_types.reduce((acc, curr) => acc + curr.count, 0) || 1;
                const pct = Math.round((d.count / total) * 100);
                const colors = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.cyan];
                const color = colors[i % colors.length];
                return (
                  <div key={i} style={{ marginBottom: 7 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 10, color: COLORS.text }}>{d.threat_type}</span>
                      <span style={{ fontSize: 10, color: color, fontFamily: "Orbitron, monospace" }}>{d.count} ({pct}%)</span>
                    </div>
                    <div style={{ height: 4, background: COLORS.panelBorder, borderRadius: 2 }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: color,
                        borderRadius: 2, boxShadow: `0 0 6px ${color}88`,
                        transition: "width 1s ease" }} />
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ fontSize: 10, color: COLORS.textDim }}>No active malware profiles.</div>
            )}
          </div>
        </div>

        {/* CENTER - Network Mesh */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8, minWidth: 0 }}>
          <div style={{ flex: 1, background: COLORS.panel,
            border: `1px solid ${COLORS.panelBorder}`, borderRadius: 10,
            position: "relative", overflow: "hidden" }}>

            {/* header */}
            <div style={{ position: "absolute", top: 12, left: 16, right: 16,
              display: "flex", justifyContent: "space-between", alignItems: "center", zIndex: 2 }}>
              <div>
                <div style={{ fontFamily: "Orbitron, monospace", fontSize: 11, fontWeight: 900,
                  color: COLORS.cyan, letterSpacing: 3 }}>KOVIRX NEXUS</div>
                <div style={{ fontSize: 9, color: COLORS.textDim, letterSpacing: 2 }}>
                  LIVE NETWORK INTELLIGENCE MESH
                </div>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                {[["🟦", "MONITORING"], ["🟩", "SAFE"], ["🟨", "SUSPICIOUS"], ["🟥", "CRITICAL"]].map(([dot, lbl]) => (
                  <div key={lbl} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <span style={{ fontSize: 7 }}>{dot}</span>
                    <span style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace", letterSpacing: 1 }}>{lbl}</span>
                  </div>
                ))}
              </div>
            </div>

            <NetworkMesh threatLevel={threatLevel} />

            {/* AI Core label overlay */}
            <div style={{ position: "absolute", bottom: 12, left: "50%",
              transform: "translateX(-50%)", textAlign: "center", zIndex: 2,
              pointerEvents: "none" }}>
              <div style={{ fontFamily: "Orbitron, monospace", fontSize: 8,
                color: COLORS.purple, letterSpacing: 3 }}>AI CORE — XGBOOST & ISOLATION FOREST ACTIVE</div>
            </div>
          </div>

          {/* Replay Panel */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim, letterSpacing: 2 }}>
                THREAT REPLAY — MITRE ATT&CK SIMULATION
              </div>
              <button onClick={() => setReplaying(true)}
                disabled={replaying}
                style={{ background: replaying ? COLORS.panelBorder : COLORS.red + "22",
                  border: `1px solid ${replaying ? COLORS.textDim : COLORS.red}`,
                  color: replaying ? COLORS.textDim : COLORS.red,
                  padding: "4px 12px", borderRadius: 4, cursor: replaying ? "default" : "pointer",
                  fontSize: 9, fontFamily: "Orbitron, monospace", letterSpacing: 2,
                  transition: "all 0.2s" }}>
                {replaying ? "▶ REPLAYING..." : "▶ REPLAY ATTACK"}
              </button>
            </div>
            <div style={{ display: "flex", gap: 0, alignItems: "center" }}>
              {REPLAY_STEPS.map((s, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", flex: 1, minWidth: 0 }}>
                  <div style={{ flex: 1, textAlign: "center",
                    opacity: replayStep >= i ? 1 : 0.3,
                    transition: "all 0.4s" }}>
                    <div style={{ width: 26, height: 26, borderRadius: "50%", margin: "0 auto 4px",
                      background: replayStep >= i ? (i === REPLAY_STEPS.length - 1 ? COLORS.red + "33" : COLORS.cyan + "22") : COLORS.panelBorder,
                      border: `1px solid ${replayStep >= i ? (i === REPLAY_STEPS.length-1 ? COLORS.red : COLORS.cyan) : COLORS.panelBorder}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 11, color: replayStep >= i ? (i === REPLAY_STEPS.length-1 ? COLORS.red : COLORS.cyan) : COLORS.textDim,
                      boxShadow: replayStep === i ? `0 0 12px ${COLORS.cyan}88` : "none",
                      transition: "all 0.4s" }}>
                      {s.icon}
                    </div>
                    <div style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace" }}>{s.ts}</div>
                    <div style={{ fontSize: 9, color: COLORS.text, marginTop: 1 }}>{s.label}</div>
                  </div>
                  {i < REPLAY_STEPS.length - 1 && (
                    <div style={{ width: 20, height: 1,
                      background: replayStep > i ? COLORS.cyan : COLORS.panelBorder,
                      transition: "background 0.4s", flexShrink: 0 }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ width: 248, display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>

          {/* AI Core Widget */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "14px", textAlign: "center" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 10 }}>AI THREAT BRAIN</div>
            <div style={{ position: "relative", display: "inline-block" }}>
              {/* concentric rings */}
              {[52, 42, 32].map((r, i) => (
                <div key={r} style={{
                  position: i === 0 ? "relative" : "absolute",
                  top: i > 0 ? (52-r) : undefined,
                  left: i > 0 ? (52-r) : undefined,
                  width: r*2, height: r*2, borderRadius: "50%",
                  border: `1px solid ${[COLORS.red, COLORS.purple, COLORS.cyan][i]}44`,
                }} />
              ))}
              <div style={{ position: "absolute", top: 10, left: 10,
                width: 84, height: 84, borderRadius: "50%",
                background: `radial-gradient(circle, ${COLORS.purple}33, ${COLORS.bg})`,
                border: `2px solid ${COLORS.purple}`,
                animation: pulseCore ? "corePulse 0.6s ease" : "none",
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center" }}>
                <div style={{ fontFamily: "Orbitron, monospace", fontSize: 18,
                  fontWeight: 900, color: COLORS.purple }}>{(summary.detection_accuracy * 100).toFixed(0)}%</div>
                <div style={{ fontSize: 7, color: COLORS.textDim, letterSpacing: 1 }}>ACCURACY</div>
              </div>
            </div>
            <div style={{ marginTop: 12, display: "flex", justifyContent: "center", gap: 6 }}>
              {["LOW", "MED", "HIGH"].map((l) => {
                const active = (l === "HIGH" && threatLevel === "critical") || (l === "MED" && threatLevel === "warning") || (l === "LOW" && threatLevel === "safe") || (l === "HIGH" && threatLevel === "high");
                const col = l === "HIGH" ? COLORS.red : l === "MED" ? COLORS.amber : COLORS.cyan;
                return (
                  <div key={l} style={{ padding: "2px 8px", borderRadius: 3,
                    background: active ? col + "33" : "transparent",
                    border: `1px solid ${active ? col : COLORS.panelBorder}`,
                    fontSize: 8, fontFamily: "Orbitron, monospace", color: active ? col : COLORS.textDim,
                    letterSpacing: 1 }}>
                    {l}
                  </div>
                );
              })}
            </div>
            <div style={{ marginTop: 8, fontSize: 9, color: threatLevel === 'safe' ? COLORS.safe : COLORS.red,
              fontFamily: "Orbitron, monospace", animation: threatLevel === 'safe' ? "none" : "threatBlink 1.5s infinite" }}>
              {threatLevel === 'safe' ? "⬡ NETWORK SECURE" : "⬡ ACTIVE THREATS DETECTED"}
            </div>
          </div>

          {/* Recent Incidents */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px", flex: 1, display: 'flex', flexDirection: 'column', overflow: "hidden" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 10 }}>SECURITY INCIDENTS</div>
            <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column' }}>
              {alerts && alerts.length > 0 ? (
                alerts.map((inc, i) => {
                  const severityWord = inc.severity.charAt(0).toUpperCase() + inc.severity.slice(1).toLowerCase();
                  return (
                    <div key={inc.id || i} style={{ display: "flex", flexDirection: "column", gap: 3,
                      padding: "8px 0", borderBottom: i < alerts.length - 1 ? `1px solid ${COLORS.panelBorder}` : "none" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: 11, fontWeight: 600 }}>{inc.title}</span>
                        <SeverityBadge sev={severityWord} />
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ fontSize: 10, color: COLORS.textDim }}>{inc.evidence?.source_ip || "System Core"}</span>
                        <span style={{ fontSize: 10, color: COLORS.textDim }}>{formatRelativeTime(inc.created_at)}</span>
                      </div>
                      {inc.status === "new" && (
                        <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                          <button
                            onClick={async () => {
                              try {
                                await updateAlertStatus(inc.id, "investigating");
                                loadDashboardData();
                              } catch (err) {
                                console.error(err);
                              }
                            }}
                            style={{
                              background: 'none',
                              border: `1px solid ${COLORS.amber}`,
                              borderRadius: '3px',
                              color: COLORS.amber,
                              fontSize: '8px',
                              padding: '2px 6px',
                              cursor: 'pointer',
                              fontFamily: 'Orbitron, monospace',
                            }}
                          >
                            INVESTIGATE
                          </button>
                          <button
                            onClick={async () => {
                              try {
                                await updateAlertStatus(inc.id, "resolved");
                                loadDashboardData();
                              } catch (err) {
                                console.error(err);
                              }
                            }}
                            style={{
                              background: 'none',
                              border: `1px solid ${COLORS.safe}`,
                              borderRadius: '3px',
                              color: COLORS.safe,
                              fontSize: '8px',
                              padding: '2px 6px',
                              cursor: 'pointer',
                              fontFamily: 'Orbitron, monospace',
                            }}
                          >
                            RESOLVE
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div style={{ fontSize: 10, color: COLORS.textDim, padding: "10px 0" }}>No security incidents.</div>
              )}
            </div>
          </div>

          {/* Device Cards */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px", maxHeight: '280px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 8 }}>DEVICE INTELLIGENCE</div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {devices && devices.length > 0 ? (
                devices.map((d, i) => {
                  const riskScore = Math.round(d.risk_score);
                  // Calculate dynamic network/cpu mock values or extract from device tags
                  const isSuspicious = riskScore > 35;
                  const isCritical = riskScore > 75;
                  return (
                    <div key={d.id || i} onClick={() => setSelectedDevice(selectedDevice?.id === d.id ? null : d)}
                      style={{ padding: "8px 10px", borderRadius: 7, marginBottom: 6, cursor: "pointer",
                        background: selectedDevice?.id === d.id ? COLORS.panelBorder : "transparent",
                        border: `1px solid ${isCritical ? COLORS.red + "55" :
                                  isSuspicious ? COLORS.amber + "55" : COLORS.panelBorder}`,
                        transition: "all 0.2s" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <div>
                          <div style={{ fontFamily: "Orbitron, monospace", fontSize: 10,
                            fontWeight: 700, color: COLORS.text }}>{d.hostname}</div>
                          <div style={{ fontSize: 9, color: COLORS.textDim }}>{d.operating_system}</div>
                        </div>
                        <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", fontWeight: 700,
                          color: isCritical ? COLORS.red : isSuspicious ? COLORS.amber : COLORS.cyan,
                          animation: isCritical ? "threatBlink 1.2s infinite" : "none" }}>
                          {isCritical ? "CRITICAL" : isSuspicious ? "SUSPICIOUS" : "SAFE"}
                        </span>
                      </div>

                      {selectedDevice?.id === d.id && (
                        <div style={{ marginTop: 6, animation: "slideIn 0.3s ease" }}>
                          {[["Risk Score", riskScore, COLORS.red], ["Network Score", isCritical ? 95 : isSuspicious ? 68 : 12, COLORS.amber], ["CPU Usage", isCritical ? 88 : 34, COLORS.cyan]].map(([lbl, val, col]) => (
                            <div key={lbl} style={{ marginBottom: 5 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                                <span style={{ fontSize: 9, color: COLORS.textDim }}>{lbl}</span>
                                <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: col }}>{val}%</span>
                              </div>
                              <div style={{ height: 3, background: COLORS.bg, borderRadius: 2 }}>
                                <div style={{ height: "100%", width: `${val}%`, background: col, borderRadius: 2 }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div style={{ fontSize: 10, color: COLORS.textDim }}>No connected nodes.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
