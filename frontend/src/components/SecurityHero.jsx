import React, { useEffect, useState } from "react";
import { Globe, Terminal, ShieldAlert } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import StatsPanel from "./StatsPanel";

export default function SecurityHero() {
  const [logFeed, setLogFeed] = useState([
    "SECURE SOCKET GATEWAY ESTABLISHED",
    "SYNCING THREAT INTELLIGENCE DATABASES",
    "BEHAVIOR ANALYTICS ACTIVE ON 2,534 HOSTS",
  ]);

  const threatFeeds = [
    "BLOCKED IP 185.220.101.5 (TOR EXIT NODE)",
    "DETECTED SUSPICIOUS POWERSHELL EXECUTION ON HOST-492",
    "QUARANTINED MALICIOUS EXE (SHA-256 MATCH)",
    "SYNCED 45 INBOUND INDICATORS OF COMPROMISE",
    "BLOCKED OUTBOUND PORT SCANNING ON DEV-WORKSTATION",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      const randomFeed = threatFeeds[Math.floor(Math.random() * threatFeeds.length)];
      const timestamp = new Date().toLocaleTimeString();
      setLogFeed((prev) => [`[${timestamp}] ${randomFeed}`, ...prev.slice(0, 2)]);
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full h-full flex flex-col justify-between p-8 md:p-12 text-[#C5D0E6] select-none">
      {/* Header Info */}
      <div className="z-10 flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
          <Globe className="h-5 w-5 animate-spin-slow" />
        </div>
        <div className="flex flex-col">
          <span className="font-orbitron font-black text-xs tracking-[2px] text-white">
            EDR PLATFORM DOMAIN
          </span>
          <span className="font-orbitron text-[7px] tracking-[1.5px] text-slate-500">
            NEXUS CORE SECURE FEED
          </span>
        </div>
      </div>

      {/* Cyber attack visualization / Rotating Globe */}
      <div className="relative flex-1 w-full flex items-center justify-center z-10 py-6">
        <div className="relative w-72 h-72 md:w-80 md:h-80 rounded-full border border-slate-800/40 flex items-center justify-center overflow-hidden">
          {/* Cyber scanner ring */}
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-cyan-500/10 animate-spin-slow" />

          {/* Grid Scanner Line */}
          <div
            className="absolute left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent pointer-events-none"
            style={{ animation: "laserScan 6s linear infinite" }}
          />

          {/* SVG Vector Globe / Attack connections */}
          <svg className="w-full h-full object-contain" viewBox="0 0 300 300">
            {/* Outline grid circles */}
            <circle cx="150" cy="150" r="130" fill="none" stroke="rgba(37, 99, 235, 0.05)" strokeWidth="1" />
            <circle cx="150" cy="150" r="90" fill="none" stroke="rgba(37, 99, 235, 0.05)" strokeWidth="1" />
            <circle cx="150" cy="150" r="50" fill="none" stroke="rgba(37, 99, 235, 0.05)" strokeWidth="1" />

            {/* Latitude/Longitude lines */}
            <path d="M 20 150 Q 150 70 280 150" fill="none" stroke="rgba(6, 182, 212, 0.08)" />
            <path d="M 20 150 Q 150 230 280 150" fill="none" stroke="rgba(6, 182, 212, 0.08)" />
            <path d="M 150 20 Q 70 150 150 280" fill="none" stroke="rgba(6, 182, 212, 0.08)" />
            <path d="M 150 20 Q 230 150 150 280" fill="none" stroke="rgba(6, 182, 212, 0.08)" />

            {/* Attack nodes (pulsing coordinates) */}
            <g>
              <circle cx="70" cy="100" r="4" fill="#EF4444" className="animate-pulse" />
              <circle cx="70" cy="100" r="8" fill="none" stroke="#EF4444" strokeWidth="1" opacity="0.5">
                <animate attributeName="r" values="2;12" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="1;0" dur="2s" repeatCount="indefinite" />
              </circle>
            </g>

            <g>
              <circle cx="210" cy="190" r="3.5" fill="#EF4444" className="animate-pulse" />
              <circle cx="210" cy="190" r="8" fill="none" stroke="#EF4444" strokeWidth="1" opacity="0.5">
                <animate attributeName="r" values="2;12" dur="2.4s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="1;0" dur="2.4s" repeatCount="indefinite" />
              </circle>
            </g>

            {/* Core Target Node */}
            <g>
              <circle cx="150" cy="150" r="6" fill="#06B6D4" />
              <circle cx="150" cy="150" r="14" fill="none" stroke="#2563EB" strokeWidth="1.5">
                <animate attributeName="r" values="6;24" dur="3s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.8;0" dur="3s" repeatCount="indefinite" />
              </circle>
            </g>

            {/* Connection Arcs (Attack Path Flows) */}
            <path
              d="M 70,100 Q 110,80 150,150"
              fill="none"
              stroke="url(#attackGrad1)"
              strokeWidth="2"
              strokeDasharray="6 3"
            >
              <animate attributeName="strokeDashoffset" values="30;0" dur="2s" repeatCount="indefinite" />
            </path>

            <path
              d="M 210,190 Q 180,210 150,150"
              fill="none"
              stroke="url(#attackGrad2)"
              strokeWidth="2"
              strokeDasharray="6 3"
            >
              <animate attributeName="strokeDashoffset" values="30;0" dur="2.5s" repeatCount="indefinite" />
            </path>

            {/* Gradients */}
            <defs>
              <linearGradient id="attackGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#EF4444" />
                <stop offset="100%" stopColor="#06B6D4" />
              </linearGradient>
              <linearGradient id="attackGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#EF4444" />
                <stop offset="100%" stopColor="#2563EB" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Live Attack Feed console overlay */}
        <div className="absolute bottom-4 left-4 right-4 glass-panel rounded-lg p-3 border border-gray-800/80 font-mono text-[9px] text-slate-400 space-y-1.5 max-w-sm hidden sm:block">
          <div className="flex items-center gap-1.5 border-b border-gray-800 pb-1.5 mb-1.5 text-[8px] font-orbitron tracking-widest text-slate-500 font-bold uppercase">
            <Terminal className="h-3 w-3 text-cyan-400 animate-pulse" />
            LIVE TELEMETRY FEEDS
          </div>
          <div className="h-16 overflow-hidden flex flex-col gap-1 justify-end">
            <AnimatePresence>
              {logFeed.map((log, index) => (
                <motion.div
                  key={log}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-start gap-1.5 leading-relaxed truncate"
                >
                  <span className="text-[#FF355E]">&gt;</span>
                  <span>{log}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Live EDR Platform Metrics Section */}
      <div className="z-10">
        <StatsPanel />
      </div>
    </div>
  );
}
