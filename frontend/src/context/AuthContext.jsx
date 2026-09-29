import React, { createContext, useContext, useEffect, useState } from "react";
import { getMe, loginUser, registerUser } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("mailsentinel_user");
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("mailsentinel_token"));
  const [loading, setLoading] = useState(true);

  const saveAuth = (newToken, newUser) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("mailsentinel_token", newToken);
    localStorage.setItem("mailsentinel_user", JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("mailsentinel_token");
    localStorage.removeItem("mailsentinel_user");
  };

  useEffect(() => {
    const checkCurrentSession = async () => {
      const savedToken = localStorage.getItem("mailsentinel_token");
      if (savedToken) {
        try {
          const profile = await getMe();
          setUser(profile);
          localStorage.setItem("mailsentinel_user", JSON.stringify(profile));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };

    checkCurrentSession();

    const handleAutoLogout = () => logout();
    window.addEventListener("auth:logout", handleAutoLogout);
    return () => window.removeEventListener("auth:logout", handleAutoLogout);
  }, []);

  const login = async (email, password) => {
    const data = await loginUser({ email, password });
    saveAuth(data.access_token, data.user);
    return data.user;
  };

  const register = async (email, password, fullName, whatsappNumber) => {
    const payload = {
      email,
      password,
      full_name: fullName || null,
      whatsapp_number: whatsappNumber || null,
    };
    const data = await registerUser(payload);
    saveAuth(data.access_token, data.user);
    return data.user;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user && !!token,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
