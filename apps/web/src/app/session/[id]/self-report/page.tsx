"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export default function SelfReportPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [distress, setDistress] = useState(0);
  const [safety, setSafety] = useState(0);
  const [urgency, setUrgency] = useState(0);
  const [canContinue, setCanContinue] = useState(0);
  const [supportNeeds, setSupportNeeds] = useState<string[]>([]);
  
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const supportOptions = [
    { id: "counselling", label: "Counselling" },
    { id: "medical", label: "Medical Help" },
    { id: "legal", label: "Legal Advice" },
    { id: "police", label: "Police Intervention" },
    { id: "shelter", label: "Safe Shelter" },
    { id: "talk", label: "Just want to talk" },
  ];

  const handleSupportToggle = (id: string) => {
    setSupportNeeds((prev) => 
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const payload = {
        session_id: sessionId,
        q1_distress: distress,
        q2_safety: safety,
        q3_urgency: urgency,
        q4_can_continue: canContinue,
        support_needs: supportNeeds,
      };

      const res = await fetch("/api/v1/assessment/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          language: "en", // fallback, typically passed from caller state
          self_report: payload,
          // Sending empty audio/context just to trigger orchestrator for demo
          audio_base64: null,
          context: {
            incident_type: "unknown",
            ongoing_threat: safety >= 3,
            prior_case: false,
            vulnerability_factors: [],
            immediate_support_requested: urgency >= 3,
          }
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to submit assessment.");
      }

      setSuccess(true);
      setTimeout(() => {
        router.push("/");
      }, 3000);
    } catch (err: any) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="py-20 px-4 max-w-xl mx-auto text-center space-y-6">
        <div className="mx-auto w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400 mb-6">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-bold text-white">Thank You</h1>
        <p className="text-slate-400">
          Your responses have been recorded and securely transmitted to our response team. 
          A trained professional is reviewing your case right now.
        </p>
        <div className="pt-8">
          <div className="animate-pulse text-brand-400 font-mono text-sm">Redirecting...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8 max-w-2xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-3">
          <ShieldAlert className="text-brand-400 w-6 h-6" />
          How are you feeling right now?
        </h1>
        <p className="text-slate-400 text-sm">
          Please answer a few quick questions to help us prioritize your support.
          <br/><span className="font-mono text-xs text-slate-500">Session #{sessionId.slice(0, 8)}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 rounded-2xl glass-panel border border-border space-y-10">
        
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl">
            {error}
          </div>
        )}

        {/* Q1 */}
        <div className="space-y-4">
          <label className="text-sm font-semibold text-slate-200">Q1. How distressed do you feel?</label>
          <input
            type="range"
            min="0"
            max="4"
            step="1"
            value={distress}
            onChange={(e) => setDistress(parseInt(e.target.value))}
            className="w-full accent-brand-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span className={distress === 0 ? "text-brand-400 font-bold" : ""}>Calm</span>
            <span className={distress === 4 ? "text-rose-400 font-bold" : ""}>Extremely distressed</span>
          </div>
        </div>

        {/* Q2 */}
        <div className="space-y-4">
          <label className="text-sm font-semibold text-slate-200">Q2. Do you feel safe right now?</label>
          <input
            type="range"
            min="0"
            max="4"
            step="1"
            value={safety}
            onChange={(e) => setSafety(parseInt(e.target.value))}
            className="w-full accent-brand-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span className={safety === 0 ? "text-emerald-400 font-bold" : ""}>Very Safe</span>
            <span className={safety === 4 ? "text-rose-400 font-bold" : ""}>Immediate Danger</span>
          </div>
        </div>

        {/* Q3 */}
        <div className="space-y-4">
          <label className="text-sm font-semibold text-slate-200">Q3. Do you need help urgently?</label>
          <input
            type="range"
            min="0"
            max="4"
            step="1"
            value={urgency}
            onChange={(e) => setUrgency(parseInt(e.target.value))}
            className="w-full accent-brand-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span className={urgency === 0 ? "text-slate-300 font-bold" : ""}>Not at all</span>
            <span className={urgency === 4 ? "text-rose-400 font-bold" : ""}>Yes, right now</span>
          </div>
        </div>

        {/* Q4 */}
        <div className="space-y-4">
          <label className="text-sm font-semibold text-slate-200">Q4. Can you continue talking?</label>
          <input
            type="range"
            min="0"
            max="4"
            step="1"
            value={canContinue}
            onChange={(e) => setCanContinue(parseInt(e.target.value))}
            className="w-full accent-brand-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span className={canContinue === 0 ? "text-emerald-400 font-bold" : ""}>Yes easily</span>
            <span className={canContinue === 4 ? "text-rose-400 font-bold" : ""}>No I cannot</span>
          </div>
        </div>

        {/* Q5 - Multi select */}
        <div className="space-y-4">
          <label className="text-sm font-semibold text-slate-200">Q5. What kind of support do you think you need?</label>
          <div className="grid grid-cols-2 gap-3">
            {supportOptions.map((opt) => (
              <label
                key={opt.id}
                className={`flex items-center p-3 rounded-xl border cursor-pointer transition-colors ${
                  supportNeeds.includes(opt.id)
                    ? "bg-brand-500/10 border-brand-500 text-white"
                    : "bg-slate-900/50 border-slate-700 hover:border-slate-500 text-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={supportNeeds.includes(opt.id)}
                  onChange={() => handleSupportToggle(opt.id)}
                  className="mr-3 w-4 h-4 text-brand-500 bg-slate-800 border-slate-600 rounded focus:ring-brand-500"
                />
                <span className="text-sm font-medium">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-6 border-t border-border/60">
          <button
            id="submit-self-report-btn"
            type="submit"
            disabled={submitting}
            className="w-full py-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <span className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
            ) : null}
            {submitting ? "Submitting securely..." : "Submit and Continue →"}
          </button>
        </div>
      </form>
    </div>
  );
}
