import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import "./HomeScreen.css";

export default function HomeScreen() {
  const navigate = useNavigate();
  const { user } = useUser();

  return (
    <div className="home-screen">
      <div className="home-screen__identity">
        <span className="home-screen__label">Logged in as</span>
        <span className="home-screen__username">@{user?.username || "player"}</span>
      </div>

      <div className="home-screen__stats">
        <div className="home-screen__stat card">
          <span className="home-screen__stat-label">Coins</span>
          <span className="home-screen__stat-value">{user?.coins ?? 0}</span>
        </div>
        <div className="home-screen__stat card">
          <span className="home-screen__stat-label">Skill Rating</span>
          <span className="home-screen__stat-value">{user?.rating ?? 1000}</span>
        </div>
      </div>

      <button
        type="button"
        className="home-screen__play btn-primary"
        onClick={() => navigate("/play")}
      >
        PLAY
      </button>

      <button
        type="button"
        className="home-screen__wallet btn-secondary"
        onClick={() => navigate("/wallet")}
      >
        Wallet
      </button>
    </div>
  );
}
