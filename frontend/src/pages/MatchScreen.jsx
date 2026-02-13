/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable react-hooks/purity */
/* eslint-disable react-hooks/immutability */
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiPost, getToken } from "../api/api"
import "./MatchScreen.css"

export default function MatchScreen() {
  const navigate = useNavigate()

  const [selectedMove, setSelectedMove] = useState(null)
  const [timeLeft, setTimeLeft] = useState(10)
  const [matchState, setMatchState] = useState("choosing")

  useEffect(() => {
    if (matchState !== "choosing") return
    if (timeLeft === 0) {
      handleAutoSelect()
      return
    }

    const timer = setTimeout(() => {
      setTimeLeft((prev) => prev - 1)
    }, 1000)

    return () => clearTimeout(timer)
  }, [timeLeft, matchState])

  const handleAutoSelect = () => {
    const moves = ["rock", "paper", "scissors"]
    const randomMove = moves[Math.floor(Math.random() * 3)]
    handleMoveSelect(randomMove)
  }

  const handleMoveSelect = async (move) => {
    if (matchState !== "choosing") return

    setSelectedMove(move)
    setMatchState("waiting")

    try {
      const data = await apiPost("/match/submit/", { move })

      navigate("/results", {
        state: {
          playerMove: data.player_move,
          opponentMove: data.opponent_move,
          result: data.result,
        },
      })
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="match-screen">
      <h1 className="match-screen__title">RPS Arena</h1>
      <p className="match-screen__subtitle">Choose your move</p>

      <div className={`match-screen__timer ${timeLeft <= 3 ? "match-screen__timer--urgent" : ""}`}>
        {timeLeft}
      </div>

      <div className="match-screen__status">
        {matchState === "choosing" && <span>Pick before time runs out</span>}
        {matchState === "waiting" && (
          <span className="match-screen__status--waiting">Waiting for opponent...</span>
        )}
      </div>

      <div className="match-screen__moves">
        <MoveButton
          label="Rock"
          emoji="🪨"
          value="rock"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
        <MoveButton
          label="Paper"
          emoji="📄"
          value="paper"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
        <MoveButton
          label="Scissors"
          emoji="✂️"
          value="scissors"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
      </div>
    </div>
  )
}

function MoveButton({ label, emoji, value, selectedMove, disabled, onClick }) {
  const isSelected = selectedMove === value

  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      disabled={disabled}
      className={`move-btn ${isSelected ? "move-btn--selected" : ""} ${disabled ? "move-btn--disabled" : ""}`}
    >
      <span className="move-btn__emoji">{emoji}</span>
      <span className="move-btn__label">{label}</span>
    </button>
  )
}
