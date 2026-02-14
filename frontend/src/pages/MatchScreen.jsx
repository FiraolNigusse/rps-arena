/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable react-hooks/purity */
/* eslint-disable react-hooks/immutability */
import { useEffect, useState, useRef } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { apiPost } from "../api/api"
import "./MatchScreen.css"

export default function MatchScreen() {
  const navigate = useNavigate()
  const location = useLocation()
  const stake = location.state?.stake ?? 50

  const [selectedMove, setSelectedMove] = useState(null)
  const [timeLeft, setTimeLeft] = useState(2)
  const [matchState, setMatchState] = useState("choosing")
  const [errorMessage, setErrorMessage] = useState(null)
  const submitInProgress = useRef(false)

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
    if (matchState !== "choosing" || submitInProgress.current) return

    submitInProgress.current = true
    setErrorMessage(null)
    setSelectedMove(move)
    setMatchState("waiting")

    try {
      const data = await apiPost("/match/submit/", { move, stake })

      navigate("/results", {
        state: {
          playerMove: data.player_move,
          opponentMove: data.opponent_move,
          result: data.result,
          coinsDelta: data.coins_delta,
          ratingDelta: data.rating_delta,
          newBalance: data.new_balance,
          newRating: data.new_rating,
        },
      })
    } catch (err) {
      console.error(err)
      const msg = err?.status === 403
        ? "Connection denied. Please refresh and try again."
        : err?.data?.error || "Something went wrong. Please try again."
      setErrorMessage(msg)
      setMatchState("choosing")
      setSelectedMove(null)
    } finally {
      submitInProgress.current = false
    }
  }

  return (
    <div className="match-screen">
      <button
        type="button"
        className="match-screen__back btn-secondary"
        onClick={() => navigate("/play")}
      >
        Back
      </button>
      <h1 className="match-screen__title">RPS Arena</h1>
      <p className="match-screen__subtitle">Choose your move</p>

      <div className={`match-screen__timer ${timeLeft <= 1 ? "match-screen__timer--urgent" : ""}`}>
        {timeLeft}
      </div>

      <div className="match-screen__status">
        {matchState === "choosing" && !errorMessage && <span>Pick before time runs out</span>}
        {matchState === "choosing" && errorMessage && (
          <span className="match-screen__status--error">{errorMessage}</span>
        )}
        {matchState === "waiting" && (
          <span className="match-screen__status--waiting">Processing your move...</span>
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
