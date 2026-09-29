import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Mail, LogOut, LayoutDashboard, Inbox, Plus, Bell, Settings as SettingsIcon, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5 text-lg font-bold tracking-tight text-white hover:opacity-90">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white shadow-md shadow-indigo-500/20">
              <Mail className="h-5 w-5" />
            </div>
            <span>MailSentinel <span className="text-indigo-400">AI</span></span>
          </Link>

          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/dashboard"
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  isActive("/dashboard")
                    ? "bg-slate-900 text-indigo-400 border border-slate-800"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <LayoutDashboard className="h-3.5 w-3.5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/emails"
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  isActive("/emails")
                    ? "bg-slate-900 text-indigo-400 border border-slate-800"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Inbox className="h-3.5 w-3.5" />
                <span>Inbox Feed</span>
              </Link>
              <Link
                to="/notifications"
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  isActive("/notifications")
                    ? "bg-slate-900 text-indigo-400 border border-slate-800"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Bell className="h-3.5 w-3.5" />
                <span>Notifications</span>
              </Link>
              <Link
                to="/settings"
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  isActive("/settings")
                    ? "bg-slate-900 text-indigo-400 border border-slate-800"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <SettingsIcon className="h-3.5 w-3.5" />
                <span>Settings</span>
              </Link>
              <Link
                to="/connect-email"
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  isActive("/connect-email")
                    ? "bg-slate-900 text-indigo-400 border border-slate-800"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Connect</span>
              </Link>
            </nav>
          )}
        </div>

        <nav className="flex items-center gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-2 text-xs text-slate-400">
                <User className="h-3.5 w-3.5 text-indigo-400" />
                <span className="max-w-[140px] truncate">{user?.full_name || user?.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-300 hover:bg-rose-500/20 transition-all"
                title="Log out"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <Link
                to="/login"
                className="rounded-lg px-3.5 py-1.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-900 transition-all"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/20 transition-all"
              >
                Get Started
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
