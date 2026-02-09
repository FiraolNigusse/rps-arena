from django.shortcuts import render
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

    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "coins": user.coins,
        "rating": user.rating,
        "new_user": created,
    })
from django.views.decorators.http import require_POST
from game.services.wallet import add_coins, deduct_coins
from game.models import User
import json


@require_POST
def wallet_balance(request):
    """
    Temporary endpoint: get wallet balance by telegram_id
    """
    body = json.loads(request.body)
    telegram_id = body.get("telegram_id")

    user = User.objects.get(telegram_id=telegram_id)

    return JsonResponse({
        "coins": user.coins
    })


@require_POST
def wallet_add_coins(request):
    """
    Admin/manual coin addition (testing only)
    """
    body = json.loads(request.body)
    telegram_id = body.get("telegram_id")
    amount = int(body.get("amount"))

    user = User.objects.get(telegram_id=telegram_id)
    add_coins(user, amount, tx_type="purchase")

    return JsonResponse({
        "message": "Coins added",
        "coins": user.coins
    })


@require_POST
def wallet_deduct_coins(request):
    """
    Deduct coins for match entry
    """
    body = json.loads(request.body)
    telegram_id = body.get("telegram_id")
    amount = int(body.get("amount"))

    user = User.objects.get(telegram_id=telegram_id)
    deduct_coins(user, amount, tx_type="stake")

    return JsonResponse({
        "message": "Coins deducted",
        "coins": user.coins
    })
