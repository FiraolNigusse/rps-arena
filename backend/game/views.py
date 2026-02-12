from django.shortcuts import render
from game.services.auth import jwt_required
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .services.telegram_auth import verify_telegram_data
from game.services.rps_engine import validate_move, decide_round_winner
from game.services.round_state import start_round, submit_move, get_round, end_round
from game.models import Match
import time
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Payment
import json


@csrf_exempt
def telegram_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    body = json.loads(request.body)
    init_data = body.get("initData")
    print("RAW INIT DATA:", init_data)

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
            "rating": user.rating.value if hasattr(user, "rating") else 1000,
        },
        "new_user": created,
    })


from game.services.wallet import add_coins, deduct_coins


@jwt_required
@require_POST
def wallet_balance(request):
    user = request.user
    return JsonResponse({
        "coins": user.coins
    })


@jwt_required
@require_POST
def wallet_add_coins(request):
    body = json.loads(request.body)
    amount = int(body.get("amount"))

    user = request.user
    add_coins(user, amount, tx_type="purchase")

    return JsonResponse({
        "message": "Coins added",
        "coins": user.coins
    })


@jwt_required
@require_POST
def wallet_deduct_coins(request):
    body = json.loads(request.body)
    amount = int(body.get("amount"))

    user = request.user
    deduct_coins(user, amount, tx_type="stake")

    return JsonResponse({
        "message": "Coins deducted",
        "coins": user.coins
    })


from game.services.matchmaking import enqueue_player


@jwt_required
@require_POST
def find_match(request):
    body = json.loads(request.body)
    stake = int(body.get("stake"))

    match = enqueue_player(request.user, stake)

    if match:
        return JsonResponse({
            "matched": True,
            "match_id": match.id
        })

    return JsonResponse({
        "matched": False,
        "message": "Waiting for opponent"
    })


@jwt_required
@require_POST
def submit_move_view(request):
    body = json.loads(request.body)
    match_id = body.get("match_id")
    move = body.get("move")

    if not validate_move(move):
        return JsonResponse({"error": "Invalid move"}, status=400)

    match = Match.objects.get(id=match_id)

    # Start round if not started
    round_data = get_round(match_id)
    if not round_data:
        start_round(match_id)
        round_data = get_round(match_id)

    # Enforce timer
    if time.time() - round_data["start_time"] > 2:
        end_round(match_id)
        return JsonResponse({"error": "Round timeout"}, status=400)

    submit_move(match_id, request.user.id, move)

    # If both players played, decide result
    moves = round_data["moves"]
    if len(moves) < 2:
        return JsonResponse({"status": "waiting"})

    # Identify players
    p1 = match.player1.id
    p2 = match.player2.id

    result = decide_round_winner(
        moves.get(p1),
        moves.get(p2)
    )

    # Update scores
    if result == "player1":
        match.player1_score += 1
    elif result == "player2":
        match.player2_score += 1

    match.save()
    end_round(match_id)

    # Check for match winner
    if match.player1_score == 2 or match.player2_score == 2:
        from game.services.payout import payout_match
        from game.services.rating_service import update_elo
        from game.services.anti_farm import can_gain_rating
        from game.models import Rating

        winner = match.player1 if match.player1_score == 2 else match.player2
        loser = match.player2 if winner == match.player1 else match.player1

        payout_match(winner, match.stake)

        if can_gain_rating(winner, loser):
            update_elo(
                Rating.objects.get(user=winner),
                Rating.objects.get(user=loser)
            )

        match.winner = winner
        match.status = "finished"
        match.save()

        return JsonResponse({
            "match_finished": True,
            "winner": winner.username
        })

    return JsonResponse({
        "round_result": result,
        "player1_score": match.player1_score,
        "player2_score": match.player2_score
    })
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Match
import random

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_match(request):
    move = request.data.get("move")

    opponent_moves = ["rock", "paper", "scissors"]
    opponent = random.choice(opponent_moves)

    if move == opponent:
        result = "draw"
    elif (
        (move == "rock" and opponent == "scissors") or
        (move == "paper" and opponent == "rock") or
        (move == "scissors" and opponent == "paper")
    ):
        result = "win"
    else:
        result = "lose"

    match = Match.objects.create(
        player=request.user,
        player_move=move,
        opponent_move=opponent,
        result=result,
    )

    return Response({
        "player_move": move,
        "opponent_move": opponent,
        "result": result
    })
@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)

        if "message" in data and "successful_payment" in data["message"]:
            payment = data["message"]["successful_payment"]

            telegram_charge_id = payment["telegram_payment_charge_id"]
            provider_charge_id = payment["provider_payment_charge_id"]
            total_amount = payment["total_amount"]

            telegram_user = data["message"]["from"]["id"]

            try:
                user = User.objects.get(telegram_id=telegram_user)

                coins_to_credit = total_amount // 100  # example rate

                Payment.objects.create(
                    user=user,
                    telegram_payment_charge_id=telegram_charge_id,
                    provider_payment_charge_id=provider_charge_id,
                    amount=total_amount,
                    coins_credited=coins_to_credit,
                )

                user.coins += coins_to_credit
                user.save()

                return JsonResponse({"status": "ok"})

            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=404)

        return JsonResponse({"status": "ignored"})

    return JsonResponse({"error": "invalid request"}, status=400)
