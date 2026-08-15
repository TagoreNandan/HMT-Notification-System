from unittest.mock import MagicMock, patch

import pytest

from core.change_detection import ChangeType, DetectedChange
from db.models import ChannelType, NotificationPreference, Product, Snapshot, User
from notifications.dispatcher import dispatch_product_changes


def _make_user(db_session, email: str = "dispatch@example.com") -> User:
    user = User(email=email, hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_product(db_session, user: User) -> Product:
    product = Product(
        user_id=user.id,
        url="https://hmtwatches.in/product_overview?id=test",
        site_name="hmt",
        title="Test Watch",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def _make_snapshot(db_session, product: Product) -> Snapshot:
    snapshot = Snapshot(
        product_id=product.id,
        title="Test Watch",
        price=1950.0,
        in_stock=True,
        raw={},
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    return snapshot


@pytest.fixture()
def actionable_changes() -> list[DetectedChange]:
    return [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGE,
            old_value="1800.0",
            new_value="1950.0",
        )
    ]


@patch("notifications.email.requests.post")
def test_dispatcher_sends_email_via_resend(
    mock_post, db_session, actionable_changes
) -> None:
    mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)

    user = _make_user(db_session)
    product = _make_product(db_session, user)
    snapshot = _make_snapshot(db_session, product)
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.EMAIL,
            destination="alerts@example.com",
            is_verified=True,
        )
    )
    db_session.commit()

    with patch("notifications.email.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.resend_from_email = "monitor@example.com"
        mock_settings.return_value.request_timeout_seconds = 30

        dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["to"] == ["alerts@example.com"]
    assert call_kwargs["json"]["from"] == "monitor@example.com"
    subject = call_kwargs["json"]["subject"]

    assert "Test Watch" in subject
    assert "Updated" in subject
    text = call_kwargs["json"]["text"]

    assert "Price" in text
    assert "1800.0" in text
    assert "1950.0" in text
    assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_key"


@patch("notifications.ntfy.requests.post")
def test_dispatcher_sends_ntfy(
    mock_post, db_session, actionable_changes
) -> None:
    mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)

    user = _make_user(db_session)
    product = _make_product(db_session, user)
    snapshot = _make_snapshot(db_session, product)
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.NTFY,
            destination="my-watch-alerts",
        )
    )
    db_session.commit()

    dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://ntfy.sh/my-watch-alerts"
    body = mock_post.call_args.kwargs["data"]

    assert b"Price" in body
    assert b"1800.0" in body
    assert b"1950.0" in body


@patch("notifications.dispatcher.ConsoleNotificationChannel")
def test_dispatcher_falls_back_to_console_without_preferences(
    mock_console_cls, db_session, actionable_changes
) -> None:
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console

    user = _make_user(db_session)
    product = _make_product(db_session, user)
    snapshot = _make_snapshot(db_session, product)

    dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_console_cls.assert_called_once()
    mock_console.send.assert_called_once_with(product, snapshot, actionable_changes)


@patch("notifications.ntfy.requests.post")
@patch("notifications.email.requests.post")
def test_dispatcher_email_missing_api_key_does_not_break_ntfy(
    mock_email_post, mock_ntfy_post, db_session, actionable_changes
) -> None:
    mock_ntfy_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)

    user = _make_user(db_session)
    product = _make_product(db_session, user)
    snapshot = _make_snapshot(db_session, product)
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.EMAIL,
            destination="alerts@example.com",
            is_verified=True,
        )
    )
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.NTFY,
            destination="fallback-topic",
        )
    )
    db_session.commit()

    with patch("notifications.email.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = ""
        mock_settings.return_value.resend_from_email = "monitor@example.com"
        mock_settings.return_value.request_timeout_seconds = 30

        dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_email_post.assert_not_called()
    mock_ntfy_post.assert_called_once()
