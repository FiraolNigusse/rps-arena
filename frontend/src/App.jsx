/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState, useCallback } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";

import { initTelegram } from "./telegram";
import { setToken } from "./api/api";
import { UserProvider } from "./context/UserContext";

import HomeScreen from "./pages/HomeScreen";
import WalletScreen from "./pages/WalletScreen";
import PlayScreen from "./pages/PlayScreen";
import MatchScreen from "./pages/MatchScreen";
import ResultsScreen from "./pages/ResultsScreen";
import WithdrawScreen from "./pages/WithdrawScreen";

import "./App.css";

function App() {
  const [status, setStatus] = useState("Initializing...");
  const [user, setUser] = useState(null);

  const doAuth = useCallback(() => {
    const tg = initTelegram();
    if (!tg) {
      setStatus("Not running inside Telegram");
      return;
    }

    const initData = tg.initData;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    setStatus("Connecting...");

    fetch(`${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api"}/auth/telegram/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initData }),
      signal: controller.signal,
    })
      .then((res) => {
        clearTimeout(timeoutId);
        if (!res.ok) throw Object.assign(new Error("Auth failed"), { status: res.status });
        return res.json();
      })
      .then((res) => {
        setToken(res.token);
        setUser(res.user);
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        console.error("Auth failed:", err?.status, err?.message);
        if (err?.name === "AbortError") {
          setStatus("Server is slow to start. Tap to try again.");
        } else if (err?.status === 0 || err?.message?.includes("fetch")) {
          setStatus("Cannot reach server. Tap to retry.");
        } else if (err?.status === 403) {
          setStatus("Invalid Telegram data. Open from Telegram.");
        } else {
          setStatus("Authentication failed. Tap to retry.");
        }
      });
  }, []);

  useEffect(() => {
    const tg = initTelegram();
    if (!tg) {
      setStatus("Not running inside Telegram");
      return;
    }
    doAuth();
  }, [doAuth]);

  if (!user) {
    const isRetryable = status.includes("Tap to retry") || status.includes("Tap to try again");
    return (
      <div
        className="auth-loading"
        role={isRetryable ? "button" : undefined}
        onClick={isRetryable ? () => { setStatus("Initializing..."); doAuth(); } : undefined}
        onKeyDown={isRetryable ? (e) => { if (e.key === "Enter" || e.key === " ") { setStatus("Initializing..."); doAuth(); } } : undefined}
        tabIndex={isRetryable ? 0 : undefined}
        style={isRetryable ? { cursor: "pointer" } : undefined}
      >
        <div className="auth-loading__spinner" />
        <p className="auth-loading__text">{status}</p>
      </div>
    );
  }

  return (
    <UserProvider initialUser={user}>
      <HashRouter>
        <div className="app-container">
          <Routes>
            <Route path="/" element={<HomeScreen />} />
            <Route path="/wallet" element={<WalletScreen />} />
            <Route path="/play" element={<PlayScreen />} />
            <Route path="/match" element={<MatchScreen />} />
            <Route path="/results" element={<ResultsScreen />} />
            <Route path="/withdraw" element={<WithdrawScreen />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </HashRouter>
    </UserProvider>
  );
}

export default App;
