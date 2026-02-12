import { useLocation, useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"

export default function ResultsScreen() {
  const location = useLocation()
  const navigate = useNavigate()

  const { playerMove, opponentMove } = location.state

  const [result, setResult] = useState("")
  const [coins, setCoins] = useState(100)
  const [rating, setRating] = useState(1200)

  useEffect(() => {
    const r = determineWinner(playerMove, opponentMove)
    setResult(r)

    if (r === "win") {
      animateValue(setCoins, 100, 115)
      animateValue(setRating, 1200, 1208)
    } else if (r === "lose") {
      animateValue(setRating, 1200, 1195)
    }
  }, [])

  const playAgain = () => {
    navigate("/")
  }

  return (
    <div style={{ textAlign: "center", marginTop: 40 }}>
      <h2>Result</h2>

      <p>Your move: {playerMove}</p>
      <p>Opponent move: {opponentMove}</p>

      <h1 style={{ color: resultColor(result) }}>
        {result.toUpperCase()}
      </h1>

      <p>Coins: {coins}</p>
      <p>Rating: {rating}</p>

      <button
        onClick={playAgain}
        style={{
          padding: "15px 30px",
          fontSize: 16,
          borderRadius: 10,
          marginTop: 20,
        }}
      >
        Play Again
      </button>
    </div>
  )
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

function resultColor(result) {
  if (result === "win") return "green"
  if (result === "lose") return "red"
  return "gray"
}
