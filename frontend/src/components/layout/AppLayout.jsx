import { useState, useEffect } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import logoImg from "../../assets/logo.jpg";
import {
  getDashboardSummary,
  getAlerts,
  getDevices,
  logout,
  getWebSocketUrl,
  getCurrentUser,
  getRefreshToken,
  setTokens,
} from "../../services/api";
import {
  LayoutDashboard,
  ShieldAlert,
  Laptop,
  FileText,
  Terminal,
  LogOut,
  Wifi,
  WifiOff,
  CheckCircle,
  AlertTriangle,
  User,
  ShieldCheck,
  Settings,
  Users,
} from "lucide-react";

export default function AppLayout() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [threatLevel, setThreatLevel] = useState("safe");
  const [summary, setSummary] = useState({
    protected_devices: 0,
    active_threats: 0,
    today_alerts: 0,
    detection_accuracy: 100.0,
    traffic_stats: { total_flows: 0, suspicious_flows: 0, blocked_flows: 0 },
    top_threat_types: [],
    severity_breakdown: {},
  });
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);

  const loadDashboardData = async () => {
    try {
      const sum = await getDashboardSummary();
      setSummary(sum);
      setThreatLevel(sum.active_threats > 0 ? "critical" : "safe");

      const al = await getAlerts();
      setAlerts(al || []);

      const dev = await getDevices();
      setDevices(dev.devices || []);
    } catch (err) {
      console.error("Dashboard reload failed:", err);
    }
  };

  useEffect(() => {
    getCurrentUser()
      .then((u) => setCurrentUser(u))
      .catch((err) => console.error(err));

    loadDashboardData();

    let ws;
    const connectWS = async () => {
      try {
        const wsUrl = getWebSocketUrl();
        if (!wsUrl) return;
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setWsConnected(true);
          console.log("WebSocket connected to KOVIRX Nexus.");
        };

        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data);
          if (msg.channel === "alerts" || msg.channel === "traffic") {
            loadDashboardData();
          }
        };

        ws.onclose = async () => {
          setWsConnected(false);
          // Silent Token Refresh on close before reconnecting
          const refreshToken = getRefreshToken();
          if (refreshToken) {
            try {
              const cleanUrl = (import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL || "").replace(/\/$/, '');
              const base = cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
              const refreshRes = await fetch(`${base}/auth/refresh`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken }),
              });
              if (refreshRes.ok) {
                const refreshData = await refreshRes.json();
                setTokens(refreshData.access_token, refreshData.refresh_token);
              }
            } catch (err) {
              console.error("WS token refresh failed:", err);
            }
          }
          setTimeout(connectWS, 5000);
        };
      } catch (err) {
        setWsConnected(false);
      }
    };

    connectWS();
    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isSuperAdmin = currentUser?.role === "super_admin";

  return (
    <div className="w-screen h-screen bg-[#060B18] text-[#C5D0E6] font-sans flex overflow-hidden">
      {/* ── SIDEBAR ────────────────────────────────────────────── */}
      <aside className="w-64 bg-[#0C1426] border-r border-[#1E293B] flex flex-col justify-between flex-shrink-0 z-20">
        <div>
          {/* Brand header */}
          <div className="flex items-center gap-3 p-5 border-b border-[#1E293B] bg-[#050A16]">
            <div className="relative">
              <div className="absolute -inset-3 rounded-full bg-cyan-500/10 blur-sm pointer-events-none" />
              <img
                src={logoImg}
                alt="KovirX Logo"
                className="h-10 w-10 object-contain filter drop-shadow-[0_0_8px_rgba(0,212,255,0.5)]"
              />
            </div>
            <div className="flex flex-col">
              <span className="font-orbitron font-black text-sm tracking-[2px] bg-gradient-to-r from-white to-[#00D4FF] bg-clip-text text-transparent">
                KOVIRX
              </span>
              <span className="font-orbitron text-[7px] tracking-[1.5px] text-[#5A7090]">
                BOTNET THREAT NEXUS
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-4 max-h-[calc(100vh-230px)] overflow-y-auto">
            {/* Operations Section */}
            <div className="space-y-1">
              <span className="font-orbitron text-[8px] font-black tracking-widest text-[#5A7090] px-4 block uppercase mb-2">
                OPERATIONS
              </span>
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <LayoutDashboard className="h-4.5 w-4.5 text-[#00D4FF]" />
                DASHBOARD
              </NavLink>

              <NavLink
                to="/alerts"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <ShieldAlert className="h-4.5 w-4.5 text-[#FF355E]" />
                INCIDENTS
                {alerts.filter((a) => a.status === "new").length > 0 && (
                  <span className="ml-auto bg-[#FF355E] text-white text-[9px] font-bold px-2 py-0.5 rounded-full font-orbitron">
                    {alerts.filter((a) => a.status === "new").length}
                  </span>
                )}
              </NavLink>

              <NavLink
                to="/devices"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <Laptop className="h-4.5 w-4.5 text-[#9B59FF]" />
                ENDPOINTS
              </NavLink>

              <NavLink
                to="/reports"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <FileText className="h-4.5 w-4.5 text-[#FFB400]" />
                REPORTS
              </NavLink>

              <NavLink
                to="/logs"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <Terminal className="h-4.5 w-4.5 text-[#00E676]" />
                AUDIT LOGS
              </NavLink>
            </div>

            {/* Security Section */}
            <div className="space-y-1 pt-2">
              <span className="font-orbitron text-[8px] font-black tracking-widest text-[#5A7090] px-4 block uppercase mb-2">
                SECURITY & IDENTITY
              </span>

              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <User className="h-4.5 w-4.5 text-[#9B59FF]" />
                MY PROFILE
              </NavLink>

              <NavLink
                to="/sessions"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <ShieldCheck className="h-4.5 w-4.5 text-[#00D4FF]" />
                ACTIVE SESSIONS
              </NavLink>

              <NavLink
                to="/security"
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                      : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                  }`
                }
              >
                <Settings className="h-4.5 w-4.5 text-[#FFB400]" />
                ACCESS SETTINGS
              </NavLink>

              {isSuperAdmin && (
                <NavLink
                  to="/users"
                  className={({ isActive }) =>
                    `w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-orbitron font-semibold tracking-wider transition-all duration-200 ${
                      isActive
                        ? "bg-gradient-to-r from-[#9B59FF]/20 to-[#00D4FF]/20 border-l-2 border-[#00D4FF] text-white"
                        : "text-[#5A7090] hover:text-white hover:bg-[#1E293B]/40 border-l-2 border-transparent"
                    }`
                  }
                >
                  <Users className="h-4.5 w-4.5 text-[#00E676]" />
                  USER MANAGEMENT
                </NavLink>
              )}
            </div>
          </nav>
        </div>

        {/* Analyst Info & Logout */}
        <div className="p-4 border-t border-[#1E293B] bg-[#050A16]/50">
          {currentUser ? (
            <div className="mb-4 flex items-center gap-3 p-2 rounded-lg bg-[#1E293B]/30">
              <div className="h-8 w-8 rounded-full bg-[#00D4FF]/15 flex items-center justify-center text-[#00D4FF] font-bold border border-[#00D4FF]/40">
                {currentUser.username.substring(0, 2).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[11px] font-bold text-white truncate">{currentUser.username}</span>
                <span className="text-[9px] text-[#5A7090] uppercase tracking-wider font-semibold font-orbitron text-[#9B59FF]">
                  {currentUser.role.replace("super_", "").replace("_", " ")}
                </span>
              </div>
            </div>
          ) : (
            <div className="mb-4 h-12 animate-pulse bg-[#1E293B]/30 rounded-lg" />
          )}

          <button
            onClick={handleLogout}
            className="w-full py-2.5 rounded-lg border border-[#FF355E]/40 bg-[#FF355E]/5 hover:bg-[#FF355E]/20 text-[#FF355E] font-orbitron text-[9px] font-bold tracking-[2px] transition-all duration-200 flex items-center justify-center gap-2"
          >
            <LogOut className="h-3 w-3" />
            SECURE EXIT
          </button>
        </div>
      </aside>

      {/* ── MAIN WORKSPACE ───────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#060B18] relative">
        {/* Header Ribbon */}
        <header className="h-16 border-b border-[#1E293B] bg-[#0C1426]/75 backdrop-blur-md flex items-center justify-between px-6 flex-shrink-0 z-10">
          <div className="flex items-center gap-6">
            {/* Status Indicator */}
            <div className="flex items-center gap-2 bg-[#050A16] px-3.5 py-1.5 rounded-lg border border-[#1E293B]">
              <span className={`h-2 w-2 rounded-full shadow-[0_0_8px] ${
                wsConnected ? "bg-[#00E676] shadow-[#00E676]" : "bg-[#FF355E] shadow-[#FF355E] animate-pulse"
              }`} />
              <span className={`font-orbitron text-[9px] font-bold tracking-wider ${
                wsConnected ? "text-[#00E676]" : "text-[#FF355E]"
              }`}>
                {wsConnected ? "NEXUS SECURE ONLINE" : "TELEMETRY DISCONNECTED"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6 divide-x divide-[#1E293B]">
            {/* System Level Gauge */}
            <div className="flex items-center gap-3">
              <span className={`h-2.5 w-2.5 rounded-full shadow-[0_0_8px] ${
                threatLevel === "critical" || threatLevel === "high"
                  ? "bg-[#FF355E] shadow-[#FF355E] animate-pulse"
                  : threatLevel === "warning"
                  ? "bg-[#FFB400] shadow-[#FFB400]"
                  : "bg-[#00E676] shadow-[#00E676]"
              }`} />
              <div className="flex flex-col">
                <span className="font-orbitron text-[8px] text-[#5A7090] tracking-wider">DEFENSE SHIELD</span>
                <span className={`text-[10px] font-orbitron font-black tracking-widest uppercase ${
                  threatLevel === "critical" || threatLevel === "high"
                    ? "text-[#FF355E]"
                    : threatLevel === "warning"
                    ? "text-[#FFB400]"
                    : "text-[#00E676]"
                }`}>
                  {threatLevel === "critical" || threatLevel === "high" ? "CRITICAL ALERT" : threatLevel === "warning" ? "WARNING" : "SECURED"}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Content Outlet */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <Outlet context={{
            summary,
            alerts,
            devices,
            threatLevel,
            wsConnected,
            currentUser,
            loadDashboardData,
          }} />
        </div>
      </main>
    </div>
  );
}
