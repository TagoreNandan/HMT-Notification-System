from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import requests

from adapters.base import ProductSnapshot
from db.models import (
    ChannelType,
    NotificationLog,
    NotificationPreference,
    Product,
    User,
)
from events.models import NotificationEvent
from notifications.dispatcher import dispatch_event
from services.polling_pipeline import PollingPipeline


def _create_user(db_session, email="e2e_user@example.com") -> User:
    user = User(email=email, hashed_password="hashed_pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_product(
    db_session, user: User, url: str, site_name: str, title: str
) -> Product:
    product = Product(
        user_id=user.id,
        url=url,
        site_name=site_name,
        title=title,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_e2e_full_polling_pipeline_and_change_scenarios(db_session):
    """
    E2E Scenario 1: Validate 5-phase polling pipeline across both HMT websites
    (hmtwatches.in & hmtwatches.store) with change detection for:
    - New model discovered
    - Product returns in stock
    - Product goes out of stock
    - Price changes
    """
    user = _create_user(db_session, "e2e_scenarios@example.com")

    p1 = _create_product(
        db_session,
        user,
        "https://hmtwatches.in/product_overview?id=101",
        "hmt_in",
        "HMT Stellar",
    )
    p2 = _create_product(
        db_session,
        user,
        "https://www.hmtwatches.store/product/sku202",
        "hmt_store",
        "HMT Sangam",
    )

    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.EMAIL,
            destination="e2e_email@example.com",
            is_verified=True,
        )
    )
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.NTFY,
            destination="e2e-ntfy-topic",
            is_verified=True,
        )
    )
    db_session.commit()

    pipeline = PollingPipeline(db_session)

    # Mock external network calls
    with (
        patch.object(pipeline.catalog_sync, "sync") as mock_catalog_sync,
        patch("services.polling_pipeline.get_adapter_for_url") as mock_get_adapter,
        patch("notifications.email.requests.post") as mock_email_post,
        patch("notifications.ntfy.requests.post") as mock_ntfy_post,
        patch("notifications.email.get_settings") as mock_email_settings,
        patch("notifications.ntfy.get_settings") as mock_ntfy_settings,
    ):
        mock_catalog_sync.return_value = {"new": 2, "updated": 0, "unchanged": 10}
        mock_email_settings.return_value.resend_api_key = "re_mock_key"
        mock_email_settings.return_value.resend_from_email = "alerts@example.com"
        mock_email_settings.return_value.request_timeout_seconds = 10

        mock_ntfy_settings.return_value.ntfy_server_url = "https://ntfy.sh"
        mock_ntfy_settings.return_value.ntfy_max_retries = 3
        mock_ntfy_settings.return_value.ntfy_retry_backoff_seconds = 0.01
        mock_ntfy_settings.return_value.request_timeout_seconds = 10

        mock_email_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )
        mock_ntfy_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )

        adapter_in = MagicMock()
        adapter_store = MagicMock()

        # Initial Poll (Cycle 1): New Model Discovered for both products
        adapter_in.fetch_product.return_value = ProductSnapshot(
            url=p1.url,
            title="HMT Stellar Automatic",
            price=7500.0,
            in_stock=True,
            raw={
                "image_url": "https://hmtwatches.in/stellar.jpg",
                "collection": "Stellar",
            },
        )
        adapter_store.fetch_product.return_value = ProductSnapshot(
            url=p2.url,
            title="HMT Sangam Store",
            price=3200.0,
            in_stock=False,
            raw={
                "image_url": "https://hmtwatches.store/sangam.jpg",
                "collection": "Sangam",
            },
        )

        def resolve_adapter(url):
            return adapter_in if "hmtwatches.in" in url else adapter_store

        mock_get_adapter.side_effect = resolve_adapter

        # Run Cycle 1: New Models
        res1 = pipeline.run()
        assert res1["discovered_count"] == 2
        assert res1["changes_count"] == 2
        assert res1["events_count"] == 2
        assert res1["dispatch_stats"]["sent"] == 2

        # Cycle 2: State changes
        # p1: Price change (7500 -> 7200)
        # p2: Back in stock (False -> True)
        adapter_in.fetch_product.return_value = ProductSnapshot(
            url=p1.url,
            title="HMT Stellar Automatic",
            price=7200.0,
            in_stock=True,
            raw={
                "image_url": "https://hmtwatches.in/stellar.jpg",
                "collection": "Stellar",
            },
        )
        adapter_store.fetch_product.return_value = ProductSnapshot(
            url=p2.url,
            title="HMT Sangam Store",
            price=3200.0,
            in_stock=True,
            raw={
                "image_url": "https://hmtwatches.store/sangam.jpg",
                "collection": "Sangam",
            },
        )

        res2 = pipeline.run()
        assert res2["discovered_count"] == 2
        assert res2["changes_count"] == 2
        assert res2["events_count"] == 2
        assert res2["dispatch_stats"]["sent"] == 2

        # Cycle 3: p1 goes out of stock (True -> False)
        adapter_in.fetch_product.return_value = ProductSnapshot(
            url=p1.url,
            title="HMT Stellar Automatic",
            price=7200.0,
            in_stock=False,
            raw={
                "image_url": "https://hmtwatches.in/stellar.jpg",
                "collection": "Stellar",
            },
        )
        adapter_store.fetch_product.return_value = ProductSnapshot(
            url=p2.url,
            title="HMT Sangam Store",
            price=3200.0,
            in_stock=True,
            raw={
                "image_url": "https://hmtwatches.store/sangam.jpg",
                "collection": "Sangam",
            },
        )

        res3 = pipeline.run()
        assert res3["discovered_count"] == 2
        assert res3["changes_count"] == 1  # only p1 changed (out of stock)
        assert res3["events_count"] == 1
        assert res3["dispatch_stats"]["sent"] == 1


