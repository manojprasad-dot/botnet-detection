import React from "react";

export default function AnimatedBackground() {
  return (
    <div className="absolute inset-0 z-0 overflow-hidden bg-[#030712] pointer-events-none">
      {/* Dynamic Cyber Grid */}
      <div className="absolute inset-0 cyber-grid opacity-25" />

      {/* Radial Gradient Mesh overlays */}
      <div className="absolute inset-0 gradient-mesh opacity-40" />

      {/* Blurred Glowing Spotlights */}
      <div className="absolute -top-[10%] -left-[10%] w-[60vw] h-[60vw] glow-spot-blue rounded-full opacity-35" />
      <div className="absolute -bottom-[20%] -right-[10%] w-[70vw] h-[70vw] glow-spot-cyan rounded-full opacity-25" />

      {/* Floating Particles and connections */}
      <svg className="absolute inset-0 w-full h-full opacity-40">
        <defs>
          <radialGradient id="glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Slow moving background particles */}
        <circle cx="12%" cy="25%" r="3" fill="url(#glow)" style={{ animation: "floatParticle 12s ease-in-out infinite" }} />
        <circle cx="85%" cy="15%" r="4" fill="url(#glow)" style={{ animation: "floatParticle 16s ease-in-out infinite 2s" }} />
        <circle cx="45%" cy="75%" r="3.5" fill="url(#glow)" style={{ animation: "floatParticle 14s ease-in-out infinite 1s" }} />
        <circle cx="70%" cy="60%" r="2" fill="url(#glow)" style={{ animation: "floatParticle 18s ease-in-out infinite 3s" }} />
        <circle cx="20%" cy="85%" r="4.5" fill="url(#glow)" style={{ animation: "floatParticle 20s ease-in-out infinite 4s" }} />

        {/* Dynamic connection paths */}
        <path
          d="M 120,250 Q 300,180 450,300 T 800,200"
          fill="none"
          stroke="rgba(37, 99, 235, 0.08)"
          strokeWidth="1.5"
        />
        <path
          d="M 50,600 Q 250,520 400,650 T 900,450"
          fill="none"
          stroke="rgba(6, 182, 212, 0.08)"
          strokeWidth="1.5"
        />
      </svg>
    </div>
  );
}
