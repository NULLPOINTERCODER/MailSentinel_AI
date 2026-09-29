import React, { useEffect, useState } from "react";
import {
  Mail,
  RefreshCw,
  Search,
  Zap,
  CheckCircle2,
  AlertCircle,
  Inbox,
  Clock,
  User,
  X,
  ExternalLink,
  ChevronRight,
  Loader2,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import Navbar from "../components/Navbar.jsx";
import { getEmails, getEmailStats, syncUserEmails } from "../services/api.js";

export default function Emails() {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);

  // Filters
  const [filterType, setFilterType] = useState("all"); // 'all' | 'important' | 'unread'
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterType === "important") params.only_important = true;
      if (filterType === "unread") params.only_unread = true;
      if (searchQuery.trim()) params.q = searchQuery.trim();

      const [emailsRes, statsRes] = await Promise.all([
        getEmails(params),
        getEmailStats().catch(() => null),
      ]);

      setEmails(emailsRes);
      if (statsRes) setStats(statsRes);
    } catch {
      // Failed to load
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  const handleSyncNow = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const result = await syncUserEmails(25);
      setSyncMessage({
        type: "success",
        text: `Sync finished: ${result.new_emails_saved} new emails ingested, ${result.duplicates_skipped} duplicates skipped. (${result.potentially_important} flagged potentially important).`,
      });
      loadData();
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to synchronize connected inboxes.";
      setSyncMessage({ type: "error", text: msg });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-6xl px-6 py-8 flex-1 space-y-6">
        {/* Header & Sync Bar */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Inbox className="h-6 w-6 text-indigo-400" />
              <span>Inbox Intelligence Feed</span>
            </h1>
            <p className="mt-1 text-xs text-slate-400">
              Ingested and normalized emails with deterministic rule-based importance triage.
            </p>
          </div>

          <button
            onClick={handleSyncNow}
            disabled={syncing}
            className="flex items-center gap-2 self-start rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
            <span>{syncing ? "Ingesting Inboxes..." : "Sync Inboxes Now"}</span>
          </button>
        </div>

        {/* Sync Feedback Alert */}
        {syncMessage && (
          <div
            className={`flex items-center gap-2.5 rounded-2xl border p-4 text-xs ${
              syncMessage.type === "success"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border-rose-500/30 bg-rose-500/10 text-rose-300"
            }`}
          >
            {syncMessage.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0" />
            )}
            <span>{syncMessage.text}</span>
          </div>
        )}

        {/* Metric Quick Stats */}
        {stats && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Ingested</p>
              <p className="text-2xl font-bold text-white mt-1">{stats.total_emails}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Unread Emails</p>
              <p className="text-2xl font-bold text-indigo-400 mt-1">{stats.unread_emails}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Potentially Important</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.potentially_important}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Critical Signals</p>
              <p className="text-2xl font-bold text-purple-400 mt-1">{stats.critical_signals_detected}</p>
            </div>
          </div>
        )}

        {/* Filter Tabs & Search Bar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/60 p-1">
            <button
              onClick={() => setFilterType("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "all"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              All Ingested
            </button>
            <button
              onClick={() => setFilterType("important")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "important"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              <span>Potentially Important</span>
            </button>
            <button
              onClick={() => setFilterType("unread")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "unread"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Unread
            </button>
          </div>

          <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sender, subject..."
              className="w-full rounded-xl border border-slate-800 bg-slate-900/60 pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </form>
        </div>

        {/* Email Cards List */}
        {loading ? (
          <div className="flex items-center justify-center rounded-3xl border border-slate-800 bg-slate-900/20 p-16">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          </div>
        ) : emails.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
              <Mail className="h-6 w-6" />
            </div>
            <h3 className="mt-3 text-base font-semibold text-white">No Emails Found</h3>
            <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
              No emails matching your filter criteria. Click "Sync Inboxes Now" to pull latest unread emails.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {emails.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedEmail(item)}
                className="cursor-pointer rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 backdrop-blur-sm transition-all hover:border-indigo-500/50 hover:bg-slate-900/70"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 border border-slate-700">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">{item.sender_name}</span>
                        <span className="text-xs text-slate-500">&lt;{item.sender_email}&gt;</span>
                      </div>
                      <h4 className="text-sm font-medium text-slate-200">{item.subject}</h4>
                      <p className="text-xs text-slate-400 line-clamp-2 max-w-2xl">{item.snippet || item.body_text}</p>
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-end justify-between sm:justify-start gap-1.5 shrink-0">
                    <div className="flex items-center gap-2">
                      {item.is_potentially_important ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-bold text-emerald-400 border border-emerald-500/20">
                          <Zap className="h-3 w-3 text-emerald-400" />
                          <span>Score: {item.rule_score}/100</span>
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] font-medium text-slate-400">
                          Score: {item.rule_score}/100
                        </span>
                      )}
                      {item.is_unread && (
                        <span className="h-2 w-2 rounded-full bg-indigo-500" title="Unread" />
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500">{item.received_at?.split(" ").slice(0, 4).join(" ")}</span>
                  </div>
                </div>

                {/* Detected Signal Chips */}
                {(item.positive_signals?.length > 0 || item.negative_signals?.length > 0) && (
                  <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/60">
                    {item.positive_signals.map((sig) => (
                      <span
                        key={sig.signal}
                        className="rounded-md bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-medium text-indigo-300"
                      >
                        +{sig.weight} {sig.signal.replace("_", " ")}
                      </span>
                    ))}
                    {item.negative_signals.map((sig) => (
                      <span
                        key={sig.signal}
                        className="rounded-md bg-rose-950/40 border border-rose-500/30 px-2 py-0.5 text-[10px] font-medium text-rose-300"
                      >
                        {sig.weight} {sig.signal}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Email Detail Drawer Modal */}
      {selectedEmail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-500/20">
                    {selectedEmail.provider.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">ID: {selectedEmail.message_id}</span>
                </div>
                <h2 className="mt-2 text-xl font-bold text-white">{selectedEmail.subject}</h2>
              </div>
              <button
                onClick={() => setSelectedEmail(null)}
                className="rounded-xl p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 text-xs bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
              <div>
                <p className="text-slate-500">From:</p>
                <p className="font-semibold text-slate-200">{selectedEmail.sender_name} &lt;{selectedEmail.sender_email}&gt;</p>
              </div>
              <div>
                <p className="text-slate-500">Received Date:</p>
                <p className="font-semibold text-slate-200">{selectedEmail.received_at}</p>
              </div>
              <div>
                <p className="text-slate-500">Rule Importance Score:</p>
                <p className="font-bold text-emerald-400">{selectedEmail.rule_score} / 100</p>
              </div>
              <div>
                <p className="text-slate-500">Deduplication Hash (SHA-256):</p>
                <p className="font-mono text-[10px] text-slate-400 truncate">{selectedEmail.content_hash}</p>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Normalized Plaintext Content:
              </h3>
              <div className="max-h-72 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                {selectedEmail.body_text || selectedEmail.snippet || "No body text extracted."}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedEmail(null)}
                className="rounded-xl bg-slate-800 px-5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
