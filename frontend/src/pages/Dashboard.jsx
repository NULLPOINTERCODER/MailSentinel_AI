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
  Layers,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Navbar from "../components/Navbar.jsx";
import { getConnectedAccounts, disconnectAccount, testAccountConnection } from "../services/api.js";

export default function Dashboard() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [testingId, setTestingId] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [actionError, setActionError] = useState("");

  const loadAccounts = async () => {
    setLoadingAccounts(true);
    setActionError("");
    try {
      const data = await getConnectedAccounts();
      setAccounts(data);
    } catch (err) {
      setActionError("Failed to fetch connected accounts.");
    } finally {
      setLoadingAccounts(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

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
      const msg =
        err.response?.data?.detail || "Gmail API connection test failed. Check Google OAuth tokens.";
      setActionError(msg);
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-6xl px-6 py-8 flex-1 space-y-8">
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
                Your AI email sentinel intelligence dashboard.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/connect-email"
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/25 transition-all"
              >
                <Plus className="h-4 w-4" />
                <span>Connect Email</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Section 1: Connected Inboxes */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Connected Inboxes</h2>
              <p className="text-xs text-slate-400">
                Email inboxes monitored for important deadlines and AI summaries.
              </p>
            </div>
            <button
              onClick={loadAccounts}
              className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>

          {actionError && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

          {loadingAccounts ? (
            <div className="flex items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/30 p-8">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
            </div>
          ) : accounts.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
                <Mail className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-base font-semibold text-white">No Email Accounts Connected</h3>
              <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
                Connect your Gmail account to enable AI email classification, action detection, and WhatsApp alerts.
              </p>
              <Link
                to="/connect-email"
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all shadow-md shadow-indigo-600/20"
              >
                <Plus className="h-3.5 w-3.5" /> Connect Gmail Now
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm transition-all hover:border-slate-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
                        <Mail className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm text-slate-100">{acc.email}</p>
                        <span className="text-[11px] uppercase tracking-wider text-slate-500">
                          {acc.provider} • OAuth 2.0
                        </span>
                      </div>
                    </div>
                    <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/20">
                      Active
                    </span>
                  </div>

                  {testResult && testResult.id === acc.id && (
                    <div className="mt-4 rounded-xl bg-slate-950/80 border border-slate-800 p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Total Messages:</span>
                        <span className="font-mono text-white">{testResult.messages_total}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Total Threads:</span>
                        <span className="font-mono text-white">{testResult.threads_total}</span>
                      </div>
                      <p className="text-[11px] text-emerald-400 pt-1">✓ Gmail API live & responsive</p>
                    </div>
                  )}

                  <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/60">
                    <button
                      onClick={() => handleTestConnection(acc.id)}
                      disabled={testingId === acc.id}
                      className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium disabled:opacity-50"
                    >
                      {testingId === acc.id ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Testing API...</span>
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-3.5 w-3.5" />
                          <span>Test Connection</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => handleDisconnect(acc.id, acc.email)}
                      className="flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 font-medium"
                      title="Disconnect Account"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>Disconnect</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Section 2: Account Security Overview */}
        <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Account Details
              </span>
              <ShieldCheck className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="mt-4 space-y-2">
              <div>
                <p className="text-xs text-slate-500">Registered Email</p>
                <p className="text-sm font-medium text-slate-200">{user?.email}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Name</p>
                <p className="text-sm font-medium text-slate-200">{user?.full_name || "Not provided"}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                WhatsApp Destination
              </span>
              <Phone className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-4">
              <p className="text-xs text-slate-500">Target Phone Number</p>
              <p className="text-sm font-medium text-slate-200 mt-1">
                {user?.whatsapp_number || "None configured"}
              </p>
              <span className="mt-3 inline-flex items-center gap-1 rounded-md bg-slate-800 px-2 py-0.5 text-[11px] text-slate-400">
                Phase 6 WhatsApp alerts target
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Token Encryption
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-4 space-y-2">
              <div>
                <p className="text-xs text-slate-500">OAuth Credentials</p>
                <p className="text-sm font-medium text-emerald-400">Fernet AES-128 Encrypted</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Multi-Tenant Boundary</p>
                <p className="text-sm font-medium text-slate-200">Scoped to user_id</p>
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Pipeline Roadmap */}
        <section>
          <h2 className="text-lg font-bold text-white mb-4">Pipeline Status</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <span className="text-xs font-semibold text-emerald-400">Phase 1 & 2</span>
              <p className="mt-1 font-semibold text-slate-200">Auth & Infrastructure</p>
              <p className="mt-1 text-xs text-slate-400">FastAPI, Motor, JWT, Security</p>
              <span className="mt-3 inline-block text-[11px] font-bold text-emerald-400">✓ Completed</span>
            </div>

            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <span className="text-xs font-semibold text-emerald-400">Phase 3</span>
              <p className="mt-1 font-semibold text-slate-200">Google OAuth / Gmail</p>
              <p className="mt-1 text-xs text-slate-400">Encrypted OAuth, Gmail Service</p>
              <span className="mt-3 inline-block text-[11px] font-bold text-emerald-400">✓ Completed</span>
            </div>

            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-4">
              <span className="text-xs font-semibold text-indigo-400">Phase 4 & 5</span>
              <p className="mt-1 font-semibold text-slate-200">Email Ingestion & Groq AI</p>
              <p className="mt-1 text-xs text-slate-400">Classification, Deadlines, Summaries</p>
              <span className="mt-3 inline-block text-[11px] font-semibold text-indigo-300">Next Phase →</span>
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
