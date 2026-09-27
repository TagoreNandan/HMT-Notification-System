import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChannelType(str, enum.Enum):
    EMAIL = "email"
    NTFY = "ntfy"
    CONSOLE = "console"
    WHATSAPP = "whatsapp"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    notification_preferences: Mapped[list["NotificationPreference"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel_type",
            "destination",
            name="uq_notification_prefs_user_channel_dest",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    channel_type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, native_enum=False),
        nullable=False,
    )

    destination: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    user: Mapped["User"] = relationship(back_populates="notification_preferences")

    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        back_populates="preference",
        cascade="all, delete-orphan",
    )


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    preference_id: Mapped[int] = mapped_column(
        ForeignKey("notification_preferences.id", ondelete="CASCADE"),
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    preference: Mapped["NotificationPreference"] = relationship(
        back_populates="verification_tokens"
    )


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "url",
            name="uq_products_user_url",
        ),
        Index("ix_products_is_active_user", "is_active", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        index=True,
    )

    site_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    user: Mapped["User"] = relationship(back_populates="products")

    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="Snapshot.fetched_at.desc()",
    )

    change_events: Mapped[list["ChangeEvent"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ChangeEvent.created_at.desc()",
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    __table_args__ = (
        Index("ix_snapshots_product_fetched", "product_id", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    in_stock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    raw: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
    )

    product: Mapped["Product"] = relationship(back_populates="snapshots")

    change_events: Mapped[list["ChangeEvent"]] = relationship(back_populates="snapshot")


class ChangeEvent(Base):
    __tablename__ = "change_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("snapshots.id", ondelete="CASCADE"),
        index=True,
    )

    change_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    old_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    new_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
    )

    product: Mapped["Product"] = relationship(back_populates="change_events")

    snapshot: Mapped["Snapshot"] = relationship(back_populates="change_events")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "catalog_product_id",
            name="uq_user_catalog_product",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    catalog_product_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_products.id", ondelete="CASCADE"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    user: Mapped["User"] = relationship(back_populates="watchlist_items")

    product: Mapped["CatalogProduct"] = relationship(back_populates="watchlist_items")


# --------------------------------------------------------------------
# Global HMT catalog (new)
# --------------------------------------------------------------------


class CatalogProduct(Base):
    __tablename__ = "catalog_products"

    __table_args__ = (Index("ix_catalog_products_site_url", "site_name", "url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    url: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
        index=True,
    )

    site_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    in_stock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "channel_type",
            "destination",
            "user_id",
            name="uq_notification_logs_event_channel_dest_user",
        ),
        Index(
            "ix_notification_logs_lookup",
            "event_id",
            "user_id",
            "channel_type",
            "destination",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    channel_type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, native_enum=False),
        nullable=False,
    )

    destination: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )
