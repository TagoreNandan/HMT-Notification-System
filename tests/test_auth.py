from unittest.mock import patch

from tests.conftest import auth_headers
from tests.test_hmt_adapter import SAMPLE_URL
from tests.test_api import MOCK_SNAPSHOT


def test_signup_returns_token(client) -> None:
    response = client.post(
        "/auth/signup",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_signup_duplicate_email_fails(client) -> None:
    payload = {"email": "duplicate@example.com", "password": "password123"}
    first = client.post("/auth/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/signup", json=payload)
    assert second.status_code == 409
    assert "already registered" in second.json()["detail"].lower()


def test_login_wrong_password_fails(client) -> None:
    client.post("/auth/signup", json={"email": "loginuser@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        json={"email": "loginuser@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_success_returns_token(client) -> None:
    client.post("/auth/signup", json={"email": "validlogin@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        json={"email": "validlogin@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_products_without_token_fails(client) -> None:
    response = client.get("/products")
    assert response.status_code == 401


@patch("api.routes.get_adapter_for_url")
@patch("scheduler.jobs.get_adapter_for_url")
def test_user_cannot_access_another_users_product(mock_jobs_adapter, mock_api_adapter, client) -> None:
    mock_adapter = mock_api_adapter.return_value
    mock_adapter.site_name = "hmt"
    mock_adapter.fetch_product.return_value = MOCK_SNAPSHOT
    mock_jobs_adapter.return_value = mock_adapter

    owner_headers = auth_headers(client, email="owner@example.com")
    create_resp = client.post("/products", json={"url": SAMPLE_URL}, headers=owner_headers)
    product_id = create_resp.json()["id"]

    other_headers = auth_headers(client, email="other@example.com")

    history_resp = client.get(f"/products/{product_id}/history", headers=other_headers)
    assert history_resp.status_code == 404

    delete_resp = client.delete(f"/products/{product_id}", headers=other_headers)
    assert delete_resp.status_code == 404


@patch("api.routes.get_adapter_for_url")
@patch("scheduler.jobs.get_adapter_for_url")
def test_user_only_sees_own_products(mock_jobs_adapter, mock_api_adapter, client) -> None:
    mock_adapter = mock_api_adapter.return_value
    mock_adapter.site_name = "hmt"
    mock_adapter.fetch_product.return_value = MOCK_SNAPSHOT
    mock_jobs_adapter.return_value = mock_adapter

    user_a_headers = auth_headers(client, email="usera@example.com")
    user_b_headers = auth_headers(client, email="userb@example.com")

    client.post("/products", json={"url": SAMPLE_URL}, headers=user_a_headers)

    user_a_products = client.get("/products", headers=user_a_headers).json()
    user_b_products = client.get("/products", headers=user_b_headers).json()

    assert len(user_a_products) == 1
    assert user_b_products == []
