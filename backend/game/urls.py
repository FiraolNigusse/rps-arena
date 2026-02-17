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
from .views import telegram_webhook, health_check, create_invoice_view, migration_status, run_migrations, repair_db

urlpatterns = [
    path("auth/telegram/", telegram_login),

    path("wallet/balance/", wallet_balance),
    path("wallet/transactions/", wallet_transactions),
    path("wallet/add/", wallet_add_coins),
    path("wallet/deduct/", wallet_deduct_coins),
    path("wallet/stars/invoice/", create_invoice_view),
    path("match/find/", find_match),
    path("match/", submit_move_view),
    path("match/submit/", quick_play_submit),
    path("withdraw/request/", request_withdrawal),
    path("withdraw/list/", withdraw_list),
    path("health/", health_check),
    path("debug/migrations/", migration_status),
    path("debug/migrate/", run_migrations),
    path("debug/repair/", repair_db),
]
