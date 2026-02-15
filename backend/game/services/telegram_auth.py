import logging
from django.conf import settings
from init_data_py import InitData

logger = logging.getLogger(__name__)


def _get_bot_token():
    """Bot token with no surrounding quotes or whitespace."""
    raw = (getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
    return raw.strip('"').strip("'").strip() if raw else ""


def verify_telegram_data(init_data_str: str):
    """
    Verify Telegram WebApp init data using init-data-py library.
    Returns a dictionary of user data if valid, else None.
    
    This handles raw vs URL-encoded data automatically.
    """
    if not init_data_str:
        return None

    token = _get_bot_token()
    if not token:
        logger.error("Telegram auth: TELEGRAM_BOT_TOKEN not set")
        return None

    try:
        # Parse the initData string
        # InitData.parse handles decoding and extracting fields
        data = InitData.parse(init_data_str)
        
        # Validate the signature
        # lifetime=None means no expiration check (for now)
        if not data.validate(token, lifetime=None):
            logger.warning("Telegram auth: validation failed (signature mismatch or expired)")
            return None
            
        # Return user data as a dictionary (compatible with view expectations)
        # The library parses 'user' into a User object.
        if not data.user:
            logger.warning("Telegram auth: valid signature but no user data")
            return None
            
        user_dict = {
            "id": data.user.id,
            "username": data.user.username,
            "first_name": data.user.first_name,
            "last_name": data.user.last_name,
            "language_code": data.user.language_code,
            "is_premium": data.user.is_premium,
        }
        return {"user": user_dict}

    except Exception as e:
        # Log the exception but return None to signify auth failure
        logger.warning(f"Telegram auth: verification error: {e}")
        return None
