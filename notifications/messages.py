from datetime import datetime, timezone
from typing import Any

from core.change_detection import ChangeType, DetectedChange
from db.models import Product, Snapshot
from events.models import NotificationEvent


def _to_event(
    event_or_product: Any,
    snapshot: Any = None,
    changes: Any = None,
) -> NotificationEvent:
    if isinstance(event_or_product, NotificationEvent):
        return event_or_product

    product = event_or_product
    actionable = [
        c
        for c in (changes or [])
        if getattr(c, "change_type", None) != ChangeType.NO_CHANGE
    ]
    c = actionable[0] if actionable else (changes[0] if changes else None)

    change_type_str = c.change_type.value if c else "product_updated"
    old_val = c.old_value if c else None
    new_val = c.new_value if c else None
    details = c.details if c else {}

    title = (
        (snapshot.title if snapshot else None)
        or (product.title if product else None)
        or "Tracked Product"
    )
    price = snapshot.price if snapshot else None
    in_stock = snapshot.in_stock if snapshot else True
    url = product.url if product else ""
    site_name = getattr(product, "site_name", "HMT Watches") or "HMT Watches"
    occurred_at = getattr(snapshot, "fetched_at", None) or datetime.now(timezone.utc)
    raw = getattr(snapshot, "raw", {}) or {}

    return NotificationEvent(
        event_id=f"evt_{getattr(product, 'id', 0)}_{change_type_str}",
        event_type=change_type_str,
        product_id=getattr(product, "id", 0),
        title=title,
        price=price,
        in_stock=in_stock,
        url=url,
        site_name=site_name,
        occurred_at=occurred_at,
        image_url=raw.get("image_url") or raw.get("image"),
        collection=raw.get("collection") or raw.get("category"),
        old_value=old_val,
        new_value=new_val,
        details=details,
    )


def format_subject(
    event_or_product: NotificationEvent | Product,
    changes: list[DetectedChange] | None = None,
) -> str:
    if isinstance(event_or_product, NotificationEvent):
        evt = event_or_product
        title = evt.title
        etype = evt.event_type
        if etype == "new_model":
            return f"✨ New Model Discovered — {title}"
        if etype in ("back_in_stock", "restocked", "RESTOCKED"):
            return f"✅ Back in Stock — {title}"
        if etype in ("out_of_stock", "OUT_OF_STOCK"):
            return f"❌ Out of Stock — {title}"
        if etype in (
            "price_change",
            "PRICE_CHANGE",
            "PRICE_INCREASED",
            "PRICE_DECREASED",
        ):
            if evt.old_value is not None and evt.new_value is not None:
                try:
                    if float(evt.new_value) < float(evt.old_value):
                        return f"💰 Price Dropped — {title}"
                    return f"📈 Price Updated — {title}"
                except ValueError:
                    pass
            return f"💰 Price Change — {title}"
        return f"🔔 Product Alert — {title}"

    product = event_or_product
    title = product.title or "Tracked product"
    for change in changes or []:
        if change.change_type == ChangeType.NEW_MODEL:
            return f"✨ New Model Discovered — {title}"
        if change.change_type == ChangeType.BACK_IN_STOCK:
            return f"✅ Back in Stock — {title}"
        if change.change_type == ChangeType.OUT_OF_STOCK:
            return f"❌ Out of Stock — {title}"
        if change.change_type == ChangeType.PRICE_CHANGE:
            if change.old_value is not None and change.new_value is not None:
                try:
                    if float(change.new_value) < float(change.old_value):
                        return f"💰 Price Dropped — {title}"
                    return f"📈 Price Updated — {title}"
                except ValueError:
                    pass
            return f"💰 Price Change — {title}"

    return f"🔔 Product Updated — {title}"


def format_plain_text(
    event_or_product: NotificationEvent | Product,
    snapshot: Snapshot | None = None,
    changes: list[DetectedChange] | None = None,
) -> str:
    evt = _to_event(event_or_product, snapshot, changes)

    price_str = f"₹{evt.price}" if evt.price is not None else "N/A"
    stock_str = "In Stock ✅" if evt.in_stock else "Out of Stock ❌"

    lines = [
        "HMT Availability Alert",
        "=" * 30,
        "",
        f"Product    : {evt.title}",
        f"Collection : {evt.collection or 'HMT Collection'}",
        f"Source     : {evt.site_name}",
        f"Price      : {price_str}",
        f"Stock      : {stock_str}",
        f"Event      : {evt.event_type.replace('_', ' ').title()}",
    ]

    if evt.old_value is not None or evt.new_value is not None:
        lines.append(f"Change     : {evt.old_value} → {evt.new_value}")

    lines.extend(
        [
            "",
            "Product URL:",
            evt.url,
        ]
    )
    return "\n".join(lines)


