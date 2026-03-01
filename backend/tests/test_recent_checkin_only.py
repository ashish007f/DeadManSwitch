"""
Tests for check-in and notification log deduplication using Mock Firestore.
"""

from datetime import datetime, timedelta, timezone
from mockfirestore import MockFirestore
from app.repositories.checkin_repo import CheckInRepository
from app.repositories.notification_repo import NotificationLogRepository

TEST_PHONE = "+16502530000"

def test_record_checkin_upserts_and_keeps_only_one_document():
    db = MockFirestore()
    repo = CheckInRepository(db)
    
    t1 = datetime.now(timezone.utc) - timedelta(hours=2)
    t2 = datetime.now(timezone.utc) - timedelta(hours=1)

    repo.record_checkin(phone=TEST_PHONE, timestamp=t1)
    repo.record_checkin(phone=TEST_PHONE, timestamp=t2)

    last = repo.get_last_checkin(TEST_PHONE)
    assert last is not None
    # In Firestore we just overwrite the same document "last_checkin"
    assert abs((last.timestamp - t2).total_seconds()) < 1


def test_notification_log_dedupes_by_phone_and_last_checkin_and_status():
    db = MockFirestore()
    last_checkin_at = datetime.now(timezone.utc) - timedelta(days=3)
    log_repo = NotificationLogRepository(db)

    assert log_repo.has_sent(phone=TEST_PHONE, last_checkin_at=last_checkin_at, status="NOTIFIED") is False
    log_repo.record_sent(phone=TEST_PHONE, last_checkin_at=last_checkin_at, status="NOTIFIED")
    assert log_repo.has_sent(phone=TEST_PHONE, last_checkin_at=last_checkin_at, status="NOTIFIED") is True
