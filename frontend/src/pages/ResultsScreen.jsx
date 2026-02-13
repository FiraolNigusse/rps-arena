/* eslint-disable react-hooks/set-state-in-effect */
import { useLocation, useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"
import "./ResultsScreen.css"

export default function ResultsScreen() {
  const location = useLocation()
  const navigate = useNavigate()

  const { playerMove, opponentMove } = location.state || {}

  const [result, setResult] = useState("")
  const [coins, setCoins] = useState(100)
  const [rating, setRating] = useState(1200)

  useEffect(() => {
    if (!playerMove || !opponentMove) return
    const r = determineWinner(playerMove, opponentMove)
    setResult(r)

    if (r === "win") {
      animateValue(setCoins, 100, 115)
      animateValue(setRating, 1200, 1208)
    } else if (r === "lose") {
      animateValue(setRating, 1200, 1195)
    }
  }, [playerMove, opponentMove])

  const playAgain = () => {
    navigate("/")
  }

  if (!playerMove || !opponentMove) {
    return (
      <div className="results-screen">
        <p className="results-screen__error">No match data. <button type="button" className="btn-secondary" onClick={() => navigate("/")}>Go to game</button></p>
      </div>
    )
  }

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
        {result.toUpperCase()}
      </div>

      <div className="results-screen__stats">
        <div className="results-screen__stat">
          <span className="results-screen__stat-label">Coins</span>
          <span className="results-screen__stat-value">{coins}</span>
        </div>
        <div className="results-screen__stat">
          <span className="results-screen__stat-label">Rating</span>
          <span className="results-screen__stat-value">{rating}</span>
        </div>
      </div>

      <div className="results-screen__actions">
        <button type="button" className="btn-primary" onClick={playAgain}>
          Play Again
        </button>
        <button type="button" className="btn-secondary" onClick={() => navigate("/withdraw")}>
          Withdraw Coins
        </button>
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

function determineWinner(player, opponent) {
  if (player === opponent) return "draw"
  if (
    (player === "rock" && opponent === "scissors") ||
    (player === "paper" && opponent === "rock") ||
    (player === "scissors" && opponent === "paper")
  ) {
    return "win"
  }
  return "lose"
}

function animateValue(setter, start, end) {
  let current = start
  const step = start < end ? 1 : -1

  const interval = setInterval(() => {
    current += step
    setter(current)
    if (current === end) clearInterval(interval)
  }, 30)
}
