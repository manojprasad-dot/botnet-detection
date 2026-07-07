import React from "react";
import { Shield, Cpu, Activity, Server, Zap, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";

export default function StatsPanel() {
  const stats = [
    { label: "PROTECTED DEVICES", value: "2,534", icon: Server, color: "text-blue-500" },
    { label: "THREATS BLOCKED", value: "18,920", icon: Shield, color: "text-red-500" },
    { label: "DETECTION ACCURACY", value: "99.84%", icon: CheckCircle2, color: "text-emerald-400" },
    { label: "ENDPOINT AGENTS", value: "1,842", icon: Cpu, color: "text-cyan-400" },
    { label: "PACKETS ANALYZED", value: "2.3M", icon: Activity, color: "text-purple-400" },
    { label: "BEHAVIOR MODELS", value: "46 Feats", icon: Zap, color: "text-amber-400" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
      {stats.map((stat, idx) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: idx * 0.05 }}
          whileHover={{ y: -2, borderColor: "rgba(6, 182, 212, 0.3)" }}
          className="glass-panel p-4 rounded-xl border border-gray-800/80 flex flex-col justify-between relative overflow-hidden group"
        >
          {/* Subtle hover background highlight */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

          <div className="flex justify-between items-start mb-2">
            <span className="font-orbitron text-[8px] font-bold tracking-widest text-slate-500 group-hover:text-cyan-400 transition-colors duration-200">
              {stat.label}
            </span>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </div>

          <span className="font-orbitron font-black text-lg text-white tracking-wide">
            {stat.value}
          </span>
        </motion.div>
      ))}

      {/* Engine Statuses */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="glass-panel p-4 rounded-xl border border-gray-800/80 col-span-2 md:col-span-3 flex justify-between items-center"
      >
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10B981] animate-pulse" />
          <span className="font-orbitron text-[9px] font-black tracking-widest text-slate-300">
            RISK ENGINE: <span className="text-emerald-400">ONLINE</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#06B6D4] animate-pulse" />
          <span className="font-orbitron text-[9px] font-black tracking-widest text-slate-300">
            THREAT INTEL: <span className="text-cyan-400">CONNECTED</span>
          </span>
        </div>
      </motion.div>
    </div>
  );
}
