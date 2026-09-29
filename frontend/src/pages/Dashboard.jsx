import React from "react";
import { Link } from "react-router-dom";
import {
  Mail,
  ShieldCheck,
  Phone,
  Calendar,
  CheckCircle2,
  Clock,
  Inbox,
  Sparkles,
  ArrowUpRight,
  UserCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Navbar from "../components/Navbar.jsx";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-6xl px-6 py-8 flex-1">
        {/* User Welcome Banner */}
        <div className="rounded-3xl border border-slate-800/80 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-slate-900/40 p-6 md:p-8 backdrop-blur-xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  <UserCheck className="h-3 w-3" /> Authenticated
                </span>
                <span className="text-xs text-slate-500">ID: {user?.id}</span>
              </div>
              <h1 className="mt-2 text-2xl md:text-3xl font-bold tracking-tight text-white">
                Welcome back, {user?.full_name || user?.email?.split("@")[0]} 👋
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                Your isolated multi-user workspace is secure and ready.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                disabled
                className="flex items-center gap-2 rounded-xl bg-slate-800/80 border border-slate-700 px-4 py-2.5 text-xs font-semibold text-slate-400 cursor-not-allowed"
                title="Available in Phase 3 (Google OAuth)"
              >
                <Mail className="h-4 w-4 text-indigo-400" />
                <span>Connect Gmail (Phase 3)</span>
              </button>
            </div>
          </div>
        </div>

        {/* User Profile / Status Grid */}
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {/* Card 1: Account Profile */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Account Details
              </span>
              <ShieldCheck className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="mt-4 space-y-2">
              <div>
                <p className="text-xs text-slate-500">Email</p>
                <p className="text-sm font-medium text-slate-200">{user?.email}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Name</p>
                <p className="text-sm font-medium text-slate-200">{user?.full_name || "Not provided"}</p>
              </div>
            </div>
          </div>

          {/* Card 2: WhatsApp Alerts */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                WhatsApp Destination
              </span>
              <Phone className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-4">
              <p className="text-xs text-slate-500">Configured Phone Number</p>
              <p className="text-sm font-medium text-slate-200 mt-1">
                {user?.whatsapp_number || "None configured (Can be set in Settings)"}
              </p>
              <span className="mt-3 inline-flex items-center gap-1 rounded-md bg-slate-800 px-2 py-0.5 text-[11px] text-slate-400">
                Phase 6 WhatsApp alerts target
              </span>
            </div>
          </div>

          {/* Card 3: Security & Session */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Session Security
              </span>
              <CheckCircle2 className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="mt-4 space-y-2">
              <div>
                <p className="text-xs text-slate-500">Password Encryption</p>
                <p className="text-sm font-medium text-emerald-400">bcrypt salted hash</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Authentication Scheme</p>
                <p className="text-sm font-medium text-slate-200">JWT Bearer (7-day validity)</p>
              </div>
            </div>
          </div>
        </div>

        {/* Roadmap Preview */}
        <section className="mt-10">
          <h2 className="text-lg font-bold text-white mb-4">Pipeline Roadmap</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <span className="text-xs font-semibold text-emerald-400">Phase 1 & 2</span>
              <p className="mt-1 font-semibold text-slate-200">Auth & Infrastructure</p>
              <p className="mt-1 text-xs text-slate-400">FastAPI, MongoDB, JWT & React</p>
              <span className="mt-3 inline-block text-[11px] font-bold text-emerald-400">✓ Completed</span>
            </div>

            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-4">
              <span className="text-xs font-semibold text-indigo-400">Phase 3</span>
              <p className="mt-1 font-semibold text-slate-200">Google OAuth / Gmail</p>
              <p className="mt-1 text-xs text-slate-400">Connect Gmail via official API</p>
              <span className="mt-3 inline-block text-[11px] font-semibold text-indigo-300">Next Phase →</span>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-4">
              <span className="text-xs font-semibold text-slate-400">Phase 4 & 5</span>
              <p className="mt-1 font-semibold text-slate-200">Email Ingestion & Groq AI</p>
              <p className="mt-1 text-xs text-slate-400">Classification, Deadlines, Summaries</p>
              <span className="mt-3 inline-block text-[11px] text-slate-500">Queued</span>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-4">
              <span className="text-xs font-semibold text-slate-400">Phase 6</span>
              <p className="mt-1 font-semibold text-slate-200">WhatsApp Cloud Alerts</p>
              <p className="mt-1 text-xs text-slate-400">Instant actionable notifications</p>
              <span className="mt-3 inline-block text-[11px] text-slate-500">Queued</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
