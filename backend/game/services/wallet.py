from django.db import transaction
from game.models import User, Transaction


def add_coins(user: User, amount: int, tx_type="purchase"):
    """
    Add coins to a user and log transaction.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")

    with transaction.atomic():
        user.coins += amount
        user.save()

        Transaction.objects.create(
            user=user,
            amount=amount,
            type=tx_type
        )


def deduct_coins(user: User, amount: int, tx_type="stake"):
    """
    Deduct coins from a user and log transaction.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")

    if user.coins < amount:
        raise ValueError("Insufficient balance")

    with transaction.atomic():
        user.coins -= amount
        user.save()

        Transaction.objects.create(
            user=user,
            amount=-amount,
            type=tx_type
        )
