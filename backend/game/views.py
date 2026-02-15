import json
import time
import random

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta


from .models import User, Match, Payment, Withdrawal, Transaction, Rating
from game.services.auth import jwt_required
from game.services.telegram_auth import verify_telegram_data
from game.services.wallet import add_coins, deduct_coins, lock_coins
from game.services.rps_engine import validate_move, decide_round_winner
from game.services.round_state import start_round, submit_move, get_round, end_round
from game.services.matchmaking import enqueue_player
from game.services.payout import payout_match
from game.services.rating_service import expected_score, update_elo

# -------------------------
# Telegram login
# -------------------------
@csrf_exempt
def telegram_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    body = json.loads(request.body)
    init_data = body.get("initData")

    if not init_data:
        return JsonResponse({"error": "Missing initData"}, status=400)

    data = verify_telegram_data(init_data)
    if not data:
        return JsonResponse({"error": "Invalid Telegram signature"}, status=403)

    user_data = json.loads(data.get("user"))
    telegram_id = user_data["id"]
    username = user_data.get("username") or f"user_{telegram_id}"

    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username},
    )
    rating_obj, _ = Rating.objects.get_or_create(user=user, defaults={"value": 1000})

    from game.services.jwt_service import generate_jwt
    token = generate_jwt(user)

    return JsonResponse({
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "coins": user.coins,
            "rating": rating_obj.value,
        },
        "new_user": created,
    })

# -------------------------
# Wallet endpoints
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def wallet_balance(request):
    return JsonResponse({
        "coins": request.user.coins,
        "locked_coins": request.user.locked_coins,
    })


@csrf_exempt
@jwt_required
@require_GET
def wallet_transactions(request):
    """List transactions for current user: type, amount, date."""
    txs = Transaction.objects.filter(user=request.user).order_by("-created_at")[:50]
    return JsonResponse({
        "transactions": [
            {
                "type": tx.type,
                "amount": tx.amount,
                "date": tx.created_at.isoformat(),
            }
            for tx in txs
        ]
    })


@csrf_exempt
@jwt_required
@require_POST
def wallet_add_coins(request):
    body = json.loads(request.body)
    amount = int(body.get("amount"))

    add_coins(request.user, amount, tx_type="purchase")

    return JsonResponse({
        "message": "Coins added",
        "coins": request.user.coins
    })


@csrf_exempt
@jwt_required
@require_POST
def wallet_deduct_coins(request):
    body = json.loads(request.body)
    amount = int(body.get("amount"))

    deduct_coins(request.user, amount, tx_type="stake")

    return JsonResponse({
        "message": "Coins deducted",
        "coins": request.user.coins
    })

# -------------------------
# Find match with IP tracking
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def find_match(request):
    body = json.loads(request.body)
    stake = int(body.get("stake"))

    ip_address = request.META.get("REMOTE_ADDR")  # <-- store IP

    match = enqueue_player(request.user, stake, ip_address)

    if match:
        return JsonResponse({
            "matched": True,
            "match_id": match.id
        })

    return JsonResponse({
        "matched": False,
        "message": "Waiting for opponent"
    })

# -------------------------
# Submit move
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def submit_move_view(request):
    body = json.loads(request.body)
    match_id = body.get("match_id")
    move = body.get("move")

    # Validate move
    if not validate_move(move):
        return JsonResponse({"error": "Invalid move"}, status=400)

    # Rapid play detection: max 10 matches per minute
    recent_matches = Match.objects.filter(
        player1=request.user
    ).filter(
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).count()

    if recent_matches > 10:
        return JsonResponse({"error": "Too many matches. Slow down."}, status=429)

    match = Match.objects.get(id=match_id)

    round_data = get_round(match_id)
    if not round_data:
        start_round(match_id)
        round_data = get_round(match_id)

    if time.time() - round_data["start_time"] > 2:
        end_round(match_id)
        return JsonResponse({"error": "Round timeout"}, status=400)

    submit_move(match_id, request.user.id, move)

    moves = round_data["moves"]
    if len(moves) < 2:
        return JsonResponse({"status": "waiting"})

    p1 = match.player1.id
    p2 = match.player2.id

    result = decide_round_winner(
        moves.get(p1),
        moves.get(p2)
    )

    if result == "player1":
        match.player1_score += 1
    elif result == "player2":
        match.player2_score += 1

    match.save()
    end_round(match_id)

    if match.player1_score == 2 or match.player2_score == 2:
        from game.services.payout import payout_match

        winner = match.player1 if match.player1_score == 2 else match.player2
        match.winner = winner
        match.status = "finished"
        match.save()

        payout_match(winner, match.stake, match=match)

        return JsonResponse({
            "match_finished": True,
            "winner": winner.username
        })

    return JsonResponse({
        "round_result": result,
        "player1_score": match.player1_score,
        "player2_score": match.player2_score
    })

