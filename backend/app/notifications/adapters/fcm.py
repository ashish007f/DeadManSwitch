from __future__ import annotations

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

        # recipient.address is the FCM token
        fcm_message = messaging.Message(
            notification=messaging.Notification(
                title=message.subject,
                body=message.body,
            ),
            token=recipient.address,
            # Add some data for the app to handle if needed
            data={
                "user_phone": event.user_phone,
                "new_status": event.new_status.value,
            }
        )

        try:
            response = messaging.send(fcm_message)
            print(f"FCM: Successfully sent message to {event.user_phone}: {response}")
        except Exception as e:
            print(f"FCM: Error sending message to {event.user_phone}: {e}")
