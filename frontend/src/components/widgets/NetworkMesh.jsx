import { useEffect, useRef } from "react";

export const COLORS = {
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

export default function NetworkMesh({ threatLevel, devices = [] }) {
  const canvasRef = useRef(null);
  const nodesRef = useRef([]);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W;
    canvas.height = H;

    const cx = W / 2, cy = H / 2;
    const nodes = [{ x: cx, y: cy, r: 18, state: "monitoring", pulse: 0, fixed: true, label: "AI CORE", deviceId: "core" }];

    if (devices && devices.length > 0) {
      devices.forEach((device, index) => {
        const count = devices.length;
        const angle = (index / count) * Math.PI * 2 - Math.PI / 2;
        const radius = count <= 4 ? 100 : count <= 8 ? 160 : 210;

        let state = "safe";
        if (device.status === "quarantined" || device.risk_score >= 85) {
          state = "critical";
        } else if (device.risk_score >= 35) {
          state = "warning";
        } else if (device.status === "online") {
          state = "monitoring";
        }

        nodes.push({
          x: cx + Math.cos(angle) * radius,
          y: cy + Math.sin(angle) * radius,
          r: 10,
          state: state,
          pulse: Math.random() * Math.PI * 2,
          fixed: false,
          label: device.hostname,
          deviceId: device.id,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          ox: cx + Math.cos(angle) * radius,
          oy: cy + Math.sin(angle) * radius,
        });
      });
    } else {
      const rings = [
        { count: 4, radius: 90, states: ["safe", "monitoring", "safe", "safe"] },
        { count: 6, radius: 170, states: ["safe", "warning", "safe", "safe", "warning", "safe"] },
      ];
      rings.forEach(ring => {
        for (let i = 0; i < ring.count; i++) {
          const angle = (i / ring.count) * Math.PI * 2 - Math.PI / 2;
          nodes.push({
            x: cx + Math.cos(angle) * ring.radius,
            y: cy + Math.sin(angle) * ring.radius,
            r: 8,
            state: ring.states[i],
            pulse: Math.random() * Math.PI * 2,
            fixed: false,
            label: `Sensor-${ring.radius}-${i}`,
            deviceId: `fallback-${ring.radius}-${i}`,
            vx: (Math.random() - 0.5) * 0.15,
            vy: (Math.random() - 0.5) * 0.15,
            ox: cx + Math.cos(angle) * ring.radius,
            oy: cy + Math.sin(angle) * ring.radius,
          });
        }
      });
    }

    nodesRef.current = nodes;
  }, [devices]);

  useEffect(() => {
    let frameId;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let prev = performance.now();

    const loop = (now) => {
      const delta = now - prev;
      prev = now;
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
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > 18) { n.vx -= dx * 0.002; n.vy -= dy * 0.002; }
      });

      // Draw edges
      nodes.forEach((a) => {
        if (a.deviceId === "core") return;
        const b = nodes[0];
        const dx = a.x - b.x, dy = a.y - b.y;
        const alpha = 0.35;
        const isActive = a.state === "critical" || a.state === "warning";
        const edgeColor = a.state === "critical" ? COLORS.red : isActive ? COLORS.amber : COLORS.cyan;
        
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = edgeColor + Math.floor(alpha * 255).toString(16).padStart(2, "0");
        ctx.lineWidth = isActive ? 1.2 : 0.6;
        ctx.stroke();

        // Traveling telemetry packets
        const packetCycles = isActive ? 1.8 : 1.0;
        if (Math.sin(t * packetCycles + a.pulse) > 0.4) {
          const progress = (t * 0.4 + a.pulse) % 1.0;
          const px = a.x + (b.x - a.x) * progress;
          const py = a.y + (b.y - a.y) * progress;
          ctx.beginPath();
          ctx.arc(px, py, isActive ? 3 : 2, 0, Math.PI * 2);
          ctx.fillStyle = edgeColor;
          ctx.shadowBlur = isActive ? 6 : 0;
          ctx.shadowColor = edgeColor;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // Draw nodes
      nodes.forEach(n => {
        const color = NODE_COLORS[n.state] || COLORS.cyan;
        const pulseScale = 1 + Math.sin(t * 2.5 + n.pulse) * 0.15;
        const glowR = n.r * (n.fixed ? 3.5 : 2.8) * pulseScale;

        // outer glow
        const grad = ctx.createRadialGradient(n.x, n.y, n.r * 0.5, n.x, n.y, glowR);
        grad.addColorStop(0, color + "44");
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

        if (n.label) {
          ctx.font = "bold 8px Orbitron, sans-serif";
          ctx.fillStyle = COLORS.text;
          ctx.textAlign = "center";
          ctx.fillText(n.label, n.x, n.y - n.r - 8);
        }

        if (n.fixed) {
          [28, 38].forEach((rr, idx) => {
            ctx.beginPath();
            ctx.arc(n.x, n.y, rr, t * (idx === 0 ? 1.2 : -0.8), t * (idx === 0 ? 1.2 : -0.8) + Math.PI * 1.4);
            ctx.strokeStyle = COLORS.purple + "77";
            ctx.lineWidth = 1;
            ctx.stroke();
          });
        }
      });

      frameId = requestAnimationFrame(loop);
    };

    frameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameId);
  }, [threatLevel]);

  return (
    <canvas ref={canvasRef} className="w-full h-full block bg-gradient-to-b from-[#060B18] to-[#0A0F1E]" />
  );
}
