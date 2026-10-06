"use client";

import { useEffect, useState } from "react";

const API = "";

interface AnalyticsSummary {
  total_sessions: number;
  total_cases: number;
  risk_band_distribution: Record<string, number>;
  safety_override_count: number;
  avg_svi: number;
  avg_confidence: number;
  avg_evidence_coverage: number;
  abstention_rate: number;
  cases_last_24h: number;
  cases_in_review: number;
}

const BAND_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-500",
  HIGH: "bg-orange-400",
  MODERATE: "bg-amber-400",
  LOW: "bg-emerald-400",
};
const BAND_TEXT: Record<string, string> = {
  CRITICAL: "text-red-400",
  HIGH: "text-orange-400",
  MODERATE: "text-amber-400",
  LOW: "text-emerald-400",
};

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="glass-panel rounded-2xl border border-border/70 p-5 flex flex-col gap-1">
      <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">{label}</span>
      <span className="text-3xl font-bold text-white">{value}</span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  );
}

function BarChart({ data, total }: { data: Record<string, number>; total: number }) {
  const bands = ["CRITICAL", "HIGH", "MODERATE", "LOW"];
  const maxVal = Math.max(...Object.values(data), 1);

  return (
    <div className="space-y-3">
      {bands.map((band) => {
        const count = data[band] ?? 0;
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        const barW = Math.round((count / maxVal) * 100);
        return (
          <div key={band} className="flex items-center gap-3">
            <span className={`w-20 text-xs font-semibold ${BAND_TEXT[band]}`}>{band}</span>
            <div className="flex-1 h-7 bg-slate-800/60 rounded-lg overflow-hidden">
              <div
                className={`h-full ${BAND_COLORS[band]} rounded-lg transition-all duration-700`}
                style={{ width: `${barW}%` }}
              />
            </div>
            <span className="w-8 text-right text-sm font-bold text-white">{count}</span>
            <span className="w-10 text-right text-xs text-slate-500">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("saathi_token") : null;
    if (!token) {
      setError("Not authenticated — please sign in.");
      setLoading(false);
      return;
    }

    fetch(`${API}/api/v1/analytics/summary`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setData(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-300">
            Analytics Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            System-wide SVI distributions, risk bands, and operational metrics
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
          Live
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-32 text-slate-400">
          <span className="w-6 h-6 border-2 border-slate-600 border-t-brand-400 rounded-full animate-spin mr-3" />
          Loading analytics…
        </div>
      )}

      {error && (
        <div className="rounded-2xl bg-red-500/10 border border-red-500/20 p-6 text-red-300">
          <p className="font-semibold mb-1">⚠ Error loading analytics</p>
          <p className="text-sm text-red-400">{error}</p>
          {error.includes("Not authenticated") && (
            <a href="/login" className="mt-3 inline-block text-sm text-brand-400 underline">
              Sign in →
            </a>
          )}
        </div>
      )}

      {data && (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total Sessions" value={data.total_sessions} />
            <StatCard label="Total Cases" value={data.total_cases} />
            <StatCard label="Last 24 Hours" value={data.cases_last_24h} sub="new cases" />
            <StatCard label="In Review" value={data.cases_in_review} sub="awaiting triage" />
            <StatCard label="Avg SVI" value={data.avg_svi.toFixed(1)} sub="0–100 scale" />
            <StatCard label="Avg Confidence" value={`${(data.avg_confidence * 100).toFixed(0)}%`} />
            <StatCard label="Safety Overrides" value={data.safety_override_count} sub="CRITICAL triggers" />
            <StatCard label="Abstention Rate" value={`${(data.abstention_rate * 100).toFixed(1)}%`} sub="voice modality" />
          </div>

          {/* Risk band chart */}
          <div className="glass-panel rounded-2xl border border-border/70 p-6 mb-6">
            <h2 className="text-lg font-semibold text-white mb-1">Risk Band Distribution</h2>
            <p className="text-xs text-slate-400 mb-5">
              {data.total_cases} total cases across all triage priorities
            </p>
            <BarChart data={data.risk_band_distribution} total={data.total_cases} />
          </div>

          {/* Evidence & confidence */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-panel rounded-2xl border border-border/70 p-6">
              <h2 className="text-base font-semibold text-white mb-4">Evidence Coverage</h2>
              <div className="flex flex-col gap-2">
                {[
                  { label: "Avg Evidence Coverage", val: data.avg_evidence_coverage },
                  { label: "Avg Model Confidence", val: data.avg_confidence },
                ].map(({ label, val }) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>{label}</span>
                      <span className="text-white font-semibold">{(val * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-brand-600 to-indigo-400 rounded-full transition-all duration-700"
                        style={{ width: `${(val * 100).toFixed(0)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel rounded-2xl border border-border/70 p-6">
              <h2 className="text-base font-semibold text-white mb-4">System Health</h2>
              <div className="space-y-3 text-sm">
                {[
                  { label: "Safety Override Rate", val: data.total_cases > 0 ? ((data.safety_override_count / data.total_cases) * 100).toFixed(1) : "0.0", unit: "%" },
                  { label: "Voice Abstention", val: (data.abstention_rate * 100).toFixed(1), unit: "%" },
                  { label: "Cases in Review", val: data.cases_in_review, unit: "" },
                ].map(({ label, val, unit }) => (
                  <div key={label} className="flex justify-between text-slate-300">
                    <span className="text-slate-400">{label}</span>
                    <span className="font-mono font-semibold text-white">{val}{unit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
