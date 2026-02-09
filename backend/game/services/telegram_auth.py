import hashlib
import hmac
import urllib.parse
from django.conf import settings

def verify_telegram_data(init_data: str) -> dict | None:
    """
    Verifies Telegram WebApp initData.
    Returns parsed data dict if valid, else None.
    """

    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if calculated_hash != received_hash:
        return None

    return parsed_data
