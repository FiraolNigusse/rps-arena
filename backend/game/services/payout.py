from django.db import transaction
from game.models import Transaction, PlatformRevenue


RAKE_PERCENT = 0.10  # 10% house fee


def payout_match(winner, stake, match=None):
    """
    Pay winner from pot minus 10% rake.
    pot = stake * 2, rake = 10%, winner gets 90%.
    """
    pot = stake * 2
    rake = int(pot * RAKE_PERCENT)
    winner_reward = pot - rake

    with transaction.atomic():
        winner.coins += winner_reward
        winner.save()

        Transaction.objects.create(
            user=winner,
            amount=winner_reward,
            type="win",
        )

        Transaction.objects.create(
            user=winner,
            amount=-rake,
            type="commission",
        )

        PlatformRevenue.objects.create(amount=rake, match=match)
