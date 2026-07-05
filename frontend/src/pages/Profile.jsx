import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { User, Phone, Briefcase, Image, CheckCircle, RefreshCw } from "lucide-react";
import { updateProfile } from "../services/api";

export default function Profile() {
  const { currentUser, loadDashboardData } = useOutletContext();

  const [formData, setFormData] = useState({
    full_name: "",
    department: "",
    phone: "",
    avatar_url: "",
  });
  
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentUser) {
      setFormData({
        full_name: currentUser.full_name || "",
        department: currentUser.department || "",
        phone: currentUser.phone || "",
        avatar_url: currentUser.avatar_url || "",
      });
    }
  }, [currentUser]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    try {
      await updateProfile(formData);
      setMessage("Profile parameters successfully updated.");
      window.dispatchEvent(new Event("auth_change"));
      loadDashboardData();
    } catch (err) {
      setError(err.message || "Failed to update profile parameters.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">ANALYST PROFILE</h2>
        <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">EDR METADATA IDENTITY</p>
      </div>

      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-6 shadow-lg relative overflow-hidden">
        {message && (
          <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-xs text-emerald-400 mb-4 text-center">
            {message}
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs text-rose-400 mb-4 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center border-b border-[#1E293B] pb-6 mb-6">
            <div className="relative">
              {formData.avatar_url ? (
                <img
                  src={formData.avatar_url}
                  alt="Avatar"
                  className="h-16 w-16 rounded-full object-cover border-2 border-[#9B59FF] shadow-[0_0_8px_rgba(155,89,255,0.3)]"
                />
              ) : (
                <div className="h-16 w-16 rounded-full bg-[#1E293B] border border-[#2E3C51] flex items-center justify-center text-white font-orbitron text-xl font-bold">
                  {currentUser?.username.substring(0, 2).toUpperCase()}
                </div>
              )}
            </div>
            <div>
              <h3 className="text-white font-bold text-sm">{currentUser?.username}</h3>
              <p className="text-xs text-[#5A7090] mt-0.5">{currentUser?.email}</p>
              <span className="inline-block px-2.5 py-0.5 rounded border border-[#9B59FF]/30 bg-[#9B59FF]/10 text-[#9B59FF] text-[9px] font-bold font-orbitron tracking-wider mt-2 uppercase">
                {currentUser?.role.replace("super_", "").replace("_", " ")}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">FULL NAME</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
                  <User className="h-4 w-4" />
                </span>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF]"
                  placeholder="e.g. John Doe"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">DEPARTMENT</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
                  <Briefcase className="h-4 w-4" />
                </span>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF]"
                  placeholder="e.g. SOC Team Alpha"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">PHONE NUMBER</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
                  <Phone className="h-4 w-4" />
                </span>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF]"
                  placeholder="e.g. +1 555-0199"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">AVATAR URL</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
                  <Image className="h-4 w-4" />
                </span>
                <input
                  type="url"
                  value={formData.avatar_url}
                  onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF]"
                  placeholder="https://..."
                />
              </div>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-lg bg-[#9B59FF] hover:bg-[#9B59FF]/80 text-white font-orbitron text-xs font-bold tracking-wider transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-purple-500/10"
            >
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              {loading ? "SAVING..." : "UPDATE METADATA"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
