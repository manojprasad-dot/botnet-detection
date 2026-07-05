import React, { useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Search,
  RefreshCw,
  UserCheck,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Eye,
} from "lucide-react";
import { updateAlertStatus, assignAlert } from "../services/api";

const COLORS = {
  cyan: "#00D4FF",
  amber: "#FFB400",
  red: "#FF355E",
  purple: "#9B59FF",
  safe: "#00E676",
};

export default function Incidents() {
  const {
    alerts,
    currentUser,
    loadDashboardData,
  } = useOutletContext();

  const [selectedAlert, setSelectedAlert] = useState(null);
  const [alertsFilter, setAlertsFilter] = useState({ severity: "", status: "", search: "" });
  const [assigneeId, setAssigneeId] = useState("");

  const handleUpdateStatus = async (alertId, status) => {
    try {
      await updateAlertStatus(alertId, status);
      setSelectedAlert(null);
      loadDashboardData();
    } catch (err) {
      alert("Failed to update status: " + err.message);
    }
  };

  const handleAssignAlert = async (e) => {
    e.preventDefault();
    if (!selectedAlert || !assigneeId) return;
    try {
      await assignAlert(selectedAlert.id, assigneeId);
      setSelectedAlert(null);
      setAssigneeId("");
      loadDashboardData();
    } catch (err) {
      alert("Failed to assign alert: " + err.message);
    }
  };

  const getSeverityBadgeClass = (sev) => {
    const s = (sev || "").toLowerCase();
    if (s === "critical") return "bg-red/10 border-red text-red shadow-[0_0_6px_rgba(255,53,94,0.1)]";
    if (s === "high") return "bg-amber/10 border-amber text-amber shadow-[0_0_6px_rgba(255,180,0,0.1)]";
    if (s === "medium") return "bg-purple/10 border-purple text-purple";
    return "bg-cyan/10 border-cyan text-cyan";
  };

  const filteredAlerts = alerts.filter((a) => {
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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">INCIDENT OPERATIONS QUEUE</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">XDR SECURITY EVENT DESK</p>
        </div>
        <button
          onClick={loadDashboardData}
          className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-lg">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative w-64">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
              <Search className="h-4 w-4" />
            </span>
            <input
              type="text"
              placeholder="Search IP, title, description..."
              value={alertsFilter.search}
              onChange={(e) => setAlertsFilter({ ...alertsFilter, search: e.target.value })}
              className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#00D4FF] transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#5A7090] font-bold font-orbitron">SEVERITY:</span>
            <select
              value={alertsFilter.severity}
              onChange={(e) => setAlertsFilter({ ...alertsFilter, severity: e.target.value })}
              className="bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]"
            >
              <option value="">ALL SEVERITIES</option>
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#5A7090] font-bold font-orbitron">STATUS:</span>
            <select
              value={alertsFilter.status}
              onChange={(e) => setAlertsFilter({ ...alertsFilter, status: e.target.value })}
              className="bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00D4FF]"
            >
              <option value="">ALL STATUSES</option>
              <option value="new">NEW</option>
              <option value="investigating">INVESTIGATING</option>
              <option value="resolved">RESOLVED</option>
              <option value="false_positive">FALSE POSITIVE</option>
            </select>
          </div>
        </div>

        <span className="text-xs text-[#5A7090] font-orbitron">
          FOUND: <span className="text-[#00D4FF] font-bold">{filteredAlerts.length}</span> INCIDENTS
        </span>
      </div>

      {/* Grid: Table & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Table list */}
        <div className="lg:col-span-2 bg-[#0C1426] border border-[#1E293B] rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] bg-[#050A16]/50">
                  <th className="p-4 font-semibold text-[#5A7090] tracking-wider">SEVERITY</th>
                  <th className="p-4 font-semibold text-[#5A7090] tracking-wider">ALERT NAME</th>
                  <th className="p-4 font-semibold text-[#5A7090] tracking-wider">DEVICE IP / HOST</th>
                  <th className="p-4 font-semibold text-[#5A7090] tracking-wider">STATUS</th>
                  <th className="p-4 font-semibold text-[#5A7090] tracking-wider">OCCURRED</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B]">
                {filteredAlerts.length > 0 ? (
                  filteredAlerts.map((a) => (
                    <tr
                      key={a.id}
                      onClick={() => setSelectedAlert(selectedAlert?.id === a.id ? null : a)}
                      className={`hover:bg-[#1E293B]/30 transition-colors cursor-pointer ${
                        selectedAlert?.id === a.id ? "bg-[#1E293B]/40" : ""
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
                      <td className="p-4 text-[#5A7090] truncate">{a.evidence?.source_ip || "System Core"}</td>
                      <td className="p-4">
                        <span className={`font-orbitron font-bold text-[9px] ${
                          a.status === "new" ? "text-[#FF355E] animate-pulse" : a.status === "investigating" ? "text-[#FFB400]" : "text-[#00E676]"
                        }`}>
                          {a.status.toUpperCase().replace("_", " ")}
                        </span>
                      </td>
                      <td className="p-4 text-[#5A7090]">
                        {new Date(a.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-[#5A7090] text-sm">
                      No security incidents match selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 shadow-lg min-h-[300px]">
          <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-4 block">
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
                <p className="text-xs text-[#5A7090] mt-1.5 leading-relaxed">{selectedAlert.description}</p>
              </div>

              <div className="space-y-2.5 border-t border-[#1E293B]/50 pt-3 text-xs text-[#5A7090]">
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
                  <span className="text-[#00D4FF] font-semibold">{selectedAlert.evidence?.source_ip || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Dest Domain:</span>
                  <span className="text-[#FFB400] truncate max-w-[140px]">{selectedAlert.evidence?.dns_query || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Assigned To:</span>
                  <span className="text-white">
                    {selectedAlert.assigned_to
                      ? selectedAlert.assigned_to.substring(0, 8) + "..."
                      : "Unassigned"}
                  </span>
                </div>
              </div>

              {/* Threat Mitigation Recommendation */}
              {selectedAlert.evidence?.recommendation && (
                <div className="p-3 bg-red-950/20 border border-[#FF355E]/30 rounded-lg text-xs">
                  <span className="font-orbitron font-bold text-[8px] text-[#FF355E] tracking-wider block mb-1">
                    CONTAINMENT ACTION RECOMMENDATION
                  </span>
                  <p className="text-white leading-relaxed">{selectedAlert.evidence.recommendation}</p>
                </div>
              )}

              {/* Status Update Actions */}
              <div className="border-t border-[#1E293B]/50 pt-3 space-y-2">
                <span className="font-orbitron text-[9px] text-[#5A7090] tracking-wider font-bold block mb-1">
                  UPDATE STATUS
                </span>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleUpdateStatus(selectedAlert.id, "investigating")}
                    className="py-1.5 rounded bg-[#1E293B]/60 hover:bg-[#1E293B] text-white text-[9px] font-bold font-orbitron transition-all"
                  >
                    INVESTIGATE
                  </button>
                  <button
                    onClick={() => handleUpdateStatus(selectedAlert.id, "resolved")}
                    className="py-1.5 rounded bg-[#00E676]/10 border border-[#00E676]/30 text-[#00E676] hover:bg-[#00E676]/20 text-[9px] font-bold font-orbitron transition-all"
                  >
                    RESOLVE
                  </button>
                  <button
                    onClick={() => handleUpdateStatus(selectedAlert.id, "false_positive")}
                    className="py-1.5 rounded bg-[#FF355E]/10 border border-[#FF355E]/30 text-[#FF355E] hover:bg-[#FF355E]/20 text-[9px] font-bold font-orbitron transition-all"
                  >
                    FALSE POS
                  </button>
                </div>
              </div>

              {/* Assign to Analyst Modal */}
              {["super_admin", "soc_manager"].includes(currentUser?.role) && (
                <form onSubmit={handleAssignAlert} className="border-t border-[#1E293B]/50 pt-3 space-y-2">
                  <span className="font-orbitron text-[9px] text-[#5A7090] tracking-wider font-bold block">
                    ASSIGN INCIDENT
                  </span>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Analyst UUID..."
                      value={assigneeId}
                      onChange={(e) => setAssigneeId(e.target.value)}
                      className="flex-1 bg-[#060B18] border border-[#1E293B] rounded px-2.5 py-1.5 text-xs text-white placeholder-[#5A7090] focus:outline-none"
                    />
                    <button
                      type="submit"
                      className="px-3 rounded bg-[#9B59FF] text-white text-[9px] font-bold font-orbitron flex items-center gap-1"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      ASSIGN
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center text-[#5A7090] space-y-2">
              <Eye className="h-8 w-8 text-[#1E293B]" />
              <span className="text-xs">Select an active threat alert to load evidence and explanations.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
