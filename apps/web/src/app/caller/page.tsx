"use client";

import React, { useState } from "react";
import { ShieldCheck, Mic, ArrowRight, CheckCircle2, AlertCircle, Languages } from "lucide-react";

export default function CallerPage() {
  const [selectedLanguage, setSelectedLanguage] = useState("hi");
  const [channel, setChannel] = useState("WEB_AUDIO");
  const [audioConsent, setAudioConsent] = useState(true);
  const [aiConsent, setAiConsent] = useState(true);
  const [sessionData, setSessionData] = useState<{ id: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const languages = [
    { code: "hi", name: "हिन्दी (Hindi)" },
    { code: "en", name: "English" },
    { code: "ta", name: "தமிழ் (Tamil)" },
    { code: "te", name: "తెలుగు (Telugu)" },
  ];

  const handleStartSession = async () => {
    if (!audioConsent || !aiConsent) {
      setError("Please acknowledge both consent items to proceed with assessment.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Create Session
      const sessionRes = await fetch("/api/v1/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel: channel,
          language: selectedLanguage,
        }),
      });

      if (!sessionRes.ok) {
        throw new Error(`Failed to create session: ${sessionRes.statusText}`);
      }
      const newSession = await sessionRes.json();

      // 2. Record Audio Recording Consent
      await fetch("/api/v1/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: newSession.id,
          consent_type: "AUDIO_RECORDING",
          status: "GRANTED",
          notes: "Caller accepted audio recording consent in portal",
        }),
      });

      // 3. Record AI Assessment Consent
      await fetch("/api/v1/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: newSession.id,
          consent_type: "AI_ASSESSMENT",
          status: "GRANTED",
          notes: "Caller accepted AI decision-support evaluation",
        }),
      });

      setSessionData(newSession);
    } catch (err: any) {
      setError(err.message || "Failed to initialize assessment session");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-white">Caller Intake & Consent</h1>
        <p className="text-slate-400 text-sm">
          National Helpline for Assault and Abuse (14566) • First-contact intake portal
        </p>
      </div>

      {!sessionData ? (
        <div className="space-y-6">
          {/* Language Selection */}
          <div className="p-6 rounded-2xl glass-panel border border-border space-y-4">
            <div className="flex items-center gap-2 text-white font-semibold text-sm">
              <Languages className="w-4 h-4 text-brand-400" />
              <span>Select Your Preferred Language / अपनी भाषा चुनें</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => setSelectedLanguage(lang.code)}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all text-left ${
                    selectedLanguage === lang.code
                      ? "border-brand-500 bg-brand-500/10 text-white shadow-sm"
                      : "border-border/60 hover:border-slate-600 bg-slate-900/50 text-slate-300"
                  }`}
                >
                  {lang.name}
                </button>
              ))}
            </div>
          </div>

          {/* Consent Section (Spec §38) */}
          <div className="p-6 rounded-2xl glass-panel border border-border space-y-5">
            <div className="flex items-center gap-2 text-white font-semibold text-sm">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Privacy & Assessment Consent (Spec §38)</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Before beginning your conversation, please review the intake policies. SAATHI-AI uses privacy-preserving acoustic analysis to assist our human responders in providing timely support.
            </p>

            <div className="space-y-3 pt-2">
              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-border/60 cursor-pointer hover:bg-slate-800/50 transition-colors">
                <input
                  type="checkbox"
                  checked={audioConsent}
                  onChange={(e) => setAudioConsent(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-brand-600 focus:ring-brand-500"
                />
                <div className="text-xs space-y-1">
                  <div className="font-semibold text-slate-200">Audio Stream Processing Consent</div>
                  <div className="text-slate-400">
                    I consent to real-time audio transmission for speech transcription and acoustic tone evaluation.
                  </div>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-border/60 cursor-pointer hover:bg-slate-800/50 transition-colors">
                <input
                  type="checkbox"
                  checked={aiConsent}
                  onChange={(e) => setAiConsent(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-brand-600 focus:ring-brand-500"
                />
                <div className="text-xs space-y-1">
                  <div className="font-semibold text-slate-200">AI-Assisted Triage Acknowledgement</div>
                  <div className="text-slate-400">
                    I understand this system assists trained human responders to prioritize urgent support and does not provide a medical diagnosis.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Action Button */}
          <button
            type="button"
            onClick={handleStartSession}
            disabled={loading}
            className="w-full py-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 glow-brand disabled:opacity-50"
          >
            {loading ? (
              <span>Initializing Secure Session...</span>
            ) : (
              <>
                <Mic className="w-4 h-4" />
                <span>Begin Assessment Session</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </div>
      ) : (
        /* Session Initialized Screen */
        <div className="p-8 rounded-2xl glass-panel-elevated border border-emerald-500/30 space-y-6 text-center">
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Session Initialized</h2>
            <p className="text-xs font-mono text-slate-400">Session ID: {sessionData.id}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-border text-left text-xs space-y-2 max-w-md mx-auto">
            <div className="flex justify-between text-slate-400">
              <span>Channel:</span>
              <span className="font-semibold text-slate-200">{channel}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Language:</span>
              <span className="font-semibold text-slate-200">{selectedLanguage.toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Consent Status:</span>
              <span className="font-semibold text-emerald-400">RECORDED (Granted)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>LiveKit Audio:</span>
              <span className="font-semibold text-brand-400">Ready for Phase 2 Pipeline</span>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={() => setSessionData(null)}
              className="px-6 py-2.5 rounded-xl glass-panel text-slate-300 text-xs font-medium hover:text-white border border-border transition-colors"
            >
              Start Another Session
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
