from django.db import models
from django.utils import timezone


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)

    coins = models.IntegerField(default=1000)
    locked_coins = models.IntegerField(default=0)
    is_banned = models.BooleanField(default=False)
    is_flagged = models.BooleanField(
        default=False,
        help_text="Suspicious account; blocks withdrawals",
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username or self.telegram_id}"


class Rating(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    value = models.IntegerField(default=1000)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.value}"


class Match(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]

    player1 = models.ForeignKey(User, related_name='player1_matches', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='player2_matches', on_delete=models.CASCADE)

    stake = models.IntegerField()

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    player1_ip = models.GenericIPAddressField(null=True, blank=True)
    player2_ip = models.GenericIPAddressField(null=True, blank=True)

    winner = models.ForeignKey(
        User,
        related_name='wins',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Match {self.id} ({self.player1} vs {self.player2})"



class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('stake', 'Stake'),
        ('win', 'Win'),
        ('commission', 'Commission'),
        ('purchase', 'Purchase'),
        ('withdrawal', 'Withdrawal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} {self.type} {self.amount}"

class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Unique ID we send to Telegram as payload
    payload_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # These are filled when the payment succeeds
    telegram_payment_charge_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    provider_payment_charge_id = models.CharField(max_length=255, null=True, blank=True)
    
    amount = models.IntegerField(help_text="Amount in Stars (XTR)")
    coins_credited = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} Stars ({self.status})"
class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    wallet_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


class PlatformRevenue(models.Model):
    """Tracks rake (10% house fee) from each match."""
    amount = models.IntegerField()
    match = models.ForeignKey(
        Match,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Null for quick-play vs AI",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rake {self.amount} coins"
