import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SAATHI-AI — Real-Time Stress & Trauma Assessment",
  description: "AI-assisted first-contact triage and support-routing layer for NHAA 14566",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-slate-100 flex flex-col">
        {/* Navigation Bar */}
        <header className="sticky top-0 z-50 glass-panel border-b border-border/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-2 group">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center font-bold text-white shadow-md glow-brand group-hover:scale-105 transition-transform">
                  S
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-indigo-300">
                    SAATHI-AI
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono tracking-wider -mt-1 uppercase">
                    NHAA 14566 Triage
                  </span>
                </div>
              </Link>
              <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-brand-500/10 text-brand-400 border border-brand-500/20">
                SIH 2026 • PS 26093
              </span>
            </div>

            <nav className="flex items-center gap-5">
              <Link
                href="/caller"
                className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
              >
                Caller Intake
              </Link>
              <Link
                href="/responder"
                className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
              >
                Triage Queue
              </Link>
              <Link
                href="/analytics"
                className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
              >
                Analytics
              </Link>
              <Link
                href="/admin"
                className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
              >
                Admin
              </Link>
              <div className="flex items-center gap-2 pl-4 border-l border-slate-700/60">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-slate-400">Online</span>
              </div>
              <Link
                href="/login"
                className="text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600/80 hover:bg-brand-500/80 text-white transition-colors"
              >
                Sign In
              </Link>
            </nav>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t border-border/60 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4">
            <p>
              SAATHI-AI is an AI-assisted decision support system for trained human responders. It does not provide autonomous medical or psychological diagnoses.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
