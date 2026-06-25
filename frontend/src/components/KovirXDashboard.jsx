import { useState, useEffect, useRef, useCallback } from "react";
import logoImg from "../assets/logo.jpg";

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

// ── Data ───────────────────────────────────────────────────────
const TIMELINE = [
  { time: "08:15", event: "DNS Anomaly Detected", type: "warning", detail: "Unusual query frequency from Node-047" },
  { time: "08:16", event: "Beaconing Pattern", type: "warning", detail: "Periodic outbound requests on port 443" },
  { time: "08:17", event: "C2 Communication", type: "critical", detail: "Command & Control server contact confirmed" },
  { time: "08:18", event: "Threat Confirmed", type: "critical", detail: "Mirai variant botnet identified" },
  { time: "08:22", event: "Isolation Triggered", type: "safe", detail: "Node quarantined by AI Core" },
];

const INCIDENTS = [
  { label: "DDoS Amplification", severity: "Critical", src: "AS45899 — Vietnam", ago: "2m ago" },
  { label: "Botnet Beacon Loop", severity: "High", src: "Node-047 — Internal", ago: "11m ago" },
  { label: "Port Scan Sweep", severity: "Medium", src: "192.168.3.44", ago: "29m ago" },
  { label: "Phishing DNS Redirect", severity: "Medium", src: "External Domain", ago: "1h ago" },
  { label: "Patch Applied", severity: "Resolved", src: "Gateway-02", ago: "2h ago" },
];

const THREAT_DNA = [
  { label: "C2 Beaconing", pct: 92, color: COLORS.red },
  { label: "Port Scanning", pct: 74, color: COLORS.amber },
  { label: "DNS Tunneling", pct: 61, color: COLORS.amber },
  { label: "Lateral Movement", pct: 48, color: COLORS.purple },
  { label: "Credential Harvest", pct: 33, color: COLORS.cyan },
];

const DEVICES = [
  { name: "WKSTN-047", os: "Windows 11", risk: 83, net: 92, cpu: 35, status: "SUSPICIOUS" },
  { name: "SRV-NGINX-01", os: "Ubuntu 22", risk: 12, net: 8, cpu: 61, status: "SAFE" },
  { name: "IOT-CAM-003", os: "Embedded", risk: 97, net: 99, cpu: 78, status: "CRITICAL" },
];

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
      <div style={{ fontSize: 22, fontFamily: "Orbitron, monospace", fontWeight: 700, color: color || COLORS.cyan }}>
        {value}
      </div>
      {delta && <div style={{ fontSize: 9, color: COLORS.amber, marginTop: 2 }}>▲ {delta} / 24h</div>}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────
