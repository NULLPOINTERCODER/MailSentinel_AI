import React, { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import { queryEmailKnowledge, reindexUserEmails } from "../services/api.js";
import {
  Sparkles,
  Search,
  Bot,
  User,
  Send,
  Loader2,
  Database,
  ExternalLink,
  Clock,
  Zap,
  HelpCircle,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Mail,
  ShieldCheck,
} from "lucide-react";

const SUGGESTED_QUERIES = [
  "What happened with my IBM assessment?",
  "Do I have any interviews or online tests this week?",
  "Summarize all recruiter conversations and job applications.",
  "Which emails have an urgent deadline or action required?",
  "Did I receive any security alerts or payment receipts?",
];

export default function AskAI() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [reindexStatus, setReindexStatus] = useState(null);
  const [chatHistory, setChatHistory] = useState([
    {
      role: "assistant",
      text: "Hello! I am your MailSentinel AI knowledge agent. You can ask me any question about your connected inboxes, application statuses, upcoming interviews, or extracted deadlines.",
      sources: [],
    },
  ]);

  const handleAsk = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const queryToRun = (customQuery || query).trim();
    if (!queryToRun || loading) return;

    const userMessage = { role: "user", text: queryToRun };
    setChatHistory((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const data = await queryEmailKnowledge(queryToRun, 5);
      const botResponse = {
        role: "assistant",
        text: data.answer,
        sources: data.sources || [],
        count: data.context_emails_count,
      };
      setChatHistory((prev) => [...prev, botResponse]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `⚠️ Error retrieving email knowledge: ${
            err.response?.data?.detail || "Could not complete RAG query."
          }`,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    setReindexStatus(null);
    try {
      const res = await reindexUserEmails();
      setReindexStatus({
        type: "success",
        text: `Vector index rebuilt successfully! Indexed ${res.indexed_emails} of ${res.total_emails} emails in ChromaDB.`,
      });
    } catch (err) {
      setReindexStatus({
        type: "error",
        text: "Failed to re-index emails into vector database.",
      });
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-5xl px-6 py-8 flex-1 flex flex-col">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2 text-indigo-400">
              <Sparkles className="h-5 w-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Retrieval-Augmented Generation (RAG)
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1">
              Ask MailSentinel AI
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Ask natural language questions across your connected emails, deadlines, and recruiter threads.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleReindex}
              disabled={reindexing}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/80 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white transition-all disabled:opacity-50"
            >
              <Database className={`h-3.5 w-3.5 ${reindexing ? "animate-spin text-indigo-400" : ""}`} />
              <span>{reindexing ? "Reindexing..." : "Re-index Vector DB"}</span>
            </button>
          </div>
        </div>

        {reindexStatus && (
          <div
            className={`my-4 flex items-center gap-3 rounded-2xl border p-3.5 text-xs ${
              reindexStatus.type === "success"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border-rose-500/30 bg-rose-500/10 text-rose-300"
            }`}
          >
            {reindexStatus.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            )}
            <span>{reindexStatus.text}</span>
          </div>
        )}

        {/* Suggested Queries Chips */}
        <div className="my-5 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider shrink-0 flex items-center gap-1">
            <HelpCircle className="h-3 w-3" /> Suggestions:
          </span>
          {SUGGESTED_QUERIES.map((sq, i) => (
            <button
              key={i}
              onClick={(e) => handleAsk(e, sq)}
              className="rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300 hover:border-indigo-500/40 hover:bg-indigo-950/30 hover:text-white shrink-0 transition-all"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Chat Conversation Thread */}
        <div className="flex-1 space-y-6 py-4">
          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3.5 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white shadow-md shadow-indigo-500/20">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-4.5 space-y-3 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                    : "bg-slate-900/70 border border-slate-800/80 text-slate-200 shadow-xl"
                }`}
              >
                <div className="text-xs sm:text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Retrieved Source Citations */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 border-t border-slate-800/80 pt-3 space-y-2">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
                      <Mail className="h-3 w-3" />
                      <span>Retrieved Source Emails ({msg.sources.length}):</span>
                    </div>

                    <div className="grid gap-2">
                      {msg.sources.map((src, sIdx) => (
                        <div
                          key={sIdx}
                          className="rounded-xl bg-slate-950/70 border border-slate-800/60 p-2.5 text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-semibold text-slate-100 truncate">
                              {src.subject}
                            </span>
                            {src.category && (
                              <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-bold text-indigo-300 border border-indigo-500/20 shrink-0">
                                {src.category}
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center justify-between">
                            <span>From: {src.sender}</span>
                            <span>{src.received_at?.split(" ").slice(0, 4).join(" ")}</span>
                          </div>
                          {src.deadline && (
                            <div className="text-[11px] text-amber-400 flex items-center gap-1 font-medium">
                              <Clock className="h-3 w-3" /> Deadline: {src.deadline}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-300 border border-slate-700">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3.5 items-center text-slate-400 text-xs py-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <span>Searching vector database and synthesizing answer with Groq AI...</span>
            </div>
          )}
        </div>

        {/* Query Input Bar */}
        <form onSubmit={handleAsk} className="sticky bottom-6 pt-4">
          <div className="relative flex items-center rounded-2xl border border-slate-800 bg-slate-900/90 p-2 shadow-2xl backdrop-blur-xl focus-within:border-indigo-500">
            <Search className="pointer-events-none absolute left-4 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about your emails, e.g. 'What is the deadline for the Amazon assessment?'"
              className="w-full bg-transparent pl-10 pr-14 py-2 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-3 inline-flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 transition-all shadow-md"
            >
              {loading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 px-2">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-emerald-400" /> Multi-user vector isolation active
            </span>
            <span>Powered by Groq & ChromaDB</span>
          </div>
        </form>
      </main>
    </div>
  );
}
