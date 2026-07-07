import React, { useEffect, useState } from "react";
import { CheckCircle2, Shield, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function LoadingOverlay({ onComplete }) {
  const stepsList = [
    "Connecting Endpoint Agents...",
    "Loading Threat Intelligence...",
    "Syncing Live Telemetry...",
    "Establishing Secure WebSocket...",
  ];

  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);

  useEffect(() => {
    if (currentStep < stepsList.length) {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => [...prev, currentStep]);
        setCurrentStep((prev) => prev + 1);
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      const timer = setTimeout(() => {
        onComplete();
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  return (
    <div className="fixed inset-0 z-50 bg-[#030712]/90 backdrop-blur-md flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-sm glass-panel p-8 rounded-2xl border border-slate-800/80 flex flex-col items-center shadow-2xl relative overflow-hidden">
        {/* Glowing top line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 via-cyan-400 to-blue-600" />

        {/* Neural connection network spinner */}
        <div className="relative mb-6">
          <div className="absolute -inset-4 rounded-full bg-cyan-500/10 blur-md pointer-events-none" />
          <Loader2 className="h-12 w-12 text-cyan-400 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center text-blue-500">
            <Shield className="h-5 w-5" />
          </div>
        </div>

        <h3 className="font-orbitron font-black text-sm tracking-[3px] text-white mb-2">
          INITIALIZING GATEWAY
        </h3>
        <p className="font-orbitron text-[8px] tracking-[1.5px] text-slate-500 mb-8 uppercase">
          Establishing EDR Operations Session
        </p>

        {/* Steps List */}
        <div className="w-full space-y-4">
          {stepsList.map((step, idx) => {
            const isCompleted = completedSteps.includes(idx);
            const isActive = currentStep === idx;

            return (
              <div
                key={step}
                className={`flex items-center gap-3 text-xs transition-opacity duration-300 ${
                  isCompleted || isActive ? "opacity-100" : "opacity-35"
                }`}
              >
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  ) : isActive ? (
                    <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
                  ) : (
                    <div className="h-2.5 w-2.5 rounded-full bg-slate-800 border border-slate-700" />
                  )}
                </div>
                <span
                  className={`font-sans tracking-wide ${
                    isCompleted
                      ? "text-slate-400 line-through decoration-slate-800"
                      : isActive
                      ? "text-cyan-400 font-semibold"
                      : "text-slate-500"
                  }`}
                >
                  {step}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
