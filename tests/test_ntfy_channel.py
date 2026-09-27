from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import requests

from db.models import ChannelType, NotificationPreference, User
from events.models import NotificationEvent
from notifications.dispatcher import dispatch_event
from notifications.ntfy import NtfyNotificationChannel, format_ntfy_message


def _create_event(event_type: str = "back_in_stock") -> NotificationEvent:
    return NotificationEvent(
        event_id="evt_ntfy_101",
        event_type=event_type,
        product_id=5,
        title="HMT Stellar Automatic Blue",
        price=7500.0,
        in_stock=True,
        url="https://hmtwatches.in/product_overview?id=stellar-blue",
        site_name="HMT Watches",
        occurred_at=datetime.now(timezone.utc),
        collection="Stellar Automatic",
    )


def test_ntfy_topic_and_url_configuration():
    # 1. Simple topic name
    ch1 = NtfyNotificationChannel("my-watch-alerts")
    assert ch1.get_url() == "https://ntfy.sh/my-watch-alerts"

    # 2. Topic with leading slash
    ch2 = NtfyNotificationChannel("/my-custom-topic/")
    assert ch2.get_url() == "https://ntfy.sh/my-custom-topic"

    # 3. Full HTTP URL
    ch3 = NtfyNotificationChannel("https://custom-ntfy.example.com/topic-x")
    assert ch3.get_url() == "https://custom-ntfy.example.com/topic-x"

    # 4. Custom server URL passed to channel constructor
    ch4 = NtfyNotificationChannel("my-topic", server_url="https://ntfy.internal.net")
    assert ch4.get_url() == "https://ntfy.internal.net/my-topic"


def test_format_ntfy_message_concise_with_emoji_price_stock_url():
    evt = _create_event("back_in_stock")
    title, body, product_url = format_ntfy_message(evt)

    # Title emoji and product name
    assert "✅" in title
    assert "Back in Stock" in title
    assert "HMT Stellar Automatic Blue" in title

    # Body fields
    assert "HMT Stellar Automatic Blue" in body
    assert "Price: ₹7,500.00" in body
    assert "Stock: In Stock ✅" in body
    assert "Collection: Stellar Automatic" in body
    assert "URL: https://hmtwatches.in/product_overview?id=stellar-blue" in body

    assert product_url == "https://hmtwatches.in/product_overview?id=stellar-blue"


@patch("notifications.ntfy.requests.post")
@patch("notifications.ntfy.get_settings")
def test_ntfy_sends_correct_headers_and_payload(mock_settings, mock_post):
    mock_settings.return_value.ntfy_server_url = "https://ntfy.sh"
    mock_settings.return_value.ntfy_max_retries = 3
    mock_settings.return_value.ntfy_retry_backoff_seconds = 0.01
    mock_settings.return_value.request_timeout_seconds = 10
    mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)

    channel = NtfyNotificationChannel("my-watch-topic")
    evt = _create_event("price_change")

    channel.send(evt)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://ntfy.sh/my-watch-topic"
    headers = kwargs["headers"]
    assert "Title" in headers
    assert "💰 Price Change — HMT Stellar Automatic Blue" in headers["Title"]
    assert headers["Click"] == "https://hmtwatches.in/product_overview?id=stellar-blue"
    assert headers["Tags"] == "watch,shopping_cart"


@patch("notifications.ntfy.time.sleep")
@patch("notifications.ntfy.requests.post")
@patch("notifications.ntfy.get_settings")
def test_ntfy_retries_transient_failures(mock_settings, mock_post, mock_sleep):
    mock_settings.return_value.ntfy_server_url = "https://ntfy.sh"
    mock_settings.return_value.ntfy_max_retries = 3
    mock_settings.return_value.ntfy_retry_backoff_seconds = 0.01
    mock_settings.return_value.request_timeout_seconds = 10

    # First 2 attempts fail with 503, 3rd attempt succeeds 200
    res_503 = MagicMock(status_code=503)
    res_503.raise_for_status.side_effect = requests.HTTPError("503 Service Unavailable")

    res_200 = MagicMock(status_code=200)
    res_200.raise_for_status.return_value = None

    mock_post.side_effect = [res_503, res_503, res_200]

    channel = NtfyNotificationChannel("retry-topic")
    evt = _create_event("new_model")

    channel.send(evt)

    assert mock_post.call_count == 3
    assert mock_sleep.call_count == 2


@patch("notifications.ntfy.time.sleep")
@patch("notifications.ntfy.requests.post")
@patch("notifications.ntfy.get_settings")
def test_ntfy_fails_fast_on_non_transient_error(mock_settings, mock_post, mock_sleep):
    mock_settings.return_value.ntfy_server_url = "https://ntfy.sh"
    mock_settings.return_value.ntfy_max_retries = 3
    mock_settings.return_value.ntfy_retry_backoff_seconds = 0.01
    mock_settings.return_value.request_timeout_seconds = 10

    # 400 Bad Request is non-transient -> fail fast, 1 call only
    res_400 = MagicMock(status_code=400)
    res_400.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
    mock_post.return_value = res_400

    channel = NtfyNotificationChannel("fail-topic")
    evt = _create_event("out_of_stock")

    channel.send(evt)

    assert mock_post.call_count == 1
    assert mock_sleep.call_count == 0


def test_ntfy_channel_integrated_in_dispatcher(db_session):
    user = User(email="ntfy_user@example.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.NTFY,
            destination="dispatcher-ntfy-topic",
            is_verified=True,
        )
    )
    db_session.commit()

    evt = _create_event("back_in_stock")

    with (
        patch("notifications.ntfy.requests.post") as mock_post,
        patch("notifications.ntfy.get_settings") as mock_settings,
    ):
        mock_settings.return_value.ntfy_server_url = "https://ntfy.sh"
        mock_settings.return_value.ntfy_max_retries = 3
        mock_settings.return_value.ntfy_retry_backoff_seconds = 0.01
        mock_settings.return_value.request_timeout_seconds = 10
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )

        dispatched = dispatch_event(db_session, user.id, evt)

        assert dispatched is True
        mock_post.assert_called_once()
        assert mock_post.call_args.args[0] == "https://ntfy.sh/dispatcher-ntfy-topic"
