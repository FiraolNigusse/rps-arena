import json
import time
import random

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import User, Match, Payment, Withdrawal
from game.services.auth import jwt_required
from game.services.telegram_auth import verify_telegram_data
from game.services.wallet import add_coins, deduct_coins
from game.services.rps_engine import validate_move, decide_round_winner
from game.services.round_state import start_round, submit_move, get_round, end_round
from game.services.matchmaking import enqueue_player

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

    from game.services.jwt_service import generate_jwt
    token = generate_jwt(user)

    return JsonResponse({
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "coins": user.coins,
        },
        "new_user": created,
    })

# -------------------------
# Wallet endpoints
# -------------------------
@jwt_required
@require_POST
def wallet_balance(request):
    return JsonResponse({"coins": request.user.coins})


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
        return Response({"error": "Too many matches. Slow down."}, status=429)

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

        payout_match(winner, match.stake)

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

# -------------------------
# Request withdrawal
# -------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_withdrawal(request):
    amount = int(request.data.get("amount"))
    wallet = request.data.get("wallet")

    MIN_WITHDRAW = 50
    DAILY_LIMIT = 500

    if amount < MIN_WITHDRAW:
        return Response({"error": "Minimum withdrawal is 50"}, status=400)

    if request.user.coins < amount:
        return Response({"error": "Insufficient balance"}, status=400)

    today = timezone.now().date()

    daily_total = Withdrawal.objects.filter(
        user=request.user,
        requested_at__date=today,
    ).aggregate(total=Sum("amount"))["total"] or 0

    if daily_total + amount > DAILY_LIMIT:
        return Response({"error": "Daily withdrawal limit exceeded"}, status=400)

    Withdrawal.objects.create(
        user=request.user,
        amount=amount,
        wallet_address=wallet,
    )

    return Response({"message": "Withdrawal request submitted"})
