/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";

import { initTelegram } from "./telegram";
import { apiPost, setToken } from "./api/api";
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

  useEffect(() => {
    const tg = initTelegram();

    if (!tg) {
      setStatus("Not running inside Telegram");
      return;
    }

    const initData = tg.initData;

    apiPost("/auth/telegram/", { initData })
      .then((res) => {
        setToken(res.token);
        setUser(res.user);
        setStatus("Logged in");
      })
      .catch(() => {
        setStatus("Authentication failed");
      });
  }, []);

  if (!user) {
    return (
      <div className="auth-loading">
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
