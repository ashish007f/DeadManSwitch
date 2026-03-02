"""
Tests for two-tier notification system using Mock Firestore.
"""

import pytest
from datetime import datetime, timedelta, timezone
from mockfirestore import MockFirestore
from app.repositories.notification_repo import NotificationLogRepository
from app.domain.status import CheckInStatus

TEST_PHONE = "+16502530000"

def test_notification_deduplication_grace_period():
    """Test that GRACE_PERIOD notification is sent only once per missed cycle"""
    db = MockFirestore()
    notif_repo = NotificationLogRepository(db)
    
    last_checkin = datetime.now(timezone.utc) - timedelta(hours=50)
    status = CheckInStatus.GRACE_PERIOD.value
    
    # First check - should not be sent yet
    assert not notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )
    
    # Record as sent
    notif_repo.record_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )
    
    # Second check - should be marked as sent
    assert notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )
    
    # Different last_checkin should not be marked as sent
    new_checkin = datetime.now(timezone.utc) - timedelta(hours=1)
    assert not notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=new_checkin,
        status=status
    )


def test_notification_deduplication_notified():
    """Test that NOTIFIED notification is sent only once per missed cycle"""
    db = MockFirestore()
    notif_repo = NotificationLogRepository(db)
    
    last_checkin = datetime.now(timezone.utc) - timedelta(hours=100)
    status = CheckInStatus.NOTIFIED.value
    
    # Should not be sent yet
    assert not notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )
    
    # Record as sent
    notif_repo.record_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )
    
    # Should be marked as sent
    assert notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=status
    )


def test_both_notifications_separate():
    """Test that GRACE_PERIOD and NOTIFIED notifications are tracked separately"""
    db = MockFirestore()
    notif_repo = NotificationLogRepository(db)
    
    last_checkin = datetime.now(timezone.utc) - timedelta(hours=100)
    
    # Record GRACE_PERIOD notification
    notif_repo.record_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=CheckInStatus.GRACE_PERIOD.value
    )
    
    # Record NOTIFIED notification
    notif_repo.record_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=CheckInStatus.NOTIFIED.value
    )
    
    # Both should be marked as sent
    assert notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=CheckInStatus.GRACE_PERIOD.value
    )
    assert notif_repo.has_sent(
        phone=TEST_PHONE,
        last_checkin_at=last_checkin,
        status=CheckInStatus.NOTIFIED.value
    )
