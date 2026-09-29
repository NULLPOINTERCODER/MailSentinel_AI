import { CheckCircle2, Loader2, XCircle } from "lucide-react";

export default function StatusCard({ title, subtitle, loading, ok }) {
  const Icon = loading ? Loader2 : ok ? CheckCircle2 : XCircle;
  const color = loading ? "text-slate-400" : ok ? "text-emerald-400" : "text-rose-400";
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 flex items-center gap-4">
      <Icon className={`h-8 w-8 shrink-0 ${color} ${loading ? "animate-spin" : ""}`} />
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-sm text-slate-400">
          {loading ? "Checking..." : ok ? subtitle : "Not reachable"}
        </p>
      </div>
    </div>
  );
}