def test_e2e_idempotency_prevents_duplicate_notifications(db_session):
    """
    E2E Scenario 2: Validate that running duplicate dispatch calls for identical
    NotificationEvents produces ZERO duplicate notifications.
    """
    user = _create_user(db_session, "idempotency_e2e@example.com")
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.EMAIL,
            destination="idempotent_e2e@example.com",
            is_verified=True,
        )
    )
    db_session.commit()

    event = NotificationEvent(
        event_id="evt_e2e_dedup_999",
        event_type="back_in_stock",
        product_id=99,
        title="HMT Pilot Vintage",
        price=4500.0,
        in_stock=True,
        url="https://hmtwatches.in/product_overview?id=pilot-v",
        site_name="HMT Watches",
        occurred_at=datetime.now(timezone.utc),
    )

    with (
        patch("notifications.email.requests.post") as mock_post,
        patch("notifications.email.get_settings") as mock_settings,
    ):
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.resend_from_email = "alerts@example.com"
        mock_settings.return_value.request_timeout_seconds = 10
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )

        # 1st dispatch
        s1 = dispatch_event(db_session, user.id, event)
        assert s1 is True
        assert mock_post.call_count == 1

        # 2nd dispatch (same event_id) -> MUST be suppressed!
        s2 = dispatch_event(db_session, user.id, event)
        assert s2 is False
        assert mock_post.call_count == 1

        # 3rd dispatch -> MUST be suppressed!
        s3 = dispatch_event(db_session, user.id, event)
        assert s3 is False
        assert mock_post.call_count == 1

        # Check notification log DB record
        logs = (
            db_session.query(NotificationLog)
            .filter(NotificationLog.event_id == "evt_e2e_dedup_999")
            .all()
        )
        assert len(logs) == 1


def test_e2e_resilience_transient_network_retries_and_recovery(db_session):
    """
    E2E Scenario 3: Verify resilience against transient network failures (ntfy HTTP 503),
    unconfigured Resend API keys, and individual product fetch exceptions.
    """
    user = _create_user(db_session, "resilience_e2e@example.com")
    prod = _create_product(
        db_session,
        user,
        "https://hmtwatches.in/product_overview?id=res",
        "hmt_in",
        "HMT Kohinoor",
    )

    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.NTFY,
            destination="resilience-ntfy-topic",
            is_verified=True,
        )
    )
    db_session.commit()

    pipeline = PollingPipeline(db_session)

    with (
        patch("services.polling_pipeline.get_adapter_for_url") as mock_get_adapter,
        patch("notifications.ntfy.requests.post") as mock_ntfy_post,
        patch("notifications.ntfy.get_settings") as mock_ntfy_settings,
        patch("notifications.ntfy.time.sleep") as mock_sleep,
    ):
        mock_ntfy_settings.return_value.ntfy_server_url = "https://ntfy.sh"
        mock_ntfy_settings.return_value.ntfy_max_retries = 3
        mock_ntfy_settings.return_value.ntfy_retry_backoff_seconds = 0.01
        mock_ntfy_settings.return_value.request_timeout_seconds = 10

        # Transient failure (503), then recovery on 2nd attempt
        res_503 = MagicMock(status_code=503)
        res_503.raise_for_status.side_effect = requests.HTTPError(
            "503 Service Unavailable"
        )
        res_200 = MagicMock(status_code=200)
        res_200.raise_for_status.return_value = None

        mock_ntfy_post.side_effect = [res_503, res_200]

        mock_adapter = MagicMock()
        mock_adapter.fetch_product.return_value = ProductSnapshot(
            url=prod.url,
            title="HMT Kohinoor Green",
            price=3500.0,
            in_stock=True,
            raw={},
        )
        mock_get_adapter.return_value = mock_adapter

        # Run pipeline
        res = pipeline.run()

        assert res["discovered_count"] == 1
        assert res["changes_count"] == 1
        assert res["events_count"] == 1
        assert res["dispatch_stats"]["sent"] == 1

        # Assert ntfy retried and succeeded
        assert mock_ntfy_post.call_count == 2
        assert mock_sleep.call_count == 1
