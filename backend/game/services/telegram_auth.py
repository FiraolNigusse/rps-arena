import hashlib
import hmac
import logging
from urllib.parse import parse_qsl, unquote
from django.conf import settings

logger = logging.getLogger(__name__)


def _check_hash(parsed_data, received_hash, use_unquote):
    """Build data_check_string and verify hash. use_unquote=True for decoded values."""
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
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
        token.encode(),
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

        if getattr(settings, "DEBUG", False):
            return parsed_data

        if not received_hash:
            logger.warning("Telegram auth: no hash in initData")
            return None

        if not (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip():
            logger.warning("Telegram auth: TELEGRAM_BOT_TOKEN not set")
            return None

        # Try unquoted first (Telegram docs / common impl), then raw
        if _check_hash(parsed_data, received_hash, use_unquote=True):
            return parsed_data
        if _check_hash(parsed_data, received_hash, use_unquote=False):
            return parsed_data

        logger.warning("Telegram auth: hash mismatch (check token and initData format)")
        return None

    except Exception as e:
        logger.exception("Telegram auth error: %s", e)
        return None
