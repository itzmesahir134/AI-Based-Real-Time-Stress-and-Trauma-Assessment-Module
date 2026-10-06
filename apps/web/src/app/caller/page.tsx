"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldCheck,
  Mic,
  MicOff,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Languages,
  UploadCloud,
  Activity,
  Radio,
} from "lucide-react";
import Link from "next/link";

export default function CallerPage() {
  const [selectedLanguage, setSelectedLanguage] = useState("hi");
  const [channel, setChannel] = useState("WEB_AUDIO");
  const [audioConsent, setAudioConsent] = useState(true);
  const [aiConsent, setAiConsent] = useState(true);
  const [sessionData, setSessionData] = useState<{ id: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live streaming states
  const [liveKitConfigured, setLiveKitConfigured] = useState<boolean | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [connectingLive, setConnectingLive] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [liveSviUpdate, setLiveSviUpdate] = useState<{ svi: number; risk_band: string } | null>(null);
  const roomRef = useRef<any>(null);

  // File upload fallback states
  const [uploadingAudio, setUploadingAudio] = useState(false);
  const [audioUploadSuccess, setAudioUploadSuccess] = useState<string | null>(null);

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

      // Check LiveKit token availability
      try {
        const tokenRes = await fetch(`/api/v1/livekit/token?session_id=${newSession.id}&identity=caller`);
        if (tokenRes.ok) {
          const tokenData = await tokenRes.json();
          setLiveKitConfigured(tokenData.token !== "LIVEKIT_NOT_CONFIGURED" && !!tokenData.url);
        }
      } catch {
        setLiveKitConfigured(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to initialize assessment session");
    } finally {
      setLoading(false);
    }
  };

  const handleGoLive = async () => {
    if (!sessionData) return;
    setConnectingLive(true);
    setStreamError(null);

    try {
      const tokenRes = await fetch(`/api/v1/livekit/token?session_id=${sessionData.id}&identity=caller`);
      const tokenData = await tokenRes.json();

      if (tokenData.token === "LIVEKIT_NOT_CONFIGURED" || !tokenData.url) {
        // Fallback demo streaming simulation
        setIsLive(true);
        setConnectingLive(false);
        return;
      }

      // Connect via LiveKit SDK
      const { Room } = await import("livekit-client");
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      await room.connect(tokenData.url, tokenData.token);
      await room.localParticipant.setMicrophoneEnabled(true);
      roomRef.current = room;
      setIsLive(true);
    } catch (err: any) {
      setStreamError(err.message || "Could not access microphone or connect to WebRTC room");
    } finally {
      setConnectingLive(false);
    }
  };

  const handleEndLive = async () => {
    if (roomRef.current) {
      try {
        await roomRef.current.disconnect();
      } catch {
        // ignore
      }
      roomRef.current = null;
    }
    setIsLive(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!sessionData || !e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploadingAudio(true);
    setAudioUploadSuccess(null);
    setError(null);

    try {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Data = (reader.result as string).split(",")[1];
          const res = await fetch("/api/v1/assessment/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionData.id,
              language: selectedLanguage,
              audio_base64: base64Data,
            }),
          });

          if (!res.ok) {
            throw new Error(`Audio processing error: ${res.statusText}`);
          }
          const data = await res.json();
          setAudioUploadSuccess(`Audio processed successfully: SVI ${data.svi} (${data.risk_band})`);
        } catch (err: any) {
          setError(err.message || "Failed to process audio file");
        } finally {
          setUploadingAudio(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (err: any) {
      setError(err.message || "Failed to read audio file");
      setUploadingAudio(false);
    }
  };

  // WebSocket listener for real-time SVI feedback during live streaming
  useEffect(() => {
    if (!sessionData || !isLive) return;
    let ws: WebSocket | null = null;
    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.hostname === "localhost" ? "localhost:8000" : window.location.host;
      ws = new WebSocket(`${protocol}//${host}/ws/svi/${sessionData.id}`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.svi !== undefined) {
            setLiveSviUpdate({ svi: data.svi, risk_band: data.risk_band });
          }
        } catch {
          // ignore
        }
      };
    } catch {
      // ws not available
    }

    return () => {
      if (ws) ws.close();
    };
  }, [sessionData, isLive]);

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
                  id="audio-consent-check"
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
                  id="ai-consent-check"
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
            id="start-session-btn"
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
        <div className="space-y-6">
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
                <span>Real-Time Engine:</span>
                <span className="font-semibold text-brand-400">
                  {liveKitConfigured ? "LiveKit WebRTC Ready" : "FastAPI Direct / Fallback Mode"}
                </span>
              </div>
            </div>

            {/* Live Audio Streaming Panel */}
            <div className="p-6 rounded-2xl glass-panel border border-brand-500/30 text-left space-y-4 max-w-lg mx-auto">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Radio className={`w-4 h-4 ${isLive ? "text-rose-400 animate-pulse" : "text-brand-400"}`} />
                  <span className="font-semibold text-white text-sm">Real-Time Audio Stream</span>
                </div>
                {isLive && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-rose-500 inline-block animate-ping" />
                    LIVE STREAMING
                  </span>
                )}
              </div>

              {isLive ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-border/80 flex flex-col items-center justify-center space-y-3">
                    <div className="flex items-center gap-1 h-8">
                      <span className="w-1 bg-brand-500 rounded-full animate-bounce h-4" />
                      <span className="w-1 bg-brand-400 rounded-full animate-bounce h-7" style={{ animationDelay: "150ms" }} />
                      <span className="w-1 bg-rose-500 rounded-full animate-bounce h-8" style={{ animationDelay: "300ms" }} />
                      <span className="w-1 bg-brand-400 rounded-full animate-bounce h-6" style={{ animationDelay: "450ms" }} />
                      <span className="w-1 bg-brand-500 rounded-full animate-bounce h-3" style={{ animationDelay: "600ms" }} />
                    </div>
                    <p className="text-xs text-slate-300 text-center font-medium">
                      Microphone active — 3s acoustic chunk analysis running
                    </p>
                    {liveSviUpdate && (
                      <div className="text-xs font-mono text-brand-300 bg-brand-950/50 px-3 py-1 rounded-lg border border-brand-500/30">
                        Provisional SVI: {liveSviUpdate.svi} ({liveSviUpdate.risk_band})
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={handleEndLive}
                    className="w-full py-3 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white font-semibold text-xs transition-all flex items-center justify-center gap-2"
                  >
                    <MicOff className="w-4 h-4" />
                    <span>End Live Stream</span>
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Stream your voice directly to SAATHI-AI to compute real-time stress and vulnerability indices during your call.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={handleGoLive}
                      disabled={connectingLive}
                      className="py-3 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-600/20"
                    >
                      <Mic className="w-4 h-4" />
                      <span>{connectingLive ? "Connecting..." : "Go Live (Mic)"}</span>
                    </button>

                    <label className="py-3 px-4 rounded-xl glass-panel text-slate-200 hover:text-white border border-border font-semibold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer text-center">
                      <UploadCloud className="w-4 h-4 text-slate-400" />
                      <span>{uploadingAudio ? "Processing Audio..." : "Upload WAV File"}</span>
                      <input
                        type="file"
                        accept="audio/wav,audio/mp3,audio/ogg"
                        onChange={handleFileUpload}
                        className="hidden"
                        disabled={uploadingAudio}
                      />
                    </label>
                  </div>

                  {audioUploadSuccess && (
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                      <span>{audioUploadSuccess}</span>
                    </div>
                  )}

                  {streamError && (
                    <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                      <span>{streamError}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Navigation links */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={() => {
                  handleEndLive();
                  setSessionData(null);
                }}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl glass-panel text-slate-300 text-xs font-medium hover:text-white border border-border transition-colors"
              >
                Start Another Session
              </button>

              <Link
                id="begin-self-assessment-link"
                href={`/session/${sessionData.id}/self-report`}
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition-all shadow-lg shadow-brand-500/20"
              >
                <span>Begin Self-Assessment</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
