"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CaseResponse, RiskBand } from "@/types/api";
import { ArrowLeft, ShieldAlert } from "lucide-react";

export default function HumanReviewPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [action, setAction] = useState<"CONFIRM" | "ESCALATE" | "DOWNGRADE" | "CLOSE">("CONFIRM");
  const [overridePriority, setOverridePriority] = useState<RiskBand>("LOW");
  const [reason, setReason] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const caseRes = await fetch(`/api/v1/cases/${caseId}`);
        if (!caseRes.ok) throw new Error("Failed to load case");
        const cData = await caseRes.json();
        setCaseData(cData);
        setOverridePriority(cData.priority);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [caseId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if ((action === "ESCALATE" || action === "DOWNGRADE") && !reason.trim()) {
      setError("Reason is required when escalating or downgrading a case.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        reviewer_id: localStorage.getItem("responder_id") || "responder_demo",
        final_action: action,
        modified_priority: action === "ESCALATE" || action === "DOWNGRADE" ? overridePriority : undefined,
        reason: reason.trim() || undefined,
      };

      const res = await fetch(`/api/v1/cases/${caseId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to submit review");
      }

      router.push(`/cases/${caseId}`);
    } catch (err: any) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-slate-400">Loading case details...</div>;
  }

  if (!caseData) {
    return <div className="py-20 text-center text-rose-400">Case not found</div>;
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href={`/cases/${caseId}`}
          className="p-2 rounded-full hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-white">Human Review</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">Case #{caseId}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 rounded-2xl glass-panel border border-border space-y-8">
        
        {/* Current State */}
        <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
          <div>
            <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Current Priority</div>
            <div className="text-lg font-bold text-white">{caseData.priority}</div>
          </div>
          <ShieldAlert className={`w-8 h-8 ${caseData.priority === "CRITICAL" ? "text-rose-500" : "text-brand-400"}`} />
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl">
            {error}
          </div>
        )}

        {/* Action Selection */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-slate-200">Your Action</label>
          <div className="space-y-2">
            {[
              { id: "CONFIRM", label: "Confirm", desc: "Accept the AI assessment as-is" },
              { id: "ESCALATE", label: "Escalate", desc: "Increase priority & route to emergency" },
              { id: "DOWNGRADE", label: "Downgrade", desc: "Reduce priority based on human context" },
              { id: "CLOSE", label: "Close Case", desc: "Case resolved, no further action needed" },
            ].map((opt) => (
              <label
                key={opt.id}
                className={`flex items-start p-3 rounded-xl border cursor-pointer transition-colors ${
                  action === opt.id
                    ? "bg-brand-500/10 border-brand-500 text-white"
                    : "bg-slate-900/30 border-slate-700 hover:border-slate-500 text-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="action"
                  value={opt.id}
                  checked={action === opt.id}
                  onChange={(e) => setAction(e.target.value as any)}
                  className="mt-1 mr-3 text-brand-500 bg-slate-800 border-slate-600 focus:ring-brand-500"
                />
                <div>
                  <div className="font-semibold text-sm">{opt.label}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Conditional Priority Selection */}
        {(action === "ESCALATE" || action === "DOWNGRADE") && (
          <div className="space-y-3 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
            <label className="text-sm font-semibold text-slate-200">Override Priority</label>
            <select
              value={overridePriority}
              onChange={(e) => setOverridePriority(e.target.value as RiskBand)}
              className="w-full p-2.5 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            >
              <option value="LOW">LOW</option>
              <option value="MODERATE">MODERATE</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        )}

        {/* Reason */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-slate-200">
            Reason / Notes {(action === "ESCALATE" || action === "DOWNGRADE") && <span className="text-rose-400">*</span>}
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Document why you are taking this action..."
            rows={4}
            className="w-full p-3 rounded-xl bg-slate-900/50 border border-slate-700 text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 resize-none"
          />
        </div>

        {/* Submit */}
        <div className="pt-4 flex justify-end gap-3 border-t border-border/60">
          <Link
            href={`/cases/${caseId}`}
            className="px-5 py-2.5 rounded-xl border border-slate-600 hover:bg-slate-800 text-slate-300 text-sm font-medium transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-bold transition-colors disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Review"}
          </button>
        </div>

      </form>
    </div>
  );
}
