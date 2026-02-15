import hashlib
import hmac
from urllib.parse import parse_qsl, unquote
from django.conf import settings


def verify_telegram_data(init_data: str):
    """
    Verify Telegram WebApp init data per https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        parsed_data.pop("signature", None)

        if getattr(settings, "DEBUG", False):
            return parsed_data

        if not received_hash:
            return None

        if not (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip():
            return None

        # Build data_check_string with UNQUOTED values (required by Telegram)
        data_check_string = "\n".join(
            f"{key}={unquote(value)}" for key, value in sorted(parsed_data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            return parsed_data

        return None

    except Exception as e:
        return None
