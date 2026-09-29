import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar.jsx";
import {
  getUserSettings,
  updateUserSettings,
  testWhatsAppPing,
  simulateWhatsAppInbound,
} from "../services/api.js";
import {
  Sliders,
  MessageSquare,
  Shield,
  Send,
  Save,
  CheckCircle2,
  AlertCircle,
  Phone,
  BellRing,
  Sparkles,
  Zap,
  Bot,
  Loader2,
} from "lucide-react";

const ALL_CATEGORIES = [
  { id: "INTERVIEW", label: "Interview Invitations", desc: "Technical, HR & Screening calls" },
  { id: "ASSESSMENT", label: "Online Assessments", desc: "Coding tests, HackerRank, OA links" },
  { id: "OFFER", label: "Job Offers", desc: "Offer letters & contract decisions" },
  { id: "RECRUITER", label: "Recruiter Messages", desc: "Direct outreach from hiring managers" },
  { id: "JOB_APPLICATION", label: "Job Applications", desc: "Application updates and confirmations" },
  { id: "MEETING", label: "Meetings & Appointments", desc: "Calendar invites & schedule changes" },
  { id: "SECURITY", label: "Security & Verification", desc: "OTP codes, 2FA, password resets" },
  { id: "FINANCE", label: "Finance & Invoices", desc: "Payment due dates, invoices & receipts" },
  { id: "COLLEGE", label: "College / University", desc: "Academic notices & professor emails" },
  { id: "PERSONAL", label: "Personal", desc: "Direct personal conversations" },
];