export default function KovirXDashboard() {
  const [threatLevel, setThreatLevel] = useState("high");
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [replaying, setReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState(-1);
  const [activeTab, setActiveTab] = useState("monitor");
  const [pulseCore, setPulseCore] = useState(false);

  // Replay animation
  useEffect(() => {
    if (!replaying) return;
    setReplayStep(0);
    const steps = REPLAY_STEPS.length;
    let i = 0;
    const iv = setInterval(() => {
      i++;
      setReplayStep(i);
      if (i >= steps - 1) { clearInterval(iv); setTimeout(() => { setReplaying(false); setReplayStep(-1); }, 1800); }
    }, 900);
    return () => clearInterval(iv);
  }, [replaying]);

  // Random core pulse
  useEffect(() => {
    const iv = setInterval(() => { setPulseCore(true); setTimeout(() => setPulseCore(false), 600); }, 4000);
    return () => clearInterval(iv);
  }, []);

  const navItems = [
    { id: "monitor", icon: "⬡", label: "NEXUS" },
    { id: "threats", icon: "⚠", label: "THREATS" },
    { id: "devices", icon: "◫", label: "DEVICES" },
    { id: "replay", icon: "▶", label: "REPLAY" },
  ];

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

        {/* NAV LINKS */}
        <div style={{ display: "flex", alignItems: "center", gap: 2, padding: "0 16px" }}>
          {navItems.map(n => (
            <button key={n.id} onClick={() => setActiveTab(n.id)} style={{
              background: activeTab === n.id ? "#00D4FF11" : "none",
              border: "none", cursor: "pointer", padding: "6px 14px", height: "100%",
              fontFamily: "Orbitron, monospace", fontSize: 10, letterSpacing: 2, fontWeight: 700,
              color: activeTab === n.id ? COLORS.cyan : COLORS.textDim,
              borderBottom: activeTab === n.id ? `2px solid ${COLORS.cyan}` : "2px solid transparent",
              borderRadius: "4px 4px 0 0", transition: "all 0.2s",
            }}>
              {n.icon} {n.label}
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        {/* RIGHT STATUS */}
        <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "0 24px",
          borderLeft: `1px solid ${COLORS.panelBorder}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: COLORS.red,
              boxShadow: `0 0 8px ${COLORS.red}`, flexShrink: 0,
              animation: "threatBlink 1.2s infinite" }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.red,
                letterSpacing: 2, fontWeight: 700 }}>LIVE THREAT</span>
              <span style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace",
                letterSpacing: 1 }}>MIRAI VARIANT ACTIVE</span>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 2, alignItems: "flex-end" }}>
            <span style={{ fontSize: 12, fontFamily: "Orbitron, monospace", color: COLORS.text, letterSpacing: 1 }}>
              {new Date().toLocaleTimeString("en-US", { hour12: false })}
            </span>
            <span style={{ fontSize: 8, color: COLORS.textDim, fontFamily: "Orbitron, monospace", letterSpacing: 2 }}>UTC · LIVE</span>
          </div>
        </div>
      </div>

      {/* STAT BAR */}
      <div style={{ display: "flex", gap: 8, padding: "8px 16px", flexShrink: 0 }}>
        <StatCard label="THREAT ACTORS" value="20" delta="9" />
        <StatCard label="ACTIVE INDICATORS" value="430K" delta="307K" color={COLORS.amber} />
        <StatCard label="MALWARE TRACKED" value="6.62K" delta="2053" color={COLORS.red} />
        <StatCard label="AI CONFIDENCE" value="98%" color={COLORS.purple} />
        <StatCard label="NODES MONITORED" value="2,847" color={COLORS.cyan} />
        <StatCard label="SYSTEM HEALTH" value="98.7%" color={COLORS.safe} />
      </div>

      {/* MAIN BODY */}
      <div style={{ flex: 1, display: "flex", gap: 8, padding: "0 16px 12px", minHeight: 0, overflow: "hidden" }}>

        {/* LEFT COLUMN */}
        <div style={{ width: 240, display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>

          {/* Threat Timeline */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px", flex: 1, overflow: "hidden" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 10 }}>THREAT TIMELINE</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {TIMELINE.map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 10, position: "relative",
                  animation: `slideIn 0.4s ease ${i * 0.1}s both` }}>
                  {/* connector */}
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 16 }}>
                    <div style={{ width: 10, height: 10, borderRadius: "50%", flexShrink: 0,
                      background: item.type === "critical" ? COLORS.red :
                                  item.type === "warning" ? COLORS.amber : COLORS.cyan,
                      border: `2px solid ${COLORS.panel}`,
                      boxShadow: `0 0 8px ${item.type === "critical" ? COLORS.red :
                                  item.type === "warning" ? COLORS.amber : COLORS.cyan}` }} />
                    {i < TIMELINE.length - 1 && (
                      <div style={{ width: 1, flex: 1, minHeight: 24,
                        background: `linear-gradient(${COLORS.panelBorder}, transparent)` }} />
                    )}
                  </div>
                  <div style={{ paddingBottom: 14, flex: 1 }}>
                    <div style={{ fontSize: 9, color: COLORS.textDim, fontFamily: "Orbitron, monospace" }}>
                      {item.time}
                    </div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: COLORS.text, marginTop: 1 }}>
                      {item.event}
                    </div>
                    <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 2, lineHeight: 1.4 }}>
                      {item.detail}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Threat DNA */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 8 }}>THREAT DNA</div>
            <div style={{ fontSize: 10, color: COLORS.red, fontFamily: "Orbitron, monospace",
              marginBottom: 8, fontWeight: 700 }}>FAMILY: MIRAI VARIANT</div>
            {THREAT_DNA.map((d, i) => (
              <div key={i} style={{ marginBottom: 7 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 10, color: COLORS.text }}>{d.label}</span>
                  <span style={{ fontSize: 10, color: d.color, fontFamily: "Orbitron, monospace" }}>{d.pct}%</span>
                </div>
                <div style={{ height: 4, background: COLORS.panelBorder, borderRadius: 2 }}>
                  <div style={{ height: "100%", width: `${d.pct}%`, background: d.color,
                    borderRadius: 2, boxShadow: `0 0 6px ${d.color}88`,
                    transition: "width 1s ease" }} />
                </div>
              </div>
            ))}
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
                color: COLORS.purple, letterSpacing: 3 }}>AI CORE — 98% CONFIDENCE</div>
            </div>
          </div>

          {/* Replay Panel */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim, letterSpacing: 2 }}>
                THREAT REPLAY — WKSTN-047
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
                  fontWeight: 900, color: COLORS.purple }}>98%</div>
                <div style={{ fontSize: 7, color: COLORS.textDim, letterSpacing: 1 }}>CONFIDENCE</div>
              </div>
            </div>
            <div style={{ marginTop: 12, display: "flex", justifyContent: "center", gap: 6 }}>
              {[["LOW", COLORS.cyan], ["MED", COLORS.amber], ["HIGH", COLORS.red]].map(([l, c]) => (
                <div key={l} style={{ padding: "2px 8px", borderRadius: 3,
                  background: l === "HIGH" ? c + "33" : "transparent",
                  border: `1px solid ${l === "HIGH" ? c : COLORS.panelBorder}`,
                  fontSize: 8, fontFamily: "Orbitron, monospace", color: l === "HIGH" ? c : COLORS.textDim,
                  letterSpacing: 1 }}>
                  {l}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 8, fontSize: 9, color: COLORS.red,
              fontFamily: "Orbitron, monospace", animation: "threatBlink 1.5s infinite" }}>
              ⬡ ACTIVE THREAT DETECTED
            </div>
          </div>

          {/* Recent Incidents */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px", flex: 1, overflow: "auto" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 10 }}>SECURITY INCIDENTS</div>
            {INCIDENTS.map((inc, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", gap: 3,
                padding: "8px 0", borderBottom: i < INCIDENTS.length - 1 ? `1px solid ${COLORS.panelBorder}` : "none" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 11, fontWeight: 600 }}>{inc.label}</span>
                  <SeverityBadge sev={inc.severity} />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 10, color: COLORS.textDim }}>{inc.src}</span>
                  <span style={{ fontSize: 10, color: COLORS.textDim }}>{inc.ago}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Device Cards */}
          <div style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelBorder}`,
            borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, fontFamily: "Orbitron, monospace", color: COLORS.textDim,
              letterSpacing: 2, marginBottom: 8 }}>DEVICE INTELLIGENCE</div>
            {DEVICES.map((d, i) => (
              <div key={i} onClick={() => setSelectedDevice(selectedDevice?.name === d.name ? null : d)}
                style={{ padding: "8px 10px", borderRadius: 7, marginBottom: 6, cursor: "pointer",
                  background: selectedDevice?.name === d.name ? COLORS.panelBorder : "transparent",
                  border: `1px solid ${d.status === "CRITICAL" ? COLORS.red + "55" :
                            d.status === "SUSPICIOUS" ? COLORS.amber + "55" : COLORS.panelBorder}`,
                  transition: "all 0.2s" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <div>
                    <div style={{ fontFamily: "Orbitron, monospace", fontSize: 10,
                      fontWeight: 700, color: COLORS.text }}>{d.name}</div>
                    <div style={{ fontSize: 9, color: COLORS.textDim }}>{d.os}</div>
                  </div>
                  <span style={{ fontSize: 9, fontFamily: "Orbitron, monospace", fontWeight: 700,
                    color: d.status === "CRITICAL" ? COLORS.red : d.status === "SUSPICIOUS" ? COLORS.amber : COLORS.cyan,
                    animation: d.status === "CRITICAL" ? "threatBlink 1.2s infinite" : "none" }}>
                    {d.status}
                  </span>
                </div>

                {selectedDevice?.name === d.name && (
                  <div style={{ marginTop: 6, animation: "slideIn 0.3s ease" }}>
                    {[["Risk Score", d.risk, COLORS.red], ["Network Score", d.net, COLORS.amber], ["CPU Usage", d.cpu, COLORS.cyan]].map(([lbl, val, col]) => (
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
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
