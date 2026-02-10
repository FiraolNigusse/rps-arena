import math
from game.models import Rating

K_FACTOR = 32


def expected_score(rating_a, rating_b):
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))


def update_elo(winner_rating, loser_rating):
    expected_winner = expected_score(winner_rating.value, loser_rating.value)
    expected_loser = expected_score(loser_rating.value, winner_rating.value)

    winner_rating.value += int(K_FACTOR * (1 - expected_winner))
    loser_rating.value += int(K_FACTOR * (0 - expected_loser))

    winner_rating.save()
    loser_rating.save()
