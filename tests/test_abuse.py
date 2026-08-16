from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from config import get_settings
from core.change_detection import ChangeType, DetectedChange
from db.models import (
    ChannelType,
    NotificationPreference,
    Product,
    Snapshot,
    User,
    VerificationToken,
)
from notifications.dispatcher import dispatch_product_changes
from tests.conftest import auth_headers
from tests.test_hmt_adapter import SAMPLE_URL


@pytest.fixture()
def actionable_changes() -> list[DetectedChange]:
    return [
        DetectedChange(
            change_type=ChangeType.PRICE_CHANGE,
            old_value="1800.0",
            new_value="1950.0",
        )
    ]


def _seed_email_preference(
    db_session, verified: bool = False
) -> tuple[User, Product, Snapshot, NotificationPreference]:
    user = User(email="verify@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    product = Product(
        user_id=user.id,
        url=SAMPLE_URL,
        site_name="hmt",
        title="Test Watch",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

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

    preference = NotificationPreference(
        user_id=user.id,
        channel_type=ChannelType.EMAIL,
        destination="alerts@example.com",
        is_verified=verified,
    )
    db_session.add(preference)
    db_session.commit()
    db_session.refresh(preference)
    return user, product, snapshot, preference


@patch("notifications.email.requests.post")
def test_dispatcher_skips_unverified_email(
    mock_post, db_session, actionable_changes
) -> None:
    _, product, snapshot, _ = _seed_email_preference(db_session, verified=False)

    with patch("notifications.email.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.resend_from_email = "monitor@example.com"
        mock_settings.return_value.request_timeout_seconds = 30

        dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_post.assert_not_called()


@patch("notifications.email.requests.post")
def test_dispatcher_sends_verified_email(
    mock_post, db_session, actionable_changes
) -> None:
    mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)
    _, product, snapshot, _ = _seed_email_preference(db_session, verified=True)

    with patch("notifications.email.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.return_value.resend_from_email = "monitor@example.com"
        mock_settings.return_value.request_timeout_seconds = 30

        dispatch_product_changes(db_session, product, snapshot, actionable_changes)

    mock_post.assert_called_once()


@patch("api.notifications.send_verification_email")
def test_email_preference_created_unverified(mock_send, client) -> None:
    headers = auth_headers(client, email="pref@example.com")
    response = client.post(
        "/notification-preferences",
        json={"channel_type": "email", "destination": "alerts@example.com"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["is_verified"] is False
    mock_send.assert_called_once()


def test_verify_endpoint_sets_is_verified(client, db_session) -> None:
    headers = auth_headers(client, email="verify-endpoint@example.com")
    create_resp = client.post(
        "/notification-preferences",
        json={"channel_type": "email", "destination": "verify-me@example.com"},
        headers=headers,
    )
    preference_id = create_resp.json()["id"]

    token = VerificationToken(
        preference_id=preference_id,
        token="valid-test-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(token)
    db_session.commit()

    verify_resp = client.get("/notification-preferences/verify?token=valid-test-token")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_verified"] is True

    preference = db_session.get(NotificationPreference, preference_id)
    assert preference is not None
    assert preference.is_verified is True


def test_verify_endpoint_rejects_invalid_token(client) -> None:
    response = client.get("/notification-preferences/verify?token=not-a-real-token")
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


def test_verify_endpoint_rejects_expired_token(client, db_session) -> None:
    headers = auth_headers(client, email="expired@example.com")
    create_resp = client.post(
        "/notification-preferences",
        json={"channel_type": "email", "destination": "expired@example.com"},
        headers=headers,
    )
    preference_id = create_resp.json()["id"]

    token = VerificationToken(
        preference_id=preference_id,
        token="expired-test-token",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(token)
    db_session.commit()

    response = client.get("/notification-preferences/verify?token=expired-test-token")
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


@patch("api.routes.get_adapter_for_url")
@patch("scheduler.jobs.get_adapter_for_url")
def test_product_limit_blocks_creation(
    mock_jobs_adapter, mock_api_adapter, client, monkeypatch
) -> None:
    from adapters.base import ProductSnapshot

    monkeypatch.setenv("MAX_PRODUCTS_PER_USER", "2")
    get_settings.cache_clear()

    mock_adapter = mock_api_adapter.return_value
    mock_adapter.site_name = "hmt"
    mock_adapter.fetch_product.return_value = ProductSnapshot(
        url=SAMPLE_URL,
        title="Watch",
        price=100.0,
        in_stock=True,
    )
    mock_jobs_adapter.return_value = mock_adapter

    headers = auth_headers(client, email="limit@example.com")

    for index in range(2):
        resp = client.post(
            "/products",
            json={"url": f"https://hmtwatches.in/product_overview?id=test{index}"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text

    blocked = client.post(
        "/products",
        json={"url": "https://hmtwatches.in/product_overview?id=test-overflow"},
        headers=headers,
    )
    assert blocked.status_code == 400
    assert "Product limit reached" in blocked.json()["detail"]

    get_settings.cache_clear()


def test_signup_rate_limit(client) -> None:
    from api.rate_limit import limiter

    limiter.enabled = True
    limiter.reset()

    for index in range(5):
        response = client.post(
            "/auth/signup",
            json={"email": f"rate{index}@example.com", "password": "password123"},
        )
        assert response.status_code == 201, response.text

    blocked = client.post(
        "/auth/signup",
        json={"email": "rate6@example.com", "password": "password123"},
    )
    assert blocked.status_code == 429


def test_delete_account_cascades(client, db_session) -> None:
    from db.models import ChangeEvent

    headers = auth_headers(client, email="delete-me@example.com")
    token = headers["Authorization"].split(" ", 1)[1]
    from core.security import decode_access_token

    user_id = decode_access_token(token)

    preference = NotificationPreference(
        user_id=user_id,
        channel_type=ChannelType.NTFY,
        destination="delete-topic",
        is_verified=True,
    )
    product = Product(
        user_id=user_id,
        url=SAMPLE_URL,
        site_name="hmt",
        title="Delete Watch",
    )
    db_session.add_all([preference, product])
    db_session.commit()
    db_session.refresh(product)

    snapshot = Snapshot(
        product_id=product.id,
        title="Delete Watch",
        price=100.0,
        in_stock=True,
        raw={},
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    event = ChangeEvent(
        product_id=product.id,
        snapshot_id=snapshot.id,
        change_type="price_change",
        old_value="90",
        new_value="100",
        details={},
    )
    db_session.add(event)
    db_session.commit()

    delete_resp = client.delete("/account", headers=headers)
    assert delete_resp.status_code == 204

    assert db_session.get(User, user_id) is None
    assert db_session.query(Product).filter(Product.user_id == user_id).count() == 0
    assert (
        db_session.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .count()
        == 0
    )
    assert db_session.query(Snapshot).count() == 0
    assert db_session.query(ChangeEvent).count() == 0
