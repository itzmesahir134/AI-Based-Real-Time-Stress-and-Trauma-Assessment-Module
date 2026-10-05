import React from "react";
import { RiskBand } from "@/types/api";
import { AlertTriangle } from "lucide-react";

interface SVIGaugeProps {
  svi: number;
  riskBand: RiskBand;
  confidence: number;
  evidenceCoverage: number;
  safetyOverride: boolean;
  size?: number;
}

export function SVIGauge({
  svi,
  riskBand,
  confidence,
  evidenceCoverage,
  safetyOverride,
  size = 220,
}: SVIGaugeProps) {
  // SVI ranges from 0 to 100. Calculate degrees (0 to 360).
  const degrees = (Math.max(0, Math.min(100, svi)) / 100) * 360;

  let color = "#10b981"; // emerald-500 (LOW)
  let shadowClass = "";
  let textClass = "text-emerald-400";
  let bgClass = "bg-emerald-500/10";
  let borderClass = "border-emerald-500/20";

  if (riskBand === "CRITICAL") {
    color = "#ef4444"; // rose-500
    shadowClass = "glow-critical";
    textClass = "text-rose-400";
    bgClass = "bg-rose-500/10";
    borderClass = "border-rose-500/20";
  } else if (riskBand === "HIGH") {
    color = "#f97316"; // orange-500
    shadowClass = "glow-high";
    textClass = "text-orange-400";
    bgClass = "bg-orange-500/10";
    borderClass = "border-orange-500/20";
  } else if (riskBand === "MODERATE") {
    color = "#f59e0b"; // amber-500
    textClass = "text-amber-400";
    bgClass = "bg-amber-500/10";
    borderClass = "border-amber-500/20";
  }

  // The conic gradient creates the ring
  const gradient = `conic-gradient(${color} ${degrees}deg, rgba(255, 255, 255, 0.05) ${degrees}deg)`;

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      {/* Outer container for the gauge */}
      <div
        className={`relative rounded-full flex items-center justify-center ${shadowClass}`}
        style={{ width: size, height: size, background: gradient }}
      >
        {/* Inner mask to create the ring effect */}
        <div
          className="absolute rounded-full flex flex-col items-center justify-center"
          style={{ width: size - 24, height: size - 24, backgroundColor: "var(--background)" }}
        >
          <span className={`text-xs font-bold tracking-widest uppercase mb-1 ${textClass}`}>
            {riskBand}
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-5xl font-extrabold text-white tracking-tight">{Math.round(svi)}</span>
          </div>
          <span className="text-xs text-slate-400 mt-1 uppercase font-mono">SVI Score</span>
          
          <div className="flex items-center gap-3 mt-3 text-[10px] text-slate-400 font-mono">
            <div className="flex flex-col items-center">
              <span className="text-white font-medium">{Math.round(confidence * 100)}%</span>
              <span>CONF</span>
            </div>
            <div className="w-px h-6 bg-border/80"></div>
            <div className="flex flex-col items-center">
              <span className="text-white font-medium">{Math.round(evidenceCoverage * 100)}%</span>
              <span>COV</span>
            </div>
          </div>
        </div>
      </div>

      {safetyOverride && (
        <div className={`mt-2 flex items-center gap-1.5 px-3 py-1 rounded-full border border-rose-500/40 bg-rose-500/10 text-rose-400 text-xs font-bold animate-pulse shadow-[0_0_12px_rgba(239,68,68,0.3)]`}>
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>SAFETY OVERRIDE</span>
        </div>
      )}
    </div>
  );
}
