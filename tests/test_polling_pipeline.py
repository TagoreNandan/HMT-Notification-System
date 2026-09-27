from unittest.mock import MagicMock, patch


from adapters.base import ProductSnapshot
from db.models import ChannelType, NotificationPreference, Product, User
from services.polling_pipeline import PollingPipeline


def _setup_test_user(db_session, email="pipeline_test@example.com") -> User:
    user = User(email=email, hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _setup_test_product(
    db_session,
    user: User,
    url="https://hmtwatches.in/product_overview?id=test1",
    site_name="hmt_in",
) -> Product:
    product = Product(
        user_id=user.id,
        url=url,
        site_name=site_name,
        title="Test Watch 1",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_polling_pipeline_five_phases(db_session):
    user = _setup_test_user(db_session)
    product1 = _setup_test_product(
        db_session, user, "https://hmtwatches.in/product_overview?id=hmt1", "hmt_in"
    )
    product2 = _setup_test_product(
        db_session, user, "https://www.hmtwatches.store/product/sku1", "hmt_store"
    )

    db_session.add(
        NotificationPreference(
            user_id=user.id,
            channel_type=ChannelType.CONSOLE,
            destination="console",
            is_verified=True,
        )
    )
    db_session.commit()

    pipeline = PollingPipeline(db_session)

    with (
        patch.object(pipeline.catalog_sync, "sync") as mock_sync,
        patch("services.polling_pipeline.get_adapter_for_url") as mock_get_adapter,
    ):
        mock_sync.return_value = {"new": 1, "updated": 0, "unchanged": 5}

        mock_adapter_in = MagicMock()
        mock_adapter_in.fetch_product.return_value = ProductSnapshot(
            url=product1.url,
            title="HMT Stellar Automatic",
            price=7500.0,
            in_stock=True,
            raw={"image_url": "http://img1.jpg", "collection": "Stellar"},
        )

        mock_adapter_store = MagicMock()
        mock_adapter_store.fetch_product.return_value = ProductSnapshot(
            url=product2.url,
            title="HMT Sangam Store",
            price=3200.0,
            in_stock=False,
            raw={"image_url": "http://img2.jpg", "collection": "Sangam"},
        )

        def side_effect(url):
            if "hmtwatches.in" in url:
                return mock_adapter_in
            return mock_adapter_store

        mock_get_adapter.side_effect = side_effect

        summary = pipeline.run()

        # Phase 1 verification
        assert summary["catalog_sync"]["new"] == 1
        mock_sync.assert_called_once()

        # Phase 2 verification (both websites processed, discovered 2 unique products)
        assert summary["discovered_count"] == 2

        # Phase 3 & 4 verification (new model changes detected & events generated)
        assert summary["changes_count"] == 2
        assert summary["events_count"] == 2

        # Phase 5 verification (dispatched to console)
        assert summary["dispatch_stats"]["sent"] == 2


def test_polling_pipeline_deduplication(db_session):
    """Verify duplicate product URLs across different users/lists are ignored during discovery phase."""
    user1 = _setup_test_user(db_session, "user1_dedup@example.com")
    user2 = _setup_test_user(db_session, "user2_dedup@example.com")

    shared_url = "https://hmtwatches.in/product_overview?id=shared_watch"
    _setup_test_product(db_session, user1, shared_url, "hmt_in")
    _setup_test_product(db_session, user2, shared_url, "hmt_in")

    pipeline = PollingPipeline(db_session)

    with patch("services.polling_pipeline.get_adapter_for_url") as mock_get_adapter:
        mock_adapter = MagicMock()
        mock_adapter.fetch_product.return_value = ProductSnapshot(
            url=shared_url,
            title="HMT Shared Watch",
            price=2900.0,
            in_stock=True,
            raw={},
        )
        mock_get_adapter.return_value = mock_adapter

        discovered = pipeline.phase_2_discover_products()
        # Should deduplicate and only fetch/process 1 unique product
        assert len(discovered) == 1
