from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


from adapters.base import ProductSnapshot
from core.change_detection import ChangeType, create_notification_event, detect_changes
from db.models import (
    ChannelType,
    NotificationLog,
    NotificationPreference,
    Product,
    User,
)
from events.models import NotificationEvent
from notifications.base import NotificationChannel
from notifications.dispatcher import dispatch_event, register_channel
from notifications.messages import (
    format_html,
    format_plain_text,
    format_subject,
    format_whatsapp,
)


def _create_user(db_session, email="pipeline_user@example.com") -> User:
    user = User(email=email, hashed_password="password_hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_product(db_session, user: User) -> Product:
    product = Product(
        user_id=user.id,
        url="https://hmtwatches.in/product_overview?id=101",
        site_name="HMT Watches",
        title="HMT Stellar Automatic",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_detect_all_four_event_types():
    """Verify that all 4 required event types are detected correctly."""
    # 1. New model (initial snapshot)
    curr_new = ProductSnapshot(
        url="https://hmtwatches.in/product_overview?id=101",
        title="HMT Stellar Automatic",
        price=7500.0,
        in_stock=True,
    )
    changes_new = detect_changes(None, curr_new)
    assert len(changes_new) == 1
    assert changes_new[0].change_type == ChangeType.NEW_MODEL

    # 2. Back in stock
    prev_out = ProductSnapshot(
        url="https://hmtwatches.in/product_overview?id=101",
        title="HMT Stellar Automatic",
        price=7500.0,
        in_stock=False,
    )
    curr_in = ProductSnapshot(
        url="https://hmtwatches.in/product_overview?id=101",
        title="HMT Stellar Automatic",
        price=7500.0,
        in_stock=True,
    )
    changes_stock_in = detect_changes(prev_out, curr_in)
    assert any(c.change_type == ChangeType.BACK_IN_STOCK for c in changes_stock_in)

    # 3. Out of stock
    changes_stock_out = detect_changes(curr_in, prev_out)
    assert any(c.change_type == ChangeType.OUT_OF_STOCK for c in changes_stock_out)

    # 4. Price change
    curr_price_change = ProductSnapshot(
        url="https://hmtwatches.in/product_overview?id=101",
        title="HMT Stellar Automatic",
        price=8200.0,
        in_stock=True,
    )
    changes_price = detect_changes(curr_in, curr_price_change)
    assert any(c.change_type == ChangeType.PRICE_CHANGE for c in changes_price)


def test_every_detected_event_produces_notification_event(db_session):
    """Verify that every detected event produces a valid NotificationEvent."""
    user = _create_user(db_session)
    product = _create_product(db_session, user)

    event_types = [
        ChangeType.NEW_MODEL,
        ChangeType.BACK_IN_STOCK,
        ChangeType.OUT_OF_STOCK,
        ChangeType.PRICE_CHANGE,
    ]

    for etype in event_types:
        change = detect_changes(
            ProductSnapshot(url=product.url, title="T", price=100.0, in_stock=False),
            ProductSnapshot(
                url=product.url,
                title="T",
                price=200.0 if etype == ChangeType.PRICE_CHANGE else 100.0,
                in_stock=etype != ChangeType.OUT_OF_STOCK,
            ),
        )[0]
        # Override change_type for test coverage
        change.change_type = etype

        event = create_notification_event(
            change=change,
            product_id=product.id,
            title=product.title,
            price=7500.0,
            in_stock=True,
            url=product.url,
            site_name=product.site_name,
        )

        assert isinstance(event, NotificationEvent)
        assert event.event_type == etype.value
        assert event.product_id == product.id
        assert event.title == product.title
        assert event.url == product.url


def test_rich_html_email_template_contains_all_required_fields():
    """
    Verify HTML email template contains product image, title, collection,
    source website, price, stock status, timestamp, and product link.
    """
    now = datetime(2026, 9, 27, 11, 4, 30, tzinfo=timezone.utc)
    event = NotificationEvent(
        event_id="evt_test_123",
        event_type="back_in_stock",
        product_id=42,
        title="HMT Pilot Hand-Wound Special",
        price=4999.50,
        in_stock=True,
        url="https://hmtwatches.in/product_overview?id=pilot",
        site_name="HMT Watches Official",
        occurred_at=now,
        image_url="https://hmtwatches.in/storage/app/public/image/all_images/pilot.jpg",
        collection="Heritage Collection",
        old_value="out_of_stock",
        new_value="in_stock",
    )

    html = format_html(event)

    # 1. Product Image
    assert "https://hmtwatches.in/storage/app/public/image/all_images/pilot.jpg" in html
    # 2. Title
    assert "HMT Pilot Hand-Wound Special" in html
    # 3. Collection
    assert "Heritage Collection" in html
    # 4. Source Website
    assert "HMT Watches Official" in html
    # 5. Price
    assert "4,999.50" in html or "4999.5" in html
    # 6. Stock Status
    assert "IN STOCK" in html
    # 7. Timestamp
    assert "September 27, 2026" in html
    # 8. Product Link
    assert "https://hmtwatches.in/product_overview?id=pilot" in html


def test_channel_agnostic_dispatcher(db_session):
    """Verify dispatcher uses registered channels dynamically."""

    class CustomChannel(NotificationChannel):
        received_events = []

        def __init__(self, destination: str | None = None):
            self.destination = destination

        def send(self, event: NotificationEvent, snapshot=None, changes=None) -> None:
            CustomChannel.received_events.append((self.destination, event))

    register_channel(ChannelType.CONSOLE, CustomChannel)

    user = _create_user(db_session, "custom_channel_user@example.com")
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.CONSOLE,
            destination="console_term",
            is_verified=True,
        )
    )
    db_session.commit()

    event = NotificationEvent(
        event_id="evt_custom_100",
        event_type="new_model",
        product_id=1,
        title="HMT Janata",
        price=2500.0,
        in_stock=True,
        url="https://hmtwatches.in/janata",
        site_name="HMT",
        occurred_at=datetime.now(timezone.utc),
    )

    CustomChannel.received_events.clear()
    dispatched = dispatch_event(db_session, user.id, event)

    assert dispatched is True
    assert len(CustomChannel.received_events) == 1
    dest, rec_event = CustomChannel.received_events[0]
    assert rec_event.event_id == "evt_custom_100"


