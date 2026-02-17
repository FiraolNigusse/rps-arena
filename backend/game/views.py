import json
import time
import random
from urllib.parse import unquote

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Sum
from datetime import timedelta


import logging
logger = logging.getLogger(__name__)

import uuid
import requests
from django.conf import settings
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
# Health check
# -------------------------
def health_check(request):
    return JsonResponse({"status": "ok", "timestamp": timezone.now().isoformat()})

# -------------------------
# Telegram login
# -------------------------
@csrf_exempt
def telegram_login(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Telegram login request received")
    
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        try:
            body = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        init_data = body.get("initData")

        if not init_data:
            return JsonResponse({"error": "Missing initData"}, status=400)

        # verify_telegram_data now uses init-data-py and returns 
        # {"user": { ...user_dict... }} if valid, else None
        data = verify_telegram_data(init_data)
        if not data:
            return JsonResponse({"error": "Invalid Telegram signature"}, status=403)

        user_data = data.get("user")
        if not user_data:
            return JsonResponse({"error": "Missing user data"}, status=400)
        
        telegram_id = user_data.get("id")
        if not telegram_id:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Telegram auth: Valid hash but missing 'id' in user data. Data: {user_data}")
            return JsonResponse({"error": "Missing user ID in data"}, status=400)

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

    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Telegram auth exception:\n%s", traceback.format_exc())
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)

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
# Telegram payment create
# -------------------------
@csrf_exempt
@jwt_required
@require_POST
def create_invoice_view(request):
    """
    Creates a pending Payment and returns a Telegram Stars invoice link.
    """
    body = json.loads(request.body)
    amount = int(body.get("amount", 10)) # Stars amount
    
    if amount <= 0:
        return JsonResponse({"error": "Invalid amount"}, status=400)

    # 1 Star = 1 Coin (adjust ratio as needed)
    coins_to_credit = amount

    payload_id = f"pay_{uuid.uuid4().hex}"
    
    payment_obj = None
    try:
        payment_obj = Payment.objects.create(
            user=request.user,
            payload_id=payload_id,
            amount=amount,
            coins_credited=coins_to_credit,
            status="pending"
        )

        # Telegram API to get invoice link
        token = settings.TELEGRAM_BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/createInvoiceLink"
        
        payload = {
            "title": f"Purchase {coins_to_credit} Coins",
            "description": f"Buy {coins_to_credit} coins for Rock-Paper-Scissors Arena",
            "payload": payload_id,
            "currency": "XTR",
            "prices": [
                {"label": f"{coins_to_credit} Coins", "amount": amount}
            ]
        }

        resp = requests.post(url, json=payload, timeout=10)
        res_data = resp.json()
        if res_data.get("ok"):
            return JsonResponse({
                "invoice_link": res_data["result"],
                "payment_id": payment_obj.id
            })
        else:
            payment_obj.status = "failed"
            payment_obj.save()
            return JsonResponse({
                "error": "Telegram API Error", 
                "details": res_data.get("description", "Unknown error"),
                "raw": res_data
            }, status=400)
    except Exception as e:
        import traceback
        error_tb = traceback.format_exc()
        logger.error(f"Invoice Creation Error: {error_tb}")
        
        # Try to mark as failed if it was created
        try:
            payment_obj.status = "failed"
            payment_obj.save()
        except:
            pass
            
        return JsonResponse({
            "error": "Internal Server Error", 
            "details": str(e),
            "traceback": error_tb if settings.DEBUG else None
        }, status=500)


# -------------------------
# Telegram webhook for payments
# -------------------------
@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid request"}, status=400)

    data = json.loads(request.body)
    token = settings.TELEGRAM_BOT_TOKEN

    # 1. Handle Pre-Checkout Query (Requirement for Telegram Payments)
    if "pre_checkout_query" in data:
        query = data["pre_checkout_query"]
        payload_id = query.get("invoice_payload")
        
        # Verify if payment exists in our DB
        valid = Payment.objects.filter(payload_id=payload_id, status="pending").exists()
        
        url = f"https://api.telegram.org/bot{token}/answerPreCheckoutQuery"
        answer = {
            "pre_checkout_query_id": query["id"],
            "ok": valid,
            "error_message": "Payment session expired or invalid." if not valid else ""
        }
        requests.post(url, json=answer, timeout=10)
        return JsonResponse({"status": "pre_checkout_handled"})

    # 2. Handle Successful Payment
    if "message" in data and "successful_payment" in data["message"]:
        sp = data["message"]["successful_payment"]
        payload_id = sp.get("invoice_payload")
        telegram_charge_id = sp.get("telegram_payment_charge_id")

        try:
            # Atomic update to prevent race conditions or duplicate processing
            with transaction.atomic():
                # Check for existing completed payment with this charge ID (extra safety)
                if Payment.objects.filter(telegram_payment_charge_id=telegram_charge_id).exists():
                    return JsonResponse({"status": "already_processed"})

                payment_obj = Payment.objects.select_for_update().get(payload_id=payload_id)
                
                if payment_obj.status == "completed":
                    return JsonResponse({"status": "already_completed"})

                # Update payment record
                payment_obj.telegram_payment_charge_id = telegram_charge_id
                payment_obj.provider_payment_charge_id = sp.get("provider_payment_charge_id")
                payment_obj.status = "completed"
                payment_obj.save()

                # Credit user
                user = payment_obj.user
                add_coins(user, payment_obj.coins_credited, tx_type="purchase")

            return JsonResponse({"status": "ok"})

        except Payment.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Payment record not found for payload: {payload_id}")
            return JsonResponse({"error": "Payment record not found"}, status=404)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Webhook error: {traceback.format_exc()}")
            return JsonResponse({"error": str(e)}, status=500)

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
