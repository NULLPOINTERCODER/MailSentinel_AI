import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Emails from "./pages/Emails.jsx";
import ConnectEmail from "./pages/ConnectEmail.jsx";
import OAuthCallback from "./pages/OAuthCallback.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/emails"
          element={
            <ProtectedRoute>
              <Emails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/connect-email"
          element={
            <ProtectedRoute>
              <ConnectEmail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/auth/google/callback"
          element={
            <ProtectedRoute>
              <OAuthCallback />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
