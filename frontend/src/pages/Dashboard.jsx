import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Mail,
  ShieldCheck,
  Phone,
  CheckCircle2,
  Trash2,
  RefreshCw,
  Plus,
  ExternalLink,
  UserCheck,
  Inbox,
  Sparkles,
  Loader2,
  AlertCircle,
  Clock,
  Zap,
  Flame,
  Bell,
  ArrowRight,
  TrendingUp,
  Briefcase,
  Layers,
  Send,
  Sliders,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Navbar from "../components/Navbar.jsx";
import {
  getConnectedAccounts,
  disconnectAccount,
  testAccountConnection,
  getEmailStats,
  getEmails,
  syncUserEmails,
  batchTriageWithAI,
  sendEmailWhatsAppAlert,
} from "../services/api.js";

const categoryPillColors = {
  INTERVIEW: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  ASSESSMENT: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
  OFFER: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  SECURITY: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  RECRUITER: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  JOB_APPLICATION: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  MEETING: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  FINANCE: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  GENERAL: "bg-slate-800 text-slate-300 border-slate-700",
};

export default function Dashboard() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [stats, setStats] = useState({
    total_emails: 0,
    unread_emails: 0,
    potentially_important: 0,
    high_importance_count: 0,
    notifications_sent: 0,
    active_deadlines_count: 0,
    ai_triaged_count: 0,
    category_breakdown: {},
  });
  const [recentImportant, setRecentImportant] = useState([]);
  const [upcomingDeadlines, setUpcomingDeadlines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [triaging, setTriaging] = useState(false);
  const [testingId, setTestingId] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [bannerMessage, setBannerMessage] = useState(null);
  const [actionError, setActionError] = useState("");

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setActionError("");

      const [accountsRes, statsRes, importantEmailsRes, allEmailsRes] = await Promise.allSettled([
        getConnectedAccounts(),
        getEmailStats(),
        getEmails({ only_important: true, limit: 6 }),
        getEmails({ limit: 50 }),
      ]);

      if (accountsRes.status === "fulfilled") setAccounts(accountsRes.value);
      if (statsRes.status === "fulfilled") setStats(statsRes.value);
      if (importantEmailsRes.status === "fulfilled") setRecentImportant(importantEmailsRes.value);

      // Extract emails with deadlines
      if (allEmailsRes.status === "fulfilled") {
        const withDeadlines = allEmailsRes.value.filter(
          (e) => e.deadline && e.deadline.trim() !== "" && e.deadline.toLowerCase() !== "null"
        );
        setUpcomingDeadlines(withDeadlines.slice(0, 5));
      }
    } catch (err) {
      setActionError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleSyncInboxes = async () => {
    setSyncing(true);
    setBannerMessage(null);
    try {
      const res = await syncUserEmails(25);
      setBannerMessage({
        type: "success",
        text: `Sync completed: ${res.new_emails_saved} new emails ingested (${res.potentially_important} flagged for AI triage).`,
      });
      await loadDashboardData();
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: err.response?.data?.detail || "Inbox synchronization failed.",
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleBatchAITriage = async () => {
    setTriaging(true);
    setBannerMessage(null);
    try {
      const res = await batchTriageWithAI(10);
      setBannerMessage({
        type: "success",
        text: `Groq AI triaged ${res.length} pending important emails.`,
      });
      await loadDashboardData();
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: err.response?.data?.detail || "AI Batch Triage failed.",
      });
    } finally {
      setTriaging(false);
    }
  };

  const handleSendWhatsAppAlert = async (emailId) => {
    try {
      const res = await sendEmailWhatsAppAlert(emailId, true);
      if (res.status === "SENT") {
        setBannerMessage({
          type: "success",
          text: res.simulated
            ? "WhatsApp Alert simulated in Dev Mode (logged to server)."
            : "WhatsApp Alert successfully dispatched to your phone!",
        });
        loadDashboardData();
      } else {
        setBannerMessage({
          type: "warning",
          text: `WhatsApp alert: ${res.reason || res.error || "Processed"}`,
        });
      }
    } catch (err) {
      setBannerMessage({
        type: "error",
        text: err.response?.data?.detail || "Failed to trigger WhatsApp alert.",
      });
    }
  };

  const handleDisconnect = async (accountId, email) => {
    if (!window.confirm(`Are you sure you want to disconnect ${email}?`)) return;
    try {
      await disconnectAccount(accountId);
      setAccounts((prev) => prev.filter((a) => a.id !== accountId));
      if (testResult?.id === accountId) setTestResult(null);
    } catch {
      alert("Failed to disconnect account.");
    }
  };

  const handleTestConnection = async (accountId) => {
    setTestingId(accountId);
    setActionError("");
    try {
      const result = await testAccountConnection(accountId);
      setTestResult({ id: accountId, ...result });
    } catch (err) {
      const msg = err.response?.data?.detail || "Gmail API connection test failed.";
      setActionError(msg);
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-6xl px-6 py-8 flex-1 space-y-8">
        {/* Welcome Header */}
        <div className="rounded-3xl border border-slate-800/80 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-slate-900/40 p-6 md:p-8 backdrop-blur-xl shadow-2xl">
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  <UserCheck className="h-3 w-3" /> Sentinel Active
                </span>
                <span className="text-xs text-slate-400">ID: {user?.id}</span>
              </div>
              <h1 className="mt-2 text-2xl md:text-3xl font-bold tracking-tight text-white">
                Intelligence Dashboard
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                Real-time email intelligence, deadline tracking, and automated WhatsApp alert sentinel.
              </p>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleSyncInboxes}
                disabled={syncing || accounts.length === 0}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 hover:text-white disabled:opacity-50 transition-all shadow-md"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin text-indigo-400" : ""}`} />
                <span>{syncing ? "Syncing..." : "Sync Inboxes"}</span>
              </button>

              <button
                onClick={handleBatchAITriage}
                disabled={triaging}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 shadow-lg shadow-indigo-600/25 transition-all"
              >
                <Sparkles className={`h-3.5 w-3.5 ${triaging ? "animate-spin" : ""}`} />
                <span>{triaging ? "Triaging..." : "Run AI Triage"}</span>
              </button>

              <Link
                to="/settings"
                className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 transition-all"
              >
                <Sliders className="h-3.5 w-3.5" />
                <span>WhatsApp Settings</span>
              </Link>
            </div>
          </div>
        </div>

        {bannerMessage && (
          <div
            className={`flex items-center gap-3 rounded-2xl border p-4 text-sm ${
              bannerMessage.type === "success"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : bannerMessage.type === "warning"
                ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
                : "border-rose-500/30 bg-rose-500/10 text-rose-300"
            }`}
          >
            {bannerMessage.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="h-5 w-5 flex-shrink-0 text-amber-400" />
            )}
            <span>{bannerMessage.text}</span>
          </div>
        )}

        {/* 1. SaaS KPI Metric Cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Total Ingested
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-indigo-400">
                <Mail className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-3xl font-extrabold text-white">{stats.total_emails}</p>
            <p className="mt-1 text-[11px] text-slate-500">Across all connected accounts</p>
          </div>

          <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/30 to-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                High Priority (≥ 80)
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-amber-400">
                <Flame className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-3xl font-extrabold text-indigo-200">
              {stats.high_importance_count || stats.potentially_important}
            </p>
            <p className="mt-1 text-[11px] text-indigo-400/80">Trigger WhatsApp candidates</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Unread Inboxes
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-300">
                <Inbox className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-3xl font-extrabold text-white">{stats.unread_emails}</p>
            <p className="mt-1 text-[11px] text-slate-500">Unread raw messages</p>
          </div>

          <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/20 to-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-300">
                Active Deadlines
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
                <Clock className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-3xl font-extrabold text-amber-200">{stats.active_deadlines_count}</p>
            <p className="mt-1 text-[11px] text-amber-400/80">Extracted action dates</p>
          </div>

          <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 to-slate-900/40 p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-300">
                WhatsApp Alerts
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                <Bell className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-3xl font-extrabold text-emerald-200">{stats.notifications_sent}</p>
            <p className="mt-1 text-[11px] text-emerald-400/80">Dispatched & logged</p>
          </div>
        </section>

        {/* 2. Main Content Grid (Upcoming Deadlines & Category Breakdown) */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Upcoming Deadlines Widget */}
          <div className="lg:col-span-2 rounded-3xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Clock className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">Upcoming Deadlines & Actions</h2>
                  <p className="text-xs text-slate-400">Extracted timelines requiring candidate or user action</p>
                </div>
              </div>
              <Link
                to="/emails?only_important=true"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="mt-5 space-y-3">
              {upcomingDeadlines.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  No upcoming deadlines detected in triaged emails yet.
                </div>
              ) : (
                upcomingDeadlines.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 transition-all hover:border-slate-700"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-sm text-white">{item.sender_name}</span>
                        {item.category && (
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${
                              categoryPillColors[item.category] || "bg-slate-800 text-slate-300"
                            }`}
                          >
                            {item.category}
                          </span>
                        )}
                        <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-300 border border-amber-500/20">
                          Due: {item.deadline}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 font-medium">{item.subject}</p>
                      {item.action && (
                        <p className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
                          <Zap className="h-3 w-3" /> {item.action}
                        </p>
                      )}
                    </div>

                    <Link
                      to="/emails"
                      className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 shrink-0"
                    >
                      <span>Open</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Category Breakdown Card */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2.5 border-b border-slate-800 pb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Layers className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">Category Distribution</h2>
                  <p className="text-xs text-slate-400">AI email categorization breakdown</p>
                </div>
              </div>

              <div className="mt-5 space-y-3">
                {Object.keys(stats.category_breakdown || {}).length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-500">
                    No categories classified yet. Run AI Triage to categorize.
                  </div>
                ) : (
                  Object.entries(stats.category_breakdown).map(([cat, count]) => (
                    <div key={cat} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-md px-2 py-0.5 font-bold text-[10px] border ${
                            categoryPillColors[cat] || "bg-slate-800 text-slate-300 border-slate-700"
                          }`}
                        >
                          {cat}
                        </span>
                      </div>
                      <span className="font-semibold text-slate-300">{count} emails</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500">
              Categories are managed and weighted in your settings.
            </div>
          </div>
        </div>

        {/* 3. Recent Important Emails Intelligence Feed */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Recent Important Emails Feed</h2>
                <p className="text-xs text-slate-400">AI triaged messages with high importance scores</p>
              </div>
            </div>
            <Link
              to="/emails"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              Open Full Inbox Feed <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {recentImportant.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No important emails found. Connect inboxes and sync to ingest new messages.
              </div>
            ) : (
              recentImportant.map((email) => (
                <div
                  key={email.id}
                  className="flex flex-col gap-3 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 transition-all hover:border-slate-700 sm:flex-row sm:items-start sm:justify-between"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm text-white">{email.sender_name}</span>
                      <span className="text-xs text-slate-500">&lt;{email.sender_email}&gt;</span>
                      {email.category && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${
                            categoryPillColors[email.category] || "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {email.category}
                        </span>
                      )}
                      <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                        Score: {email.final_importance || email.rule_score}/100
                      </span>
                    </div>

                    <h4 className="text-xs font-medium text-slate-200">{email.subject}</h4>

                    {email.summary && (
                      <p className="text-xs text-slate-400 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/60 leading-relaxed">
                        {email.summary}
                      </p>
                    )}
                  </div>

                  <div className="flex sm:flex-col items-end justify-between sm:justify-start gap-2 shrink-0">
                    <button
                      onClick={() => handleSendWhatsAppAlert(email.id)}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 transition-all"
                    >
                      <Send className="h-3 w-3" />
                      <span>WhatsApp Alert</span>
                    </button>
                    <span className="text-[11px] text-slate-500">{email.received_at?.split(" ").slice(0, 4).join(" ")}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* 4. Connected Inboxes Status */}
        <section className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Connected Gmail Accounts</h2>
              <p className="text-xs text-slate-400">Authenticated Google OAuth 2.0 Inboxes</p>
            </div>
            <Link
              to="/connect-email"
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/20"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Account</span>
            </Link>
          </div>

          {accounts.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-400">
              No Gmail accounts connected yet.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
                      <Mail className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-200">{acc.email}</p>
                      <span className="text-[10px] uppercase text-emerald-400 font-semibold">Active Monitoring</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTestConnection(acc.id)}
                      disabled={testingId === acc.id}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      {testingId === acc.id ? "Testing..." : "Test"}
                    </button>
                    <button
                      onClick={() => handleDisconnect(acc.id, acc.email)}
                      className="text-xs text-rose-400 hover:text-rose-300 font-medium ml-2"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
