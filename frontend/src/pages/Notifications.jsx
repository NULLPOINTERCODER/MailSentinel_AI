import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar.jsx";
import { getNotifications } from "../services/api.js";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  MessageSquare,
  Clock,
  Send,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Link } from "react-router-dom";

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadNotifications = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const data = await getNotifications({ limit: 50, skip: 0 });
      setNotifications(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError("Failed to load notifications history.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case "SENT":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
            <CheckCircle2 className="h-3 w-3" />
            Sent
          </span>
        );
      case "DUPLICATE":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400">
            <AlertTriangle className="h-3 w-3" />
            Duplicate
          </span>
        );
      case "SKIPPED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-slate-700 bg-slate-800/60 px-2.5 py-0.5 text-xs font-medium text-slate-400">
            Skipped
          </span>
        );
      case "FAILED":
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/30 bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 py-10">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400">
              <Bell className="h-5 w-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">Audit Trail</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              WhatsApp Notification History
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Complete dispatch log of real-time alerts sent to your verified WhatsApp number.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => loadNotifications(true)}
              disabled={refreshing || loading}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-all"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
            <Link
              to="/settings"
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/20 transition-all"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              <span>Configure WhatsApp</span>
            </Link>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
            <XCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="rounded-2xl border border-slate-800/80 bg-slate-900/30 p-12 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-slate-500 border border-slate-800 mb-4">
              <MessageSquare className="h-7 w-7" />
            </div>
            <h3 className="text-base font-semibold text-white">No notifications dispatched yet</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Once important emails are analyzed and meet your threshold, alert records will appear here.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Link
                to="/settings"
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all"
              >
                Configure WhatsApp Number
              </Link>
              <Link
                to="/emails"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-all"
              >
                Go to Inbox Feed
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {notifications.map((item) => (
              <div
                key={item.id}
                className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-5 shadow-lg backdrop-blur-sm transition-all hover:border-slate-700/80"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {getStatusBadge(item.status)}
                      <span className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[11px] font-medium text-slate-300">
                        {item.channel}
                      </span>
                      {item.category && (
                        <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-[11px] font-semibold text-indigo-300 border border-indigo-500/20">
                          {item.category}
                        </span>
                      )}
                      {item.importance !== null && (
                        <span className="text-xs font-semibold text-slate-400">
                          Score: <span className="text-white">{item.importance}/100</span>
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-semibold text-white pt-1">
                      {item.subject || "WhatsApp Notification"}
                    </h3>

                    <div className="text-xs text-slate-400">
                      To: <span className="text-slate-300 font-mono">{item.recipient}</span>
                      {item.sender && <span className="ml-3">From: {item.sender}</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-500 flex-shrink-0">
                    <Clock className="h-3.5 w-3.5" />
                    <span>
                      {new Date(item.created_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>

                {/* Preformatted WhatsApp Message Content */}
                <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 font-mono text-xs text-emerald-300/90 whitespace-pre-wrap leading-relaxed">
                  {item.message_body}
                </div>

                {item.error_message && (
                  <div className="mt-3 text-xs text-rose-400">
                    Error details: {item.error_message}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
