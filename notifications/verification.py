import logging
import secrets
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from config import get_settings
from db.models import NotificationPreference, VerificationToken

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def create_verification_token(db: Session, preference: NotificationPreference) -> VerificationToken:
    settings = get_settings()
    for existing in list(preference.verification_tokens):
        db.delete(existing)

    token = VerificationToken(
        preference_id=preference.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.email_verification_expire_hours),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def send_verification_email(preference: NotificationPreference, token: VerificationToken) -> None:
    settings = get_settings()
    if not settings.resend_api_key or not settings.resend_from_email:
        logger.warning(
            "Resend is not configured; verification email not sent for preference_id=%s",
            preference.id,
        )
        return

    verify_url = (
        f"{settings.base_url.rstrip('/')}/notification-preferences/verify?token={token.token}"
    )
    payload = {
        "from": settings.resend_from_email,
        "to": [preference.destination],
        "subject": "Verify your notification email",
        "text": (
            "Please verify this email address to receive product change notifications.\n\n"
            f"Click to verify: {verify_url}\n\n"
            f"This link expires in {settings.email_verification_expire_hours} hours."
        ),
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            RESEND_API_URL,
            json=payload,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        logger.info(
            "Sent verification email to %s for preference_id=%s",
            preference.destination,
            preference.id,
        )
    except requests.RequestException as exc:
        logger.error(
            "Failed to send verification email to %s for preference_id=%s: %s",
            preference.destination,
            preference.id,
            exc,
        )
