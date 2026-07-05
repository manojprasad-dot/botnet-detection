import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import logoImg from "../assets/logo.jpg";
import { resetPassword } from "../services/api";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

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
      setError("Passwords do not match.");
      return;
    }

    if (strengthScore < 5) {
      setError("Password does not meet complexity requirements.");
      return;
    }

    setLoading(true);
    setMessage("");
    setError("");

    try {
      await resetPassword(token, newPassword);
      setMessage("Password reset successfully. You can now log in.");
    } catch (err) {
      setError(err.message || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060B18] text-[#C5D0E6] flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-[#0C1426] border border-[#1E293B] rounded-xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-[#00D4FF]" />

        <div className="flex flex-col items-center mb-6">
          <img src={logoImg} alt="Kovirx" className="h-12 w-12 object-contain mb-3" />
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">RESET EDR PASSWORD</h2>
          <span className="font-orbitron text-[8px] tracking-[1.5px] text-[#5A7090] mt-1">SECURE CREATION DESK</span>
        </div>

        {message && (
          <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-xs text-emerald-400 mb-4 text-center">
            {message}
            <div className="mt-2">
              <Link to="/login" className="text-xs font-bold text-white underline">LOG IN NOW</Link>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs text-rose-400 mb-4 text-center">
            {error}
          </div>
        )}

        {!message && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">NEW PASSWORD</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-[#00D4FF]"
                placeholder="Minimum 12 characters..."
              />
            </div>

            {/* Password strength indicator */}
            {newPassword && (
              <div className="space-y-1">
                <div className="flex justify-between text-[9px] text-[#5A7090] font-orbitron font-bold">
                  <span>STRENGTH PROFILE:</span>
                  <span style={{ color: strengthScore === 5 ? "#00E676" : "#FFB400" }}>
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
                <p className="text-[8px] text-[#5A7090] leading-relaxed">
                  Requires 12+ chars, uppercase, lowercase, numbers, and special symbols.
                </p>
              </div>
            )}

            <div>
              <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">CONFIRM NEW PASSWORD</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-[#00D4FF]"
                placeholder="Verify new password..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-lg bg-[#00D4FF] hover:bg-[#00D4FF]/80 text-black font-orbitron text-xs font-bold tracking-wider transition-all shadow-lg shadow-cyan-500/10 cursor-pointer ${
                loading ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {loading ? "SAVING..." : "UPDATE CREDENTIALS"}
            </button>
          </form>
        )}

        <div className="text-center mt-6">
          <Link to="/login" className="text-xs text-[#5A7090] hover:text-white transition-colors font-orbitron">
            BACK TO LOGIN
          </Link>
        </div>
      </div>
    </div>
  );
}
