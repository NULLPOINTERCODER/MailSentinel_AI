import axios from "axios";

const baseURL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 15000,
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

export async function fetchUnreadEmails(accountId, maxResults = 10) {
  const response = await apiClient.get(`/api/gmail/accounts/${accountId}/unread?max_results=${maxResults}`);
  return response.data;
}
