"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch("/api/v1/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Invalid credentials");
      }

      const data = await res.json();
      localStorage.setItem("saathi_token", data.access_token);
      localStorage.setItem("saathi_role", data.role);
      localStorage.setItem("saathi_username", username);
      setRole(data.role);

      setTimeout(() => {
        const dest =
          data.role === "ADMIN" || data.role === "SUPERVISOR"
            ? "/analytics"
            : "/responder";
        router.push(dest);
      }, 800);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-400 shadow-xl glow-brand mb-4">
            <span className="text-2xl font-bold text-white">S</span>
          </div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-indigo-300">
            SAATHI-AI
          </h1>
          <p className="text-slate-400 text-sm mt-1">Secure Responder Access — SIH 2026</p>
        </div>

        {/* Card */}
        <div className="glass-panel rounded-2xl border border-border/80 shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Sign In</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-800/60 border border-slate-700/80 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/60 focus:border-brand-500/60 transition-all"
                placeholder="responder / admin / auditor"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-800/60 border border-slate-700/80 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/60 focus:border-brand-500/60 transition-all"
                placeholder="••••••••••••••••"
              />
            </div>

            {error && (
              <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-300 flex items-center gap-2">
                <span className="text-red-400">⚠</span>
                {error}
              </div>
            )}

            {role && (
              <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-300 flex items-center gap-2">
                <span className="animate-pulse">✓</span>
                Signed in as <strong>{role}</strong> — redirecting…
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-500 text-white font-semibold text-sm hover:from-brand-500 hover:to-indigo-400 transition-all shadow-lg hover:shadow-brand-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating…
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-6 pt-5 border-t border-slate-700/60">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3">Demo Credentials</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                { user: "admin", pwd: "saathi-admin-2026", label: "ADMIN", color: "text-rose-400" },
                { user: "responder", pwd: "saathi-resp-2026", label: "RESPONDER", color: "text-sky-400" },
                { user: "supervisor", pwd: "saathi-super-2026", label: "SUPERVISOR", color: "text-amber-400" },
                { user: "auditor", pwd: "saathi-audit-2026", label: "AUDITOR", color: "text-slate-400" },
              ].map(({ user, pwd, label, color }) => (
                <button
                  key={user}
                  type="button"
                  onClick={() => {
                    setUsername(user);
                    setPassword(pwd);
                  }}
                  className="text-left px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/40 hover:border-slate-600/60 transition-colors"
                >
                  <span className={`font-semibold ${color}`}>{label}</span>
                  <br />
                  <span className="text-slate-500">{user}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          SAATHI-AI is a decision-support tool for trained human responders.
        </p>
      </div>
    </div>
  );
}
