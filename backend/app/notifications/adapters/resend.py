from __future__ import annotations

import httpx
from app.notifications.adapters.base import NotificationAdapter
from app.notifications.models import NotificationMessage, NotificationRecipient, StatusChangeEvent
from app.config import settings


class ResendEmailNotificationAdapter(NotificationAdapter):
    def send(
        self,
        *,
        recipient: NotificationRecipient,
        message: NotificationMessage,
        event: StatusChangeEvent,
    ) -> None:
        if settings.resend_api_key == "test_api_key":
            print(f"Resend: API key not set, skipping email to {recipient.address}")
            return

        payload = {
            "from": settings.resend_sender,
            "to": [recipient.address],
            "subject": message.subject,
            "text": message.body,
        }
        
        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            if response.status_code >= 200 and response.status_code < 300:
                print(f"Resend: Successfully sent email to {recipient.address}: {response.json()}")
            else:
                print(f"Resend: Failed to send email to {recipient.address}: {response.status_code} {response.text}")
        except Exception as e:
            print(f"Resend: Error sending email to {recipient.address}: {e}")
