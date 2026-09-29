import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Mail,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  ExternalLink,
  Lock,
  Loader2,
} from "lucide-react";
import Navbar from "../components/Navbar.jsx";
import { getGoogleOAuthUrl } from "../services/api.js";

export default function ConnectEmail() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showGuide, setShowGuide] = useState(false);

  const handleConnectGmail = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getGoogleOAuthUrl();
      if (data?.url) {
        // Redirect browser to Google's official OAuth consent screen
        window.location.href = data.url;
      } else {
        setError("Failed to retrieve Google OAuth URL.");
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        "Could not initiate Google OAuth. Please check backend GOOGLE_CLIENT_ID configuration.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="mx-auto w-full max-w-4xl px-6 py-12 flex-1">
        <div className="text-center max-w-xl mx-auto">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-lg shadow-indigo-600/10">
            <Mail className="h-7 w-7" />
          </div>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Connect Your Email
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            MailSentinel AI securely analyzes incoming unread emails using read-only API access.
            We never see or store your Google password.
          </p>
        </div>

        {error && (
          <div className="mt-8 mx-auto max-w-lg flex items-start gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Connection Error</p>
              <p className="mt-0.5 text-xs text-rose-400">{error}</p>
            </div>
          </div>
        )}

        {/* Provider Cards */}
        <div className="mt-10 grid gap-6 sm:grid-cols-2 max-w-2xl mx-auto">
          {/* Gmail Card */}
          <div className="rounded-3xl border border-indigo-500/30 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-xl flex flex-col justify-between hover:border-indigo-500/60 transition-all">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-900 shadow-md">
                  <svg className="h-6 w-6" viewBox="0 0 24 24">
                    <path
                      fill="#EA4335"
                      d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.272H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L12 9.545l8.073-6.052C21.69 2.28 24 3.434 24 5.457z"
                    />
                  </svg>
                </div>
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/20">
                  Ready
                </span>
              </div>
              <h3 className="mt-4 text-xl font-bold text-white">Google Gmail</h3>
              <p className="mt-1 text-xs text-slate-400">
                Official Google OAuth 2.0. Scopes: <code className="text-indigo-300">gmail.readonly</code>.
              </p>
            </div>

            <button
              onClick={handleConnectGmail}
              disabled={loading}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 active:scale-[0.99]"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <span>Connect Gmail</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>

          {/* Microsoft Outlook Card (Future) */}
          <div className="rounded-3xl border border-slate-800/80 bg-slate-900/30 p-6 flex flex-col justify-between opacity-75">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
                  <Mail className="h-6 w-6" />
                </div>
                <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] font-medium text-slate-400">
                  Upcoming
                </span>
              </div>
              <h3 className="mt-4 text-xl font-bold text-slate-300">Microsoft Outlook</h3>
              <p className="mt-1 text-xs text-slate-500">
                Microsoft Graph API & OAuth integration for enterprise Microsoft 365 accounts.
              </p>
            </div>

            <button
              disabled
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-900/40 py-3 text-sm font-medium text-slate-500 cursor-not-allowed"
            >
              <span>Coming Soon</span>
            </button>
          </div>
        </div>

        {/* Security Assurance */}
        <div className="mt-12 max-w-2xl mx-auto rounded-2xl border border-slate-800 bg-slate-900/30 p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Lock className="h-4 w-4 text-indigo-400" />
            <span>How your data is protected:</span>
          </div>
          <ul className="mt-3 space-y-2 text-xs text-slate-400">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span>OAuth 2.0 tokens are encrypted using AES-128 Fernet before saving in MongoDB.</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span>We never ask for or store passwords. Access can be revoked anytime in your Google Account.</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span>Multi-tenant isolation strictly isolates email processing per user ID.</span>
            </li>
          </ul>
        </div>

        {/* Google Cloud Console Setup Guide Accordion */}
        <div className="mt-6 max-w-2xl mx-auto">
          <button
            onClick={() => setShowGuide(!showGuide)}
            className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3 text-xs font-semibold text-slate-300 hover:bg-slate-900/80 transition-all"
          >
            <span className="flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-indigo-400" />
              <span>Google Cloud Console Credentials Setup Guide</span>
            </span>
            {showGuide ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showGuide && (
            <div className="mt-2 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-xs text-slate-300 space-y-3 leading-relaxed">
              <p className="font-semibold text-white">Steps to configure Google OAuth 2.0:</p>
              <ol className="list-decimal list-inside space-y-2 text-slate-400">
                <li>
                  Go to the{" "}
                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-400 underline inline-flex items-center gap-0.5"
                  >
                    Google Cloud Console <ExternalLink className="h-3 w-3 inline" />
                  </a>
                  .
                </li>
                <li>Create a project and enable the <strong>Gmail API</strong>.</li>
                <li>Go to <strong>OAuth consent screen</strong> → Set user type to External → Add scope <code>https://www.googleapis.com/auth/gmail.readonly</code>.</li>
                <li>Add your Google account under <strong>Test users</strong>.</li>
                <li>Go to <strong>Credentials</strong> → <strong>Create Credentials</strong> → <strong>OAuth client ID</strong> (Web application).</li>
                <li>
                  Set <strong>Authorized redirect URIs</strong> to:
                  <div className="mt-1 rounded-lg bg-slate-950 p-2 font-mono text-indigo-300 border border-slate-800">
                    http://localhost:5173/auth/google/callback
                  </div>
                </li>
                <li>
                  Copy your <code>Client ID</code> & <code>Client Secret</code> into your <code>backend/.env</code>:
                  <pre className="mt-1 rounded-lg bg-slate-950 p-2 font-mono text-emerald-300 border border-slate-800">
{`GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback`}
                  </pre>
                </li>
              </ol>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
