from django.db.models import Q
from game.models import Match


def is_same_ip_farming(match) -> bool:
    """
    Detect same-IP farming: two accounts from same IP playing each other repeatedly.
    Returns True if we should block rating gains / treat as suspicious.
    """
    if not match.player1_ip or not match.player2_ip:
        return False
    if match.player1_ip != match.player2_ip:
        return False

    # Same IP on this match: check if they play each other repeatedly
    recent = Match.objects.filter(
        Q(player1=match.player1, player2=match.player2)
        | Q(player1=match.player2, player2=match.player1)
    ).order_by("-created_at")[:5]

    return recent.count() >= 3


def can_gain_rating(player, opponent, match=None) -> bool:
    """
    Block rating gains if same pair plays repeatedly or same-IP farming.
    """
    if match and is_same_ip_farming(match):
        return False

    recent_matches = Match.objects.filter(
        Q(player1=player, player2=opponent) | Q(player1=opponent, player2=player)
    ).order_by("-created_at")[:5]

    return recent_matches.count() < 3
