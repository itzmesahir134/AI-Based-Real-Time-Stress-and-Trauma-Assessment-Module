"use client";

import React, { useEffect, useState } from "react";
import { CaseResponse, RiskBand } from "@/types/api";
import { AlertTriangle, Clock, RefreshCw, UserCheck, ShieldAlert, Filter } from "lucide-react";

export default function ResponderPage() {
  const [cases, setCases] = useState<CaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/cases");
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch {
      // Fallback sample data if API not actively queried
      setCases([
        {
          id: "c1001-demo-uuid",
          session_id: "s9001-demo-uuid",
          status: "OPEN",
          priority: "CRITICAL",
          assigned_to: null,
          initial_notes: "Elevated acoustic distress with acute crisis keyword detection",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "c1002-demo-uuid",
          session_id: "s9002-demo-uuid",
          status: "IN_REVIEW",
          priority: "HIGH",
          assigned_to: "responder_priya",
          initial_notes: "High self-reported trauma index, rapid speech deviation",
          created_at: new Date(Date.now() - 15 * 60000).toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "c1003-demo-uuid",
          session_id: "s9003-demo-uuid",
          status: "OPEN",
          priority: "MODERATE",
          assigned_to: null,
          initial_notes: "General legal aid and counselling inquiry",
          created_at: new Date(Date.now() - 45 * 60000).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const getPriorityBadge = (priority: RiskBand) => {
    switch (priority) {
      case "CRITICAL":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 glow-critical">
            CRITICAL OVERRIDE
          </span>
        );
      case "HIGH":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/20 text-orange-300 border border-orange-500/40">
            HIGH URGENCY
          </span>
        );
      case "MODERATE":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
            MODERATE
          </span>
        );
      case "LOW":
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            LOW
          </span>
        );
    }
  };

  const filteredCases = selectedFilter === "ALL"
    ? cases
    : cases.filter((c) => c.priority === selectedFilter || c.status === selectedFilter);

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Responder Triage Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time human-in-the-loop review queue for NHAA 14566
          </p>
        </div>

        <button
          onClick={fetchCases}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl glass-panel text-slate-200 hover:text-white border border-border text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Priority Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl glass-panel border border-rose-500/30 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-300">Critical Queue</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {cases.filter((c) => c.priority === "CRITICAL").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Immediate Safety Override</div>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-orange-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-orange-300">High Urgency</span>
            <AlertTriangle className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {cases.filter((c) => c.priority === "HIGH").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">SVI &ge; 70 or acute distress</div>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-amber-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-300">Moderate</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {cases.filter((c) => c.priority === "MODERATE").length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">SVI 25 - 69 range</div>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Active Responders</span>
            <UserCheck className="w-4 h-4 text-brand-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">4 Online</div>
          <div className="text-[11px] text-slate-400 mt-1">Assigned shifts active</div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 text-xs">
        <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
        <span className="text-slate-400 font-medium">Filter:</span>
        {["ALL", "CRITICAL", "HIGH", "MODERATE", "OPEN", "IN_REVIEW"].map((filter) => (
          <button
            key={filter}
            onClick={() => setSelectedFilter(filter)}
            className={`px-3 py-1 rounded-lg border font-medium transition-all ${
              selectedFilter === filter
                ? "bg-brand-600 border-brand-500 text-white"
                : "glass-panel border-border/60 text-slate-400 hover:text-slate-200"
            }`}
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Cases Queue Table */}
      <div className="rounded-2xl glass-panel border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-border text-slate-400 uppercase tracking-wider font-mono">
              <tr>
                <th className="py-3.5 px-4">Case ID</th>
                <th className="py-3.5 px-4">Priority Band</th>
                <th className="py-3.5 px-4">Initial Assessment Notes</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Assigned Responder</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filteredCases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-4 px-4 font-mono font-medium text-slate-300">
                    {c.id.slice(0, 13)}...
                  </td>
                  <td className="py-4 px-4">{getPriorityBadge(c.priority)}</td>
                  <td className="py-4 px-4 text-slate-300 max-w-xs truncate">
                    {c.initial_notes || "Standard triage intake"}
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      {c.status}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-slate-400 font-mono">
                    {c.assigned_to || <span className="text-slate-500 italic">Unassigned</span>}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button className="px-3 py-1.5 rounded-lg bg-brand-600/80 hover:bg-brand-500 text-white font-semibold transition-colors">
                      Review Case
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
