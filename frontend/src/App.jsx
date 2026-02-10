/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { initTelegram } from "./telegram";
import { apiPost, setToken } from "./api";

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
        setStatus("Auth failed");
      });
  }, []);

  if (!user) {
    return <div>{status}</div>;
  }

  return (
    <div>
      <h3>Welcome {user.username}</h3>
      <p>Coins: {user.coins}</p>
      <p>Rating: {user.rating}</p>
    </div>
  );
}

export default App;
