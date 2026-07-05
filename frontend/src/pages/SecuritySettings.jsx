import React, { useState } from "react";
import { ShieldAlert, RefreshCw, Key, Check } from "lucide-react";
import { changePassword } from "../services/api";

export default function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const getPasswordStrength = (pw) => {
    let score = 0;
    if (pw.length >= 12) score += 1;
    if (/[A-Z]/.test(pw)) score += 1;
    if (/[a-z]/.test(pw)) score += 1;
    if (/\d/.test(pw)) score += 1;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pw)) score += 1;
    return score;
  };

  const strengthScore = getPasswordStrength(newPassword);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    if (strengthScore < 5) {
      setError("Password complexity requirements not satisfied.");
      return;
    }

    setLoading(true);
    setMessage("");
    setError("");

    try {
      await changePassword(currentPassword, newPassword);
      setMessage("Credential key has been updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message || "Failed to change credentials key.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">SECURITY ACCESS SETTINGS</h2>
        <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">EDR SECURE SESSION VAULT</p>
      </div>

      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-6 shadow-lg">
        <span className="font-orbitron text-[10px] text-[#5A7090] tracking-wider font-semibold border-b border-[#1E293B]/50 pb-2 mb-5 block">
          ROTATION OF PASSWORD KEY
        </span>

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

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">CURRENT PASSWORD</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-[#9B59FF]"
              placeholder="Enter current credential..."
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">NEW PASSWORD</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-[#9B59FF]"
              placeholder="Minimum 12 characters..."
            />
          </div>

          {/* Password strength profile */}
          {newPassword && (
            <div className="space-y-1.5 bg-[#060B18] p-3 rounded-lg border border-[#1E293B]">
              <div className="flex justify-between text-[9px] text-[#5A7090] font-orbitron font-bold">
                <span>STRENGTH METRIC:</span>
                <span className={strengthScore === 5 ? "text-[#00E676]" : "text-[#FFB400]"}>
                  {strengthScore === 5 ? "COMPLIANT" : "WEAK"}
                </span>
              </div>
              <div className="h-1 bg-[#1E293B] rounded-full overflow-hidden flex gap-0.5">
                {Array.from({ length: 5 }).map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-full flex-1 transition-all duration-300 ${
                      strengthScore > idx
                        ? strengthScore === 5
                          ? "bg-[#00E676]"
                          : "bg-[#FFB400]"
                        : "bg-[#1E293B]"
                    }`}
                  />
                ))}
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[8px] text-[#5A7090] pt-1">
                <span className="flex items-center gap-1">
                  <Check className={`h-2.5 w-2.5 ${newPassword.length >= 12 ? "text-[#00E676]" : "text-[#5A7090]"}`} /> 12+ Chars
                </span>
                <span className="flex items-center gap-1">
                  <Check className={`h-2.5 w-2.5 ${/[A-Z]/.test(newPassword) ? "text-[#00E676]" : "text-[#5A7090]"}`} /> Uppercase (A-Z)
                </span>
                <span className="flex items-center gap-1">
                  <Check className={`h-2.5 w-2.5 ${/[a-z]/.test(newPassword) ? "text-[#00E676]" : "text-[#5A7090]"}`} /> Lowercase (a-z)
                </span>
                <span className="flex items-center gap-1">
                  <Check className={`h-2.5 w-2.5 ${/\d/.test(newPassword) ? "text-[#00E676]" : "text-[#5A7090]"}`} /> Number (0-9)
                </span>
                <span className="flex items-center gap-1 col-span-2">
                  <Check className={`h-2.5 w-2.5 ${/[!@#$%^&*(),.?":{}|<>]/.test(newPassword) ? "text-[#00E676]" : "text-[#5A7090]"}`} /> Special Symbol (!@#...)
                </span>
              </div>
            </div>
          )}

          <div>
            <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1.5">CONFIRM NEW PASSWORD</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-[#9B59FF]"
              placeholder="Confirm new password..."
            />
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-lg bg-[#00D4FF] hover:bg-[#00D4FF]/80 text-black font-orbitron text-xs font-bold tracking-wider transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-cyan-500/10"
            >
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Key className="h-4 w-4" />}
              {loading ? "CHANGING..." : "CHANGE PASSWORD"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
