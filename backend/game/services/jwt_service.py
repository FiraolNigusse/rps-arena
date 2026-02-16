import jwt
import datetime
from django.conf import settings


def generate_jwt(user):
    payload = {
        "user_id": user.id,
        "telegram_id": user.telegram_id,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            seconds=settings.JWT_EXP_DELTA_SECONDS
        )
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_jwt(token):
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
