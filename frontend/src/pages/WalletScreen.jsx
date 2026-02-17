import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { apiGet, apiPost } from "../api/api";
import "./WalletScreen.css";

export default function WalletScreen() {
  const navigate = useNavigate();
  const { user, updateUser } = useUser();
  const [coins, setCoins] = useState(user?.coins ?? 0);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    apiPost("/wallet/balance/", {})
      .then((res) => {
        setCoins(res.coins ?? 0);
        updateUser({ coins: res.coins });
      })
      .catch(() => { });
  }, []);

  useEffect(() => {
    apiGet("/wallet/transactions/")
      .then((res) => setTransactions(res.transactions ?? []))
      .catch(() => setTransactions([]));
  }, []);

  const buyCoins = async (amount = 100) => {
    const tg = window.Telegram?.WebApp;
    const showMsg = (msg) => tg?.showAlert?.(msg) ?? alert(msg);

    if (!tg?.openInvoice) {
      showMsg("Please open this app from Telegram to purchase coins.");
      return;
    }

    try {
      // 1. Get live invoice link from backend
      const res = await apiPost("/wallet/stars/invoice/", { amount });

      if (!res.invoice_link) {
        showMsg("Failed to generate invoice. Please try again later.");
        return;
      }

      // 2. Open Telegram payment UI
      tg.openInvoice(res.invoice_link, (status) => {
        if (status === "paid" || status === "completed") {
          // 3. Refresh balance after payment
          apiPost("/wallet/balance/", {}).then((balanceRes) => {
            setCoins(balanceRes.coins ?? 0);
            updateUser({ coins: balanceRes.coins });
            showMsg("Payment successful! Coins added to your wallet.");
          }).catch(() => { });
        } else if (status === "cancelled") {
          // Ignored
        } else {
          showMsg(`Payment status: ${status}`);
        }
      });
    } catch (err) {
      console.error("Payment error:", err);
      showMsg("Could not connect to payment server. Please try again.");
    }
  };

  const formatDate = (iso) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
    } catch (_) {
      return iso;
    }
  };

  const typeLabel = (type) => {
    const map = { win: "Match win", purchase: "Purchase", withdrawal: "Withdrawal", stake: "Stake" };
    return map[type] || type;
  };

  return (
    <div className="wallet-screen">
      <h1 className="wallet-screen__title">Wallet</h1>

      <div className="wallet-screen__balance card">
        <span className="wallet-screen__balance-label">Coin balance</span>
        <span className="wallet-screen__balance-value">{coins}</span>
      </div>

      <p className="wallet-screen__info">
        Coins are used to play games and earn rewards.
      </p>

      <div className="wallet-screen__packages">
        <h2 className="wallet-screen__subtitle">Get more coins</h2>
        <div className="wallet-screen__package-list">
          {[50, 100, 250].map((amount) => (
            <button
              key={amount}
              type="button"
              className="wallet-screen__package-btn"
              onClick={() => buyCoins(amount)}
            >
              <span className="package-amount">{amount}</span>
              <span className="package-price">{amount} Stars</span>
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="btn-secondary wallet-screen__withdraw"
        onClick={() => navigate("/withdraw")}
        disabled={coins < 50}
      >
        Withdraw
      </button>
      {coins < 50 && (
        <p className="wallet-screen__withdraw-hint">Minimum withdrawal: 50 coins</p>
      )}

      <div className="wallet-screen__history">
        <h2 className="wallet-screen__history-title">Transaction history</h2>
        <ul className="wallet-screen__list">
          {transactions.length === 0 && (
            <li className="wallet-screen__list-empty">No transactions yet</li>
          )}
          {transactions.map((tx, i) => (
            <li key={i} className="wallet-screen__list-item">
              <span className="wallet-screen__list-type">{typeLabel(tx.type)}</span>
              <span className={`wallet-screen__list-amount ${tx.amount >= 0 ? "positive" : "negative"}`}>
                {tx.amount >= 0 ? "+" : ""}{tx.amount}
              </span>
              <span className="wallet-screen__list-date">{formatDate(tx.date)}</span>
            </li>
          ))}
        </ul>
      </div>

      <button type="button" className="btn-secondary wallet-screen__back" onClick={() => navigate("/")}>
        Back to Home
      </button>
    </div>
  );
}
