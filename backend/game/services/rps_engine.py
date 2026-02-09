import time

VALID_MOVES = ["rock", "paper", "scissors"]
ROUND_TIMEOUT = 2  # seconds
ROUNDS_TO_WIN = 2


def validate_move(move: str):
    return move in VALID_MOVES


def decide_round_winner(move1, move2):
    if move1 == move2:
        return "draw"

    if (
        (move1 == "rock" and move2 == "scissors") or
        (move1 == "scissors" and move2 == "paper") or
        (move1 == "paper" and move2 == "rock")
    ):
        return "player1"

    return "player2"
