/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { initTelegram } from "./telegram";
import { apiPost, setToken } from "./api/api";

import Home from "./pages/Home";
import Wallet from "./pages/Wallet";

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
    return <div style={{ padding: 20 }}>{status}</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home user={user} />} />
        <Route path="/wallet" element={<Wallet user={user} />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
