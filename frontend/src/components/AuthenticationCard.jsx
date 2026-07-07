import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Key, Shield, AlertCircle, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import logoImg from "../assets/logo.jpg";
import FloatingInput from "./FloatingInput";
import PasswordInput from "./PasswordInput";
import RememberDevice from "./RememberDevice";
import { login } from "../services/api";

export default function AuthenticationCard({ onSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);

  const loadingPhases = [
    "Authenticating...",
    "Verifying Identity...",
    "Connecting Security Services...",
    "Opening Security Operations Center...",
  ];

  // Rotate loading text phases when authenticating
  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setLoadingPhase((prev) => (prev < loadingPhases.length - 1 ? prev + 1 : prev));
      }, 1000);
    } else {
      setLoadingPhase(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Credentials required.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      await login(email, password);
      // Wait for the final phase to complete before displaying success loading overlay
      setTimeout(() => {
        onSuccess();
      }, 3500);
    } catch (err) {
      setError(err.message || "Access Denied. Check credentials.");
      setLoading(false);
    }
  };

  const handleAutofill = () => {
    setEmail("admin@kovirx.com");
    setPassword("KovirX@2024!");
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full max-w-[440px] px-8 py-10 rounded-2xl glass-panel relative overflow-hidden flex flex-col items-center"
    >
      {/* Top neon strip */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-600 via-cyan-400 to-cyan-500" />

      {/* Brand Header logo */}
      <div className="relative mb-6">
        <div className="absolute -inset-4 rounded-full bg-cyan-500/10 blur-md pointer-events-none" />
        <img
          src={logoImg}
          alt="Kovirx"
          className="h-14 w-14 object-contain filter drop-shadow-[0_0_10px_rgba(6,182,212,0.4)] logo-blend"
        />
      </div>

      <h1 className="font-orbitron text-2xl font-black text-white tracking-[4px] mb-1 bg-gradient-to-r from-white to-cyan-400 bg-clip-text text-transparent">
        KOVIRX
      </h1>
      <p className="font-orbitron text-[8px] tracking-[2px] text-slate-500 mb-8 uppercase font-bold text-center">
        AI-Powered Enterprise EDR
      </p>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full p-3.5 rounded-lg bg-red-950/20 border border-red-500/30 text-red-400 text-xs mb-6 flex items-start gap-2.5 font-sans"
        >
          <AlertCircle className="h-4.5 w-4.5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex flex-col">
            <strong className="font-orbitron text-[9px] tracking-wider font-bold">ACCESS DENIED</strong>
            <span className="text-[11px] mt-0.5 leading-relaxed">{error}</span>
          </div>
        </motion.div>
      )}

      <form onSubmit={handleSubmit} className="w-full space-y-6">
        <FloatingInput
          id="email-field"
          type="email"
          label="ANALYST EMAIL"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={loading}
          icon={Shield}
        />

        <PasswordInput
          id="password-field"
          label="SECURE KEY / PASSWORD"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />

        {/* Lockout reminder & Forgot Password */}
        <div className="flex justify-between items-center text-[9px] font-orbitron font-medium tracking-wider">
          <span className="text-slate-500">
            5 FAILED ATTEMPTS LOCKS ACCOUNT
          </span>
          <Link
            to="/forgot-password"
            className="text-cyan-400 hover:text-white transition-colors duration-200"
          >
            FORGOT PASSWORD?
          </Link>
        </div>

        {/* Remember me & Seed button layout */}
        <div className="flex justify-between items-center pt-2">
          <RememberDevice
            checked={rememberMe}
            onChange={setRememberMe}
            disabled={loading}
          />
          
          {/* Custom Seed Key autofill tool */}
          <button
            type="button"
            onClick={handleAutofill}
            disabled={loading}
            className="p-1.5 rounded-md border border-slate-800 hover:border-cyan-500/50 hover:bg-cyan-500/5 text-slate-500 hover:text-cyan-400 transition-all duration-200 cursor-pointer disabled:opacity-50"
            title="Auto-fill Credentials"
          >
            <Key className="h-4 w-4" />
          </button>
        </div>

        {/* Multi-phase launch button */}
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
          <span className="uppercase">
            {loading ? loadingPhases[loadingPhase] : "LAUNCH SECURITY CONSOLE"}
          </span>
        </button>
      </form>
    </motion.div>
  );
}
