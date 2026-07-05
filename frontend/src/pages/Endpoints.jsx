import React, { useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Laptop,
  Plus,
  Trash2,
  Activity,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Search,
} from "lucide-react";
import { registerDevice, deleteDevice } from "../services/api";

export default function Endpoints() {
  const {
    devices,
    currentUser,
    loadDashboardData,
  } = useOutletContext();

  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [deviceError, setDeviceError] = useState("");
  const [newDevice, setNewDevice] = useState({
    hostname: "",
    operating_system: "windows",
    ip_address: "",
    mac_address: "",
    os_version: "",
    architecture: "",
    agent_version: "1.0.0",
  });

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
        agent_version: "1.0.0",
      });
      loadDashboardData();
    } catch (err) {
      setDeviceError(err.message || "Failed to register endpoint device.");
    }
  };

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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">MANAGED ENDPOINTS INVENTORY</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">EDR AGENT DEPLOYMENTS</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowAddDeviceModal(true)}
            className="px-4 py-2 bg-[#9B59FF] hover:bg-[#9B59FF]/80 text-white font-orbitron text-xs font-bold tracking-wider rounded-lg flex items-center gap-2 cursor-pointer transition-colors shadow-lg shadow-purple-500/10"
          >
            <Plus className="h-4 w-4" />
            REGISTER ENDPOINT
          </button>
          <button
            onClick={loadDashboardData}
            className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Devices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {devices.length > 0 ? (
          devices.map((dev) => {
            const hasThreat = dev.risk_score >= 50;
            return (
              <div
                key={dev.id}
                className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-5 shadow-lg flex flex-col justify-between relative overflow-hidden"
              >
                {/* Edge accent */}
                <div className={`absolute top-0 left-0 right-0 h-1 ${
                  hasThreat ? "bg-[#FF355E]" : dev.status === "online" ? "bg-[#00E676]" : "bg-[#5A7090]"
                }`} />

                <div className="flex items-start gap-4">
                  <div className={`h-10 w-10 rounded-lg flex items-center justify-center border ${
                    hasThreat
                      ? "bg-[#FF355E]/10 border-[#FF355E]/40 text-[#FF355E]"
                      : dev.status === "online"
                      ? "bg-[#00E676]/10 border-[#00E676]/40 text-[#00E676]"
                      : "bg-[#1E293B]/50 border-[#1E293B] text-[#5A7090]"
                  }`}>
                    <Laptop className="h-5 w-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center">
                      <span className="font-orbitron font-bold text-xs text-white truncate max-w-[150px]">{dev.hostname}</span>
                      <span className={`px-2 py-0.5 rounded text-[8px] font-bold font-orbitron tracking-wider ${
                        dev.operating_system === "windows"
                          ? "bg-blue-500/10 border border-blue-500/20 text-blue-400"
                          : "bg-orange-500/10 border border-orange-500/20 text-orange-400"
                      }`}>
                        {dev.operating_system.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-[10px] text-[#5A7090] font-mono block mt-1">{dev.ip_address || "No IP Registered"}</span>
                  </div>
                </div>

                <div className="border-t border-[#1E293B]/50 my-4 pt-4 grid grid-cols-2 gap-4 text-xs text-[#5A7090]">
                  <div>
                    <span className="text-[9px] text-[#5A7090] uppercase tracking-wider block">RISK SCORE</span>
                    <span className={`font-orbitron font-black text-sm block mt-0.5 ${
                      hasThreat ? "text-[#FF355E]" : dev.risk_score >= 20 ? "text-[#FFB400]" : "text-[#00E676]"
                    }`}>
                      {dev.risk_score.toFixed(0)}/100
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] text-[#5A7090] uppercase tracking-wider block">AGENT STATE</span>
                    <span className={`font-orbitron font-bold text-xs block mt-0.5 capitalize ${
                      dev.status === "online" ? "text-[#00E676]" : "text-[#5A7090]"
                    }`}>
                      {dev.status}
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center text-[10px] text-[#5A7090] border-t border-[#1E293B]/30 pt-3">
                  <span>LAST ACTIVE: {dev.last_seen_at ? new Date(dev.last_seen_at).toLocaleTimeString() : "NEVER"}</span>
                  
                  {currentUser?.role === "super_admin" && (
                    <button
                      onClick={() => handleDeleteDevice(dev.id)}
                      className="p-1 text-[#5A7090] hover:text-[#FF355E] cursor-pointer transition-colors"
                      title="De-register Device"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-full bg-[#0C1426] border border-[#1E293B] rounded-xl p-12 text-center text-[#5A7090] text-sm">
            No devices are currently registered to send telemetry.
          </div>
        )}
      </div>

      {/* Register Endpoint Modal */}
      {showAddDeviceModal && (
        <div className="fixed inset-0 bg-[#060B18]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl w-full max-w-md p-6 relative shadow-2xl">
            <span className="font-orbitron text-xs font-black text-white tracking-[2px] border-b border-[#1E293B] pb-2.5 mb-4 block">
              REGISTER NEW ENDPOINT AGENT
            </span>

            {deviceError && (
              <div className="p-3 bg-red-950/20 border border-[#FF355E]/40 rounded-lg text-xs text-[#FF355E] mb-4">
                {deviceError}
              </div>
            )}

            <form onSubmit={handleAddDevice} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">HOST NAME</label>
                <input
                  type="text"
                  required
                  value={newDevice.hostname}
                  onChange={(e) => setNewDevice({ ...newDevice, hostname: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#00D4FF]"
                  placeholder="DESKTOP-87F8"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">PLATFORM</label>
                  <select
                    value={newDevice.operating_system}
                    onChange={(e) => setNewDevice({ ...newDevice, operating_system: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="windows">Windows</option>
                    <option value="linux">Linux</option>
                    <option value="macos">macOS</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">IP ADDRESS</label>
                  <input
                    type="text"
                    required
                    value={newDevice.ip_address}
                    onChange={(e) => setNewDevice({ ...newDevice, ip_address: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none"
                    placeholder="192.168.1.105"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">MAC ADDRESS</label>
                  <input
                    type="text"
                    value={newDevice.mac_address}
                    onChange={(e) => setNewDevice({ ...newDevice, mac_address: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none"
                    placeholder="00:1A:2B:3C:4D:5E"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">OS VERSION</label>
                  <input
                    type="text"
                    value={newDevice.os_version}
                    onChange={(e) => setNewDevice({ ...newDevice, os_version: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none"
                    placeholder="Build 22631"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddDeviceModal(false)}
                  className="px-4 py-2 border border-[#1E293B] rounded-lg text-xs font-bold text-white font-orbitron hover:bg-[#1E293B]"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#9B59FF] hover:bg-[#9B59FF]/80 rounded-lg text-xs font-bold text-white font-orbitron"
                >
                  REGISTER AGENT
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
