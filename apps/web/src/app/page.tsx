import Link from "next/link";
import { Mic, MessageSquare, PhoneCall, ShieldAlert, Activity, Users, ArrowRight } from "lucide-react";

export default function HomePage() {
  const channels = [
    {
      title: "Web Audio Intake",
      description: "Direct browser-based voice session with real-time Silero VAD and Whisper transcription.",
      icon: Mic,
      channel: "WEB_AUDIO",
      href: "/caller?channel=WEB_AUDIO",
      badge: "Primary Demo",
      color: "from-indigo-500/20 to-brand-500/10 border-indigo-500/30",
    },
    {
      title: "Telephony Voice Simulation",
      description: "Emulates an incoming 14566 PSTN phone call with acoustic feature extraction.",
      icon: PhoneCall,
      channel: "VOICE_CALL",
      href: "/caller?channel=VOICE_CALL",
      badge: "NHAA 14566",
      color: "from-blue-500/20 to-sky-500/10 border-blue-500/30",
    },
    {
      title: "Multilingual Chat",
      description: "Text-first distress assessment supporting Hindi, Tamil, Telugu, and English.",
      icon: MessageSquare,
      channel: "CHAT_TEXT",
      href: "/caller?channel=CHAT_TEXT",
      badge: "NLP Pipeline",
      color: "from-purple-500/20 to-pink-500/10 border-purple-500/30",
    },
  ];

  return (
    <div className="py-12 sm:py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-16">
      {/* Hero Section */}
      <div className="text-center space-y-6 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-brand-500/10 text-brand-400 border border-brand-500/20 shadow-sm">
          <Activity className="w-3.5 h-3.5 animate-pulse text-indigo-400" />
          <span>Multimodal Decision Support System</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          AI-Assisted First-Contact{" "}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
            Stress & Trauma Triage
          </span>
        </h1>
        <p className="text-lg text-slate-400 leading-relaxed">
          SAATHI-AI fuses acoustic biomarkers, speech transcripts, self-reported responses, and intake context into an explainable Support Vulnerability Index (SVI) to help responders prioritize urgent care.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/caller"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-all glow-brand hover:scale-105"
          >
            <span>Start Caller Intake</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/responder"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl glass-panel hover:bg-slate-800/80 text-slate-200 font-semibold text-sm transition-all border border-border"
          >
            <Users className="w-4 h-4 text-slate-400" />
            <span>Open Responder Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Intake Channel Cards */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span>Select Intake Channel</span>
          </h2>
          <span className="text-xs text-slate-400">Spec §0 & §19 Supported Inputs</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {channels.map((c) => {
            const Icon = c.icon;
            return (
              <Link
                key={c.channel}
                href={c.href}
                className={`relative group p-6 rounded-2xl glass-panel border ${c.color} hover:scale-[1.02] transition-all flex flex-col justify-between`}
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-brand-400 group-hover:text-white transition-colors">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800/90 text-slate-300 border border-slate-700">
                      {c.badge}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-brand-300 transition-colors">
                    {c.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-normal">
                    {c.description}
                  </p>
                </div>

                <div className="pt-6 flex items-center text-xs font-semibold text-brand-400 group-hover:translate-x-1 transition-transform">
                  <span>Launch Session</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Architecture Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4">
        <div className="p-4 rounded-xl glass-panel border border-border/80">
          <div className="text-brand-400 font-bold text-2xl">0 - 100</div>
          <div className="text-xs font-semibold text-slate-300 mt-1">SVI Fusion Engine</div>
          <div className="text-xs text-slate-500 mt-0.5">Continuous mathematical vulnerability scoring</div>
        </div>
        <div className="p-4 rounded-xl glass-panel border border-border/80">
          <div className="text-emerald-400 font-bold text-2xl">4 Bands</div>
          <div className="text-xs font-semibold text-slate-300 mt-1">Risk Stratification</div>
          <div className="text-xs text-slate-500 mt-0.5">LOW, MODERATE, HIGH, and CRITICAL</div>
        </div>
        <div className="p-4 rounded-xl glass-panel border border-border/80">
          <div className="text-amber-400 font-bold text-2xl">100%</div>
          <div className="text-xs font-semibold text-slate-300 mt-1">Explainable Breakdown</div>
          <div className="text-xs text-slate-500 mt-0.5">Acoustic, NLP & context contribution factors</div>
        </div>
        <div className="p-4 rounded-xl glass-panel border border-border/80">
          <div className="text-rose-400 font-bold text-2xl">Safety-First</div>
          <div className="text-xs font-semibold text-slate-300 mt-1">Crisis Overrides</div>
          <div className="text-xs text-slate-500 mt-0.5">Immediate escalation on self-harm / danger flags</div>
        </div>
      </div>
    </div>
  );
}
