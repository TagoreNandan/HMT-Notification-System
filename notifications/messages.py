from core.change_detection import ChangeType, DetectedChange
from db.models import Product, Snapshot


def _title(product: Product, snapshot: Snapshot) -> str:
    return snapshot.title or product.title or "Tracked product"


def format_subject(
    product: Product,
    changes: list[DetectedChange],
) -> str:
    title = product.title or "Tracked product"

    for change in changes:
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

    return f"🔔 Product Updated — {title}"


def format_plain_text(
    product: Product,
    snapshot: Snapshot,
    changes: list[DetectedChange],
) -> str:
    lines = [
        "HMT Availability Alert",
        "=" * 30,
        "",
        f"Product : {_title(product, snapshot)}",
        f"Price   : ₹{snapshot.price}",
        f"Stock   : {'In Stock ✅' if snapshot.in_stock else 'Out of Stock ❌'}",
        "",
        "Detected changes:",
    ]

    for change in changes:
        lines.append(
            f" • {_change_label(change)}: {change.old_value} → {change.new_value}"
        )

    lines.extend(
        [
            "",
            "Product URL:",
            product.url,
        ]
    )

    return "\n".join(lines)


def format_html(
    product: Product,
    snapshot: Snapshot,
    changes: list[DetectedChange],
) -> str:
    rows = "".join(
        f"<li><b>{c.change_type.value}</b>: {c.old_value} → {c.new_value}</li>"
        for c in changes
    )

    stock = "✅ In Stock" if snapshot.in_stock else "❌ Out of Stock"

    return f"""
<html>
<body style="font-family:Arial,sans-serif">

<h2>⌚ HMT Availability Alert</h2>

<p><b>Product</b><br>{_title(product, snapshot)}</p>

<p><b>Price</b><br>₹{snapshot.price}</p>

<p><b>Status</b><br>{stock}</p>

<p><b>Detected Changes</b></p>

<ul>
{rows}
</ul>

<p>
<a href="{product.url}">
View Product
</a>
</p>

</body>
</html>
""".strip()


def format_whatsapp(
    product: Product,
    snapshot: Snapshot,
    changes: list[DetectedChange],
) -> str:
    message = [
        "⌚ *HMT Availability Alert*",
        "",
        f"*{_title(product, snapshot)}*",
        "",
        f"Price: ₹{snapshot.price}",
        f"Status: {'✅ In Stock' if snapshot.in_stock else '❌ Out of Stock'}",
        "",
        "*Changes:*",
    ]

    for change in changes:
        message.append(
            f"• {_change_label(change)}: {change.old_value} → {change.new_value}"
        )

    message.extend(
        [
            "",
            product.url,
        ]
    )

    return "\n".join(message)


def _change_label(change: DetectedChange) -> str:
    if change.change_type == ChangeType.PRICE_CHANGE:
        return "Price"

    if change.change_type == ChangeType.BACK_IN_STOCK:
        return "Availability"

    if change.change_type == ChangeType.OUT_OF_STOCK:
        return "Availability"

    return change.change_type.value.replace("_", " ").title()
