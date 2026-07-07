import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, RefreshCw, Key, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import logoImg from "../assets/logo.jpg";
import { forgotPassword } from "../services/api";
import FloatingInput from "../components/FloatingInput";
import AnimatedBackground from "../components/AnimatedBackground";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const res = await forgotPassword(email);
      setMessage(res.message || "Reset token has been generated.");
    } catch (err) {
      setError(err.message || "Failed to submit request.");
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
          <img src={logoImg} alt="Kovirx" className="h-12 w-12 object-contain filter drop-shadow-[0_0_8px_rgba(6,182,212,0.4)] mb-3 logo-blend" />
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">RECOVER CREDENTIALS</h2>
          <span className="font-orbitron text-[8px] tracking-[1.5px] text-slate-500 mt-1 uppercase">EDR SECURITY DOMAIN</span>
        </div>

        {message && (
          <div className="w-full p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-[11px] text-emerald-400 mb-6 text-center font-sans">
            {message}
          </div>
        )}

        {error && (
          <div className="w-full p-3.5 bg-red-950/20 border border-red-500/30 rounded-lg text-[11px] text-red-400 mb-6 text-center font-sans flex items-center gap-2">
            <ShieldAlert className="h-4.5 w-4.5 text-red-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="w-full space-y-6">
          <FloatingInput
            id="forgot-email"
            type="email"
            label="ENTER REGISTERED EMAIL"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            icon={Mail}
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
            <span>{loading ? "PROCESSING..." : "REQUEST RESET LINK"}</span>
          </button>
        </form>

        <div className="text-center mt-8">
          <Link to="/login" className="text-[10px] text-slate-500 hover:text-cyan-400 transition-colors font-orbitron font-semibold tracking-wider">
            RETURN TO SIGN IN
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
