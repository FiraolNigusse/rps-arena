from django.shortcuts import render
from game.services.auth import jwt_required
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .services.telegram_auth import verify_telegram_data

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

    # ISSUE JWT AFTER VERIFIED LOGIN
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

from django.views.decorators.http import require_POST
from game.services.wallet import add_coins, deduct_coins
from game.models import User
import json


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
