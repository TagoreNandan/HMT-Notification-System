
from tests.conftest import auth_headers


def test_create_and_list_notification_preference(client) -> None:
    headers = auth_headers(client, email="notify@example.com")

    create_resp = client.post(
        "/notification-preferences",
        json={"channel_type": "email", "destination": "alerts@example.com"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["channel_type"] == "email"
    assert body["destination"] == "alerts@example.com"
    assert body["is_verified"] is False

    list_resp = client.get("/notification-preferences", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_notification_preferences_require_auth(client) -> None:
    response = client.get("/notification-preferences")
    assert response.status_code == 401


def test_user_cannot_delete_another_users_preference(client) -> None:
    owner_headers = auth_headers(client, email="owner-notify@example.com")
    other_headers = auth_headers(client, email="other-notify@example.com")

    create_resp = client.post(
        "/notification-preferences",
        json={"channel_type": "ntfy", "destination": "owner-topic"},
        headers=owner_headers,
    )
    preference_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/notification-preferences/{preference_id}",
        headers=other_headers,
    )
    assert delete_resp.status_code == 404


def test_users_only_see_own_notification_preferences(client) -> None:
    user_a_headers = auth_headers(client, email="usera-notify@example.com")
    user_b_headers = auth_headers(client, email="userb-notify@example.com")

    client.post(
        "/notification-preferences",
        json={"channel_type": "email", "destination": "a@example.com"},
        headers=user_a_headers,
    )
    client.post(
        "/notification-preferences",
        json={"channel_type": "ntfy", "destination": "b-topic"},
        headers=user_b_headers,
    )

    user_a_prefs = client.get("/notification-preferences", headers=user_a_headers).json()
    user_b_prefs = client.get("/notification-preferences", headers=user_b_headers).json()

    assert len(user_a_prefs) == 1
    assert user_a_prefs[0]["destination"] == "a@example.com"
    assert len(user_b_prefs) == 1
    assert user_b_prefs[0]["destination"] == "b-topic"
