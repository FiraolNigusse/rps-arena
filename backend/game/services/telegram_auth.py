import hashlib
import hmac
import logging
from urllib.parse import parse_qsl, unquote
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_bot_token():
    """Bot token with no surrounding quotes or whitespace."""
    raw = (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
    return raw.strip('"').strip("'").strip() if raw else ""


def _calculate_hmac(key: bytes, message: str) -> str:
    return hmac.new(
        key,
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_telegram_data(init_data: str):
    """
    Verify Telegram WebApp init data.
    Validates using the "Web App" strategy (HMAC-SHA256 of "WebAppData" as secret).
    
    Attempt 1: Standard (Unquoted) - parses query string, unquotes values, sorts.
    Attempt 2: Raw (Encoded) - Splits string, keeps raw values, sorts.
    """
    if not init_data:
        return None

    try:
        # 1. Parse standard (decodes keys/values)
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        logger.warning("Telegram auth: failed to parse init_data")
        return None

    received_hash = parsed_data.pop("hash", None)
    if not received_hash:
        logger.warning("Telegram auth: no hash in initData")
        return None

    token = _get_bot_token()
    if not token:
        logger.warning("Telegram auth: TELEGRAM_BOT_TOKEN not set")
        return None

    # Calculate secret keys
    try:
        # Web App Mode (Standard)
        secret_key_webapp = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        
        # Login Widget Mode (Legacy/Different)
        secret_key_login = hashlib.sha256(token.encode("utf-8")).digest()
    except Exception as e:
        logger.error(f"Telegram auth: error generating secret keys: {e}")
        return None

    # --- Verification Strategy 1: Standard (Unquoted values) ---
    # This is the most common standard. parse_qsl unquotes values (e.g. %7B -> {).
    try:
        data_check_string_unquoted = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        # Check WebApp signature
        if hmac.compare_digest(_calculate_hmac(secret_key_webapp, data_check_string_unquoted), received_hash):
            return parsed_data
            
        # Check Login Widget signature
        if hmac.compare_digest(_calculate_hmac(secret_key_login, data_check_string_unquoted), received_hash):
            return parsed_data

    except Exception as e:
        logger.warning(f"Telegram auth: Standard check error: {e}")

    # --- Verification Strategy 2: Raw (Preserve Encoding) ---
    # Some clients/setups might hash the raw URL-encoded values.
    # We manually split to avoid unquoting.
    try:
        raw_pairs = []
        for chunk in init_data.split('&'):
            if not chunk or '=' not in chunk:
                continue
            key, value = chunk.split('=', 1)
            if key == 'hash':
                continue
            raw_pairs.append(f"{key}={value}")
        
        raw_pairs.sort()
        data_check_string_raw = "\n".join(raw_pairs)

        if hmac.compare_digest(_calculate_hmac(secret_key_webapp, data_check_string_raw), received_hash):
            return parsed_data # Return the parsed dict for easy usage
            
        if hmac.compare_digest(_calculate_hmac(secret_key_login, data_check_string_raw), received_hash):
            return parsed_data

    except Exception as e:
        logger.warning(f"Telegram auth: Raw check error: {e}")

    logger.warning("Telegram auth: hash mismatch (checked Standard and Raw)")
    return None

