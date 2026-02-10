from game.models import Match


def can_gain_rating(player, opponent):
    recent_matches = Match.objects.filter(
        player1=player,
        player2=opponent
    ).order_by("-created_at")[:5]

    return recent_matches.count() < 3
