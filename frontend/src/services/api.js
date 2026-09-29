import axios from "axios";

const baseURL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically inject JWT token into all outgoing requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("mailsentinel_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 Unauthorized responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (localStorage.getItem("mailsentinel_token")) {
        localStorage.removeItem("mailsentinel_token");
        localStorage.removeItem("mailsentinel_user");
        window.dispatchEvent(new Event("auth:logout"));
      }
    }
    return Promise.reject(error);
  }
);

// --- Health ---
export async function getHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}

export async function getDbHealth() {
  const response = await apiClient.get("/health/db");
  return response.data;
}

export async function fetchHealth() {
  const [backendRes, dbRes] = await Promise.allSettled([
    apiClient.get("/health"),
    apiClient.get("/health/db"),
  ]);

  return {
    backend: backendRes.status === "fulfilled" ? backendRes.value.data : null,
    db: dbRes.status === "fulfilled" ? dbRes.value.data : null,
  };
}

// --- Authentication ---
export async function registerUser(payload) {
  const response = await apiClient.post("/auth/register", payload);
  return response.data;
}

export async function loginUser(payload) {
  const response = await apiClient.post("/auth/login", payload);
  return response.data;
}

export async function getMe() {
  const response = await apiClient.get("/auth/me");
  return response.data;
}

// --- Gmail & Google OAuth ---
export async function getGoogleOAuthUrl() {
  const response = await apiClient.get("/api/gmail/oauth/url");
  return response.data;
}

export async function handleGoogleOAuthCallback(payload) {
  const response = await apiClient.post("/api/gmail/oauth/callback", payload);
  return response.data;
}

export async function getConnectedAccounts() {
  const response = await apiClient.get("/api/gmail/accounts");
  return response.data;
}

export async function disconnectAccount(accountId) {
  const response = await apiClient.delete(`/api/gmail/accounts/${accountId}`);
  return response.data;
}

export async function testAccountConnection(accountId) {
  const response = await apiClient.get(`/api/gmail/accounts/${accountId}/test`);
  return response.data;
}

// --- Email Ingestion & Queries ---
export async function syncUserEmails(maxPerAccount = 20) {
  const response = await apiClient.post(`/api/emails/sync?max_per_account=${maxPerAccount}`);
  return response.data;
}

export async function getEmails(params = {}) {
  const response = await apiClient.get("/api/emails", { params });
  return response.data;
}

export async function getEmailStats() {
  const response = await apiClient.get("/api/emails/stats/summary");
  return response.data;
}

export async function getEmailById(emailId) {
  const response = await apiClient.get(`/api/emails/${emailId}`);
  return response.data;
}

// --- Groq AI Triage (Phase 5) ---
export async function triageEmailWithAI(emailId) {
  const response = await apiClient.post(`/api/ai/triage/${emailId}`);
  return response.data;
}

export async function batchTriageWithAI(limit = 10) {
  const response = await apiClient.post(`/api/ai/batch-triage?limit=${limit}`);
  return response.data;
}

// --- Settings & User Preferences (Phase 6) ---
export async function getUserSettings() {
  const response = await apiClient.get("/api/settings");
  return response.data;
}

export async function updateUserSettings(payload) {
  const response = await apiClient.put("/api/settings", payload);
  return response.data;
}

// --- WhatsApp Notifications (Phase 6) ---
export async function getNotifications(params = {}) {
  const response = await apiClient.get("/api/notifications", { params });
  return response.data;
}

export async function sendEmailWhatsAppAlert(emailId, forceResend = false) {
  const response = await apiClient.post(`/api/notifications/send/${emailId}?force_resend=${forceResend}`);
  return response.data;
}

export async function testWhatsAppPing(payload) {
  const response = await apiClient.post("/api/notifications/test-whatsapp", payload);
  return response.data;
}

// --- RAG over Historical Emails (Phase 9) ---
export async function queryEmailKnowledge(query, topK = 5) {
  const response = await apiClient.post("/api/rag/query", { query, top_k: topK });
  return response.data;
}

export async function reindexUserEmails() {
  const response = await apiClient.post("/api/rag/reindex");
  return response.data;
}


