from __future__ import annotations

from abc import ABC, abstractmethod

from app.notifications.models import NotificationMessage, NotificationRecipient, StatusChangeEvent


class NotificationAdapter(ABC):
    @abstractmethod
    def send(
        self,
        *,
        recipient: NotificationRecipient,
        message: NotificationMessage,
        event: StatusChangeEvent,
    ) -> None:
        raise NotImplementedError

