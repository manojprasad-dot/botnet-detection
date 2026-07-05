import React from "react";

const MITRE_TACTICS = [
  {
    name: "Initial Access",
    techniques: [
      { id: "T1190", name: "Exploit Public Application" },
      { id: "T1133", name: "External Remote Services" }
    ]
  },
  {
    name: "Execution",
    techniques: [
      { id: "T1059", name: "Command & Script Interpreter" },
      { id: "T1204", name: "User Execution" }
    ]
  },
  {
    name: "Persistence",
    techniques: [
      { id: "T1547", name: "Registry Run Keys / Startup" },
      { id: "T1053", name: "Scheduled Task/Job" }
    ]
  },
  {
    name: "Credential Access",
    techniques: [
      { id: "T1110", name: "Brute Force" },
      { id: "T1003", name: "OS Credential Dumping" }
    ]
  },
  {
    name: "Discovery",
    techniques: [
      { id: "T1046", name: "Network Service Discovery" },
      { id: "T1082", name: "System Information Discovery" }
    ]
  },
  {
    name: "Lateral Movement",
    techniques: [
      { id: "T1021", name: "Remote Services" },
      { id: "T1080", name: "Shared Content" }
    ]
  },
  {
    name: "Command & Control",
    techniques: [
      { id: "T1071", name: "Application Layer Protocol" },
      { id: "T1090", name: "Proxy Connection" }
    ]
  },
  {
    name: "Exfiltration",
    techniques: [
      { id: "T1048", name: "Exfiltration Over Protocol" },
      { id: "T1041", name: "Exfiltration Over C2 Channel" }
    ]
  }
];

export default function MitreMap({ activeAlerts = [] }) {
  // Determine which techniques are currently active based on current alerts titles/descriptions
  const activeIds = new Set();
  
  activeAlerts.forEach(alert => {
    const desc = (alert.description || "").toLowerCase();
    const title = (alert.title || "").toLowerCase();
    
    if (desc.includes("brute force") || desc.includes("t1110")) activeIds.add("T1110");
    if (desc.includes("discovery") || desc.includes("scanning") || desc.includes("t1046") || desc.includes("scan")) activeIds.add("T1046");
    if (desc.includes("lateral") || desc.includes("t1021") || desc.includes("remote services")) activeIds.add("T1021");
    if (desc.includes("exfiltration") || desc.includes("t1048") || desc.includes("exfil")) activeIds.add("T1048");
    if (title.includes("dns") || desc.includes("dns") || title.includes("beacon") || desc.includes("beacon")) activeIds.add("T1071");
    if (desc.includes("cron") || desc.includes("scheduled") || desc.includes("persistence")) activeIds.add("T1053");
  });

  return (
    <div className="bg-panel border border-panelBorder rounded-xl p-5 shadow-lg">
      <div className="border-b border-panelBorder/50 pb-2 mb-4">
        <h3 className="font-orbitron font-bold text-xs text-cyan tracking-wider">MITRE ATT&CK MATRIX</h3>
        <p className="text-[9px] text-textDim tracking-wider mt-0.5">REAL-TIME THREAT MAP</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {MITRE_TACTICS.map((tactic, idx) => (
          <div key={idx} className="flex flex-col space-y-2">
            <div className="bg-[#050A16] border border-panelBorder rounded p-2 text-center">
              <span className="font-orbitron text-[9px] font-black text-white block uppercase tracking-wider leading-tight">
                {tactic.name}
              </span>
            </div>

            <div className="flex-1 space-y-1.5">
              {tactic.techniques.map((tech, techIdx) => {
                const isActive = activeIds.has(tech.id);
                return (
                  <div
                    key={techIdx}
                    className={`border rounded p-2 transition-all duration-300 min-h-[56px] flex flex-col justify-between ${
                      isActive
                        ? "bg-red/10 border-red text-red shadow-[0_0_8px_rgba(255,53,94,0.15)] animate-pulse"
                        : "bg-[#060B18]/45 border-panelBorder/50 text-textDim"
                    }`}
                  >
                    <span className="font-orbitron text-[8px] font-bold block">{tech.id}</span>
                    <span className="text-[9px] font-medium leading-tight line-clamp-2 mt-0.5">
                      {tech.name}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
