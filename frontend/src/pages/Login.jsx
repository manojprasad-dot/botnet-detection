import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import AnimatedBackground from "../components/AnimatedBackground";
import SecurityHero from "../components/SecurityHero";
import AuthenticationCard from "../components/AuthenticationCard";
import LoadingOverlay from "../components/LoadingOverlay";

export default function Login() {
  const navigate = useNavigate();
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false);

  const handleLoginSuccess = () => {
    setShowLoadingOverlay(true);
  };

  const handleInitializationComplete = () => {
    window.dispatchEvent(new Event("auth_change"));
    navigate("/");
  };

  return (
    <div className="relative w-screen h-screen bg-[#030712] flex overflow-hidden font-sans select-none">
      {/* ── Background layers ── */}
      <AnimatedBackground />

      {/* ── Split screen layout ── */}
      <div className="relative w-full h-full flex flex-col md:flex-row z-10">
        
        {/* Left Panel Showcase (55% width) */}
        <div className="hidden md:flex md:w-[55%] h-full border-r border-slate-900/50 bg-gray-950/20 backdrop-blur-[2px] items-center justify-center">
          <SecurityHero />
        </div>

        {/* Right Panel Card container (45% width) */}
        <div className="w-full md:w-[45%] h-full flex items-center justify-center p-6 sm:p-12">
          <AuthenticationCard onSuccess={handleLoginSuccess} />
        </div>
      </div>

      {/* ── Initialization loading sequence checklist ── */}
      {showLoadingOverlay && (
        <LoadingOverlay onComplete={handleInitializationComplete} />
      )}
    </div>
  );
}
