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
  Sparkles,
  ShieldAlert,
  Loader2,
  Calendar,
  ArrowRight,
  Flame,
  Check,
} from "lucide-react";
import Navbar from "../components/Navbar.jsx";
import {
  getEmails,
  getEmailStats,
  syncUserEmails,
  triageEmailWithAI,
  batchTriageWithAI,
  sendEmailWhatsAppAlert,
} from "../services/api.js";
import { MessageSquare, Send } from "lucide-react";

const categoryColors = {
  INTERVIEW: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  ASSESSMENT: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
  OFFER: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  SECURITY: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  RECRUITER: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  JOB_APPLICATION: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  MEETING: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  FINANCE: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  PROMOTION: "bg-slate-800 text-slate-400 border-slate-700",
  NEWSLETTER: "bg-slate-800 text-slate-400 border-slate-700",
  GENERAL: "bg-slate-800 text-slate-300 border-slate-700",
};

export default function Emails() {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [triagingId, setTriagingId] = useState(null);
  const [batchTriaging, setBatchTriaging] = useState(false);
  const [sendingWhatsAppId, setSendingWhatsAppId] = useState(null);
  const [syncMessage, setSyncMessage] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);

  // Filters
  const [filterType, setFilterType] = useState("all");
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
      if (result.synced_accounts === 0) {
        setSyncMessage({
          type: "info",
          text: "No connected email accounts found for this user. Please go to the Connect tab and click 'Connect Gmail Account' first.",
        });
      } else {
        setSyncMessage({
          type: "success",
          text: `Sync finished: ${result.new_emails_saved} new emails ingested, ${result.duplicates_skipped} duplicates skipped (${result.potentially_important} flagged potentially important) from ${result.synced_accounts} connected account(s).`,
        });
      }
      loadData();
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to synchronize connected inboxes. Please ensure your Gmail account is connected.";
      setSyncMessage({ type: "error", text: msg });
    } finally {
      setSyncing(false);
    }
  };

  const handleRunAITriage = async (e, emailId) => {
    e.stopPropagation();
    setTriagingId(emailId);
    try {
      const result = await triageEmailWithAI(emailId);
      // Update local state immediately
      setEmails((prev) =>
        prev.map((m) => (m.id === emailId ? { ...m, ...result, ai_processed: true } : m))
      );
      if (selectedEmail && selectedEmail.id === emailId) {
        setSelectedEmail((prev) => ({ ...prev, ...result, ai_processed: true }));
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Groq AI Triage failed.");
    } finally {
      setTriagingId(null);
    }
  };

  const handleBatchAITriage = async () => {
    setBatchTriaging(true);
    setSyncMessage(null);
    try {
      const results = await batchTriageWithAI(10);
      if (results.length === 0) {
        setSyncMessage({
          type: "info",
          text: "All emails in your inbox have already been analyzed and triaged by Groq AI.",
        });
      } else {
        setSyncMessage({
          type: "success",
          text: `Groq AI batch triage completed for ${results.length} email(s)! Importance scores and deadlines updated.`,
        });
      }
      loadData();
    } catch (err) {
      setSyncMessage({
        type: "error",
        text: err.response?.data?.detail || "Batch AI triage failed. Please check Groq API key or try again.",
      });
    } finally {
      setBatchTriaging(false);
    }
  };

  const handleSendWhatsApp = async (e, emailId, force = false) => {
    if (e) e.stopPropagation();
    setSendingWhatsAppId(emailId);
    try {
      const res = await sendEmailWhatsAppAlert(emailId, force);
      if (res.status === "SENT") {
        setSyncMessage({
          type: "success",
          text: res.simulated
            ? "WhatsApp Alert simulated in Dev Mode! (Logged to backend output)."
            : "WhatsApp Alert successfully dispatched to your phone!",
        });
        setEmails((prev) =>
          prev.map((m) => (m.id === emailId ? { ...m, whatsapp_notified: true } : m))
        );
        if (selectedEmail && selectedEmail.id === emailId) {
          setSelectedEmail((prev) => ({ ...prev, whatsapp_notified: true }));
        }
      } else if (res.status === "DUPLICATE") {
        setSyncMessage({
          type: "info",
          text: "Notification was already sent previously for this email.",
        });
      } else if (res.status === "SKIPPED") {
        setSyncMessage({
          type: "warning",
          text: `WhatsApp alert skipped: ${res.reason || "Does not meet settings criteria."}`,
        });
      } else {
        setSyncMessage({
          type: "error",
          text: res.error || "Failed to dispatch WhatsApp alert.",
        });
      }
    } catch (err) {
      setSyncMessage({
        type: "error",
        text: err.response?.data?.detail || "Failed to send WhatsApp alert.",
      });
    } finally {
      setSendingWhatsAppId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-6xl px-6 py-8 flex-1 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Inbox className="h-6 w-6 text-indigo-400" />
              <span>Inbox AI Intelligence Feed</span>
            </h1>
            <p className="mt-1 text-xs text-slate-400">
              Groq LLM structured extraction: classifications, summaries, actions & deadlines.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handleBatchAITriage}
              disabled={batchTriaging}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:from-purple-500 hover:to-indigo-500 shadow-md shadow-purple-600/20 transition-all disabled:opacity-50"
            >
              <Sparkles className={`h-3.5 w-3.5 ${batchTriaging ? "animate-spin" : ""}`} />
              <span>{batchTriaging ? "Analyzing with Groq..." : "Batch AI Triage"}</span>
            </button>

            <button
              onClick={handleSyncNow}
              disabled={syncing}
              className="flex items-center gap-1.5 rounded-xl bg-slate-800 border border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
              <span>{syncing ? "Syncing..." : "Sync Inboxes"}</span>
            </button>
          </div>
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

        {/* Quick Stats */}
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
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">AI Triaged</p>
              <p className="text-2xl font-bold text-purple-400 mt-1">{stats.ai_triaged_count || 0}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Potentially Important</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.potentially_important}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/60 p-1">
            <button
              onClick={() => setFilterType("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "all" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              All Ingested
            </button>
            <button
              onClick={() => setFilterType("important")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "important" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              <span>Potentially Important</span>
            </button>
            <button
              onClick={() => setFilterType("unread")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                filterType === "unread" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"
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

        {/* Emails List */}
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
              Sync your inboxes to fetch new emails and run Groq AI triage.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {emails.map((item) => {
              const catColor =
                categoryColors[item.category] || "bg-slate-800 text-slate-300 border-slate-700";
              const isHigh = item.final_importance >= 80;

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedEmail(item)}
                  className={`cursor-pointer rounded-2xl border p-4 backdrop-blur-sm transition-all hover:bg-slate-900/80 ${
                    item.ai_processed
                      ? isHigh
                        ? "border-indigo-500/40 bg-gradient-to-r from-indigo-950/20 to-slate-900/60"
                        : "border-slate-800 bg-slate-900/40"
                      : "border-slate-800/80 bg-slate-900/40"
                  }`}
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-start gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 border border-slate-700">
                        <User className="h-4 w-4" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-white">{item.sender_name}</span>
                          <span className="text-xs text-slate-500">&lt;{item.sender_email}&gt;</span>
                          {item.category && (
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold border ${catColor}`}>
                              {item.category}
                            </span>
                          )}
                          {item.urgency && item.urgency !== "LOW" && (
                            <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-[10px] font-bold text-rose-400 border border-rose-500/20">
                              {item.urgency}
                            </span>
                          )}
                        </div>
                        <h4 className="text-sm font-medium text-slate-200">{item.subject}</h4>

                        {/* AI Summary Banner if triaged */}
                        {item.ai_processed && item.summary && (
                          <div className="rounded-xl bg-indigo-950/40 border border-indigo-500/20 p-2.5 text-xs text-indigo-200 mt-2 space-y-1.5">
                            <div className="flex items-center gap-1.5 text-indigo-300 font-semibold text-[11px]">
                              <Sparkles className="h-3 w-3" />
                              <span>AI Summary:</span>
                            </div>
                            <p className="text-slate-300 text-xs leading-relaxed">{item.summary}</p>

                            <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px]">
                              {item.action && (
                                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                                  <Zap className="h-3 w-3" /> Action: {item.action}
                                </span>
                              )}
                              {item.deadline && (
                                <span className="flex items-center gap-1 text-amber-300 font-medium">
                                  <Clock className="h-3 w-3" /> Deadline: {item.deadline}
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {!item.ai_processed && (
                          <p className="text-xs text-slate-400 line-clamp-2 max-w-2xl">
                            {item.snippet || item.body_text}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex sm:flex-col items-end justify-between sm:justify-start gap-2 shrink-0">
                      <div className="flex items-center gap-2">
                        {item.ai_processed ? (
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold border ${
                              isHigh
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                : "bg-slate-800 text-slate-300 border-slate-700"
                            }`}
                          >
                            <Flame className="h-3 w-3 text-amber-400" />
                            <span>AI Score: {item.final_importance}/100</span>
                          </span>
                        ) : (
                          <button
                            onClick={(e) => handleRunAITriage(e, item.id)}
                            disabled={triagingId === item.id}
                            className="flex items-center gap-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 px-2.5 py-1 text-[11px] font-semibold text-indigo-300 hover:bg-indigo-600 hover:text-white transition-all disabled:opacity-50"
                          >
                            {triagingId === item.id ? (
                              <>
                                <Loader2 className="h-3 w-3 animate-spin" />
                                <span>Triaging...</span>
                              </>
                            ) : (
                              <>
                                <Sparkles className="h-3 w-3" />
                                <span>Run AI Triage</span>
                              </>
                            )}
                          </button>
                        )}

                        {item.is_unread && <span className="h-2 w-2 rounded-full bg-indigo-500" title="Unread" />}
                      </div>
                      <span className="text-[11px] text-slate-500">
                        {item.received_at?.split(" ").slice(0, 4).join(" ")}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
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
                  {selectedEmail.category && (
                    <span className="rounded-full bg-purple-500/10 px-2.5 py-0.5 text-[11px] font-bold text-purple-400 border border-purple-500/20">
                      {selectedEmail.category}
                    </span>
                  )}
                  {selectedEmail.urgency && (
                    <span className="rounded-full bg-rose-500/10 px-2.5 py-0.5 text-[11px] font-bold text-rose-400 border border-rose-500/20">
                      {selectedEmail.urgency}
                    </span>
                  )}
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

            {/* AI Breakdown Card */}
            {selectedEmail.ai_processed ? (
              <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-300">
                    <Sparkles className="h-4 w-4" />
                    <span>Groq AI Intelligence Triage</span>
                  </div>
                  <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-extrabold text-emerald-400 border border-emerald-500/30">
                    Final Score: {selectedEmail.final_importance}/100
                  </span>
                </div>

                <div className="text-xs space-y-1.5 pt-1">
                  <p className="font-semibold text-slate-200">Summary:</p>
                  <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    {selectedEmail.summary}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 text-xs">
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    <p className="text-slate-400 font-semibold flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-emerald-400" /> Action Required:
                    </p>
                    <p className="mt-1 text-slate-200 font-medium">
                      {selectedEmail.action || "No action required."}
                    </p>
                  </div>
                  <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                    <p className="text-slate-400 font-semibold flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-amber-400" /> Extracted Deadline:
                    </p>
                    <p className="mt-1 text-slate-200 font-medium">
                      {selectedEmail.deadline || "No specific deadline found."}
                    </p>
                  </div>
                </div>

                {selectedEmail.reason && (
                  <p className="text-[11px] text-slate-400 italic">
                    Reasoning: {selectedEmail.reason}
                  </p>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <span className="text-xs text-slate-400">Groq AI analysis not yet executed on this email.</span>
                <button
                  onClick={(e) => handleRunAITriage(e, selectedEmail.id)}
                  disabled={triagingId === selectedEmail.id}
                  className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all shadow-md shadow-indigo-600/20"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Analyze with Groq</span>
                </button>
              </div>
            )}

            {/* Headers Breakdown */}
            <div className="grid gap-3 sm:grid-cols-2 text-xs bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
              <div>
                <p className="text-slate-500">From:</p>
                <p className="font-semibold text-slate-200">
                  {selectedEmail.sender_name} &lt;{selectedEmail.sender_email}&gt;
                </p>
              </div>
              <div>
                <p className="text-slate-500">Received Date:</p>
                <p className="font-semibold text-slate-200">{selectedEmail.received_at}</p>
              </div>
              <div>
                <p className="text-slate-500">Rule Pre-Filter Score:</p>
                <p className="font-bold text-slate-300">{selectedEmail.rule_score} / 100</p>
              </div>
              <div>
                <p className="text-slate-500">WhatsApp Alert Threshold:</p>
                <p className="font-semibold text-emerald-400">
                  {selectedEmail.final_importance >= 80 ? "Eligible (Score >= 80)" : "Below threshold (< 80)"}
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Normalized Plaintext Content:
              </h3>
              <div className="max-h-60 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                {selectedEmail.body_text || selectedEmail.snippet || "No body text extracted."}
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-800 pt-4">
              {selectedEmail.ai_processed && (
                <button
                  onClick={(e) => handleSendWhatsApp(e, selectedEmail.id, true)}
                  disabled={sendingWhatsAppId === selectedEmail.id}
                  className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50 transition-all"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span>
                    {sendingWhatsAppId === selectedEmail.id
                      ? "Sending WhatsApp..."
                      : selectedEmail.whatsapp_notified
                      ? "Re-send WhatsApp Alert"
                      : "Send WhatsApp Alert"}
                  </span>
                </button>
              )}
              <button
                onClick={() => setSelectedEmail(null)}
                className="rounded-xl bg-slate-800 px-5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 ml-auto"
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
