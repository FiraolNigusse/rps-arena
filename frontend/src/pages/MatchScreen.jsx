/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable react-hooks/purity */
/* eslint-disable react-hooks/immutability */
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

export default function MatchScreen() {
  const navigate = useNavigate()

  const [selectedMove, setSelectedMove] = useState(null)
  const [timeLeft, setTimeLeft] = useState(10)
  const [matchState, setMatchState] = useState("choosing") 
  // choosing | waiting

  // Countdown Timer
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

  const handleMoveSelect = (move) => {
    if (matchState !== "choosing") return

    setSelectedMove(move)
    setMatchState("waiting")

    // simulate opponent response
    setTimeout(() => {
      const moves = ["rock", "paper", "scissors"]
      const opponentMove = moves[Math.floor(Math.random() * 3)]

      navigate("/results", {
        state: {
          playerMove: move,
          opponentMove: opponentMove,
        },
      })
    }, 3000)
  }

  return (
    <div style={containerStyle}>
      <h2>Match</h2>

      <div style={timerStyle(timeLeft)}>
        {timeLeft}
      </div>

      <div style={{ marginTop: 20 }}>
        {matchState === "choosing" && <p>Choose your move</p>}
        {matchState === "waiting" && <p>Waiting for opponent...</p>}
      </div>

      <div style={buttonContainer}>
        <MoveButton
          label="Rock"
          value="rock"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
        <MoveButton
          label="Paper"
          value="paper"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
        <MoveButton
          label="Scissors"
          value="scissors"
          selectedMove={selectedMove}
          disabled={matchState !== "choosing"}
          onClick={handleMoveSelect}
        />
      </div>
    </div>
  )
}

function MoveButton({ label, value, selectedMove, disabled, onClick }) {
  const isSelected = selectedMove === value

  return (
    <button
      onClick={() => onClick(value)}
      disabled={disabled}
      style={{
        padding: "15px 30px",
        fontSize: 16,
        borderRadius: 12,
        border: isSelected ? "3px solid green" : "1px solid #ccc",
        backgroundColor: disabled ? "#eee" : "white",
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      {label}
    </button>
  )
}

const containerStyle = {
  textAlign: "center",
  marginTop: 40,
}

const buttonContainer = {
  marginTop: 30,
  display: "flex",
  justifyContent: "center",
  gap: 20,
}

const timerStyle = (timeLeft) => ({
  fontSize: 40,
  fontWeight: "bold",
  color: timeLeft <= 3 ? "red" : "black",
})
