from django.db import models
from django.utils import timezone


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)

    coins = models.IntegerField(default=1000)
    is_banned = models.BooleanField(default=False)

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
    winner = models.ForeignKey(
        User,
        related_name='wins',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

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


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coins = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.coins} ({self.status})"


# Create your models here.
