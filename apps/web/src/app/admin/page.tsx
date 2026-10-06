import Link from "next/link";
import { Cpu, ShieldCheck, Database, ArrowRight } from "lucide-react";

export default function AdminPage() {
  const cards = [
    {
      title: "Model Version Registry",
      description: "Inspect active inference models, deployed checkpoints, architecture versions, and operational health.",
      icon: Cpu,
      href: "/admin/models",
      badge: "Inference Engine",
      color: "from-indigo-500/20 to-brand-500/10 border-indigo-500/30",
    },
    {
      title: "Immutable Audit Log",
      description: "Full regulatory audit trail for triage assessments, human responder overrides, and system activities.",
      icon: ShieldCheck,
      href: "/admin/audit",
      badge: "Compliance & Safety",
      color: "from-purple-500/20 to-pink-500/10 border-purple-500/30",
    },
  ];

  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-brand-500/10 text-brand-400 border border-brand-500/20 mb-3">
          <Database className="w-3.5 h-3.5" />
          <span>System Administration & Governance</span>
        </div>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-300">
          Admin Portal
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Manage machine learning inference pipelines, audit trail compliance, and system configurations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Link
              key={c.href}
              href={c.href}
              className={`p-6 rounded-2xl glass-panel border ${c.color} hover:scale-[1.02] transition-all flex flex-col justify-between group`}
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
                <h2 className="text-xl font-bold text-white group-hover:text-brand-300 transition-colors">
                  {c.title}
                </h2>
                <p className="text-sm text-slate-400 leading-normal">
                  {c.description}
                </p>
              </div>

              <div className="pt-6 flex items-center text-xs font-semibold text-brand-400 group-hover:translate-x-1 transition-transform">
                <span>Open Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
