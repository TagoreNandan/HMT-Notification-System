from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, TypeAdapter, field_validator, model_validator
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.rate_limit import (
    get_notification_preference_key,
    limiter,
    notification_preference_rate_limit,
)
from db.models import ChannelType, NotificationPreference, User, VerificationToken
from notifications.verification import (
    create_verification_token,
    send_verification_email,
)

router = APIRouter(tags=["notification-preferences"])

email_adapter = TypeAdapter(EmailStr)


class NotificationPreferenceCreateRequest(BaseModel):
    channel_type: ChannelType
    destination: str | None = None

    @field_validator("channel_type")
    @classmethod
    def validate_supported_channel(cls, value: ChannelType) -> ChannelType:
        if value == ChannelType.CONSOLE:
            raise ValueError(
                "Console is a fallback channel and cannot be configured via API"
            )
        return value

    @model_validator(mode="after")
    def validate_destination_for_channel(self) -> "NotificationPreferenceCreateRequest":
        if (
            self.channel_type in {ChannelType.EMAIL, ChannelType.NTFY}
            and not self.destination
        ):
            raise ValueError("destination is required for email and ntfy channels")

        if self.channel_type == ChannelType.EMAIL and self.destination:
            email_adapter.validate_python(self.destination)

        if self.channel_type == ChannelType.NTFY and self.destination:
            topic = self.destination.strip()
            if not topic or any(ch.isspace() for ch in topic):
                raise ValueError("ntfy topic must be a non-empty string without spaces")
            self.destination = topic

        return self


class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: int
    channel_type: ChannelType
    destination: str | None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationResponse(BaseModel):
    message: str
    preference_id: int
    is_verified: bool


@router.post(
    "/notification-preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(
    notification_preference_rate_limit, key_func=get_notification_preference_key
)
def create_notification_preference(
    request: Request,
    payload: NotificationPreferenceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreference:
    existing = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.channel_type == payload.channel_type,
            NotificationPreference.destination == payload.destination,
        )
        .one_or_none()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Notification preference already exists",
        )

    preference = NotificationPreference(
        user_id=current_user.id,
        channel_type=payload.channel_type,
        destination=payload.destination,
        is_verified=False,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    if preference.channel_type == ChannelType.EMAIL:
        token = create_verification_token(db, preference)
        send_verification_email(preference, token)

    return preference


@router.get(
    "/notification-preferences", response_model=list[NotificationPreferenceResponse]
)
def list_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationPreference]:
    return (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == current_user.id)
        .order_by(NotificationPreference.created_at.desc())
        .all()
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/notification-preferences/verify", response_model=VerificationResponse)
def verify_notification_preference(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
) -> VerificationResponse:
    record = (
        db.query(VerificationToken)
        .filter(VerificationToken.token == token)
        .one_or_none()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if _ensure_utc(record.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    preference = record.preference
    preference.is_verified = True
    db.delete(record)
    db.commit()

    return VerificationResponse(
        message="Email notification preference verified successfully",
        preference_id=preference.id,
        is_verified=True,
    )


@router.delete(
    "/notification-preferences/{preference_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_notification_preference(
    preference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    preference = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.id == preference_id,
            NotificationPreference.user_id == current_user.id,
        )
        .one_or_none()
    )
    if preference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found"
        )
    db.delete(preference)
    db.commit()
