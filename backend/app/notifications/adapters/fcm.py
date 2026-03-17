from __future__ import annotations

import os
from firebase_admin import messaging
from app.notifications.adapters.base import NotificationAdapter
from app.notifications.models import NotificationMessage, NotificationRecipient, StatusChangeEvent
from app.domain.auth_provider import initialize_firebase


class FCMNotificationAdapter(NotificationAdapter):
    def send(
        self,
        *,
        recipient: NotificationRecipient,
        message: NotificationMessage,
        event: StatusChangeEvent,
    ) -> None:
        if not initialize_firebase():
            print("FCM: Firebase not initialized, cannot send notification.")
            return

        if not recipient.address:
            print(f"FCM: No token for recipient {recipient.name or event.user_phone}")
            return

        # Web-specific configuration for actions
        frontend_url = os.getenv("FRONTEND_URL", "https://imgood.web.app")
        webpush_fcm_options = None
        
        # FCM requires HTTPS for the link property
        if frontend_url.startswith("https://"):
            webpush_fcm_options = messaging.WebpushFCMOptions(link=frontend_url)

        fcm_message = messaging.Message(
            token=recipient.address,
            # Move title/body to data to avoid browser auto-notification doubling
            # with our custom service worker notification.
            data={
                "title": message.subject,
                "body": message.body,
                "user_phone": event.user_phone,
                "new_status": event.new_status.value,
                "action": "checkin"
            },
            webpush=messaging.WebpushConfig(fcm_options=webpush_fcm_options) if webpush_fcm_options else None
        )

        try:
            response = messaging.send(fcm_message)
            print(f"FCM: Successfully sent message to {event.user_phone}: {response}")
        except Exception as e:
            print(f"FCM: Error sending message to {event.user_phone}: {e}")
