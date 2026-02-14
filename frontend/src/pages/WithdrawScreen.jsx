import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { apiPost, apiGet } from "../api/api"
import "./WithdrawScreen.css"

const MIN_WITHDRAW = 50

export default function WithdrawScreen() {
  const navigate = useNavigate()
  const [coins, setCoins] = useState(0)
  const [amount, setAmount] = useState("")
  const [wallet, setWallet] = useState("")
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState("")
  const [withdrawals, setWithdrawals] = useState([])

  useEffect(() => {
    apiPost("/wallet/balance/", {})
      .then((res) => setCoins(res.coins ?? 0))
      .catch(() => setCoins(0))
  }, [])

  useEffect(() => {
    apiGet("/withdraw/list/")
      .then((res) => setWithdrawals(res.withdrawals ?? []))
      .catch(() => setWithdrawals([]))
  }, [status])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (Number(amount) < MIN_WITHDRAW) {
      setError(`Minimum withdrawal is ${MIN_WITHDRAW} coins`)
      return
    }

    if (Number(amount) > coins) {
      setError("Insufficient balance")
      return
    }

    try {
      setStatus("submitting")
      await apiPost("/withdraw/request/", { amount: Number(amount), wallet })
      setStatus("pending")
      setAmount("")
      setWallet("")
      apiGet("/withdraw/list/").then((res) => setWithdrawals(res.withdrawals ?? []))
    } catch (err) {
      setStatus("error")
      setError(err?.data?.error || "Request failed")
    }
  }

  const formatDate = (iso) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
    } catch (_) {
      return iso
    }
  }

  const canWithdraw = coins >= MIN_WITHDRAW

  return (
    <div className="withdraw-screen">
      <h1 className="withdraw-screen__title">Withdraw</h1>

      <div className="withdraw-screen__info card">
        <div className="withdraw-screen__info-row">
          <span className="withdraw-screen__info-label">Current balance</span>
          <span className="withdraw-screen__info-value">{coins} coins</span>
        </div>
        <p className="withdraw-screen__info-note">
          Minimum withdrawal: {MIN_WITHDRAW} coins. Withdrawals are reviewed manually; status is shown below.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="withdraw-screen__form">
        <input
          type="number"
          placeholder="Amount to withdraw"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          min={MIN_WITHDRAW}
          max={coins}
          className="withdraw-screen__input"
        />
        <input
          type="text"
          placeholder="Wallet address"
          value={wallet}
          onChange={(e) => setWallet(e.target.value)}
          required
          className="withdraw-screen__input"
        />
        <button
          type="submit"
          disabled={status === "submitting" || !canWithdraw}
          className="btn-primary withdraw-screen__submit-btn"
        >
          {status === "submitting" ? "Submitting..." : "Request Withdrawal"}
        </button>
      </form>

      {status === "error" && error && (
        <p className="withdraw-screen__error">{error}</p>
      )}

      <div className="withdraw-screen__status-section">
        <h3 className="withdraw-screen__status-title">Withdrawal status</h3>
        <ul className="withdraw-screen__status-list">
          {withdrawals.length === 0 && (
            <li className="withdraw-screen__status-empty">No withdrawals yet</li>
          )}
          {withdrawals.map((w, i) => (
            <li key={i} className="withdraw-screen__status-item">
              <span>{w.amount} coins</span>
              <span className={`withdraw-screen__status-badge withdraw-screen__status-badge--${w.status}`}>
                {w.status}
              </span>
              <span className="withdraw-screen__status-date">{formatDate(w.date)}</span>
            </li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        className="btn-secondary withdraw-screen__back"
        onClick={() => navigate("/wallet")}
      >
        Back to Wallet
      </button>
    </div>
  )
}
