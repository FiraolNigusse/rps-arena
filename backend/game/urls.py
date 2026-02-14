from .views import find_match
from django.urls import path
from .views import (
    telegram_login,
    wallet_balance,
    wallet_transactions,
    wallet_add_coins,
    wallet_deduct_coins,
    request_withdrawal,
    withdraw_list,
)
from .views import submit_move_view, quick_play_submit
from .views import telegram_webhook

urlpatterns = [
    path("auth/telegram/", telegram_login),

    path("wallet/balance/", wallet_balance),
    path("wallet/transactions/", wallet_transactions),
    path("wallet/add/", wallet_add_coins),
    path("wallet/deduct/", wallet_deduct_coins),
    path("match/find/", find_match),
    path("match/", submit_move_view),
    path("match/submit/", quick_play_submit),
    path("telegram/webhook/", telegram_webhook),
    path("withdraw/request/", request_withdrawal),
    path("withdraw/list/", withdraw_list),

]
