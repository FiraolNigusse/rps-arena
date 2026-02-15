import { useEffect, useCallback } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { useUser } from "../context/UserContext"
import "./ResultsScreen.css"

export default function ResultsScreen() {
  const location = useLocation()
  const navigate = useNavigate()
  const { updateUser } = useUser()

  const {
    playerMove,
    opponentMove,
    result,
    coinsDelta,
    ratingDelta,
    newBalance,
    newRating,
  } = location.state || {}

  const playAgain = useCallback(() => {
    navigate("/play")
  }, [navigate])

  useEffect(() => {
    if (newBalance != null) updateUser({ coins: newBalance })
    if (newRating != null) updateUser({ rating: newRating })
  }, [newBalance, newRating, updateUser])

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    const mainBtn = tg?.MainButton

    if (mainBtn && playerMove && opponentMove != null) {
      mainBtn.setText("Play Again")
      mainBtn.onClick(playAgain)
      mainBtn.show()

      return () => {
        if (mainBtn.offClick) mainBtn.offClick(playAgain)
        mainBtn.hide()
      }
    }
  }, [playerMove, opponentMove, playAgain])

  if (!playerMove || !opponentMove || result == null) {
    return (
      <div className="results-screen">
        <p className="results-screen__error">
          No match data.{" "}
          <button type="button" className="btn-secondary" onClick={() => navigate("/")}>
            Go to Home
          </button>
        </p>
      </div>
    )
  }

  const resultLabel = result === "win" ? "You Won" : result === "lose" ? "You Lost" : "Draw"
  const coinsDisplay = coinsDelta != null ? (coinsDelta >= 0 ? `+${coinsDelta}` : `${coinsDelta}`) : ""
  const ratingDisplay = ratingDelta != null ? (ratingDelta >= 0 ? `+${ratingDelta}` : `${ratingDelta}`) : ""

  return (
    <div className="results-screen">
      <h1 className="results-screen__title">Result</h1>

      <div className="results-screen__moves">
        <div className="results-screen__move-card">
          <span className="results-screen__move-emoji">{moveEmoji(playerMove)}</span>
          <span className="results-screen__move-label">You</span>
          <span className="results-screen__move-value">{playerMove}</span>
        </div>
        <span className="results-screen__vs">vs</span>
        <div className="results-screen__move-card">
          <span className="results-screen__move-emoji">{moveEmoji(opponentMove)}</span>
          <span className="results-screen__move-label">Opponent</span>
          <span className="results-screen__move-value">{opponentMove}</span>
        </div>
      </div>

      <div className={`results-screen__result results-screen__result--${result}`}>
        {resultLabel}
      </div>

      <div className="results-screen__changes">
        {coinsDisplay && (
          <div className="results-screen__change">
            <span className="results-screen__change-label">Coins</span>
            <span className={coinsDelta >= 0 ? "results-screen__change-value positive" : "results-screen__change-value negative"}>
              {coinsDisplay}
            </span>
          </div>
        )}
        {ratingDisplay && (
          <div className="results-screen__change">
            <span className="results-screen__change-label">Rating</span>
            <span className={ratingDelta >= 0 ? "results-screen__change-value positive" : "results-screen__change-value negative"}>
              {ratingDisplay}
            </span>
          </div>
        )}
      </div>

      <div className="results-screen__actions">
        <a href="#/play" className="btn-primary results-screen__action-btn">
          Play Again
        </a>
        <a href="#/wallet" className="btn-secondary results-screen__action-btn">
          Wallet
        </a>
      </div>
    </div>
  )
}

function moveEmoji(move) {
  if (move === "rock") return "🪨"
  if (move === "paper") return "📄"
  if (move === "scissors") return "✂️"
  return "❓"
}

