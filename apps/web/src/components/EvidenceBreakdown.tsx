import React from "react";
import { MasterAssessmentObject } from "@/types/api";

interface EvidenceBreakdownProps {
  modality_scores: MasterAssessmentObject["modality_scores"];
  quality: MasterAssessmentObject["quality"];
  contributions: MasterAssessmentObject["contributions"];
  contributors: string[];
  missing_evidence: string[];
}

export function EvidenceBreakdown({
  modality_scores,
  quality,
  contributions,
  contributors,
  missing_evidence,
}: EvidenceBreakdownProps) {
  
  const renderBar = (label: string, key: keyof MasterAssessmentObject["modality_scores"]) => {
    const score = modality_scores?.[key];
    const qual = quality?.[key];
    const contrib = contributions?.[key];
    
    // If the modality is missing or completely abstained
    if (score === undefined || score === null || qual === undefined || qual === 0) {
      return (
        <div className="flex items-center gap-4 py-2" key={key}>
          <div className="w-24 text-xs font-medium text-slate-500">{label}</div>
          <div className="flex-1 h-3 rounded-full border border-dashed border-slate-700 bg-slate-800/30"></div>
          <div className="w-20 text-right text-xs text-slate-500 italic">Abstained</div>
        </div>
      );
    }

    // Min opacity 0.3, max 1.0 based on quality
    const opacity = Math.max(0.3, qual);
    const fillPercent = Math.max(0, Math.min(100, score));
    
    return (
      <div className="flex flex-col gap-1 py-2" key={key}>
        <div className="flex items-center gap-4">
          <div className="w-24 text-xs font-medium text-slate-300">{label}</div>
          <div className="flex-1 h-3 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
            <div 
              className="h-full bg-brand-500 transition-all rounded-full" 
              style={{ width: `${fillPercent}%`, opacity }}
            />
          </div>
          <div className="w-20 flex items-center justify-end gap-2">
            <span className="text-xs font-bold text-white">{Math.round(score)}</span>
            <span className="text-[10px] text-slate-500 font-mono hidden sm:inline">pt</span>
          </div>
        </div>
        <div className="flex justify-between items-center pl-28 pr-20">
          <span className="text-[10px] text-slate-500">
            Quality: {Math.round(qual * 100)}%
          </span>
          {contrib !== undefined && (
            <span className="text-[10px] text-brand-400/80">
              +{Math.round(contrib)} to SVI
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-200">Modality Breakdown</h3>
        <p className="text-xs text-slate-400">Score composition and signal quality</p>
      </div>
      
      <div className="space-y-1">
        {renderBar("Voice (Acoustic)", "voice")}
        {renderBar("Text (Linguistic)", "text")}
        {renderBar("Self-Report", "self_report")}
        {renderBar("Context", "context")}
      </div>

      {(contributors.length > 0 || missing_evidence.length > 0) && (
        <div className="mt-6 pt-4 border-t border-border/60 space-y-4">
          {contributors.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-slate-400 mb-2">Key Distress Contributors</h4>
              <div className="flex flex-wrap gap-2">
                {contributors.map((c, i) => (
                  <span key={i} className="px-2 py-1 rounded border border-brand-500/30 bg-brand-500/10 text-brand-300 text-[10px] font-mono">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {missing_evidence.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-slate-400 mb-2">Missing Evidence Factors</h4>
              <div className="flex flex-wrap gap-2">
                {missing_evidence.map((c, i) => (
                  <span key={i} className="px-2 py-1 rounded border border-slate-700 bg-slate-800 text-slate-400 text-[10px] font-mono">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
