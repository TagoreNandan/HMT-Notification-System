import logging
import requests

from config import get_settings
from db.models import CatalogProduct

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class HMTEmailNotifier:
    def __init__(self, destination: str):
        self.destination = destination

    def send(self, product: CatalogProduct):
        settings = get_settings()

        if not settings.resend_api_key:
            logger.error("Missing RESEND_API_KEY")
            return

        if not settings.resend_from_email:
            logger.error("Missing RESEND_FROM_EMAIL")
            return

        payload = {
            "from": settings.resend_from_email,
            "to": [self.destination],
            "subject": f"✅ Back in Stock — {product.title}",
            "html": f"""
            <h2>⌚ HMT Availability Alert</h2>

            <p><b>{product.title}</b></p>

            <p>Status: ✅ <b>IN STOCK</b></p>

            <p>Price: ₹{product.price}</p>

            <p>
                <a href="{product.url}">
                    View Product
                </a>
            </p>
            """,
            "text": f"""
HMT Availability Alert

Product:
{product.title}

Status:
IN STOCK

Price:
₹{product.price}

{product.url}
""",
        }

        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                RESEND_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 400:
                print("Status:", response.status_code)
                print("Response:", response.text)

            response.raise_for_status()

            print(f"📧 Email sent for {product.title}")

        except Exception as e:
            print(e)
