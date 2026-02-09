from .views import find_match
from django.urls import path
from .views import (
    telegram_login,
    wallet_balance,
    wallet_add_coins,
    wallet_deduct_coins
)

urlpatterns = [
    path("auth/telegram/", telegram_login),

    path("wallet/balance/", wallet_balance),
    path("wallet/add/", wallet_add_coins),
    path("wallet/deduct/", wallet_deduct_coins),
    path("match/find/", find_match),

]
