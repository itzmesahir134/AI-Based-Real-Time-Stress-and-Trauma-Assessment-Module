"use client";

import { useEffect, useState } from "react";

const API = "http://localhost:8000";

interface ModelVersion {
  module: string;
  version: string;
  status: string;
  deployed_at: string;
}

export default function AdminModelsPage() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("saathi_token") : null;
    if (!token) { setError("Not authenticated"); setLoading(false); return; }

    fetch(`${API}/api/v1/admin/model-versions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setModels)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-300">
          Model Version Registry
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          All deployed inference modules and their current versions
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-400 py-20 justify-center">
          <span className="w-5 h-5 border-2 border-slate-600 border-t-brand-400 rounded-full animate-spin" />
          Loading registry…
        </div>
      )}

      {error && (
        <div className="rounded-2xl bg-red-500/10 border border-red-500/20 p-6 text-red-300">
          <p className="font-semibold">⚠ {error}</p>
          {error.includes("Not authenticated") && (
            <a href="/login" className="mt-2 inline-block text-sm text-brand-400 underline">Sign in →</a>
          )}
        </div>
      )}

      {models.length > 0 && (
        <div className="glass-panel rounded-2xl border border-border/70 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/60 bg-slate-800/40">
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Module</th>
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Version</th>
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Deployed At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {models.map((m) => (
                <tr key={m.module} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-brand-300 text-xs">{m.module}</td>
                  <td className="px-5 py-3.5 font-mono text-xs text-slate-200">{m.version}</td>
                  <td className="px-5 py-3.5">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      {m.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-400 font-mono">
                    {new Date(m.deployed_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