def format_html(
    event_or_product: NotificationEvent | Product,
    snapshot: Snapshot | None = None,
    changes: list[DetectedChange] | None = None,
) -> str:
    evt = _to_event(event_or_product, snapshot, changes)

    etype = evt.event_type
    if etype == "new_model":
        header_badge = "✨ NEW MODEL DISCOVERED"
    elif etype in ("back_in_stock", "restocked", "RESTOCKED"):
        header_badge = "✅ BACK IN STOCK"
    elif etype in ("out_of_stock", "OUT_OF_STOCK"):
        header_badge = "❌ OUT OF STOCK"
    elif etype in ("price_change", "PRICE_CHANGE"):
        header_badge = "💰 PRICE CHANGE ALERT"
    else:
        header_badge = "🔔 PRODUCT ALERT"

    if evt.price is not None:
        try:
            formatted_price = f"₹{evt.price:,.2f}"
        except (ValueError, TypeError):
            formatted_price = f"₹{evt.price}"
    else:
        formatted_price = "N/A"

    if evt.in_stock:
        stock_badge = '<span style="display: inline-block; padding: 4px 12px; background-color: #d1fae5; color: #065f46; font-size: 13px; font-weight: 700; border-radius: 20px;">IN STOCK ✅</span>'
    else:
        stock_badge = '<span style="display: inline-block; padding: 4px 12px; background-color: #fee2e2; color: #991b1b; font-size: 13px; font-weight: 700; border-radius: 20px;">OUT OF STOCK ❌</span>'

    formatted_time = evt.occurred_at.strftime("%B %d, %Y at %I:%M %p UTC")

    if evt.image_url:
        image_section = f"""
          <tr>
            <td align="center" style="padding: 24px 30px 0 30px; background-color: #ffffff;">
              <img src="{evt.image_url}" alt="{evt.title}" style="max-width: 100%; max-height: 280px; object-fit: contain; border-radius: 8px; border: 1px solid #e2e8f0; display: block;" />
            </td>
          </tr>
        """
    else:
        image_section = ""

    change_detail_html = ""
    if evt.old_value is not None or evt.new_value is not None:
        change_detail_html = f"""
        <tr>
          <td colspan="2" style="padding: 16px; border-bottom: 1px solid #e2e8f0; background-color: #f1f5f9;">
            <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Detected Change</div>
            <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-top: 2px;">
              <span style="color: #64748b;">{evt.old_value or "None"}</span> &rarr; <span style="color: #2563eb;">{evt.new_value or "None"}</span>
            </div>
          </td>
        </tr>
        """

    site_name = evt.site_name or "HMT Watches"
    collection = evt.collection or "HMT Collection"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{evt.title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f6f9; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
          
          <!-- Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 30px; text-align: left;">
              <table width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <span style="display: inline-block; padding: 4px 10px; background-color: rgba(255, 255, 255, 0.15); border-radius: 20px; font-size: 11px; font-weight: 700; color: #e2e8f0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                      {site_name}
                    </span>
                    <h2 style="margin: 0; color: #ffffff; font-size: 20px; font-weight: 700;">
                      {header_badge}
                    </h2>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Product Image -->
          {image_section}

          <!-- Main Content Body -->
          <tr>
            <td style="padding: 24px 30px;">
              <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; color: #0f172a; line-height: 1.3;">
                {evt.title}
              </h1>

              <div style="margin-bottom: 20px;">
                <span style="font-size: 13px; font-weight: 600; color: #64748b; background-color: #f1f5f9; padding: 4px 10px; border-radius: 4px; display: inline-block;">
                  Collection: {collection}
                </span>
              </div>

              <!-- Product Details Grid -->
              <table width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border-radius: 8px; border: 1px solid #f1f5f9; margin-bottom: 24px;">
                {change_detail_html}
                <tr>
                  <td style="padding: 16px; border-bottom: 1px solid #e2e8f0;" width="50%">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Price</div>
                    <div style="font-size: 20px; font-weight: 800; color: #0f172a; margin-top: 2px;">{formatted_price}</div>
                  </td>
                  <td style="padding: 16px; border-bottom: 1px solid #e2e8f0;" width="50%">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Stock Status</div>
                    <div style="margin-top: 4px;">{stock_badge}</div>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 16px;" width="50%">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Source Website</div>
                    <div style="font-size: 14px; font-weight: 600; color: #334155; margin-top: 2px;">{site_name}</div>
                  </td>
                  <td style="padding: 16px;" width="50%">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Detected At</div>
                    <div style="font-size: 13px; font-weight: 500; color: #334155; margin-top: 2px;">{formatted_time}</div>
                  </td>
                </tr>
              </table>

              <!-- Action Button -->
              <table width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center" style="padding-top: 8px; padding-bottom: 12px;">
                    <a href="{evt.url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 15px; font-weight: 700; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);">
                      View Product on {site_name} &rarr;
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; padding: 18px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
              <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                Sent automatically by HMT Watch Monitor Service.<br>
                Timestamp: {formatted_time}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>""".strip()


def format_whatsapp(
    event_or_product: NotificationEvent | Product,
    snapshot: Snapshot | None = None,
    changes: list[DetectedChange] | None = None,
) -> str:
    evt = _to_event(event_or_product, snapshot, changes)

    price_str = f"₹{evt.price}" if evt.price is not None else "N/A"
    stock_str = "✅ In Stock" if evt.in_stock else "❌ Out of Stock"

    message = [
        f"⌚ *{evt.site_name} Alert*",
        "",
        f"*{evt.title}*",
        f"Collection: {evt.collection or 'HMT Collection'}",
        "",
        f"Price: {price_str}",
        f"Status: {stock_str}",
        f"Event: {evt.event_type.replace('_', ' ').title()}",
    ]

    if evt.old_value is not None or evt.new_value is not None:
        message.append(f"Change: {evt.old_value} → {evt.new_value}")

    message.extend(
        [
            "",
            evt.url,
        ]
    )

    return "\n".join(message)
