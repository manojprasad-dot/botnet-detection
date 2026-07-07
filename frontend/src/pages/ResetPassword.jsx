import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { RefreshCw, ShieldAlert, KeyRound, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import logoImg from "../assets/logo.jpg";
import { resetPassword } from "../services/api";
import FloatingInput from "../components/FloatingInput";
import PasswordInput from "../components/PasswordInput";
import AnimatedBackground from "../components/AnimatedBackground";

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
    <div className="relative w-screen h-screen bg-[#030712] flex items-center justify-center p-4 overflow-hidden select-none">
      <AnimatedBackground />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-[420px] px-8 py-10 rounded-2xl glass-panel relative z-10 flex flex-col items-center shadow-2xl"
      >
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-600 via-cyan-400 to-cyan-500" />

        <div className="flex flex-col items-center mb-6">
          <img src={logoImg} alt="Kovirx" className="h-12 w-12 object-contain mb-3 filter drop-shadow-[0_0_8px_rgba(6,182,212,0.4)] logo-blend" />
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">RESET EDR PASSWORD</h2>
          <span className="font-orbitron text-[8px] tracking-[1.5px] text-slate-500 mt-1 uppercase">SECURE CREATION DESK</span>
        </div>

        {message && (
          <div className="w-full p-4 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-center">
            <div className="flex items-center justify-center gap-2 text-emerald-400 text-xs font-semibold mb-3">
              <CheckCircle2 className="h-5 w-5" />
              <span>{message}</span>
            </div>
            <Link
              to="/login"
              className="inline-block py-2 px-4 rounded bg-cyan-500 text-black font-orbitron font-bold text-[9px] tracking-wider hover:bg-cyan-400 transition-colors"
            >
              LOG IN NOW
            </Link>
          </div>
        )}

        {error && (
          <div className="w-full p-3.5 bg-red-950/20 border border-red-500/30 rounded-lg text-[11px] text-red-400 mb-6 text-center font-sans flex items-center gap-2">
            <ShieldAlert className="h-4.5 w-4.5 text-red-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!message && (
          <form onSubmit={handleSubmit} className="w-full space-y-6">
            <PasswordInput
              id="new-pass"
              label="NEW SECURITY PASSWORD"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              disabled={loading}
            />

            {/* Password strength profile */}
            {newPassword && (
              <div className="space-y-2">
                <div className="flex justify-between text-[9px] text-slate-500 font-orbitron font-bold tracking-wider">
                  <span>STRENGTH PROFILE:</span>
                  <span className={strengthScore === 5 ? "text-emerald-400" : "text-amber-400"}>
                    {strengthScore === 5 ? "COMPLIANT" : "WEAK"}
                  </span>
                </div>
                <div className="h-1 bg-gray-900 rounded-full overflow-hidden flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, idx) => (
                    <div
                      key={idx}
                      className={`h-full flex-1 transition-all duration-300 ${
                        strengthScore > idx
                          ? strengthScore === 5
                            ? "bg-emerald-400 shadow-[0_0_6px_#10B981]"
                            : "bg-amber-400 shadow-[0_0_6px_#F59E0B]"
                          : "bg-slate-800"
                      }`}
                    />
                  ))}
                </div>
                <p className="text-[8px] text-slate-500 leading-normal font-sans">
                  Requires 12+ chars, uppercase, lowercase, numbers, and special symbols.
                </p>
              </div>
            )}

            <PasswordInput
              id="confirm-pass"
              label="CONFIRM SECURITY PASSWORD"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={loading}
            />

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3.5 rounded-lg text-white font-orbitron text-[10px] font-bold tracking-[3px] shadow-lg transition-all duration-300 relative overflow-hidden flex items-center justify-center cursor-pointer ${
                loading
                  ? "bg-slate-800 text-slate-500 shadow-none border border-slate-700/50"
                  : "bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-500 hover:shadow-cyan-500/20 hover:brightness-110 shadow-blue-500/10"
              }`}
            >
              {loading && (
                <RefreshCw className="h-3.5 w-3.5 animate-spin absolute left-4 text-cyan-400" />
              )}
              <span>{loading ? "SAVING..." : "UPDATE CREDENTIALS"}</span>
            </button>
          </form>
        )}

        <div className="text-center mt-8">
          <Link to="/login" className="text-[10px] text-slate-500 hover:text-cyan-400 transition-colors font-orbitron font-semibold tracking-wider">
            BACK TO LOGIN
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
