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
    Verify Telegram WebApp init data per
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        parsed_data.pop("signature", None)

        # Early return in DEBUG mode can be disabled if we want to test hash validation locally
        # if getattr(settings, "DEBUG", False):
        #    return parsed_data

        if not received_hash:
            logger.warning("Telegram auth: no hash in initData")
            return None

        token = _get_bot_token()
        if not token:
            logger.warning("Telegram auth: TELEGRAM_BOT_TOKEN not set")
            return None

        # Prepare check string
        # Telegram docs say: "key=value" pairs sorted alphabetically
        # Values should be UNQUOTED (decoded) for the check string? 
        # Actually docs say: "data-check-string is a chain of all received fields, sorted alphabetically... 
        # in the format key=<value> with a line feed character ('\n') as separator."
        # And "received fields" usually implies the values as they are? 
        # But previous working implementations often unquote.
        # We will try both variations if needed, but for logging we will show the main one.

        # Variation 1: Unquoted values (Standard for Web App?)
        data_check_string_unquoted = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed_data.items())
        )
        # Variation 2: Raw values
        data_check_string_raw = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        # --- Calculations ---

        # 1. Web App Style: HMAC-SHA256("WebAppData", token)
        secret_key_webapp = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        hash_webapp_unquoted = hmac.new(secret_key_webapp, data_check_string_unquoted.encode("utf-8"), hashlib.sha256).hexdigest()
        hash_webapp_raw = hmac.new(secret_key_webapp, data_check_string_raw.encode("utf-8"), hashlib.sha256).hexdigest()

        # 2. Login Widget Style (User suggested): SHA256(token)
        secret_key_login = hashlib.sha256(token.encode("utf-8")).digest()
        hash_login_unquoted = hmac.new(secret_key_login, data_check_string_unquoted.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # Check against received hash
        received_hash_decoded = unquote(received_hash) # Just in case hash itself was encoded

        if hmac.compare_digest(hash_webapp_unquoted, received_hash) or \
           hmac.compare_digest(hash_webapp_unquoted, received_hash_decoded):
            return parsed_data
        
        if hmac.compare_digest(hash_webapp_raw, received_hash) or \
           hmac.compare_digest(hash_webapp_raw, received_hash_decoded):
            return parsed_data

        # --- Debugging Logs on Failure ---
        token_preview = f"{token[:5]}...{token[-5:]}" if len(token) > 10 else "N/A"
        
        logger.warning("Telegram auth: HASH MISMATCH DEBUGGING")
        logger.warning(f"  > Init Data Raw: {init_data}")
        logger.warning(f"  > Received Hash: {received_hash}")
        logger.warning(f"  > Token Used:    {token_preview}")
        logger.warning(f"  > Data Check String (Unquoted): {data_check_string_unquoted!r}")
        
        logger.warning(f"  > CALC 1 (WebApp + Unquoted): {hash_webapp_unquoted}")
        logger.warning(f"  > CALC 2 (WebApp + Raw):      {hash_webapp_raw}")
        logger.warning(f"  > CALC 3 (LoginWidget Style): {hash_login_unquoted}")

        if hmac.compare_digest(hash_login_unquoted, received_hash):
             logger.warning("Telegram auth: MATCH FOUND using Login Widget style. Allowing auth.")
             return parsed_data

        return None

    except Exception as e:
        logger.exception("Telegram auth error: %s", e)
        return None
