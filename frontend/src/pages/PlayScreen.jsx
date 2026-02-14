import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiPost } from "../api/api";
import "./PlayScreen.css";

const STAKE_OPTIONS = [50, 100, 200];

export default function PlayScreen() {
  const navigate = useNavigate();
  const { user, updateUser } = useUser();
  const [balance, setBalance] = useState(user?.coins ?? 0);
  const [selectedStake, setSelectedStake] = useState(null);

  useEffect(() => {
    apiPost("/wallet/balance/", {})
      .then((res) => setBalance(res.coins ?? 0))
      .catch(() => setBalance(user?.coins ?? 0));
  }, [user?.coins]);

  const handleConfirm = () => {
    if (selectedStake == null || balance < selectedStake) return;
    navigate("/match", { state: { stake: selectedStake } });
  };

  const canConfirm = selectedStake != null && balance >= selectedStake;

  return (
    <div className="play-screen">
      <h1 className="play-screen__title">Choose your stake</h1>
      <p className="play-screen__balance">
        Balance: <strong>{balance}</strong> coins
      </p>

      <div className="play-screen__options">
        {STAKE_OPTIONS.map((stake) => {
          const disabled = balance < stake;
          const selected = selectedStake === stake;
          return (
            <button
              key={stake}
              type="button"
              className={`play-screen__stake card ${selected ? "play-screen__stake--selected" : ""} ${disabled ? "play-screen__stake--disabled" : ""}`}
              onClick={() => !disabled && setSelectedStake(stake)}
              disabled={disabled}
            >
              {stake} coins
            </button>
          );
        })}
      </div>

      <p className="play-screen__hint">Select one stake to continue. No custom amounts.</p>

      <div className="play-screen__actions">
        <button
          type="button"
          className="btn-primary play-screen__confirm"
          disabled={!canConfirm}
          onClick={handleConfirm}
        >
          Confirm
        </button>
        <button
          type="button"
          className="btn-secondary play-screen__back"
          onClick={() => navigate("/")}
        >
          Back
        </button>
      </div>
    </div>
  );
}
