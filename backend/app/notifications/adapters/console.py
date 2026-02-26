from __future__ import annotations

from app.notifications.adapters.base import NotificationAdapter
from app.notifications.models import NotificationMessage, NotificationRecipient, StatusChangeEvent


class ConsoleNotificationAdapter(NotificationAdapter):
    def send(
        self,
        *,
        recipient: NotificationRecipient,
        message: NotificationMessage,
        event: StatusChangeEvent,
    ) -> None:
        print(
            "\n".join(
                [
                    "---- notification (console adapter) ----",
                    f"channel: {recipient.channel}",
                    f"to: {recipient.address}",
                    f"name: {recipient.name or ''}",
                    f"user_phone: {event.user_phone}",
                    f"status: {event.new_status}",
                    f"last_checkin_at: {event.last_checkin_at}",
                    f"subject: {message.subject}",
                    "body:",
                    message.body,
                    "---------------------------------------",
                ]
            )
        )