export default function Settings() {
  const [settings, setSettings] = useState({
    whatsapp_phone_number: "",
    whatsapp_notifications_enabled: true,
    minimum_importance_threshold: 80,
    enabled_categories: [
      "INTERVIEW",
      "ASSESSMENT",
      "OFFER",
      "RECRUITER",
      "JOB_APPLICATION",
      "MEETING",
      "SECURITY",
      "FINANCE",
    ],
    auto_notify_on_sync: true,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingPing, setTestingPing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [pingStatus, setPingStatus] = useState(null);
  const [error, setError] = useState(null);

  // WhatsApp Bot Simulator State
  const [simMessage, setSimMessage] = useState("Show important emails");
  const [simulating, setSimulating] = useState(false);
  const [simReply, setSimReply] = useState(null);

  const handleSimulateMessage = async () => {
    if (!settings.whatsapp_phone_number) {
      setSimReply("⚠️ Please enter and save your WhatsApp phone number above first.");
      return;
    }
    if (!simMessage.trim() || simulating) return;

    setSimulating(true);
    setSimReply(null);
    try {
      const res = await simulateWhatsAppInbound(
        settings.whatsapp_phone_number.trim(),
        simMessage.trim()
      );
      setSimReply(res.reply || "No response received.");
    } catch (err) {
      setSimReply(`⚠️ Simulation error: ${err.response?.data?.detail || "Failed to process message"}`);
    } finally {
      setSimulating(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await getUserSettings();
      setSettings({
        whatsapp_phone_number: data.whatsapp_phone_number || "",
        whatsapp_notifications_enabled: data.whatsapp_notifications_enabled ?? true,
        minimum_importance_threshold: data.minimum_importance_threshold ?? 80,
        enabled_categories: data.enabled_categories || [],
        auto_notify_on_sync: data.auto_notify_on_sync ?? true,
      });
    } catch (err) {
      setError("Failed to load user settings.");
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (catId) => {
    setSettings((prev) => {
      const exists = prev.enabled_categories.includes(catId);
      const updated = exists
        ? prev.enabled_categories.filter((c) => c !== catId)
        : [...prev.enabled_categories, catId];
      return { ...prev, enabled_categories: updated };
    });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      await updateUserSettings({
        whatsapp_phone_number: settings.whatsapp_phone_number.trim() || null,
        whatsapp_notifications_enabled: settings.whatsapp_notifications_enabled,
        minimum_importance_threshold: Number(settings.minimum_importance_threshold),
        enabled_categories: settings.enabled_categories,
        auto_notify_on_sync: settings.auto_notify_on_sync,
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleTestPing = async () => {
    if (!settings.whatsapp_phone_number) {
      setPingStatus({
        type: "error",
        message: "Please enter a valid WhatsApp phone number first.",
      });
      return;
    }

    try {
      setTestingPing(true);
      setPingStatus(null);
      const res = await testWhatsAppPing({
        phone_number: settings.whatsapp_phone_number.trim(),
      });

      if (res.simulated) {
        setPingStatus({
          type: "warning",
          message:
            "Sandbox/Dev Mode: Simulated WhatsApp message logged to backend server logs. (Configure WHATSAPP_ACCESS_TOKEN & PHONE_NUMBER_ID in .env for live Meta delivery).",
        });
      } else {
        setPingStatus({
          type: "success",
          message: `Test alert sent successfully to ${settings.whatsapp_phone_number}!`,
        });
      }
    } catch (err) {
      setPingStatus({
        type: "error",
        message: err.response?.data?.detail || "Failed to send test message.",
      });
    } finally {
      setTestingPing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <Navbar />
        <div className="flex h-[70vh] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Navbar />

      <main className="mx-auto max-w-4xl px-6 py-10">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400">
              <Sliders className="h-5 w-5" />
              <span className="text-xs font-semibold uppercase tracking-wider">Preferences & AI Rules</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Notification & WhatsApp Settings
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Control your WhatsApp alert delivery, importance sensitivity, and category filters.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {saveSuccess && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-emerald-400" />
            <span>Settings updated successfully!</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-8">
          {/* WhatsApp Channel Config */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center gap-3 border-b border-slate-800/80 pb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <MessageSquare className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">WhatsApp Delivery Channel</h2>
                <p className="text-xs text-slate-400">Official Meta WhatsApp Business Cloud API Integration</p>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              {/* Master Toggle */}
              <div className="flex items-center justify-between rounded-xl bg-slate-950/60 p-4 border border-slate-800">
                <div>
                  <label className="text-sm font-semibold text-white">Enable WhatsApp Notifications</label>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Receive immediate WhatsApp alerts when high-importance emails are analyzed.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setSettings((p) => ({
                      ...p,
                      whatsapp_notifications_enabled: !p.whatsapp_notifications_enabled,
                    }))
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                    settings.whatsapp_notifications_enabled ? "bg-emerald-500" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.whatsapp_notifications_enabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              {/* Phone Number Input */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  WhatsApp Phone Number (with Country Code)
                </label>
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1">
                    <Phone className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="+919876543210 or 919876543210"
                      value={settings.whatsapp_phone_number}
                      onChange={(e) =>
                        setSettings((p) => ({ ...p, whatsapp_phone_number: e.target.value }))
                      }
                      className="w-full rounded-xl border border-slate-800 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleTestPing}
                    disabled={testingPing || !settings.whatsapp_phone_number}
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50 transition-all"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>{testingPing ? "Sending..." : "Test WhatsApp Ping"}</span>
                  </button>
                </div>
                <p className="mt-1.5 text-[11px] text-slate-500">
                  Must include country code without spaces or dashes (e.g., +91 for India, +1 for US).
                </p>
              </div>

              {/* Ping feedback message */}
              {pingStatus && (
                <div
                  className={`rounded-xl border p-3.5 text-xs ${
                    pingStatus.type === "success"
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                      : pingStatus.type === "warning"
                      ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
                      : "border-rose-500/30 bg-rose-500/10 text-rose-300"
                  }`}
                >
                  {pingStatus.message}
                </div>
              )}
            </div>
          </div>

          {/* Importance Sensitivity Slider */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Importance Scoring Threshold</h2>
                  <p className="text-xs text-slate-400">
                    Only notify when hybrid AI importance is equal to or greater than this score.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-3.5 py-1.5">
                <span className="text-lg font-bold text-indigo-300">
                  {settings.minimum_importance_threshold}
                </span>
                <span className="text-xs text-indigo-400/80">/ 100</span>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={settings.minimum_importance_threshold}
                onChange={(e) =>
                  setSettings((p) => ({
                    ...p,
                    minimum_importance_threshold: parseInt(e.target.value, 10),
                  }))
                }
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <div className="flex justify-between text-[11px] font-medium text-slate-500">
                <span>0 (All Emails)</span>
                <span>50 (Moderate)</span>
                <span className="text-indigo-400 font-semibold">80 (Recommended for High Priority)</span>
                <span>100 (Strictly Urgent Only)</span>
              </div>
            </div>
          </div>

          {/* Enabled Categories */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center gap-3 border-b border-slate-800/80 pb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Permitted Alert Categories</h2>
                <p className="text-xs text-slate-400">
                  Select which email categories are eligible to trigger instant WhatsApp pings.
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {ALL_CATEGORIES.map((cat) => {
                const isSelected = settings.enabled_categories.includes(cat.id);
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => handleCategoryToggle(cat.id)}
                    className={`flex items-start gap-3 rounded-xl border p-3.5 text-left transition-all ${
                      isSelected
                        ? "border-indigo-500/40 bg-indigo-500/10 text-white"
                        : "border-slate-800/80 bg-slate-950/40 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div
                      className={`mt-0.5 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-600 text-white"
                          : "border-slate-700 bg-slate-900"
                      }`}
                    >
                      {isSelected && <CheckCircle2 className="h-3 w-3" />}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{cat.label}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{cat.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 disabled:opacity-50 transition-all"
            >
              <Save className="h-4 w-4" />
              <span>{saving ? "Saving Changes..." : "Save Preferences"}</span>
            </button>
          </div>
        </form>

        {/* WhatsApp Conversational AI Webhook Simulator */}
        <section className="mt-12 rounded-3xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl backdrop-blur-sm space-y-5">
          <div className="flex items-center gap-3 border-b border-slate-800/80 pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">WhatsApp Conversational Bot Simulator</h2>
              <p className="text-xs text-slate-400">
                Simulate inbound WhatsApp messages sent from your phone to test the conversational AI agent
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Quick Test Prompts:
              </span>
              {["Show important emails", "Check deadlines", "Summarize recruiters", "Help"].map((cmd) => (
                <button
                  key={cmd}
                  type="button"
                  onClick={() => setSimMessage(cmd)}
                  className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-slate-300 hover:border-emerald-500/40 hover:text-emerald-300 transition-all"
                >
                  {cmd}
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <input
                type="text"
                value={simMessage}
                onChange={(e) => setSimMessage(e.target.value)}
                placeholder="Type a message (e.g. 'Show important emails' or 'What happened with Google?')"
                className="flex-1 rounded-xl border border-slate-800 bg-slate-950/80 px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleSimulateMessage}
                disabled={simulating || !simMessage.trim()}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/20"
              >
                {simulating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                <span>Simulate Inbound</span>
              </button>
            </div>

            {simReply && (
              <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                  <Bot className="h-3.5 w-3.5" />
                  <span>WhatsApp Bot Response:</span>
                </div>
                <div className="font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {simReply}
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
