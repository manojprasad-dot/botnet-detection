import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Activity,
  Play,
  CheckCircle,
  AlertTriangle,
  Radio,
  Shield,
  Search,
} from "lucide-react";
import NetworkMesh, { COLORS } from "../components/widgets/NetworkMesh";
import MitreMap from "../components/widgets/MitreMap";
import { ingestTelemetry } from "../services/api";

const REPLAY_STEPS = [
  { ts: "08:15:03", label: "Agent Connect", icon: "◉" },
  { ts: "08:15:47", label: "Entropy Query", icon: "⚠" },
  { ts: "08:16:22", label: "Botnet Beacon", icon: "⬆" },
  { ts: "08:17:01", label: "C2 Handshake", icon: "⚡" },
  { ts: "08:18:00", label: "AI Containment", icon: "✕" },
];

export default function Overview() {
  const {
    summary,
    alerts,
    devices,
    wsConnected,
    loadDashboardData,
  } = useOutletContext();

  const [threatLevel, setThreatLevel] = useState("safe");
  const [replaying, setReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState(-1);

  // Sync internal threat level with alerts count
  useEffect(() => {
    setThreatLevel(summary.active_threats > 0 ? "critical" : "safe");
  }, [summary.active_threats]);

  // Construct flow data history
  const networkFlowData = Array.from({ length: 12 }).map((_, idx) => {
    const total = summary.traffic_stats?.total_flows || 120;
    const baseVal = Math.round(total / 12);
    return {
      time: `${(8 + idx) % 12 || 12} ${idx >= 4 ? "PM" : "AM"}`,
      flows: Math.max(10, baseVal + Math.round((Math.random() - 0.5) * (baseVal * 0.4))),
    };
  });

  const handleRunMalwareAttack = async () => {
    if (replaying) return;
    setReplaying(true);
    setReplayStep(0);
    setThreatLevel("warning");

    const mockEvents = [
      {
        event_type: "socket_snapshot",
        source: "agent_ml",
        payload: { unique_remote_ips: 15, public_remote_ips: 8, listening_ports: 5, top_remote_ports: [{ port: 80, count: 12 }] }
      },
      {
        event_type: "dns_query",
        source: "agent_ml",
        payload: { query: "subdomain.malicious-botnet-c2-server-beacon.com", entropy: 4.8 }
      },
      {
        event_type: "network_summary",
        source: "agent_ml",
        payload: { flow_duration: 12.5, connection_count: 85, bytes_sent: 5200, bytes_recv: 1200, packets_sent: 45, packets_recv: 35, tcp_flag_score: 0.8, beacon_interval_score: 0.9, outbound_frequency: 3.5, failed_connection_ratio: 0.7 }
      }
    ];

    try {
      // Step 1
      await new Promise(r => setTimeout(r, 1500));
      setReplayStep(1);
      // Step 2
      await new Promise(r => setTimeout(r, 2000));
      setReplayStep(2);
      // Step 3
      await new Promise(r => setTimeout(r, 2000));
      setReplayStep(3);
      setThreatLevel("critical");

      const devId = devices[0]?.id || "cf5349e5-066e-4d32-b4aa-c841738846e0";
      await ingestTelemetry({
        device_id: devId,
        events: [
          {
            flow: {
              source_ip: "192.168.1.105",
              dest_ip: "185.220.101.5",
              protocol: "TCP",
              packet_count: 80,
              byte_count: 6400,
              flow_duration: 12.5,
              dns_query: "subdomain.malicious-botnet-c2-server-beacon.com",
              dns_entropy: 4.8,
              beacon_interval: 0.9,
              failed_connections: 5,
              start_time: new Date(Date.now() - 15000).toISOString(),
              end_time: new Date().toISOString(),
            },
            prediction: {
              model_name: "local_hybrid_detector",
              threat_type: "botnet",
              xgb_score: 0.95,
              features_used: {
                dns_entropy: 4.8,
                flow_duration: 12.5,
                connection_count: 85,
                beacon_interval_score: 0.9,
              }
            },
            risk: {
              risk_score: 92,
              severity: "critical",
              recommendation: "Quarantine host: block all outbound flows to 185.220.101.5 immediately."
            }
          }
        ]
      });

      // Step 4
      await new Promise(r => setTimeout(r, 2500));
      setReplayStep(4);
      loadDashboardData();
    } catch (err) {
      console.error("Malware simulation failed:", err);
    } finally {
      await new Promise(r => setTimeout(r, 2000));
      setReplaying(false);
      setReplayStep(-1);
    }
  };

  const severityPieData = Object.entries(summary.severity_breakdown || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    value: val,
  }));

  const pieColors = [COLORS.red, COLORS.amber, COLORS.purple, COLORS.cyan];

  return (
    <div className="space-y-6">
      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "MONITORED ENDPOINTS", value: summary.protected_devices, color: "border-purple" },
          { label: "ACTIVE INCIDENTS", value: summary.active_threats, color: "border-red" },
          { label: "ALERTS TODAY", value: summary.today_alerts, color: "border-amber" },
          { label: "AI ENGINE ACCURACY", value: `${parseFloat(summary.detection_accuracy).toFixed(1)}%`, color: "border-cyan" },
          { label: "SUSPICIOUS FLOWS", value: summary.traffic_stats?.suspicious_flows || 0, color: "border-safe" }
        ].map((c, i) => (
          <div key={i} className={`bg-[#0C1426] border border-[#1E293B] border-l-4 ${c.color} rounded-xl p-5 shadow-lg`}>
            <span className="font-orbitron text-[9px] text-[#5A7090] tracking-wider font-bold block">
              {c.label}
            </span>
            <span className="font-orbitron text-2xl font-black text-white block mt-2">
              {c.value}
            </span>
          </div>
        ))}
      </div>

      {/* Topology NEXUS & ML AI CORE */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Stats: Incident Timeline & Dist */}
        <div className="space-y-6 lg:col-span-1">
          {/* Incident Timeline */}
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 flex flex-col h-[320px]">
            <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-4 block">
              INCIDENT TIMELINE
            </span>
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {alerts.length > 0 ? (
                alerts.slice(0, 10).map((a, idx) => (
                  <div key={idx} className="flex gap-3 text-xs">
                    <div className="flex flex-col items-center">
                      <span className={`h-2 w-2 rounded-full ${
                        a.severity === "critical" ? "bg-[#FF355E]" : a.severity === "high" ? "bg-[#FFB400]" : "bg-[#00D4FF]"
                      }`} />
                      <div className="w-[1px] flex-1 bg-[#1E293B]/40 mt-1" />
                    </div>
                    <div className="flex-1">
                      <span className="font-orbitron text-[8px] text-[#5A7090] block">
                        {new Date(a.created_at).toLocaleTimeString("en-US", { hour12: false })}
                      </span>
                      <span className="font-bold text-white block mt-0.5 truncate">{a.title}</span>
                      <p className="text-[10px] text-[#5A7090] line-clamp-1">{a.description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-[#5A7090] text-xs py-10">No incident alerts recorded.</div>
              )}
            </div>
          </div>

          {/* AI Classification Distribution */}
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5">
            <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-4 block">
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
                      <div className="h-1.5 bg-[#1E293B]/60 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${percentage}%`, backgroundColor: stroke }} />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center text-[#5A7090] text-xs py-4">No active threat profiles.</div>
              )}
            </div>
          </div>
        </div>

        {/* Center Topology Mesh */}
        <div className="lg:col-span-2 bg-[#0C1426] border border-[#1E293B] rounded-xl h-[480px] overflow-hidden relative flex flex-col shadow-inner">
          <div className="absolute top-5 left-5 z-10">
            <h3 className="font-orbitron font-bold text-xs text-[#00D4FF] tracking-wider">NETWORK TOPOLOGY NEXUS</h3>
            <p className="text-[9px] text-[#5A7090] tracking-wider mt-0.5">CYBER-FLOW HEURISTIC GRAPH</p>
          </div>

          <div className="absolute top-5 right-5 z-10 flex gap-4 text-[9px] font-orbitron font-medium text-[#5A7090]">
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#00D4FF]" /> SCANNING</span>
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#00E676]" /> SECURED</span>
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-[#FF355E] animate-pulse" /> ANOMALY</span>
          </div>

          <div className="flex-1 w-full relative">
            <NetworkMesh threatLevel={threatLevel} devices={devices} />
          </div>

          <div className="absolute bottom-5 left-1/2 transform -translate-x-1/2 z-10 text-center pointer-events-none">
            <span className="font-orbitron text-[8px] text-[#9B59FF] tracking-[2px] font-semibold bg-[#0C1426]/85 px-4 py-1.5 border border-[#1E293B] rounded-full shadow-lg">
              VOTING CLASSIFIER & ENSEMBLE ACTIVE
            </span>
          </div>
        </div>

        {/* Right Column: AI Brain & Simulated Replay */}
        <div className="lg:col-span-1 space-y-6">
          {/* Pulsing Core Widget */}
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 flex flex-col items-center justify-center text-center h-[260px] relative overflow-hidden">
            <span className="absolute top-4 left-4 font-orbitron text-[8px] text-[#5A7090] tracking-widest">
              AI DETECTOR CORE
            </span>
            <div className="relative my-4 flex items-center justify-center">
              <div className="absolute h-28 w-28 rounded-full border border-[#9B59FF]/30 animate-ping pointer-events-none" />
              <div className="absolute h-24 w-24 rounded-full border border-[#00D4FF]/20 pointer-events-none" />
              <div className="h-20 w-20 rounded-full bg-[#050A16] border-2 border-[#9B59FF] flex flex-col items-center justify-center shadow-[0_0_20px_rgba(155,89,255,0.2)] animate-pulse">
                <span className="font-orbitron text-lg font-black text-[#9B59FF]">{parseFloat(summary.detection_accuracy).toFixed(0)}%</span>
                <span className="text-[7px] text-[#5A7090] font-bold font-orbitron uppercase tracking-widest mt-0.5">STABILITY</span>
              </div>
            </div>
            <div className="text-[10px] font-orbitron tracking-widest uppercase mt-2">
              {threatLevel === "safe" ? (
                <span className="text-[#00E676] flex items-center gap-1.5"><CheckCircle className="h-3 w-3" /> SHIELD SECURE</span>
              ) : (
                <span className="text-[#FF355E] flex items-center gap-1.5 animate-pulse"><AlertTriangle className="h-3 w-3" /> COMPROMISED</span>
              )}
            </div>
          </div>

          {/* MITRE Threat Replay control */}
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 flex flex-col justify-between h-[200px]">
            <div>
              <span className="font-orbitron text-[9px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-3 block">
                MITRE ATT&CK REPLAY SIMULATOR
              </span>
              <div className="flex gap-1.5 justify-between items-center my-3">
                {REPLAY_STEPS.map((s, idx) => (
                  <div key={idx} className="flex flex-col items-center flex-1">
                    <div
                      className={`h-6 w-6 rounded-full border flex items-center justify-center text-[10px] transition-all duration-300 ${
                        replayStep >= idx
                          ? idx === REPLAY_STEPS.length - 1
                            ? "bg-[#FF355E]/20 border-[#FF355E] text-[#FF355E] shadow-[0_0_6px_#FF355E]"
                            : "bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_6px_#00D4FF]"
                          : "bg-[#1E293B]/40 border-[#1E293B]/70 text-[#5A7090]"
                      }`}
                    >
                      {s.icon}
                    </div>
                    <span className="text-[7px] text-[#5A7090] mt-1 truncate max-w-[40px] text-center">{s.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleRunMalwareAttack}
              disabled={replaying}
              className={`w-full py-2.5 rounded-lg border font-orbitron text-[9px] font-bold tracking-[2px] transition-all duration-200 flex items-center justify-center gap-2 ${
                replaying
                  ? "bg-[#1E293B]/50 border-[#1E293B] text-[#5A7090] cursor-not-allowed"
                  : "bg-[#FF355E]/10 border-[#FF355E] hover:bg-[#FF355E]/20 text-[#FF355E] cursor-pointer"
              }`}
            >
              <Play className="h-3.5 w-3.5" />
              {replaying ? "SIMULATOR ACTIVE..." : "RUN MALWARE ATTACK"}
            </button>
          </div>
        </div>
      </div>

      {/* MITRE Matrix & Distribution charts */}
      <MitreMap activeAlerts={alerts} />

      {/* Bottom Traffic charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Network Ingestion line chart */}
        <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5">
          <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold mb-4 block uppercase">
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
                  labelClassName="font-orbitron text-[#00D4FF]"
                />
                <Line type="monotone" dataKey="flows" stroke={COLORS.cyan} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity distribution chart */}
        <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5">
          <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold mb-4 block uppercase">
            Severity distribution breakdown
          </span>
          <div className="h-60 w-full flex items-center">
            <div className="w-1/2 h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityPieData.length > 0 ? severityPieData : [{ name: "SECURED", value: 1 }]}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {severityPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-1/2 space-y-2 pl-4">
              {severityPieData.map((d, i) => (
                <div key={i} className="flex items-center gap-2.5 text-xs">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: pieColors[i % pieColors.length] }} />
                  <span className="font-orbitron font-bold text-white">{d.name}:</span>
                  <span className="font-mono text-[#5A7090]">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
