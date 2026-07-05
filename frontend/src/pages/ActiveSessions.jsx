import React, { useState, useEffect } from "react";
import { Laptop, XCircle, Trash2, RefreshCw } from "lucide-react";
import { getSessions, revokeSession, revokeAllSessions } from "../services/api";

export default function ActiveSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadSessionsList = async () => {
    setLoading(true);
    try {
      const list = await getSessions();
      setSessions(list || []);
    } catch (err) {
      console.error("Failed to load active sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessionsList();
  }, []);

  const handleRevokeSession = async (sessionId) => {
    if (confirm("Are you sure you want to terminate this login session? The device will be logged out immediately.")) {
      try {
        await revokeSession(sessionId);
        loadSessionsList();
      } catch (err) {
        alert(err.message || "Failed to terminate session");
      }
    }
  };

  const handleRevokeAllSessions = async () => {
    if (confirm("Are you sure you want to terminate all other login sessions? This will log out all other devices.")) {
      try {
        await revokeAllSessions();
        loadSessionsList();
      } catch (err) {
        alert(err.message || "Failed to terminate all sessions");
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">ACTIVE SESSIONS</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">EDR AUTHORIZED DEVICES</p>
        </div>
        <div className="flex gap-3">
          {sessions.length > 1 && (
            <button
              onClick={handleRevokeAllSessions}
              className="px-4 py-2 border border-[#FF355E] bg-[#FF355E]/10 hover:bg-[#FF355E]/20 text-[#FF355E] font-orbitron text-xs font-bold tracking-wider rounded-lg flex items-center gap-2 cursor-pointer transition-all"
            >
              <Trash2 className="h-4 w-4" />
              TERMINATE ALL OTHER
            </button>
          )}
          <button
            onClick={loadSessionsList}
            className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {sessions.length > 0 ? (
          sessions.map((s) => (
            <div
              key={s.id}
              className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 shadow-lg flex flex-col justify-between relative overflow-hidden"
            >
              {/* Top border accent */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-[#00D4FF]" />

              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-lg flex items-center justify-center border border-[#1E293B] bg-[#060B18] text-[#00D4FF]">
                  <Laptop className="h-5 w-5" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <span className="font-orbitron font-bold text-xs text-white block truncate">{s.device_name || "Unknown Device"}</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[8px] font-bold font-orbitron tracking-wider">
                      {s.browser || "Unknown"}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#5A7090] font-mono block mt-1">{s.ip_address || "No IP Address"}</span>
                </div>
              </div>

              <div className="border-t border-[#1E293B]/50 my-4 pt-4 text-xs text-[#5A7090] space-y-1">
                <div className="flex justify-between">
                  <span>LOGGED IN AT:</span>
                  <span className="text-white font-medium">{new Date(s.created_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>EXPIRES:</span>
                  <span className="text-white font-medium">{new Date(s.expires_at).toLocaleString()}</span>
                </div>
              </div>

              <div className="flex justify-end border-t border-[#1E293B]/30 pt-3">
                <button
                  onClick={() => handleRevokeSession(s.id)}
                  className="px-3 py-1.5 border border-[#FF355E]/30 bg-[#FF355E]/5 hover:bg-[#FF355E]/15 text-[#FF355E] text-[9px] font-bold font-orbitron tracking-wider rounded flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <XCircle className="h-3.5 w-3.5" />
                  TERMINATE
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full bg-[#0C1426] border border-[#1E293B] rounded-xl p-12 text-center text-[#5A7090] text-sm">
            No active sessions recorded.
          </div>
        )}
      </div>
    </div>
  );
}
