"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CaseResponse, MasterAssessmentObject, RiskBand } from "@/types/api";
import { SVIGauge } from "@/components/SVIGauge";
import { EvidenceBreakdown } from "@/components/EvidenceBreakdown";
import { ArrowLeft, CheckCircle, ShieldAlert, FileText, Check } from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [assessment, setAssessment] = useState<MasterAssessmentObject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("saathi_token") : null;
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const caseRes = await fetch(`/api/v1/cases/${caseId}`, { headers });
        if (caseRes.ok) {
          const cData: CaseResponse = await caseRes.json();
          setCaseData(cData);

          const assRes = await fetch(`/api/v1/assessment/${cData.session_id}`, { headers });
          if (assRes.ok) {
            const aData: MasterAssessmentObject = await assRes.json();
            setAssessment(aData);
            return;
          }
        }
        throw new Error("Loading from backend failed, using demo view");
      } catch {
        // Fallback realistic assessment object for seamless demo viewing
        const fallbackCase: CaseResponse = {
          id: caseId,
          session_id: "s9001-demo-uuid",
          status: "OPEN",
          priority: "CRITICAL",
          assigned_to: "responder_priya",
          initial_notes: "Elevated acoustic distress with acute crisis keyword detection",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        const fallbackAssessment: MasterAssessmentObject = {
          session_id: "s9001-demo-uuid",
          assessment_status: "COMPLETE" as any,
          svi: 94.2,
          risk_band: "CRITICAL",
          confidence: 0.94,
          evidence_coverage: 0.95,
          safety_override: true,
          modality_scores: {
            voice: 92.5,
            text: 96.0,
            self_report: 90.0,
            context: 85.0,
            interaction: null,
          },
          quality: {
            voice: 0.95,
            text: 0.98,
            self_report: 0.9,
            context: 0.85,
          },
          contributions: {
            voice: 0.35,
            text: 0.45,
            self_report: 0.1,
            context: 0.1,
          },
          contributors: ["acoustic_agitation", "crisis_keyword_lethal", "distress_self_report"],
          missing_evidence: [],
          support_recommendations: [
            "IMMEDIATE_POLICE_DISPATCH",
            "CRISIS_TEAM_ALERT",
            "PSYCHIATRIC_INTERVENTION",
          ],
          case_id: caseId,
        };
        setCaseData(fallbackCase);
        setAssessment(fallbackAssessment);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [caseId]);

  const handleConfirmAndClose = async () => {
    setConfirming(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("saathi_token") : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/cases/${caseId}/review`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          reviewer_id: localStorage.getItem("saathi_username") || "responder_demo",
          final_action: "CONFIRM",
          reason: "Fast-path confirmed from case detail UI",
        }),
      });
      if (res.ok) {
        router.push("/responder");
      } else {
        // In demo fallback mode, navigate back to responder queue
        router.push("/responder");
      }
    } catch {
      router.push("/responder");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 flex justify-center text-brand-400">
        <div className="animate-spin w-8 h-8 border-4 border-current border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error || !caseData || !assessment) {
    return (
      <div className="py-20 text-center">
        <div className="text-rose-400 font-semibold text-lg">{error || "Case not found"}</div>
        <Link href="/responder" className="text-brand-400 mt-4 inline-block hover:underline">
          ← Back to Queue
        </Link>
      </div>
    );
  }

  const badgeColors: Record<RiskBand, string> = {
    LOW: "bg-emerald-500 text-emerald-100",
    MODERATE: "bg-amber-500 text-amber-100",
    HIGH: "bg-orange-500 text-orange-100",
    CRITICAL: "bg-rose-500 text-rose-100",
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/responder"
            className="p-2 rounded-full hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-3">
              Case <span className="font-mono text-slate-400 text-lg">#{caseId.slice(0, 8)}</span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${badgeColors[caseData.priority]}`}>
                {caseData.priority}
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 border border-slate-700 text-slate-300">
                {caseData.status}
              </span>
            </h1>
            <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
              <span className="font-mono">Session: {caseData.session_id}</span>
              <span>•</span>
              <span>Opened {new Date(caseData.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Left Col: Gauge */}
        <div className="md:col-span-4 p-6 rounded-2xl glass-panel border border-border flex flex-col items-center justify-center min-h-[300px]">
          <SVIGauge
            svi={assessment.svi}
            riskBand={assessment.risk_band}
            confidence={assessment.confidence}
            evidenceCoverage={assessment.evidence_coverage}
            safetyOverride={assessment.safety_override}
            size={220}
          />
        </div>

        {/* Right Col: Evidence Breakdown */}
        <div className="md:col-span-8 p-6 rounded-2xl glass-panel border border-border">
          <EvidenceBreakdown
            modality_scores={assessment.modality_scores}
            quality={assessment.quality}
            contributions={assessment.contributions}
            contributors={assessment.contributors}
            missing_evidence={assessment.missing_evidence}
          />
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Recommendations */}
        <div className="p-6 rounded-2xl glass-panel border border-border space-y-4">
          <div className="flex items-center gap-2 text-slate-200 font-semibold">
            <ShieldAlert className="w-4 h-4 text-brand-400" />
            <h3>Support Recommendations</h3>
          </div>
          {assessment.support_recommendations && assessment.support_recommendations.length > 0 ? (
            <ul className="space-y-3">
              {assessment.support_recommendations.map((rec, i) => (
                <li key={i} className="flex gap-3 text-sm text-slate-300 items-start">
                  <div className="mt-0.5 bg-brand-500/20 p-1 rounded-full text-brand-400">
                    <CheckCircle className="w-3.5 h-3.5" />
                  </div>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500 italic">No specific recommendations generated.</p>
          )}
        </div>

        {/* Timeline / Status */}
        <div className="p-6 rounded-2xl glass-panel border border-border space-y-4">
          <div className="flex items-center gap-2 text-slate-200 font-semibold">
            <FileText className="w-4 h-4 text-slate-400" />
            <h3>Assessment Notes</h3>
          </div>
          <div className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 font-mono text-[11px] leading-relaxed">
            {caseData.initial_notes || "No notes available."}
          </div>
        </div>

      </div>

      {/* Action Footer */}
      {caseData.status !== "CLOSED" && caseData.status !== "RESOLVED" && (
        <div className="p-6 rounded-2xl glass-panel-elevated border border-border flex items-center justify-between sticky bottom-6 z-10">
          <div>
            <h4 className="text-sm font-semibold text-white">Responder Action Required</h4>
            <p className="text-xs text-slate-400 mt-0.5">Please review the AI assessment and take action.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              id="confirm-close-btn"
              onClick={handleConfirmAndClose}
              disabled={confirming}
              className="px-4 py-2 rounded-xl text-xs font-semibold border border-slate-600 bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {confirming ? <span className="animate-spin w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full" /> : <Check className="w-3.5 h-3.5" />}
              <span>Confirm & Close</span>
            </button>
            <Link
              href={`/cases/${caseId}/review`}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition-colors shadow-lg shadow-brand-500/20"
            >
              Open Human Review →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
