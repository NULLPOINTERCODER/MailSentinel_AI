import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2, CheckCircle2, XCircle, ArrowRight } from "lucide-react";
import Navbar from "../components/Navbar.jsx";
import { handleGoogleOAuthCallback } from "../services/api.js";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState("processing"); // 'processing' | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState("");
  const [connectedEmail, setConnectedEmail] = useState("");

  const executedRef = useRef(false);

  useEffect(() => {
    if (executedRef.current) return;
    executedRef.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setStatus("error");
      setErrorMessage(`Google OAuth was declined or failed: ${errorParam}`);
      return;
    }

    if (!code || !state) {
      setStatus("error");
      setErrorMessage("Missing authorization code or state from Google callback.");
      return;
    }

    const completeOAuth = async () => {
      try {
        const response = await handleGoogleOAuthCallback({ code, state });
        setConnectedEmail(response.email);
        setStatus("success");
        setTimeout(() => {
          navigate("/dashboard");
        }, 2500);
      } catch (err) {
        const msg =
          err.response?.data?.detail || "Failed to finalize OAuth credentials with server.";
        setStatus("error");
        setErrorMessage(msg);
      }
    };

    completeOAuth();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex flex-1 items-center justify-center px-4 py-16">
        <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/70 p-8 text-center shadow-2xl backdrop-blur-xl">
          {status === "processing" && (
            <div className="space-y-4">
              <Loader2 className="mx-auto h-12 w-12 animate-spin text-indigo-500" />
              <h2 className="text-xl font-bold text-white">Linking Gmail Account...</h2>
              <p className="text-xs text-slate-400">
                Securely exchanging authorization credentials and encrypting tokens in MongoDB.
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h2 className="text-xl font-bold text-white">Gmail Connected!</h2>
              <p className="text-sm text-slate-300">
                <span className="font-semibold text-emerald-400">{connectedEmail}</span> has been
                successfully linked to your account.
              </p>
              <p className="text-xs text-slate-500">Redirecting to Dashboard...</p>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <XCircle className="h-8 w-8" />
              </div>
              <h2 className="text-xl font-bold text-white">Connection Failed</h2>
              <p className="text-xs text-rose-300 leading-relaxed">{errorMessage}</p>
              <button
                onClick={() => navigate("/connect-email")}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition-all"
              >
                <span>Try Again</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
