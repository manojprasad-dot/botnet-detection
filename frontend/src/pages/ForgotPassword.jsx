import React, { useState } from "react";
import { Link } from "react-router-dom";
import logoImg from "../assets/logo.jpg";
import { forgotPassword } from "../services/api";

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
    <div className="min-h-screen bg-[#060B18] text-[#C5D0E6] flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-[#0C1426] border border-[#1E293B] rounded-xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-[#9B59FF]" />
        
        <div className="flex flex-col items-center mb-6">
          <img src={logoImg} alt="Kovirx" className="h-12 w-12 object-contain filter drop-shadow-[0_0_8px_rgba(155,89,255,0.4)] mb-3" />
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">RECOVER CREDENTIALS</h2>
          <span className="font-orbitron text-[8px] tracking-[1.5px] text-[#5A7090] mt-1">EDR SECURITY DOMAIN</span>
        </div>

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
            <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">EMAIL ADDRESS</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF] transition-all"
              placeholder="e.g. operator@kovirx.com"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2.5 rounded-lg bg-[#9B59FF] hover:bg-[#9B59FF]/80 text-white font-orbitron text-xs font-bold tracking-wider transition-all shadow-lg shadow-purple-500/10 cursor-pointer ${
              loading ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {loading ? "PROCESSING..." : "REQUEST RESET LINK"}
          </button>
        </form>

        <div className="text-center mt-6">
          <Link to="/login" className="text-xs text-[#5A7090] hover:text-[#9B59FF] transition-colors font-orbitron">
            RETURN TO SIGN IN
          </Link>
        </div>
      </div>
    </div>
  );
}
