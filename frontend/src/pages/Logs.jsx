import React, { useState, useEffect } from "react";
import {
  Terminal,
  Database,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Filter,
} from "lucide-react";
import { getSystemLogs, getAuditLogs } from "../services/api";

export default function Logs() {
  const [logsType, setLogsType] = useState("system"); // system or audit
  const [logsList, setLogsList] = useState([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logsPage, setLogsPage] = useState(1);
  const [logsLevel, setLogsLevel] = useState("");
  const [logsModule, setLogsModule] = useState("");
  const [logsAction, setLogsAction] = useState("");

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
    loadLogsList();
  }, [logsType, logsPage, logsLevel, logsModule, logsAction]);

  const handleTypeChange = (type) => {
    setLogsType(type);
    setLogsPage(1);
    setLogsLevel("");
    setLogsModule("");
    setLogsAction("");
  };

  const getLogLevelColor = (level) => {
    const l = (level || "").toLowerCase();
    if (l === "error" || l === "critical") return "text-[#FF355E] font-bold";
    if (l === "warning") return "text-[#FFB400]";
    return "text-[#5A7090]";
  };

  const totalPages = Math.ceil(logsTotal / 20) || 1;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">SYSTEM & AUDIT LOGS NEXUS</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">XDR DIAGNOSTIC CENTER</p>
        </div>
        <button
          onClick={loadLogsList}
          className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-[#1E293B] pb-px">
        <button
          onClick={() => handleTypeChange("system")}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-orbitron text-xs font-bold tracking-wider transition-all cursor-pointer ${
            logsType === "system"
              ? "border-[#00D4FF] text-white"
              : "border-transparent text-[#5A7090] hover:text-white"
          }`}
        >
          <Terminal className="h-4.5 w-4.5" />
          SYSTEM METRIC LOGS
        </button>
        <button
          onClick={() => handleTypeChange("audit")}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-orbitron text-xs font-bold tracking-wider transition-all cursor-pointer ${
            logsType === "audit"
              ? "border-[#00D4FF] text-white"
              : "border-transparent text-[#5A7090] hover:text-white"
          }`}
        >
          <Database className="h-4.5 w-4.5" />
          ADMIN AUDIT LOGS
        </button>
      </div>

      {/* Filter toolbar */}
      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-lg text-xs">
        <div className="flex items-center gap-3 flex-wrap">
          <Filter className="h-4 w-4 text-[#5A7090]" />

          {logsType === "system" ? (
            <>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#5A7090] font-bold font-orbitron">LOG LEVEL:</span>
                <select
                  value={logsLevel}
                  onChange={(e) => { setLogsLevel(e.target.value); setLogsPage(1); }}
                  className="bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="">ALL LEVELS</option>
                  <option value="info">INFO</option>
                  <option value="warning">WARNING</option>
                  <option value="error">ERROR</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#5A7090] font-bold font-orbitron">MODULE:</span>
                <input
                  type="text"
                  placeholder="e.g. telemetry..."
                  value={logsModule}
                  onChange={(e) => { setLogsModule(e.target.value); setLogsPage(1); }}
                  className="bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-1.5 text-white placeholder-[#5A7090] focus:outline-none"
                />
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#5A7090] font-bold font-orbitron">ACTION:</span>
              <input
                type="text"
                placeholder="e.g. login..."
                value={logsAction}
                onChange={(e) => { setLogsAction(e.target.value); setLogsPage(1); }}
                className="bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-1.5 text-white placeholder-[#5A7090] focus:outline-none"
              />
            </div>
          )}
        </div>

        <span className="font-orbitron text-[#5A7090]">
          TOTAL ENTRIES: <span className="text-[#00D4FF] font-bold">{logsTotal}</span>
        </span>
      </div>

      {/* Logs Table */}
      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          {logsType === "system" ? (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] bg-[#050A16]/50 text-[#5A7090] font-semibold tracking-wider">
                  <th className="p-4">LEVEL</th>
                  <th className="p-4">MODULE</th>
                  <th className="p-4">MESSAGE</th>
                  <th className="p-4">DETAILS</th>
                  <th className="p-4">TIMESTAMP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B] text-white">
                {logsList.length > 0 ? (
                  logsList.map((log) => (
                    <tr key={log.id} className="hover:bg-[#1E293B]/20">
                      <td className="p-4 uppercase font-bold">
                        <span className={getLogLevelColor(log.level)}>{log.level}</span>
                      </td>
                      <td className="p-4 font-semibold text-[#00D4FF] truncate max-w-[120px]">{log.module}</td>
                      <td className="p-4 max-w-[300px] truncate">{log.message}</td>
                      <td className="p-4 font-mono text-[10px] text-[#5A7090] max-w-[200px] truncate">
                        {log.details ? JSON.stringify(log.details) : "None"}
                      </td>
                      <td className="p-4 text-[#5A7090]">{new Date(log.created_at).toLocaleString()}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-[#5A7090] text-sm">
                      No system logs found matching filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] bg-[#050A16]/50 text-[#5A7090] font-semibold tracking-wider">
                  <th className="p-4">ANALYST</th>
                  <th className="p-4">ACTION</th>
                  <th className="p-4">RESOURCE</th>
                  <th className="p-4">DETAILS</th>
                  <th className="p-4">TIMESTAMP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B] text-white">
                {logsList.length > 0 ? (
                  logsList.map((log) => (
                    <tr key={log.id} className="hover:bg-[#1E293B]/20">
                      <td className="p-4 font-bold text-[#9B59FF]">{log.user?.username || "SYSTEM"}</td>
                      <td className="p-4 font-semibold text-white uppercase tracking-wider">{log.action.replace("_", " ")}</td>
                      <td className="p-4 text-[#00D4FF] font-mono text-[10px]">{log.resource_id ? `${log.resource} (${log.resource_id.substring(0, 8)})` : log.resource}</td>
                      <td className="p-4 font-mono text-[10px] text-[#5A7090] max-w-[250px] truncate">
                        {log.details ? JSON.stringify(log.details) : "None"}
                      </td>
                      <td className="p-4 text-[#5A7090]">{new Date(log.created_at).toLocaleString()}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-[#5A7090] text-sm">
                      No administrator audit logs found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination footer */}
        <div className="p-4 border-t border-[#1E293B] bg-[#050A16]/30 flex items-center justify-between">
          <span className="text-xs text-[#5A7090] font-orbitron">
            PAGE <span className="text-white font-bold">{logsPage}</span> OF <span className="text-white">{totalPages}</span>
          </span>

          <div className="flex gap-2">
            <button
              onClick={() => setLogsPage(Math.max(1, logsPage - 1))}
              disabled={logsPage === 1}
              className="p-1.5 rounded border border-[#1E293B] text-white hover:bg-[#1E293B] disabled:text-[#5A7090] disabled:hover:bg-transparent cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setLogsPage(Math.min(totalPages, logsPage + 1))}
              disabled={logsPage === totalPages}
              className="p-1.5 rounded border border-[#1E293B] text-white hover:bg-[#1E293B] disabled:text-[#5A7090] disabled:hover:bg-transparent cursor-pointer"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
