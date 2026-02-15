import hashlib
import hmac
import logging
from urllib.parse import parse_qsl, unquote
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_bot_token():
    """Bot token with no surrounding quotes or whitespace (Render may store as "123:ABC")."""
    raw = (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
    return raw.strip('"').strip("'").strip() if raw else ""


def _check_hash(parsed_data, received_hash, use_unquote):
    """Build data_check_string and verify hash. use_unquote=True for decoded values."""
    token = _get_bot_token()
    if not token:
        return False

    if use_unquote:
        data_check_string = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed_data.items())
        )
    else:
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

    secret_key = hmac.new(
        b"WebAppData",
        token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    calculated = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Hash from query string might be URL-encoded
    received = unquote(received_hash) if received_hash else ""
    return hmac.compare_digest(calculated, received)


def verify_telegram_data(init_data: str):
    """
    Verify Telegram WebApp init data.
    Based on User's snippet:
    1. Parse with parse_qsl (this unquotes values).
    2. Pop "hash".
    3. KEEP "signature" (do not pop it).
    4. Sort and join key=value.
    5. Calculate hash.
    """
    try:
        # 1. Parse and extract hash
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        
        if not received_hash:
            logger.warning("Telegram auth: no hash in initData")
            return None

        token = _get_bot_token()
        if not token:
            logger.warning("Telegram auth: TELEGRAM_BOT_TOKEN not set")
            return None

        # 2. Build check string
        # User said: "key=value pairs sorted by key, joined by '\n'"
        # User's snippet used parsed_data directly (which is unquoted).
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        # 3. Calculate Hash
        
        # Strategy A: Login Widget Style (User's Snippet)
        # secret_key = hashlib.sha256(bot_token.encode()).digest()
        secret_key_login = hashlib.sha256(token.encode("utf-8")).digest()
        hash_login = hmac.new(secret_key_login, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        # Strategy B: Web App Style (Standard)
        # secret_key = HMAC("WebAppData", token)
        secret_key_webapp = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        hash_webapp = hmac.new(secret_key_webapp, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        # Check match
        if hmac.compare_digest(hash_login, received_hash):
            return parsed_data
        
        if hmac.compare_digest(hash_webapp, received_hash):
            return parsed_data

        # --- Debugging ---
        logger.warning("Telegram auth mismatch (strict mode)")
        logger.warning(f"  > Received: {received_hash}")
        logger.warning(f"  > Calc Login: {hash_login}")
        logger.warning(f"  > Calc WebApp: {hash_webapp}")
        
        # Also try without signature just to see (for debugging)
        if "signature" in parsed_data:
            parsed_data_no_sig = parsed_data.copy()
            parsed_data_no_sig.pop("signature")
            dcs_no_sig = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data_no_sig.items()))
            h_login_ns = hmac.new(secret_key_login, dcs_no_sig.encode("utf-8"), hashlib.sha256).hexdigest()
            h_webapp_ns = hmac.new(secret_key_webapp, dcs_no_sig.encode("utf-8"), hashlib.sha256).hexdigest()
            logger.warning(f"  > Calc Login (No Sig): {h_login_ns}")
            logger.warning(f"  > Calc WebApp (No Sig): {h_webapp_ns}")

        return None

    except Exception as e:
        logger.exception("Telegram auth error: %s", e)
        return None
