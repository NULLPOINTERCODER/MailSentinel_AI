import React from "react";
import { Link } from "react-router-dom";
import { Mail, MessageCircle, RefreshCw, ShieldCheck, Sparkles, ArrowRight, Zap, CheckCircle2 } from "lucide-react";
import StatusCard from "../components/StatusCard.jsx";
import Navbar from "../components/Navbar.jsx";
import useHealth from "../hooks/useHealth.js";
import { useAuth } from "../context/AuthContext.jsx";

const features = [
  {
    icon: Sparkles,
    title: "AI Triage Engine",
    text: "Groq-powered classification, importance scoring, and instant email summaries.",
  },
  {
    icon: Mail,
    title: "Gmail Integration",
    text: "Official OAuth 2.0. We never see or store your raw email account passwords.",
  },
  {
    icon: MessageCircle,
    title: "WhatsApp Cloud Alerts",
    text: "Only genuinely critical emails, interview calls, and deadlines reach your phone.",
  },
  {
    icon: ShieldCheck,
    title: "Multi-User Isolation",
    text: "Strict user_id scoping ensures your emails and preferences remain strictly private.",
  },
];

export default function Home() {
  const { loading, backend, db, refresh } = useHealth();
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 pb-20 flex-1">
        {/* Hero Section */}
        <section className="py-14 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur-md">
            <Zap className="h-3.5 w-3.5 text-indigo-400" />
            <span>Phase 2: Multi-User Authentication Live</span>
          </div>

          <h1 className="mt-6 text-4xl font-extrabold sm:text-6xl tracking-tight leading-tight">
            Your inbox, <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">understood.</span>
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-slate-400 text-base sm:text-lg">
            AI-powered email intelligence that finds what matters, extracts deadlines and actions,
            and notifies you directly on WhatsApp.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-500 shadow-xl shadow-indigo-600/30 transition-all hover:scale-105 active:scale-95"
              >
                <span>Go to Dashboard ({user?.email})</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-500 shadow-xl shadow-indigo-600/30 transition-all hover:scale-105 active:scale-95"
                >
                  <span>Get Started Free</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/login"
                  className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-6 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-800/80 hover:text-white transition-all"
                >
                  <span>Sign In</span>
                </Link>
              </>
            )}
          </div>
        </section>

        {/* Live Infrastructure Status */}
        <section className="mt-6">
          <div className="flex items-center justify-between mb-3 px-1">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              System Infrastructure Health
            </h2>
            <button
              onClick={refresh}
              className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              <RefreshCw className="h-3 w-3" /> Re-check
            </button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <StatusCard
              title="Backend (FastAPI)"
              subtitle={backend ? `${backend.service} is running` : "Port 8000"}
              loading={loading}
              ok={backend?.status === "ok"}
            />
            <StatusCard
              title="Database (MongoDB)"
              subtitle={db?.status === "ok" ? "Connected & responsive" : "mongodb://localhost:27017"}
              loading={loading}
              ok={db?.status === "ok"}
            />
          </div>
        </section>

        {/* Feature Highlights */}
        <section className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, title, text }) => (
            <div
              key={title}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm transition-all hover:border-slate-700"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Icon className="h-5 w-5" />
              </div>
              <p className="mt-3 font-semibold text-slate-200">{title}</p>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">{text}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
