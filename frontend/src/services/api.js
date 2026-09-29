import axios from "axios";

const baseURL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 10000,
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
      // If token expired or invalid, clear local auth
      if (localStorage.getItem("mailsentinel_token")) {
        localStorage.removeItem("mailsentinel_token");
        localStorage.removeItem("mailsentinel_user");
        window.dispatchEvent(new Event("auth:logout"));
      }
    }
    return Promise.reject(error);
  }
);

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
