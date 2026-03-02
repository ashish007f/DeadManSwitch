from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from app.notifications.adapters.fcm import FCMNotificationAdapter
from app.notifications.models import NotificationMessage, NotificationRecipient, StatusChangeEvent
from app.domain.status import CheckInStatus

@patch("app.notifications.adapters.fcm.initialize_firebase")
@patch("firebase_admin.messaging.send")
def test_fcm_notification_send(mock_send, mock_init_firebase):
    # Mock firebase initialization
    mock_init_firebase.return_value = True
    
    # Mock successful send response
    mock_send.return_value = "projects/test-project/messages/123"
    
    adapter = FCMNotificationAdapter()
    
    recipient = NotificationRecipient(channel="push", address="test-fcm-token")
    message = NotificationMessage(subject="Test Subject", body="Test Body")
    event = StatusChangeEvent(
        user_phone="5551112222",
        new_status=CheckInStatus.DUE_SOON,
        last_checkin_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    
    # Send notification
    adapter.send(recipient=recipient, message=message, event=event)
    
    # Verify messaging.send was called
    assert mock_send.called
    args, kwargs = mock_send.call_args
    fcm_message = args[0]
    
    assert fcm_message.notification.title == "Test Subject"
    assert fcm_message.notification.body == "Test Body"
    assert fcm_message.token == "test-fcm-token"
    assert fcm_message.data["user_phone"] == "5551112222"
    assert fcm_message.data["new_status"] == CheckInStatus.DUE_SOON.value

@patch("app.notifications.adapters.fcm.initialize_firebase")
@patch("firebase_admin.messaging.send")
def test_fcm_notification_no_token(mock_send, mock_init_firebase):
    # Mock firebase initialization
    mock_init_firebase.return_value = True
    
    adapter = FCMNotificationAdapter()
    
    recipient = NotificationRecipient(channel="push", address="")
    message = NotificationMessage(subject="Test Subject", body="Test Body")
    event = StatusChangeEvent(
        user_phone="5551112222",
        new_status=CheckInStatus.DUE_SOON,
        last_checkin_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    
    # Send notification with no token
    adapter.send(recipient=recipient, message=message, event=event)
    
    # Verify messaging.send was NOT called
    assert not mock_send.called
