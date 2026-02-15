from game.models import Match, User
from game.services.wallet import deduct_coins


def enter_match(player1: User, player2: User, stake: int, player1_ip=None, player2_ip=None):
    """
    Deduct coins from both players and create match (escrow).
    """
    deduct_coins(player1, stake, tx_type="stake")
    deduct_coins(player2, stake, tx_type="stake")

    match = Match.objects.create(
        player1=player1,
        player2=player2,
        stake=stake,
        status="active",
        player1_ip=player1_ip,
        player2_ip=player2_ip,
    )

    return match
