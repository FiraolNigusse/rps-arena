/* eslint-disable no-unused-vars */ 
import { useState, useEffect } from "react"

export default function WithdrawScreen() {
  const [coins] = useState(115) // replace later with real user data
  const [amount, setAmount] = useState("")
  const [wallet, setWallet] = useState("")
  const [status, setStatus] = useState("idle") 
  // idle | submitting | pending | error

  const MIN_WITHDRAW = 50

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (amount < MIN_WITHDRAW) {
      alert(`Minimum withdrawal is ${MIN_WITHDRAW} coins`)
      return
    }

    if (amount > coins) {
      alert("Insufficient balance")
      return
    }

    try {
      setStatus("submitting")

      // 🔜 Later we connect to backend
      setTimeout(() => {
        setStatus("pending")
      }, 1000)

    } catch (err) {
      setStatus("error")
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
      window.Telegram.WebApp.openInvoice(invoiceLink, (status) => {
        if (status === "paid") {
          alert("Payment successful! Coins will be credited shortly.")
        } else {
          alert("Payment cancelled or failed.")
        }
      })
    }
  }
  
  return (
    <div style={{ maxWidth: 400, margin: "40px auto", textAlign: "center" }}>
      <h2>Withdraw Coins</h2>

      <div style={{ background: "#f5f5f5", padding: 15, borderRadius: 10 }}>
        <p><strong>Available Coins:</strong> {coins}</p>
        <p><strong>Minimum Withdrawal:</strong> {MIN_WITHDRAW} coins</p>
        <p style={{ fontSize: 12, color: "#666" }}>
          Withdrawals are reviewed manually within 24 hours.
        </p>
      </div>

      {/* BUY COINS BUTTON */}
      <button
        onClick={buyCoins}
        style={{
          width: "100%",
          padding: 12,
          borderRadius: 8,
          marginBottom: 20,
          fontSize: 16,
          cursor: "pointer",
        }}
      >
        Buy Coins
      </button>

      {status !== "pending" && (
        <form onSubmit={handleSubmit} style={{ marginTop: 20 }}>
          <input
            type="number"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            required
            style={inputStyle}
          />

          <input
            type="text"
            placeholder="Wallet Address"
            value={wallet}
            onChange={(e) => setWallet(e.target.value)}
            required
            style={inputStyle}
          />

          <button type="submit" style={buttonStyle}>
            {status === "submitting" ? "Submitting..." : "Request Withdrawal"}
          </button>
        </form>
      )}

      {status === "pending" && (
        <div style={{ marginTop: 20, color: "orange" }}>
          <h3>Request Submitted</h3>
          <p>Status: Pending Review</p>
        </div>
      )}
    </div>
  )
}

const inputStyle = {
  width: "100%",
  padding: 10,
  marginBottom: 10,
  borderRadius: 6,
  border: "1px solid #ccc",
}

const buttonStyle = {
  width: "100%",
  padding: 12,
  borderRadius: 8,
  fontSize: 16,
  cursor: "pointer",
}
