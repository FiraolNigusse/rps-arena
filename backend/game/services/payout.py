from django.db import transaction
from game.models import Transaction


PLATFORM_COMMISSION = 0.05


def payout_match(winner, stake):
    total_pot = stake * 2
    commission = int(total_pot * PLATFORM_COMMISSION)
    payout = total_pot - commission

    with transaction.atomic():
        winner.coins += payout
        winner.save()

        Transaction.objects.create(
            user=winner,
            amount=payout,
            type="win"
        )

        Transaction.objects.create(
            user=winner,
            amount=-commission,
            type="commission"
        )
