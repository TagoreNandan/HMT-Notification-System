from fastapi import Request
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings
from core.security import decode_access_token

limiter = Limiter(key_func=get_remote_address)


def signup_rate_limit() -> str:
    return get_settings().signup_rate_limit


def notification_preference_rate_limit() -> str:
    return get_settings().notification_preference_rate_limit


def get_notification_preference_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            user_id = decode_access_token(token)
            return f"user:{user_id}"
        except JWTError:
            pass
    return get_remote_address(request)
