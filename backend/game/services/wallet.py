from django.db import transaction
from game.models import User, Transaction


def get_available_balance(user: User) -> int:
    """Coins available to spend or withdraw (excludes locked)."""
    return user.coins


def lock_coins(user: User, amount: int) -> None:
    """
    Move coins to locked (e.g. for withdrawal request).
    User cannot spend locked coins until withdrawal is approved or rejected.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if user.coins < amount:
        raise ValueError("Insufficient balance")

    with transaction.atomic():
        user.coins -= amount
        user.locked_coins += amount
        user.save()


def unlock_coins(user: User, amount: int) -> None:
    """Move locked coins back to available (e.g. withdrawal rejected)."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if user.locked_coins < amount:
        raise ValueError("Insufficient locked balance")

    with transaction.atomic():
        user.locked_coins -= amount
        user.coins += amount
        user.save()


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
