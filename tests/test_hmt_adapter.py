from pathlib import Path

from adapters.hmt import HMTAdapter

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "hmt_product_sample.html"
SAMPLE_URL = (
    "https://hmtwatches.in/product_overview?id=eyJpdiI6Ik15aG9OVzNJd0NzMUxVKy9iWlBTNlE9PSIsInZhbHVl"
    "IjoibGtyRk9oVm8zcGQvRnN0OTJwN08zQT09IiwibWFjIjoiNGM4ZGUyNjUzOTEzOTJjM2RhZTdhODMzZTFmNWUx"
    "NjUxNzNkYWVmNGZhZDgwMjJkMjQ0NzMyOTdjZTg1NmNjNiIsInRhZyI6IiJ9"
)


def test_hmt_adapter_parses_fixture_html() -> None:
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    adapter = HMTAdapter()
    snapshot = adapter.parse_html(SAMPLE_URL, html)

    assert snapshot.title == "HMT Pace UGSL 102 Turquoise Blue"
    assert snapshot.price == 1950.0
    assert snapshot.in_stock is True
    assert snapshot.raw.get("is_add_to_cart") == "1"
    assert snapshot.raw.get("prodInStock") == "yes"
    assert snapshot.raw.get("prodQty") == 1


def test_hmt_adapter_url_validation() -> None:
    adapter = HMTAdapter()
    assert adapter.is_supported_url(SAMPLE_URL) is True
    assert adapter.is_supported_url("https://hmtwatches.in/watches") is False
    assert adapter.is_supported_url("https://example.com/product_overview?id=x") is False