def test_idempotency_prevents_duplicate_notifications(db_session):
    """Verify duplicate alerts are suppressed for the same event."""
    user = _create_user(db_session, "idempotent_user@example.com")
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.EMAIL,
            destination="idempotent@example.com",
            is_verified=True,
        )
    )
    db_session.commit()

    event = NotificationEvent(
        event_id="evt_idempotency_test_001",
        event_type="price_change",
        product_id=99,
        title="HMT Kohinoor Mechanical",
        price=3200.0,
        in_stock=True,
        url="https://hmtwatches.in/kohinoor",
        site_name="HMT Watches",
        occurred_at=datetime.now(timezone.utc),
        old_value="3500.0",
        new_value="3200.0",
    )

    with (
        patch("notifications.email.requests.post") as mock_post,
        patch("notifications.email.get_settings") as mock_settings,
    ):
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.resend_from_email = "alerts@example.com"
        mock_settings.return_value.request_timeout_seconds = 30
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )

        # First dispatch -> should send email
        res1 = dispatch_event(db_session, user.id, event)
        assert res1 is True
        assert mock_post.call_count == 1

        # Check DB log created
        log_count = (
            db_session.query(NotificationLog)
            .filter(NotificationLog.event_id == "evt_idempotency_test_001")
            .count()
        )
        assert log_count == 1

        # Second dispatch with identical event_id -> MUST BE SUPPRESSED (Idempotent!)
        res2 = dispatch_event(db_session, user.id, event)
        assert res2 is False
        assert mock_post.call_count == 1  # Still 1 call! No duplicate email sent!


def test_format_subject_all_event_types():
    def base_evt(etype: str) -> NotificationEvent:
        return NotificationEvent(
            event_id="e1",
            event_type=etype,
            product_id=1,
            title="HMT Sona",
            price=2000.0,
            in_stock=True,
            url="http://x",
            site_name="HMT",
            occurred_at=datetime.now(timezone.utc),
            old_value="2500.0",
            new_value="2000.0",
        )

    assert "New Model" in format_subject(base_evt("new_model"))
    assert "Back in Stock" in format_subject(base_evt("back_in_stock"))
    assert "Out of Stock" in format_subject(base_evt("out_of_stock"))
    assert "Price Dropped" in format_subject(base_evt("price_change"))


def test_format_plain_text_and_whatsapp():
    evt = NotificationEvent(
        event_id="e2",
        event_type="back_in_stock",
        product_id=1,
        title="HMT Tareeq",
        price=1800.0,
        in_stock=True,
        url="https://hmtwatches.in/tareeq",
        site_name="HMT",
        occurred_at=datetime.now(timezone.utc),
        collection="Tareeq Series",
    )
    text = format_plain_text(evt)
    assert "HMT Tareeq" in text
    assert "Tareeq Series" in text

    wa = format_whatsapp(evt)
    assert "HMT Tareeq" in wa
    assert "Tareeq Series" in wa