# -------------------------
# Telegram webhook for payments
# -------------------------
@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid request"}, status=400)

    data = json.loads(request.body)

    if "message" in data and "successful_payment" in data["message"]:
        payment = data["message"]["successful_payment"]

        telegram_user = data["message"]["from"]["id"]
        total_amount = payment["total_amount"]

        try:
            user = User.objects.get(telegram_id=telegram_user)
            coins_to_credit = total_amount // 100

            Payment.objects.create(
                user=user,
                telegram_payment_charge_id=payment["telegram_payment_charge_id"],
                provider_payment_charge_id=payment["provider_payment_charge_id"],
                amount=total_amount,
                coins_credited=coins_to_credit,
            )

            user.coins += coins_to_credit
            user.save()

            return JsonResponse({"status": "ok"})

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"status": "ignored"})

# Stake options (fixed values only, Phase 1)
STAKE_OPTIONS = [50, 100, 200]
AI_OPPONENT_RATING = 1000
K_FACTOR = 32


# -------------------------
# Quick-play vs AI (for Telegram Mini App)
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def quick_play_submit(request):
    """Single-round RPS vs random opponent. Deducts stake, pays out on win, updates rating."""
    body = json.loads(request.body)
    move = body.get("move")
    stake = int(body.get("stake", 0))

    if not validate_move(move):
        return JsonResponse({"error": "Invalid move"}, status=400)

    if stake not in STAKE_OPTIONS:
        return JsonResponse({"error": "Invalid stake"}, status=400)

    if request.user.coins < stake:
        return JsonResponse({"error": "Insufficient balance"}, status=400)

    # Deduct stake
    deduct_coins(request.user, stake, tx_type="stake")
    balance_after_stake = request.user.coins

    opponent_move = random.choice(["rock", "paper", "scissors"])
    result = decide_round_winner(move, opponent_move)

    # Map internal result to frontend format
    result_map = {"player1": "win", "player2": "lose", "draw": "draw"}
    result_str = result_map.get(result, "draw")

    if result_str == "win":
        payout_match(request.user, stake)
        request.user.refresh_from_db()
        coins_delta = request.user.coins - balance_after_stake
    else:
        coins_delta = -stake

    # Rating: get or create, then update vs AI (fixed 1000)
    rating_obj, _ = Rating.objects.get_or_create(user=request.user, defaults={"value": 1000})
    old_rating = rating_obj.value
    expected = expected_score(old_rating, AI_OPPONENT_RATING)
    actual = 1 if result_str == "win" else (0.5 if result_str == "draw" else 0)
    rating_delta = int(K_FACTOR * (actual - expected))
    rating_obj.value = max(0, old_rating + rating_delta)
    rating_obj.save()

    return JsonResponse({
        "player_move": move,
        "opponent_move": opponent_move,
        "result": result_str,
        "coins_delta": coins_delta,
        "rating_delta": rating_delta,
        "new_balance": request.user.coins,
        "new_rating": rating_obj.value,
    })


# -------------------------
# Request withdrawal
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def request_withdrawal(request):
    body = json.loads(request.body)
    amount = int(body.get("amount", 0))
    wallet = body.get("wallet", "").strip()

    MIN_WITHDRAW = 50
    DAILY_LIMIT = 500

    if amount < MIN_WITHDRAW:
        return JsonResponse({"error": "Minimum withdrawal is 50"}, status=400)

    if not wallet:
        return JsonResponse({"error": "Wallet address is required"}, status=400)

    if request.user.is_flagged:
        return JsonResponse(
            {"error": "Account under review. Withdrawals are temporarily disabled."},
            status=403,
        )

    if request.user.coins < amount:
        return JsonResponse({"error": "Insufficient balance"}, status=400)

    today = timezone.now().date()
    daily_total = Withdrawal.objects.filter(
        user=request.user,
        requested_at__date=today,
    ).aggregate(total=Sum("amount"))["total"] or 0

    if daily_total + amount > DAILY_LIMIT:
        return JsonResponse({"error": "Daily withdrawal limit exceeded"}, status=400)

    try:
        lock_coins(request.user, amount)
    except ValueError:
        return JsonResponse({"error": "Insufficient balance"}, status=400)

    Withdrawal.objects.create(
        user=request.user,
        amount=amount,
        wallet_address=wallet,
    )

    return JsonResponse({"message": "Withdrawal request submitted"})


@csrf_exempt
@jwt_required
@require_GET
def withdraw_list(request):
    """List withdrawals for current user: amount, status, date."""
    withdrawals = Withdrawal.objects.filter(user=request.user).order_by("-requested_at")[:20]
    return JsonResponse({
        "withdrawals": [
            {
                "amount": w.amount,
                "status": w.status,
                "date": w.requested_at.isoformat(),
            }
            for w in withdrawals
        ]
    })
