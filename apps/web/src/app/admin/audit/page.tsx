"use client";

import { useEffect, useState } from "react";

const API = "http://localhost:8000";

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: string | null;
  timestamp: string | null;
}

interface AuditPage {
  page: number;
  limit: number;
  total: number;
  entries: AuditEntry[];
}

const ACTION_COLORS: Record<string, string> = {
  ASSESSMENT_COMPLETED: "text-brand-400 bg-brand-500/10 border-brand-500/20",
  M26_REVIEW_CLOSE: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  M26_REVIEW_ESCALATE: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  DEFAULT: "text-slate-400 bg-slate-700/40 border-slate-600/30",
};

function ActionBadge({ action }: { action: string }) {
  const cls = ACTION_COLORS[action] ?? ACTION_COLORS.DEFAULT;
  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {action}
    </span>
  );
}

export default function AdminAuditPage() {
  const [data, setData] = useState<AuditPage | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const LIMIT = 20;

  const fetchPage = (p: number) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("saathi_token") : null;
    if (!token) { setError("Not authenticated"); setLoading(false); return; }

    setLoading(true);
    const params = new URLSearchParams({ page: String(p), limit: String(LIMIT) });
    if (search) params.set("action", search);

    fetch(`${API}/api/v1/admin/audit-log?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: AuditPage) => { setData(d); setPage(p); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchPage(1); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 1;

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-300">
            Audit Log
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {data ? `${data.total} total entries` : "Loading…"} — immutable action trail
          </p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Filter by action…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate-800/60 border border-slate-700/80 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 transition-all"
          />
          <button
            onClick={() => fetchPage(1)}
            className="px-4 py-2 text-sm font-medium bg-brand-600/80 hover:bg-brand-500/80 text-white rounded-xl transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-red-500/10 border border-red-500/20 p-6 text-red-300 mb-6">
          <p className="font-semibold">⚠ {error}</p>
        </div>
      )}

      <div className="glass-panel rounded-2xl border border-border/70 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/60 bg-slate-800/40">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Timestamp</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">User</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Resource</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-slate-500">
                  <span className="inline-flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-slate-600 border-t-brand-400 rounded-full animate-spin" />
                    Loading…
                  </span>
                </td>
              </tr>
            ) : data?.entries.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-slate-500">No audit entries found</td>
              </tr>
            ) : (
              data?.entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">
                    {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3"><ActionBadge action={entry.action} /></td>
                  <td className="px-4 py-3 text-xs text-slate-300">{entry.user_id ?? "system"}</td>
                  <td className="px-4 py-3 text-xs text-slate-400 font-mono">
                    <span className="text-slate-500">{entry.resource_type}/</span>
                    {entry.resource_id ? entry.resource_id.slice(0, 8) + "…" : "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate" title={entry.details ?? ""}>
                    {entry.details ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => fetchPage(page - 1)}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800/60 border border-slate-700/60 text-slate-300 rounded-lg hover:bg-slate-700/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => fetchPage(page + 1)}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800/60 border border-slate-700/60 text-slate-300 rounded-lg hover:bg-slate-700/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
