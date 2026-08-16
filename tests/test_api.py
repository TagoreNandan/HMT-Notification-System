from unittest.mock import patch

from adapters.base import ProductSnapshot
from tests.conftest import auth_headers
from tests.test_hmt_adapter import SAMPLE_URL

MOCK_SNAPSHOT = ProductSnapshot(
    url=SAMPLE_URL,
    title="HMT Pace UGSL 102 Turquoise Blue",
    price=1950.0,
    in_stock=True,
    raw={"is_add_to_cart": "1", "prodInStock": "yes", "prodQty": 1},
)


@patch("api.routes.get_adapter_for_url")
@patch("scheduler.jobs.get_adapter_for_url")
def test_health(mock_jobs_adapter, mock_api_adapter, client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("api.routes.get_adapter_for_url")
@patch("scheduler.jobs.get_adapter_for_url")
def test_create_list_delete_product(
    mock_jobs_adapter, mock_api_adapter, client
) -> None:
    mock_adapter = mock_api_adapter.return_value
    mock_adapter.site_name = "hmt"
    mock_adapter.fetch_product.return_value = MOCK_SNAPSHOT
    mock_jobs_adapter.return_value = mock_adapter

    headers = auth_headers(client)

    create_resp = client.post("/products", json={"url": SAMPLE_URL}, headers=headers)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["url"] == SAMPLE_URL
    assert body["site_name"] == "hmt"
    assert body["title"] == MOCK_SNAPSHOT.title
    product_id = body["id"]

    list_resp = client.get("/products", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    history_resp = client.get(f"/products/{product_id}/history", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert history["product"]["id"] == product_id
    assert len(history["snapshots"]) >= 1
    assert history["snapshots"][0]["price"] == 1950.0
    assert history["snapshots"][0]["in_stock"] is True

    delete_resp = client.delete(f"/products/{product_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_after = client.get("/products", headers=headers)
    assert list_after.json() == []


def test_create_product_requires_auth(client) -> None:
    response = client.post("/products", json={"url": SAMPLE_URL})
    assert response.status_code == 401


@patch("api.routes.get_adapter_for_url")
def test_create_product_rejects_unsupported_url(mock_api_adapter, client) -> None:
    from adapters.registry import UnsupportedSiteError

    mock_api_adapter.side_effect = UnsupportedSiteError("unsupported")
    headers = auth_headers(client)
    response = client.post(
        "/products",
        json={"url": "https://example.com/product_overview?id=abc"},
        headers=headers,
    )
    assert response.status_code == 400
