import { useState, useEffect, useRef } from "react";
import logoImg from "../assets/logo.jpg";
import {
  getDashboardSummary,
  getAlerts,
  getDevices,
  updateAlertStatus,
  logout,
  getWebSocketUrl,
  getCurrentUser,
  registerDevice,
  deleteDevice,
  assignAlert,
  generateReport,
  getReports,
  downloadReport,
  getSystemLogs,
  getAuditLogs,
  ingestTelemetry
} from "../services/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  ShieldAlert,
  Laptop,
  FileText,
  Terminal,
  LogOut,
  Activity,
  Wifi,
  WifiOff,
  Clock,
  Plus,
  Search,
  Download,
  RefreshCw,
  User,
  UserCheck,
  Radio,
  Trash2,
  Play,
  CheckCircle,
  AlertTriangle,
  FileSpreadsheet,
  XCircle,
  Database,
  Filter,
  ChevronLeft,
  ChevronRight,
  Shield,
  Eye
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie
} from "recharts";

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

// ── Network Mesh Canvas Component ────────────────────────────────────────
function NetworkMesh({ threatLevel, devices = [] }) {
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

    // Render registered devices dynamically around the center AI CORE
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
      // Fallback static rings if no devices are registered
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

      // Draw edges connecting all active sensor nodes to the center AI Core
      nodes.forEach((a) => {
        if (a.deviceId === "core") return;
        const b = nodes[0]; // center core
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const alpha = 0.35;
        const isActive = a.state === "critical" || a.state === "warning";
        const edgeColor = a.state === "critical" ? COLORS.red : isActive ? COLORS.amber : COLORS.cyan;
        
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = edgeColor + Math.floor(alpha * 255).toString(16).padStart(2, "0");
        ctx.lineWidth = isActive ? 1.2 : 0.6;
        ctx.stroke();

        // Animated traveling telemetry packets on connection line
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
          ctx.shadowBlur = 0; // reset
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

        // Text label
        if (n.label) {
          ctx.font = "bold 8px Orbitron, sans-serif";
          ctx.fillStyle = COLORS.text;
          ctx.textAlign = "center";
          ctx.fillText(n.label, n.x, n.y - n.r - 8);
        }

        // AI Core rotating rings
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

// ── Replay Steps ───────────────────────────────────────────────
const REPLAY_STEPS = [
  { ts: "08:15:03", label: "Agent Connect", icon: "◉" },
  { ts: "08:15:47", label: "Entropy Query", icon: "⚠" },
  { ts: "08:16:22", label: "Botnet Beacon", icon: "⬆" },
  { ts: "08:17:01", label: "C2 Handshake", icon: "⚡" },
  { ts: "08:18:00", label: "AI Containment", icon: "✕" },
];

export default function KovirXDashboard() {
  // Navigation
  const [activeView, setActiveView] = useState("dashboard");

  // User Profile
  const [currentUser, setCurrentUser] = useState(null);

  // Replay threat state
  const [threatLevel, setThreatLevel] = useState("high");
  const [replaying, setReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState(-1);
  const [pulseCore, setPulseCore] = useState(false);

  // API Ingested States
  const [summary, setSummary] = useState({
    protected_devices: 0,
    active_threats: 0,
    today_alerts: 0,
    detection_accuracy: 0.0,
    botnet_attempts_24h: 0,
    traffic_stats: { total_flows: 0, suspicious_flows: 0, blocked_flows: 0 },
    top_threat_types: [],
    severity_breakdown: {}
  });

  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);

  // Dynamic moving charts state
  const [networkFlowData, setNetworkFlowData] = useState([]);

  // Alerts View States
  const [alertsFilter, setAlertsFilter] = useState({ severity: "", status: "", search: "" });
  const [alertsPage, setAlertsPage] = useState(1);
  const [selectedAlert, setSelectedAlert] = useState(null);

  // Devices View States
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [deviceError, setDeviceError] = useState("");
  const [selectedDeviceDetails, setSelectedDeviceDetails] = useState(null);
  const [newDevice, setNewDevice] = useState({
    hostname: "",
    operating_system: "windows",
    ip_address: "",
    mac_address: "",
    os_version: "",
    architecture: "",
    agent_version: "1.0.0"
  });

  // Reports View States
  const [reports, setReports] = useState([]);
  const [reportType, setReportType] = useState("daily");
  const [reportFormat, setReportFormat] = useState("csv");
  const [reportsLoading, setReportsLoading] = useState(false);

  // Logs View States
  const [logsType, setLogsType] = useState("system"); // system or audit
  const [logsList, setLogsList] = useState([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logsPage, setLogsPage] = useState(1);
  const [logsLevel, setLogsLevel] = useState(""); // system filter
  const [logsModule, setLogsModule] = useState(""); // system filter
  const [logsAction, setLogsAction] = useState(""); // audit filter

  // Initialize network chart mock data
  useEffect(() => {
    const data = [];
    const now = new Date();
    for (let i = 15; i >= 0; i--) {
      const t = new Date(now.getTime() - i * 12000);
      data.push({
        time: t.toLocaleTimeString("en-US", { hour12: false }),
        flows: Math.floor(Math.random() * 45) + 15,
        volume: Math.floor(Math.random() * 30000) + 6000
      });
    }
    setNetworkFlowData(data);
  }, []);

  // Fetch initial profile and stats
  const loadDashboardData = async () => {
    try {
      const [sumData, alertsData, devicesData, profile] = await Promise.all([
        getDashboardSummary(),
        getAlerts(),
        getDevices(),
        getCurrentUser().catch(() => null)
      ]);
      setSummary(sumData);
      setAlerts(alertsData);
      setDevices(devicesData);
      if (profile) setCurrentUser(profile);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Sync threat level
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

      console.log("Connecting WebSocket to alerts/telemetry nexus:", wsUrl);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isMounted) setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.channel === "alerts" && payload.event === "new") {
            const newAlert = payload.data;
            if (isMounted) {
              setAlerts((prev) => [newAlert, ...prev]);
              setPulseCore(true);
              setTimeout(() => setPulseCore(false), 700);
              setSummary((prev) => ({
                ...prev,
                today_alerts: (prev.today_alerts || 0) + 1,
                active_threats: (prev.active_threats || 0) + 1,
              }));
            }
          } else if (payload.channel === "traffic" && payload.event === "ingested") {
            const flowCount = payload.data.flow_count || 1;
            if (isMounted) {
              setSummary((prev) => ({
                ...prev,
                traffic_stats: {
                  ...prev.traffic_stats,
                  total_flows: (prev.traffic_stats?.total_flows || 0) + flowCount,
                }
              }));
              // Append a live data point to Recharts line chart
              setNetworkFlowData(prev => {
                const nextTime = new Date().toLocaleTimeString("en-US", { hour12: false });
                const newPoint = {
                  time: nextTime,
                  flows: Math.floor(Math.random() * 25) + flowCount * 5,
                  volume: (Math.floor(Math.random() * 25) + flowCount * 5) * (Math.floor(Math.random() * 600) + 150)
                };
                return [...prev.slice(1), newPoint];
              });
            }
          }
        } catch (err) {
          console.error("Error parsing WS payload:", err);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWS, 4000);
        }
      };

      ws.onerror = () => {
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

  const handleRunMalwareAttack = async () => {
    setReplaying(true);

    const deviceId = "cf5349e5-066e-4d32-b4aa-c841738846e0";
    const scenarios = [
      {
        flow: {
          source_ip: "192.168.1.105",
          dest_ip: "185.220.101.42",
          protocol: "UDP",
          packet_count: 120,
          byte_count: 15000,
          flow_duration: 1.5,
          start_time: new Date().toISOString(),
          end_time: new Date().toISOString(),
          dns_query: "x7k9m2p4q8r1.evil-botnet.xyz",
          dns_entropy: 4.6
        },
        prediction: {
          xgb_score: 0.98,
          is_anomaly: true,
          threat_type: "DNS Abuse",
          features_used: { max_dns_entropy: 4.6, dns_query_count: 10.0 }
        },
        risk: {
          risk_score: 85,
          severity: "critical",
          recommendation: "Quarantine device immediately and run offline malware scan."
        }
      },
      {
        flow: {
          source_ip: "192.168.1.42",
          dest_ip: "45.33.32.156",
          protocol: "TCP",
          packet_count: 35,
          byte_count: 6000,
          flow_duration: 30.0,
          start_time: new Date().toISOString(),
          end_time: new Date().toISOString(),
          beacon_interval: 0.005
        },
        prediction: {
          xgb_score: 0.99,
          is_anomaly: true,
          threat_type: "Beaconing",
          features_used: { beacon_interval_score: 0.9, connection_count: 5.0 }
        },
        risk: {
          risk_score: 96,
          severity: "critical",
          recommendation: "Block C2 destination IP and investigate endpoint registry."
        }
      },
      {
        flow: {
          source_ip: "192.168.1.200",
          dest_ip: "10.0.0.50",
          protocol: "TCP",
          packet_count: 6,
          byte_count: 400,
          flow_duration: 0.2,
          start_time: new Date().toISOString(),
          end_time: new Date().toISOString(),
          failed_connections: 5
        },
        prediction: {
          xgb_score: 0.88,
          is_anomaly: true,
          threat_type: "Port Scan",
          features_used: { failed_connection_ratio: 0.8, tcp_flag_score: 0.5 }
        },
        risk: {
          risk_score: 75,
          severity: "high",
          recommendation: "Block port scan source host and review internal network map."
        }
      },
      {
        flow: {
          source_ip: "192.168.1.77",
          dest_ip: "104.21.45.12",
          protocol: "TCP",
          packet_count: 1200,
          byte_count: 1200000,
          flow_duration: 60.0,
          start_time: new Date().toISOString(),
          end_time: new Date().toISOString()
        },
        prediction: {
          xgb_score: 0.92,
          is_anomaly: true,
          threat_type: "Command & Control",
          features_used: { bytes_sent: 1000000.0, outbound_frequency: 10.0 }
        },
        risk: {
          risk_score: 90,
          severity: "high",
          recommendation: "Quarantine exfiltration target and isolate host from internet."
        }
      }
    ];

    scenarios.forEach((scenario, idx) => {
      setTimeout(async () => {
        try {
          const payload = {
            device_id: deviceId,
            events: [
              {
                ...scenario,
                collected_at: new Date().toISOString()
              }
            ],
            generated_at: new Date().toISOString()
          };
          await ingestTelemetry(payload);
          console.log(`Ingested scenario ${idx + 1}`);
        } catch (err) {
          console.error("Failed to ingest scenario:", err);
        }
      }, idx * 1100);
    });
  };

  // MITRE Replay Simulation Effect
  useEffect(() => {
    if (!replaying) return;
    setReplayStep(0);
    const steps = REPLAY_STEPS.length;
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setReplayStep(i);
      if (i >= steps - 1) {
        clearInterval(interval);
        setTimeout(() => {
          setReplaying(false);
          setReplayStep(-1);
        }, 2000);
      }
    }, 1100);
    return () => clearInterval(interval);
  }, [replaying]);

  // Load past reports
  const loadReportsList = async () => {
    try {
      const reportList = await getReports();
      setReports(reportList);
    } catch (err) {
      console.error(err);
    }
  };

  // Poll pending reports
  useEffect(() => {
    let interval = null;
    const hasPending = reports.some(r => r.status === "pending");
    if (hasPending) {
      interval = setInterval(() => {
        loadReportsList();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [reports]);

  // Trigger loading reports list when entering reports view
  useEffect(() => {
    if (activeView === "reports") {
      loadReportsList();
    }
  }, [activeView]);

  // Load logs when logs view settings change
  const loadLogsList = async () => {
    try {
      const skip = (logsPage - 1) * 20;
      if (logsType === "system") {
        const res = await getSystemLogs(logsLevel || null, logsModule || null, skip, 20);
        setLogsList(res.logs || []);
        setLogsTotal(res.total || 0);
      } else {
        const res = await getAuditLogs(null, logsAction || null, skip, 20);
        setLogsList(res.logs || []);
        setLogsTotal(res.total || 0);
      }
    } catch (err) {
      console.error("Failed to load logs:", err);
    }
  };

  useEffect(() => {
    if (activeView === "logs") {
      loadLogsList();
    }
  }, [activeView, logsType, logsPage, logsLevel, logsModule, logsAction]);

  // Handle device registration
  const handleAddDevice = async (e) => {
    e.preventDefault();
    setDeviceError("");
    try {
      await registerDevice(newDevice);
      setShowAddDeviceModal(false);
      setNewDevice({
        hostname: "",
        operating_system: "windows",
        ip_address: "",
        mac_address: "",
        os_version: "",
        architecture: "",
        agent_version: "1.0.0"
      });
      loadDashboardData();
    } catch (err) {
      setDeviceError(err.message || "Failed to register endpoint device.");
    }
  };

  // Handle device deletion
  const handleDeleteDevice = async (deviceId) => {
    if (confirm("Are you sure you want to delete this device? This will remove all associated logs and metrics.")) {
      try {
        await deleteDevice(deviceId);
        loadDashboardData();
      } catch (err) {
        alert(err.message || "Error deleting device");
      }
    }
  };

  // Handle report generation trigger
  const handleGenerateReport = async () => {
    setReportsLoading(true);
    try {
      await generateReport(reportType, reportFormat);
      await loadReportsList();
    } catch (err) {
      alert("Report generation failed: " + err.message);
    } finally {
      setReportsLoading(false);
    }
  };

  // Handle report download
  const handleDownloadReport = async (reportId, filename) => {
    try {
      const blob = await downloadReport(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Download failed: " + err.message);
    }
  };

  // Severity style helper
  const getSeverityBadgeClass = (sev) => {
    const s = (sev || "").toLowerCase();
    if (s === "critical") return "bg-red/10 border-red text-red";
    if (s === "high") return "bg-amber/10 border-amber text-amber";
    if (s === "medium") return "bg-purple/10 border-purple text-purple";
    return "bg-cyan/10 border-cyan text-cyan";
  };

  // OS Logo Resolver
  const getOSIcon = (os) => {
    const o = (os || "").toLowerCase();
    if (o.includes("win")) return "Windows";
    if (o.includes("lin") || o.includes("ubuntu")) return "Linux";
    if (o.includes("mac") || o.includes("ios")) return "MacOS";
    if (o.includes("andr")) return "Android";
    return "IoT/Unknown";
  };

  // Filter Alerts
  const filteredAlerts = alerts.filter(a => {
    if (alertsFilter.severity && a.severity.toLowerCase() !== alertsFilter.severity.toLowerCase()) return false;
    if (alertsFilter.status && a.status.toLowerCase() !== alertsFilter.status.toLowerCase()) return false;
    if (alertsFilter.search) {
      const q = alertsFilter.search.toLowerCase();
      const titleMatch = a.title.toLowerCase().includes(q);
      const descMatch = (a.description || "").toLowerCase().includes(q);
      const ipMatch = (a.evidence?.source_ip || "").toLowerCase().includes(q);
      if (!titleMatch && !descMatch && !ipMatch) return false;
    }
    return true;
  });

  return (
    <div className="w-screen h-screen bg-bg text-text font-sans flex overflow-hidden">
      {/* ── SIDEBAR ────────────────────────────────────────────── */}
      <aside className="w-64 bg-panel border-r border-panelBorder flex flex-col justify-between flex-shrink-0 z-20">
        <div>
          {/* Brand header */}
          <div className="flex items-center gap-3 p-5 border-b border-panelBorder bg-[#050A16]">
            <div className="relative">
              <div className="absolute -inset-3 rounded-full bg-cyan/10 blur-sm pointer-events-none" />
              <img
                src={logoImg}
                alt="KovirX Logo"
                className="h-10 w-10 object-contain filter drop-shadow-[0_0_8px_rgba(0,212,255,0.5)]"
              />
            </div>
            <div className="flex flex-col">
              <span className="font-orbitron font-black text-sm tracking-[2px] bg-gradient-to-r from-white to-cyan bg-clip-text text-transparent">
                KOVIRX
              </span>
              <span className="font-orbitron text-[7px] tracking-[1.5px] text-textDim">
                BOTNET THREAT NEXUS
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <button
              onClick={() => setActiveView("dashboard")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                activeView === "dashboard"
                  ? "bg-gradient-to-r from-purple/20 to-cyan/20 border-l-2 border-cyan text-white"
                  : "text-textDim hover:text-white hover:bg-panelBorder/40 border-l-2 border-transparent"
              }`}
            >
              <LayoutDashboard className="h-4.5 w-4.5 text-cyan" />
              DASHBOARD
            </button>

            <button
              onClick={() => { setActiveView("alerts"); setAlertsPage(1); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                activeView === "alerts"
                  ? "bg-gradient-to-r from-purple/20 to-cyan/20 border-l-2 border-cyan text-white"
                  : "text-textDim hover:text-white hover:bg-panelBorder/40 border-l-2 border-transparent"
              }`}
            >
              <ShieldAlert className="h-4.5 w-4.5 text-red" />
              INCIDENTS
              {alerts.filter(a => a.status === 'new').length > 0 && (
                <span className="ml-auto bg-red text-white text-[9px] font-bold px-2 py-0.5 rounded-full font-orbitron">
                  {alerts.filter(a => a.status === 'new').length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveView("devices")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                activeView === "devices"
                  ? "bg-gradient-to-r from-purple/20 to-cyan/20 border-l-2 border-cyan text-white"
                  : "text-textDim hover:text-white hover:bg-panelBorder/40 border-l-2 border-transparent"
              }`}
            >
              <Laptop className="h-4.5 w-4.5 text-purple" />
              ENDPOINTS
            </button>

            <button
              onClick={() => setActiveView("reports")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                activeView === "reports"
                  ? "bg-gradient-to-r from-purple/20 to-cyan/20 border-l-2 border-cyan text-white"
                  : "text-textDim hover:text-white hover:bg-panelBorder/40 border-l-2 border-transparent"
              }`}
            >
              <FileText className="h-4.5 w-4.5 text-amber" />
              REPORTS
            </button>

            <button
              onClick={() => { setActiveView("logs"); setLogsPage(1); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                activeView === "logs"
                  ? "bg-gradient-to-r from-purple/20 to-cyan/20 border-l-2 border-cyan text-white"
                  : "text-textDim hover:text-white hover:bg-panelBorder/40 border-l-2 border-transparent"
              }`}
            >
              <Terminal className="h-4.5 w-4.5 text-safe" />
              AUDIT LOGS
            </button>
          </nav>
        </div>

        {/* Analyst Info & Logout */}
        <div className="p-4 border-t border-panelBorder bg-[#050A16]/50">
          {currentUser ? (
            <div className="mb-4 flex items-center gap-3 p-2 rounded-lg bg-panelBorder/30">
              <div className="h-8 w-8 rounded-full bg-cyan/15 flex items-center justify-center text-cyan font-bold border border-cyan/40">
                {currentUser.username.substring(0, 2).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[11px] font-bold text-white truncate">{currentUser.username}</span>
                <span className="text-[9px] text-textDim uppercase tracking-wider font-semibold font-orbitron text-purple">
                  {currentUser.role.replace("super_", "").replace("_", " ")}
                </span>
              </div>
            </div>
          ) : (
            <div className="mb-4 h-12 animate-pulse bg-panelBorder/30 rounded-lg" />
          )}

          <button
            onClick={logout}
            className="w-full py-2.5 rounded-lg border border-red/40 bg-red/5 hover:bg-red/20 text-red font-orbitron text-[9px] font-bold tracking-[2px] transition-all duration-200 flex items-center justify-center gap-2"
          >
            <LogOut className="h-3 w-3" />
            SECURE EXIT
          </button>
        </div>
      </aside>

      {/* ── MAIN WORKSPACE ───────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-bg relative">
        {/* Header Ribbon */}
        <header className="h-16 border-b border-panelBorder bg-panel/75 backdrop-blur-md flex items-center justify-between px-6 flex-shrink-0 z-10">
          <div className="flex items-center gap-6">
            {/* Status Indicator */}
            <div className="flex items-center gap-2 bg-[#050A16] px-3.5 py-1.5 rounded-lg border border-panelBorder">
              <span className={`h-2 w-2 rounded-full shadow-[0_0_8px] ${
                wsConnected ? "bg-safe shadow-safe" : "bg-red shadow-red animate-pulse"
              }`} />
              <span className={`font-orbitron text-[9px] font-bold tracking-wider ${
                wsConnected ? "text-safe" : "text-red"
              }`}>
                {wsConnected ? "NEXUS SECURE ONLINE" : "TELEMETRY DISCONNECTED"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6 divide-x divide-panelBorder">
            {/* System Level Gauge */}
            <div className="flex items-center gap-3">
              <span className={`h-2.5 w-2.5 rounded-full shadow-[0_0_8px] ${
                threatLevel === "critical" || threatLevel === "high"
                  ? "bg-red shadow-red animate-pulse"
                  : threatLevel === "warning"
                  ? "bg-amber shadow-amber"
                  : "bg-safe shadow-safe"
              }`} />
              <div className="flex flex-col">
                <span className="font-orbitron text-[8px] text-textDim tracking-wider">DEFENSE SHIELD</span>
                <span className={`text-[10px] font-orbitron font-black tracking-widest uppercase ${
                  threatLevel === "critical" || threatLevel === "high"
                    ? "text-red"
                    : threatLevel === "warning"
                    ? "text-amber"
                    : "text-safe"
                }`}>
                  {threatLevel === "critical" || threatLevel === "high" ? "CRITICAL ALERT" : threatLevel === "warning" ? "WARNING" : "SECURED"}
                </span>
              </div>
            </div>

            {/* Time Stamp */}
            <div className="pl-6 flex items-center gap-3">
              <Clock className="h-4.5 w-4.5 text-textDim" />
              <div className="flex flex-col items-end font-orbitron">
                <span className="text-[11px] font-bold text-white tracking-widest">
                  {new Date().toLocaleTimeString("en-US", { hour12: false })}
                </span>
                <span className="text-[7px] text-textDim tracking-wider">UTC LIVE CHRONOS</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Content Views */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            {/* 1. DASHBOARD VIEW */}
            {activeView === "dashboard" && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Stats Counter Bar */}
                <div className="grid grid-cols-6 gap-4">
                  {[
                    { label: "ACTIVE THREATS", val: summary.active_threats, col: COLORS.red },
                    { label: "NET FLOWS", val: (summary.traffic_stats?.total_flows || 0).toLocaleString(), col: COLORS.amber },
                    { label: "SUSPICIOUS TRAFFIC", val: (summary.traffic_stats?.suspicious_flows || 0).toLocaleString(), col: COLORS.red },
                    { label: "AI DETECTOR ACCURACY", val: `${summary.detection_accuracy}%`, col: COLORS.purple },
                    { label: "MONITORED ENDPOINTS", val: summary.protected_devices, col: COLORS.cyan },
                    { label: "TODAY'S ALERTS", val: summary.today_alerts, col: COLORS.safe },
                  ].map((s, idx) => (
                    <div
                      key={idx}
                      className="bg-panel border border-panelBorder rounded-xl p-4 flex flex-col justify-between shadow-lg relative overflow-hidden group"
                    >
                      <div className="absolute top-0 right-0 h-10 w-10 bg-gradient-to-bl from-white/5 to-transparent rounded-bl-full pointer-events-none" />
                      <span className="font-orbitron text-[9px] text-textDim tracking-widest mb-2 font-bold block">{s.label}</span>
                      <span className="font-orbitron text-xl font-black text-white" style={{ color: s.col || COLORS.cyan }}>
                        {s.val}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Primary Network Grid & Cyber core */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  {/* Left stats: Timeline & Threat DNA */}
                  <div className="space-y-6 lg:col-span-1">
                    {/* Incidents Feed */}
                    <div className="bg-panel border border-panelBorder rounded-xl p-5 flex flex-col h-[320px]">
                      <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-4 block">
                        INCIDENT TIMELINE
                      </span>
                      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                        {alerts.length > 0 ? (
                          alerts.slice(0, 10).map((a, idx) => (
                            <div key={idx} className="flex gap-3 text-xs">
                              <div className="flex flex-col items-center">
                                <span className={`h-2 w-2 rounded-full ${
                                  a.severity === "critical" ? "bg-red" : a.severity === "high" ? "bg-amber" : "bg-cyan"
                                }`} />
                                <div className="w-[1px] flex-1 bg-panelBorder/40 mt-1" />
                              </div>
                              <div className="flex-1">
                                <span className="font-orbitron text-[8px] text-textDim block">
                                  {new Date(a.created_at).toLocaleTimeString("en-US", { hour12: false })}
                                </span>
                                <span className="font-bold text-white block mt-0.5 truncate">{a.title}</span>
                                <p className="text-[10px] text-textDim line-clamp-1">{a.description}</p>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center text-textDim text-xs py-10">No incident alerts recorded.</div>
                        )}
                      </div>
                    </div>

                    {/* Threat DNA list */}
                    <div className="bg-panel border border-panelBorder rounded-xl p-5">
                      <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-4 block">
                        AI CLASSIFICATION DISTRIBUTION
                      </span>
                      <div className="space-y-3">
                        {summary.top_threat_types && summary.top_threat_types.length > 0 ? (
                          summary.top_threat_types.map((th, idx) => {
                            const total = summary.top_threat_types.reduce((acc, curr) => acc + curr.count, 0) || 1;
                            const percentage = Math.round((th.count / total) * 100);
                            const palette = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.cyan];
                            const stroke = palette[idx % palette.length];
                            return (
                              <div key={idx} className="text-xs">
                                <div className="flex justify-between mb-1">
                                  <span className="text-white truncate font-medium max-w-[120px]">{th.threat_type}</span>
                                  <span className="font-orbitron font-semibold" style={{ color: stroke }}>
                                    {th.count} ({percentage}%)
                                  </span>
                                </div>
                                <div className="h-1.5 bg-panelBorder/60 rounded-full overflow-hidden">
                                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${percentage}%`, backgroundColor: stroke }} />
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div className="text-center text-textDim text-xs py-4">No active threat profiles.</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Center Node Mesh */}
                  <div className="lg:col-span-2 bg-panel border border-panelBorder rounded-xl h-[480px] overflow-hidden relative flex flex-col shadow-inner">
                    <div className="absolute top-5 left-5 z-10">
                      <h3 className="font-orbitron font-bold text-xs text-cyan tracking-wider">NETWORK TOPOLOGY NEXUS</h3>
                      <p className="text-[9px] text-textDim tracking-wider mt-0.5">CYBER-FLOW HEURISTIC GRAPH</p>
                    </div>

                    <div className="absolute top-5 right-5 z-10 flex gap-4 text-[9px] font-orbitron font-medium text-textDim">
                      <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-cyan" /> SCANNING</span>
                      <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-safe" /> SECURED</span>
                      <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-red animate-pulse" /> ANOMALY</span>
                    </div>

                    <div className="flex-1 w-full relative">
                      <NetworkMesh threatLevel={threatLevel} devices={devices} />
                    </div>

                    <div className="absolute bottom-5 left-1/2 transform -translate-x-1/2 z-10 text-center pointer-events-none">
                      <span className="font-orbitron text-[8px] text-purple tracking-[2px] font-semibold bg-panel/85 px-4 py-1.5 border border-panelBorder rounded-full shadow-lg">
                        XGBOOST CORE & ISOLATION DETECTOR ACTIVE
                      </span>
                    </div>
                  </div>

                  {/* Right Column: AI Brain & Incidents */}
                  <div className="lg:col-span-1 space-y-6">
                    {/* Pulsing Core Widget */}
                    <div className="bg-panel border border-panelBorder rounded-xl p-5 flex flex-col items-center justify-center text-center h-[260px] relative overflow-hidden">
                      <span className="absolute top-4 left-4 font-orbitron text-[8px] text-textDim tracking-widest">
                        AI DETECTOR CORE
                      </span>
                      <div className="relative my-4 flex items-center justify-center">
                        <div className="absolute h-28 w-28 rounded-full border border-purple/30 animate-ping pointer-events-none" />
                        <div className="absolute h-24 w-24 rounded-full border border-cyan/20 pointer-events-none" />
                        <div className="h-20 w-20 rounded-full bg-[#050A16] border-2 border-purple flex flex-col items-center justify-center shadow-[0_0_20px_rgba(155,89,255,0.2)] animate-pulse">
                          <span className="font-orbitron text-lg font-black text-purple">{parseFloat(summary.detection_accuracy).toFixed(0)}%</span>
                          <span className="text-[7px] text-textDim font-bold font-orbitron uppercase tracking-widest mt-0.5">STABILITY</span>
                        </div>
                      </div>
                      <div className="text-[10px] font-orbitron tracking-widest uppercase mt-2">
                        {threatLevel === "safe" ? (
                          <span className="text-safe flex items-center gap-1.5"><CheckCircle className="h-3 w-3" /> SHIELD SECURE</span>
                        ) : (
                          <span className="text-red flex items-center gap-1.5 animate-pulse"><AlertTriangle className="h-3 w-3" /> COMPROMISED</span>
                        )}
                      </div>
                    </div>

                    {/* MITRE Threat Replay control */}
                    <div className="bg-panel border border-panelBorder rounded-xl p-5 flex flex-col justify-between h-[200px]">
                      <div>
                        <span className="font-orbitron text-[9px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-3 block">
                          MITRE ATT&CK REPLAY SIMULATOR
                        </span>
                        <div className="flex gap-1.5 justify-between items-center my-3">
                          {REPLAY_STEPS.map((s, idx) => (
                            <div key={idx} className="flex flex-col items-center flex-1">
                              <div
                                className={`h-6 w-6 rounded-full border flex items-center justify-center text-[10px] transition-all duration-300 ${
                                  replayStep >= idx
                                    ? idx === REPLAY_STEPS.length - 1
                                      ? "bg-red/20 border-red text-red shadow-[0_0_6px_#FF355E]"
                                      : "bg-cyan/20 border-cyan text-cyan shadow-[0_0_6px_#00D4FF]"
                                    : "bg-panelBorder/40 border-panelBorder/70 text-textDim"
                                }`}
                              >
                                {s.icon}
                              </div>
                              <span className="text-[7px] text-textDim mt-1 truncate max-w-[40px] text-center">{s.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <button
                        onClick={handleRunMalwareAttack}
                        disabled={replaying}
                        className={`w-full py-2.5 rounded-lg border font-orbitron text-[9px] font-bold tracking-[2px] transition-all duration-200 flex items-center justify-center gap-2 ${
                          replaying
                            ? "bg-panelBorder/50 border-panelBorder text-textDim cursor-not-allowed"
                            : "bg-red/10 border-red hover:bg-red/20 text-red cursor-pointer"
                        }`}
                      >
                        <Play className="h-3.5 w-3.5" />
                        {replaying ? "SIMULATOR ACTIVE..." : "RUN MALWARE ATTACK"}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Bottom Charts section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Realtime line charts */}
                  <div className="bg-panel border border-panelBorder rounded-xl p-5">
                    <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold mb-4 block uppercase">
                      Real-time Network Flow Ingestion (24h Trend)
                    </span>
                    <div className="h-60 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={networkFlowData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                          <XAxis dataKey="time" stroke="#5A7090" fontSize={8} tickLine={false} />
                          <YAxis stroke="#5A7090" fontSize={8} tickLine={false} />
                          <Tooltip
                            contentStyle={{ background: "#0C1426", borderColor: "#1E293B", borderRadius: "8px", fontSize: "11px" }}
                            labelClassName="font-orbitron text-cyan"
                          />
                          <Line type="monotone" dataKey="flows" stroke={COLORS.cyan} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Top categories breakdown */}
                  <div className="bg-panel border border-panelBorder rounded-xl p-5">
                    <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold mb-4 block uppercase">
                      Threat Distribution Breakdown
                    </span>
                    <div className="h-60 w-full flex items-center">
                      <div className="w-1/2 h-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={summary.top_threat_types && summary.top_threat_types.length > 0 ? summary.top_threat_types : [{ threat_type: "Safe", count: 100 }]}
                              dataKey="count"
                              nameKey="threat_type"
                              innerRadius={60}
                              outerRadius={80}
                              paddingAngle={4}
                            >
                              {(summary.top_threat_types || []).map((entry, index) => {
                                const palette = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.cyan];
                                return <Cell key={`cell-${index}`} fill={palette[index % palette.length]} />;
                              })}
                            </Pie>
                            <Tooltip contentStyle={{ background: "#0C1426", borderColor: "#1E293B", borderRadius: "8px", fontSize: "11px" }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="w-1/2 space-y-3 pr-4">
                        {(summary.top_threat_types || []).map((item, idx) => {
                          const colors = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.cyan];
                          return (
                            <div key={idx} className="flex items-center justify-between text-xs border-b border-panelBorder/30 pb-1.5">
                              <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: colors[idx % colors.length] }} />
                                <span className="text-white truncate max-w-[120px]">{item.threat_type}</span>
                              </div>
                              <span className="font-orbitron font-semibold text-textDim">{item.count}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 2. ALERTS VIEW */}
            {activeView === "alerts" && (
              <motion.div
                key="alerts"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center border-b border-panelBorder pb-4">
                  <div>
                    <h2 className="font-orbitron font-black text-lg tracking-wider text-white">INCIDENT RESPONSE</h2>
                    <p className="text-xs text-textDim mt-0.5">Analyze and mitigate security alerts triggered by ML sensors.</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={loadDashboardData}
                      className="border border-panelBorder hover:border-cyan text-textDim hover:text-white p-2.5 rounded-lg transition-colors bg-panel"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Filter Toolbar */}
                <div className="bg-panel border border-panelBorder rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-lg">
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="relative w-64">
                      <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-textDim">
                        <Search className="h-4 w-4" />
                      </span>
                      <input
                        type="text"
                        placeholder="Search IP, title, evidence..."
                        value={alertsFilter.search}
                        onChange={(e) => setAlertsFilter({ ...alertsFilter, search: e.target.value })}
                        className="w-full bg-[#060B18] border border-panelBorder rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-textDim focus:outline-none focus:border-cyan transition-all"
                      />
                    </div>

                    {/* Severity select */}
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-textDim font-bold font-orbitron">SEVERITY:</span>
                      <select
                        value={alertsFilter.severity}
                        onChange={(e) => setAlertsFilter({ ...alertsFilter, severity: e.target.value })}
                        className="bg-[#060B18] border border-panelBorder rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan"
                      >
                        <option value="">ALL SEVERITIES</option>
                        <option value="critical">CRITICAL</option>
                        <option value="high">HIGH</option>
                        <option value="medium">MEDIUM</option>
                        <option value="low">LOW</option>
                      </select>
                    </div>

                    {/* Status select */}
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-textDim font-bold font-orbitron">STATUS:</span>
                      <select
                        value={alertsFilter.status}
                        onChange={(e) => setAlertsFilter({ ...alertsFilter, status: e.target.value })}
                        className="bg-[#060B18] border border-panelBorder rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan"
                      >
                        <option value="">ALL STATUSES</option>
                        <option value="new">NEW</option>
                        <option value="investigating">INVESTIGATING</option>
                        <option value="resolved">RESOLVED</option>
                        <option value="false_positive">FALSE POSITIVE</option>
                      </select>
                    </div>
                  </div>

                  <span className="text-xs text-textDim font-orbitron">
                    FOUND: <span className="text-cyan font-bold">{filteredAlerts.length}</span> INCIDENTS
                  </span>
                </div>

                {/* Table & Details split layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                  <div className="lg:col-span-2 bg-panel border border-panelBorder rounded-xl overflow-hidden shadow-lg">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-panelBorder bg-[#050A16]/50">
                            <th className="p-4 font-semibold text-textDim tracking-wider">SEVERITY</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">ALERT NAME</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">DEVICE IP / HOST</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">STATUS</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">OCCURRED</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-panelBorder">
                          {filteredAlerts.length > 0 ? (
                            filteredAlerts.map((a) => (
                              <tr
                                key={a.id}
                                onClick={() => setSelectedAlert(selectedAlert?.id === a.id ? null : a)}
                                className={`hover:bg-panelBorder/30 transition-colors cursor-pointer ${
                                  selectedAlert?.id === a.id ? "bg-panelBorder/40" : ""
                                }`}
                              >
                                <td className="p-4">
                                  <span className={`px-2 py-0.5 rounded border text-[8px] font-orbitron font-bold tracking-wider ${
                                    getSeverityBadgeClass(a.severity)
                                  }`}>
                                    {a.severity.toUpperCase()}
                                  </span>
                                </td>
                                <td className="p-4 font-semibold text-white truncate max-w-[200px]">{a.title}</td>
                                <td className="p-4 text-textDim truncate">{a.evidence?.source_ip || "System Core"}</td>
                                <td className="p-4">
                                  <span className={`font-orbitron font-bold text-[9px] ${
                                    a.status === "new" ? "text-red animate-pulse" : a.status === "investigating" ? "text-amber" : "text-safe"
                                  }`}>
                                    {a.status.toUpperCase().replace("_", " ")}
                                  </span>
                                </td>
                                <td className="p-4 text-textDim">
                                  {new Date(a.created_at).toLocaleString()}
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan="5" className="p-8 text-center text-textDim text-sm">
                                No security incidents match selected filters.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Detail Panel */}
                  <div className="bg-panel border border-panelBorder rounded-xl p-5 shadow-lg min-h-[300px]">
                    <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-4 block">
                      INCIDENT INVESTIGATION DESK
                    </span>

                    {selectedAlert ? (
                      <div className="space-y-4">
                        <div>
                          <span className={`px-2 py-0.5 rounded border text-[8px] font-orbitron font-bold tracking-wider inline-block mb-2 ${
                            getSeverityBadgeClass(selectedAlert.severity)
                          }`}>
                            {selectedAlert.severity.toUpperCase()}
                          </span>
                          <h3 className="font-bold text-sm text-white">{selectedAlert.title}</h3>
                          <p className="text-xs text-textDim mt-1.5 leading-relaxed">{selectedAlert.description}</p>
                        </div>

                        <div className="space-y-2.5 border-t border-panelBorder/50 pt-3 text-xs text-textDim">
                          <div className="flex justify-between">
                            <span>ID:</span>
                            <span className="font-mono text-[10px] text-white select-all">{selectedAlert.id.substring(0, 18)}...</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Target Device:</span>
                            <span className="text-white font-mono">{selectedAlert.device_id.substring(0, 8)}...</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Source IP:</span>
                            <span className="text-cyan font-semibold">{selectedAlert.evidence?.source_ip || "N/A"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Dest Domain:</span>
                            <span className="text-amber truncate max-w-[140px]">{selectedAlert.evidence?.dns_query || "N/A"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Assigned Analyst:</span>
                            <span className="text-purple font-semibold">{selectedAlert.assigned_to ? "Analyst Active" : "Unassigned"}</span>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="border-t border-panelBorder/50 pt-4 space-y-2">
                          {selectedAlert.status === "new" && (
                            <button
                              onClick={async () => {
                                await updateAlertStatus(selectedAlert.id, "investigating");
                                loadDashboardData();
                                setSelectedAlert(null);
                              }}
                              className="w-full py-2 bg-amber/10 border border-amber hover:bg-amber/20 text-amber rounded-lg font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer"
                            >
                              INITIATE INVESTIGATION
                            </button>
                          )}

                          {selectedAlert.status !== "resolved" && selectedAlert.status !== "false_positive" && (
                            <div className="flex gap-2">
                              <button
                                onClick={async () => {
                                  await updateAlertStatus(selectedAlert.id, "resolved");
                                  loadDashboardData();
                                  setSelectedAlert(null);
                                }}
                                className="flex-1 py-2 bg-safe/10 border border-safe hover:bg-safe/20 text-safe rounded-lg font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer"
                              >
                                RESOLVE INCIDENT
                              </button>
                              <button
                                onClick={async () => {
                                  await updateAlertStatus(selectedAlert.id, "false_positive");
                                  loadDashboardData();
                                  setSelectedAlert(null);
                                }}
                                className="flex-1 py-2 bg-panelBorder border border-panelBorder hover:border-red/40 hover:text-red rounded-lg font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer text-textDim"
                              >
                                FALSE POSITIVE
                              </button>
                            </div>
                          )}

                          {/* Assignment Selection */}
                          <div className="bg-[#050A16] border border-panelBorder rounded-lg p-2 flex flex-col gap-1.5">
                            <span className="text-[8px] text-textDim font-orbitron font-bold">ASSIGN TO ANALYST:</span>
                            <select
                              defaultValue=""
                              onChange={async (e) => {
                                if (e.target.value) {
                                  await assignAlert(selectedAlert.id, e.target.value);
                                  alert("Alert successfully assigned!");
                                  loadDashboardData();
                                  setSelectedAlert(null);
                                }
                              }}
                              className="bg-panel border border-panelBorder rounded px-2 py-1 text-[10px] text-white focus:outline-none focus:border-cyan"
                            >
                              <option value="" disabled>SELECT ANALYST</option>
                              {currentUser && <option value={currentUser.id}>{currentUser.username} (Self)</option>}
                              <option value="8cdf24fc-b8b8-4c3e-8c31-9f9363847edf">Security Analyst Alpha</option>
                              <option value="9a29e2f4-7e9b-449e-b81b-a2c3d4f5e6a7">SOC Agent Beta</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-textDim text-xs py-14">
                        Select an incident from the threat table to review telemetry details and assign mitigation tasks.
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* 3. DEVICES VIEW */}
            {activeView === "devices" && (
              <motion.div
                key="devices"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center border-b border-panelBorder pb-4">
                  <div>
                    <h2 className="font-orbitron font-black text-lg tracking-wider text-white">ENDPOINT INTELLIGENCE</h2>
                    <p className="text-xs text-textDim mt-0.5">Monitor and register cyber-sensors deployed on your nodes.</p>
                  </div>

                  <button
                    onClick={() => setShowAddDeviceModal(true)}
                    className="bg-gradient-to-r from-purple to-cyan text-white hover:shadow-cyan/30 shadow-lg px-4 py-2 rounded-lg font-orbitron text-[10px] font-bold tracking-wider transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <Plus className="h-4 w-4" />
                    REGISTER ENDPOINT
                  </button>
                </div>

                {/* Device Table Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                  <div className="lg:col-span-2 bg-panel border border-panelBorder rounded-xl overflow-hidden shadow-lg">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-panelBorder bg-[#050A16]/50">
                          <th className="p-4 font-semibold text-textDim tracking-wider">ENDPOINT</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">PLATFORM</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">IP ADDRESS</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">RISK THRESHOLD</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">STATUS</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider text-right">MITIGATION</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-panelBorder">
                        {devices.length > 0 ? (
                          devices.map((d) => {
                            const riskVal = Math.round(d.risk_score);
                            const isCritical = riskVal > 75;
                            const isSuspicious = riskVal > 35;
                            return (
                              <tr
                                key={d.id}
                                onClick={() => setSelectedDeviceDetails(selectedDeviceDetails?.id === d.id ? null : d)}
                                className={`hover:bg-panelBorder/20 transition-colors cursor-pointer ${
                                  selectedDeviceDetails?.id === d.id ? "bg-panelBorder/30" : ""
                                }`}
                              >
                                <td className="p-4">
                                  <div className="flex flex-col">
                                    <span className="font-bold text-white font-orbitron tracking-wider">{d.hostname}</span>
                                    <span className="text-[9px] text-textDim font-mono select-all">{d.id.substring(0, 14)}...</span>
                                  </div>
                                </td>
                                <td className="p-4">
                                  <span className="px-2 py-0.5 rounded bg-panelBorder text-white text-[9px]">
                                    {getOSIcon(d.operating_system)}
                                  </span>
                                </td>
                                <td className="p-4 text-textDim font-mono">{d.ip_address || "N/A"}</td>
                                <td className="p-4">
                                  <div className="flex items-center gap-2">
                                    <div className="w-16 bg-bg h-1.5 rounded-full overflow-hidden">
                                      <div
                                        className={`h-full rounded-full ${
                                          isCritical ? "bg-red" : isSuspicious ? "bg-amber" : "bg-cyan"
                                        }`}
                                        style={{ width: `${riskVal}%` }}
                                      />
                                    </div>
                                    <span className={`font-orbitron font-bold text-[10px] ${
                                      isCritical ? "text-red" : isSuspicious ? "text-amber" : "text-cyan"
                                    }`}>{riskVal}%</span>
                                  </div>
                                </td>
                                <td className="p-4">
                                  <span className={`h-2.5 w-2.5 rounded-full inline-block ${
                                    d.status === "online" ? "bg-safe" : d.status === "offline" ? "bg-textDim" : "bg-red animate-pulse"
                                  }`} />
                                  <span className="ml-2 font-orbitron text-[9px] font-bold text-white uppercase">{d.status}</span>
                                </td>
                                <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                                  <button
                                    onClick={() => handleDeleteDevice(d.id)}
                                    className="p-2 hover:bg-red/10 border border-transparent hover:border-red/40 text-textDim hover:text-red rounded-lg transition-all cursor-pointer"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </td>
                              </tr>
                            );
                          })
                        ) : (
                          <tr>
                            <td colSpan="6" className="p-8 text-center text-textDim text-sm">
                              No endpoints registered on the network.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Device Metadata Drawer */}
                  <div className="bg-panel border border-panelBorder rounded-xl p-5 shadow-lg min-h-[300px]">
                    <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-4 block">
                      ENDPOINT TELEMETRY PROFILE
                    </span>

                    {selectedDeviceDetails ? (
                      <div className="space-y-4">
                        <div>
                          <h3 className="font-bold text-white font-orbitron text-sm tracking-wider flex items-center gap-1.5">
                            <Laptop className="h-4 w-4 text-cyan" /> {selectedDeviceDetails.hostname}
                          </h3>
                          <span className="text-[10px] text-textDim block mt-1 font-mono">Agent ID: {selectedDeviceDetails.id}</span>
                        </div>

                        <div className="space-y-2.5 border-t border-panelBorder/50 pt-3 text-xs text-textDim">
                          <div className="flex justify-between">
                            <span>OS Platform:</span>
                            <span className="text-white">{selectedDeviceDetails.operating_system}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>OS Release:</span>
                            <span className="text-white">{selectedDeviceDetails.os_version || "Unknown"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Architecture:</span>
                            <span className="text-white">{selectedDeviceDetails.architecture || "x86_64"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>IP Address:</span>
                            <span className="text-cyan font-mono">{selectedDeviceDetails.ip_address || "N/A"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>MAC Address:</span>
                            <span className="text-white font-mono">{selectedDeviceDetails.mac_address || "N/A"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Agent Core:</span>
                            <span className="text-amber">v{selectedDeviceDetails.agent_version}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Last Connection:</span>
                            <span className="text-white">
                              {selectedDeviceDetails.last_seen_at ? new Date(selectedDeviceDetails.last_seen_at).toLocaleString() : "Never"}
                            </span>
                          </div>
                        </div>

                        <div className="border-t border-panelBorder/50 pt-4 bg-[#050A16]/50 p-3 rounded-lg border border-dashed border-panelBorder text-[10px] text-textDim leading-relaxed">
                          <span className="font-orbitron font-bold text-purple tracking-wider block mb-1">SENSOR DIRECTIVE</span>
                          This sensor generates real-time telemetry flows mapped to a 23-dimensional feature schema for inference by the AI threat engine.
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-textDim text-xs py-14">
                        Select a cyber-endpoint node from the registered inventory to inspect software stack releases, architecture, and network parameters.
                      </div>
                    )}
                  </div>
                </div>

                {/* Device Registration Modal */}
                {showAddDeviceModal && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 backdrop-blur-sm">
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-panel border border-panelBorder rounded-2xl w-full max-w-[460px] p-6 shadow-2xl"
                    >
                      <h3 className="font-orbitron font-black text-white text-base tracking-wider mb-2">REGISTER CYBER SENSOR</h3>
                      <p className="text-[11px] text-textDim mb-4">Enroll a new network daemon to stream telemetry packets to the AI analyzer.</p>

                      {deviceError && (
                        <div className="p-3 bg-red/10 border border-red text-red rounded-lg text-xs font-semibold mb-4">
                          {deviceError}
                        </div>
                      )}

                      <form onSubmit={handleAddDevice} className="space-y-4 text-xs">
                        <div>
                          <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1 tracking-wider">HOSTNAME</label>
                          <input
                            type="text"
                            required
                            placeholder="DESKTOP-SOC-SEC"
                            value={newDevice.hostname}
                            onChange={(e) => setNewDevice({ ...newDevice, hostname: e.target.value })}
                            className="w-full bg-bg border border-panelBorder rounded-lg px-3 py-2 text-white outline-none focus:border-cyan transition-colors"
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1 tracking-wider">OPERATING SYSTEM</label>
                            <select
                              value={newDevice.operating_system}
                              onChange={(e) => setNewDevice({ ...newDevice, operating_system: e.target.value })}
                              className="w-full bg-bg border border-panelBorder rounded-lg px-3 py-2 text-white outline-none focus:border-cyan"
                            >
                              <option value="windows">Windows</option>
                              <option value="linux">Linux</option>
                              <option value="macos">macOS</option>
                              <option value="android">Android</option>
                              <option value="iot">IoT / Embedded</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1 tracking-wider">IP ADDRESS</label>
                            <input
                              type="text"
                              required
                              placeholder="192.168.1.105"
                              value={newDevice.ip_address}
                              onChange={(e) => setNewDevice({ ...newDevice, ip_address: e.target.value })}
                              className="w-full bg-bg border border-panelBorder rounded-lg px-3 py-2 text-white outline-none focus:border-cyan"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1 tracking-wider">MAC ADDRESS</label>
                            <input
                              type="text"
                              placeholder="00:1A:2B:3C:4D:5E"
                              value={newDevice.mac_address}
                              onChange={(e) => setNewDevice({ ...newDevice, mac_address: e.target.value })}
                              className="w-full bg-[#060B18] border border-panelBorder rounded-lg px-3 py-2 text-white outline-none focus:border-cyan"
                            />
                          </div>

                          <div>
                            <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1 tracking-wider">OS RELEASE VERSION</label>
                            <input
                              type="text"
                              placeholder="Windows 11 Build 22631"
                              value={newDevice.os_version}
                              onChange={(e) => setNewDevice({ ...newDevice, os_version: e.target.value })}
                              className="w-full bg-[#060B18] border border-panelBorder rounded-lg px-3 py-2 text-white outline-none focus:border-cyan"
                            />
                          </div>
                        </div>

                        <div className="flex gap-3 justify-end pt-4 border-t border-panelBorder/50">
                          <button
                            type="button"
                            onClick={() => setShowAddDeviceModal(false)}
                            className="px-4 py-2 border border-panelBorder text-textDim hover:text-white rounded-lg font-orbitron text-[9px] font-bold tracking-wider cursor-pointer"
                          >
                            CANCEL
                          </button>
                          <button
                            type="submit"
                            className="px-4 py-2 bg-gradient-to-r from-purple to-cyan text-white hover:brightness-110 rounded-lg font-orbitron text-[9px] font-bold tracking-wider cursor-pointer"
                          >
                            REGISTER SENSOR
                          </button>
                        </div>
                      </form>
                    </motion.div>
                  </div>
                )}
              </motion.div>
            )}

            {/* 4. REPORTS VIEW */}
            {activeView === "reports" && (
              <motion.div
                key="reports"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center border-b border-panelBorder pb-4">
                  <div>
                    <h2 className="font-orbitron font-black text-lg tracking-wider text-white">THREAT REPORT COMPILER</h2>
                    <p className="text-xs text-textDim mt-0.5">Generate daily, weekly, and monthly PDF summaries or raw CSV audit datasets.</p>
                  </div>
                </div>

                {/* Form & Table */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                  <div className="bg-panel border border-panelBorder rounded-xl p-5 shadow-lg space-y-4">
                    <span className="font-orbitron text-[10px] text-textDim tracking-wider font-semibold border-b border-panelBorder/50 pb-2 mb-2 block">
                      TRIGGER NEW REPORT
                    </span>

                    <div className="space-y-4 text-xs">
                      <div>
                        <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1.5 tracking-wider">REPORT INTERVAL</label>
                        <div className="flex gap-2">
                          {["daily", "weekly", "monthly"].map((t) => (
                            <button
                              key={t}
                              type="button"
                              onClick={() => setReportType(t)}
                              className={`flex-1 py-2 border rounded-lg font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer ${
                                reportType === t
                                  ? "bg-purple/20 border-purple text-purple"
                                  : "border-panelBorder hover:border-textDim text-textDim"
                              }`}
                            >
                              {t.toUpperCase()}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-[9px] font-orbitron text-textDim font-bold mb-1.5 tracking-wider">EXPORT FORMAT</label>
                        <div className="flex gap-2">
                          {[
                            { id: "pdf", label: "PDF DOCUMENT", icon: FileSpreadsheet },
                            { id: "csv", label: "CSV DATASET", icon: FileText }
                          ].map((f) => (
                            <button
                              key={f.id}
                              type="button"
                              onClick={() => setReportFormat(f.id)}
                              className={`flex-1 py-2.5 border rounded-lg font-orbitron text-[9px] font-bold tracking-wider transition-colors flex items-center justify-center gap-1.5 cursor-pointer ${
                                reportFormat === f.id
                                  ? "bg-cyan/20 border-cyan text-cyan"
                                  : "border-panelBorder hover:border-textDim text-textDim"
                              }`}
                            >
                              <f.icon className="h-3.5 w-3.5" />
                              {f.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      <button
                        onClick={handleGenerateReport}
                        disabled={reportsLoading}
                        className="w-full py-3 bg-gradient-to-r from-purple to-cyan text-white hover:brightness-110 rounded-lg font-orbitron text-[10px] font-bold tracking-widest transition-all cursor-pointer shadow-lg disabled:brightness-75"
                      >
                        {reportsLoading ? "COMPILING REPORT..." : "QUEUE BACKGROUND TASK"}
                      </button>
                    </div>
                  </div>

                  {/* Past reports */}
                  <div className="lg:col-span-2 bg-panel border border-panelBorder rounded-xl overflow-hidden shadow-lg">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-panelBorder bg-[#050A16]/50">
                          <th className="p-4 font-semibold text-textDim tracking-wider">FILENAME</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">PERIOD</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">FORMAT</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider">STATUS</th>
                          <th className="p-4 font-semibold text-textDim tracking-wider text-right">ACTION</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-panelBorder">
                        {reports.length > 0 ? (
                          reports.map((r) => (
                            <tr key={r.id} className="hover:bg-panelBorder/10 transition-colors">
                              <td className="p-4">
                                <div className="flex flex-col">
                                  <span className="font-semibold text-white truncate max-w-[200px]">{r.filename}</span>
                                  <span className="text-[9px] text-textDim font-orbitron font-medium uppercase tracking-wider">{r.report_type} REPORT</span>
                                </div>
                              </td>
                              <td className="p-4 text-textDim text-[11px]">
                                {new Date(r.period_start).toLocaleDateString()} to {new Date(r.period_end).toLocaleDateString()}
                              </td>
                              <td className="p-4">
                                <span className={`px-2 py-0.5 rounded border text-[9px] font-bold font-orbitron ${
                                  r.format === "pdf" ? "bg-red/10 border-red text-red" : "bg-cyan/10 border-cyan text-cyan"
                                }`}>
                                  {r.format.toUpperCase()}
                                </span>
                              </td>
                              <td className="p-4">
                                <span className={`font-orbitron font-bold text-[9px] ${
                                  r.status === "completed" ? "text-safe" : r.status === "failed" ? "text-red" : "text-amber animate-pulse"
                                }`}>
                                  {r.status.toUpperCase()}
                                </span>
                              </td>
                              <td className="p-4 text-right">
                                {r.status === "completed" ? (
                                  <button
                                    onClick={() => handleDownloadReport(r.id, r.filename)}
                                    className="px-3 py-1.5 bg-cyan/15 border border-cyan/40 hover:bg-cyan/25 hover:border-cyan text-cyan rounded font-orbitron text-[9px] font-bold tracking-wider cursor-pointer"
                                  >
                                    DOWNLOAD
                                  </button>
                                ) : r.status === "failed" ? (
                                  <span className="text-red/70 text-[10px] italic">Failed compilation</span>
                                ) : (
                                  <span className="text-amber/70 text-[10px] animate-pulse">Compiling...</span>
                                )}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="5" className="p-8 text-center text-textDim text-sm">
                              No reports generated. Select an interval and trigger compilation.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 5. LOGS VIEW */}
            {activeView === "logs" && (
              <motion.div
                key="logs"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center border-b border-panelBorder pb-4">
                  <div>
                    <h2 className="font-orbitron font-black text-lg tracking-wider text-white">AUDIT TRAIL & LOGS</h2>
                    <p className="text-xs text-textDim mt-0.5">Investigate detailed API requests and system events logs.</p>
                  </div>

                  {/* Sub navigation tabs */}
                  <div className="flex gap-2 bg-[#050A16] border border-panelBorder p-1 rounded-lg">
                    <button
                      onClick={() => { setLogsType("system"); setLogsPage(1); }}
                      className={`px-4 py-1.5 rounded-md font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer ${
                        logsType === "system" ? "bg-panel border border-panelBorder text-white" : "text-textDim hover:text-white"
                      }`}
                    >
                      SYSTEM LOGS
                    </button>
                    <button
                      onClick={() => { setLogsType("audit"); setLogsPage(1); }}
                      className={`px-4 py-1.5 rounded-md font-orbitron text-[9px] font-bold tracking-wider transition-colors cursor-pointer ${
                        logsType === "audit" ? "bg-panel border border-panelBorder text-white" : "text-textDim hover:text-white"
                      }`}
                    >
                      AUDIT LOGS
                    </button>
                  </div>
                </div>

                {/* Filters Row */}
                <div className="bg-panel border border-panelBorder rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-lg">
                  <div className="flex items-center gap-3">
                    {logsType === "system" ? (
                      <>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-textDim font-bold font-orbitron">LEVEL:</span>
                          <select
                            value={logsLevel}
                            onChange={(e) => { setLogsLevel(e.target.value); setLogsPage(1); }}
                            className="bg-bg border border-panelBorder rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan"
                          >
                            <option value="">ALL LEVELS</option>
                            <option value="debug">DEBUG</option>
                            <option value="info">INFO</option>
                            <option value="warning">WARNING</option>
                            <option value="error">ERROR</option>
                            <option value="critical">CRITICAL</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-textDim font-bold font-orbitron">MODULE:</span>
                          <input
                            type="text"
                            placeholder="e.g. kovirx.ml"
                            value={logsModule}
                            onChange={(e) => { setLogsModule(e.target.value); setLogsPage(1); }}
                            className="bg-bg border border-panelBorder rounded-lg px-3 py-1.5 text-xs text-white placeholder-textDim focus:outline-none focus:border-cyan"
                          />
                        </div>
                      </>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-textDim font-bold font-orbitron">ACTION:</span>
                        <input
                          type="text"
                          placeholder="e.g. user_login"
                          value={logsAction}
                          onChange={(e) => { setLogsAction(e.target.value); setLogsPage(1); }}
                          className="bg-bg border border-panelBorder rounded-lg px-3 py-1.5 text-xs text-white placeholder-textDim focus:outline-none focus:border-cyan"
                        />
                      </div>
                    )}
                  </div>

                  <span className="text-xs text-textDim font-orbitron">
                    TOTAL MATCHES: <span className="text-cyan font-bold">{logsTotal}</span> LOGS
                  </span>
                </div>

                {/* Logs Table */}
                <div className="bg-panel border border-panelBorder rounded-xl overflow-hidden shadow-lg">
                  <div className="overflow-x-auto">
                    {logsType === "system" ? (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-panelBorder bg-[#050A16]/50">
                            <th className="p-4 font-semibold text-textDim tracking-wider">LEVEL</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">MODULE</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">MESSAGE</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">OCCURRED</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-panelBorder font-mono">
                          {logsList.length > 0 ? (
                            logsList.map((l) => {
                              const levelClass = l.level === "error" || l.level === "critical"
                                ? "text-red" : l.level === "warning" ? "text-amber" : "text-cyan";
                              return (
                                <tr key={l.id} className="hover:bg-panelBorder/10 transition-colors">
                                  <td className="p-4 font-orbitron font-bold">
                                    <span className={levelClass}>{l.level.toUpperCase()}</span>
                                  </td>
                                  <td className="p-4 text-purple font-semibold">{l.module}</td>
                                  <td className="p-4 text-white text-[11px] max-w-lg truncate" title={l.message}>{l.message}</td>
                                  <td className="p-4 text-textDim">{new Date(l.created_at).toLocaleString()}</td>
                                </tr>
                              );
                            })
                          ) : (
                            <tr>
                              <td colSpan="4" className="p-8 text-center text-textDim text-sm font-sans">
                                No system log records found.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    ) : (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-panelBorder bg-[#050A16]/50">
                            <th className="p-4 font-semibold text-textDim tracking-wider">ACTION</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">RESOURCE</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">ANALYST ID</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">IP ADDRESS</th>
                            <th className="p-4 font-semibold text-textDim tracking-wider">OCCURRED</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-panelBorder font-mono">
                          {logsList.length > 0 ? (
                            logsList.map((l) => (
                              <tr key={l.id} className="hover:bg-panelBorder/10 transition-colors">
                                <td className="p-4 text-safe font-bold">{l.action}</td>
                                <td className="p-4 text-white font-semibold">{l.resource} ({l.resource_id || "global"})</td>
                                <td className="p-4 text-textDim truncate max-w-[120px] select-all" title={l.user_id}>{l.user_id || "system"}</td>
                                <td className="p-4 text-cyan font-semibold">{l.ip_address || "127.0.0.1"}</td>
                                <td className="p-4 text-textDim">{new Date(l.created_at).toLocaleString()}</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan="5" className="p-8 text-center text-textDim text-sm font-sans">
                                No audit log records found.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* Pagination Controls */}
                  {logsTotal > 20 && (
                    <div className="p-4 border-t border-panelBorder bg-[#050A16]/30 flex justify-between items-center text-xs">
                      <span className="text-textDim">
                        Showing page <span className="text-white font-bold">{logsPage}</span> of <span className="text-white">{Math.ceil(logsTotal / 20)}</span>
                      </span>

                      <div className="flex gap-2">
                        <button
                          onClick={() => setLogsPage(prev => Math.max(prev - 1, 1))}
                          disabled={logsPage === 1}
                          className="px-3 py-1.5 bg-panel border border-panelBorder hover:border-cyan text-white rounded transition-colors disabled:opacity-30 disabled:hover:border-panelBorder cursor-pointer"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setLogsPage(prev => Math.min(prev + 1, Math.ceil(logsTotal / 20)))}
                          disabled={logsPage >= Math.ceil(logsTotal / 20)}
                          className="px-3 py-1.5 bg-panel border border-panelBorder hover:border-cyan text-white rounded transition-colors disabled:opacity-30 disabled:hover:border-panelBorder cursor-pointer"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
