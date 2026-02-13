import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { apiPost } from "../api/api"
import "./WithdrawScreen.css"

export default function WithdrawScreen() {
  const navigate = useNavigate()
  const [coins, setCoins] = useState(0)
  const [amount, setAmount] = useState("")
  const [wallet, setWallet] = useState("")
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState("")

  const MIN_WITHDRAW = 50

  useEffect(() => {
    apiPost("/wallet/balance/", {})
      .then((res) => setCoins(res.coins ?? 0))
      .catch(() => setCoins(0))
  }, [])

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
    } catch (err) {
      setStatus("error")
      setError(err?.data?.error || "Request failed")
    }
  }

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready()
    }
  }, [])

  const buyCoins = () => {
    const invoiceLink = "YOUR_INVOICE_LINK_FROM_BACKEND"

    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openInvoice(invoiceLink, (invoiceStatus) => {
        if (invoiceStatus === "paid") {
          alert("Payment successful! Coins will be credited shortly.")
        } else {
          alert("Payment cancelled or failed.")
        }
      })
    }
  }

  return (
    <div className="withdraw-screen">
      <h1 className="withdraw-screen__title">Withdraw Coins</h1>

      <div className="withdraw-screen__info card">
        <div className="withdraw-screen__info-row">
          <span className="withdraw-screen__info-label">Available</span>
          <span className="withdraw-screen__info-value">{coins} coins</span>
        </div>
        <div className="withdraw-screen__info-row">
          <span className="withdraw-screen__info-label">Minimum</span>
          <span className="withdraw-screen__info-value">{MIN_WITHDRAW} coins</span>
        </div>
        <p className="withdraw-screen__info-note">
          Withdrawals are reviewed manually within 24 hours.
        </p>
      </div>

      <button
        type="button"
        onClick={buyCoins}
        className="btn-primary withdraw-screen__buy-btn"
      >
        Buy Coins
      </button>

      {status !== "pending" && (
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
            disabled={status === "submitting"}
            className="btn-primary withdraw-screen__submit-btn"
          >
            {status === "submitting" ? "Submitting..." : "Request Withdrawal"}
          </button>
        </form>
      )}

      {status === "error" && error && (
        <p className="withdraw-screen__error">{error}</p>
      )}

      {status === "pending" && (
        <div className="withdraw-screen__pending card">
          <h3 className="withdraw-screen__pending-title">Request Submitted</h3>
          <p className="withdraw-screen__pending-status">Status: Pending Review</p>
        </div>
      )}

      <button
        type="button"
        className="btn-secondary withdraw-screen__back"
        onClick={() => navigate("/")}
      >
        ← Back to Game
      </button>
    </div>
  )
}
