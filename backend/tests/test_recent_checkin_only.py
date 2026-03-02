"""
Tests for check-in and notification log deduplication using Mock Firestore.
"""

from datetime import datetime, timedelta, timezone
from mockfirestore import MockFirestore
from app.repositories.checkin_repo import CheckInRepository
from app.repositories.notification_repo import NotificationLogRepository
from app.domain.security import secure_phone_identity

TEST_PHONE = "+16502530000"

def test_record_checkin_upserts_and_keeps_only_one_document():
    db = MockFirestore()
    repo = CheckInRepository(db)
    _, p_hash = secure_phone_identity(TEST_PHONE)

    t1 = datetime.now(timezone.utc) - timedelta(hours=2)
    t2 = datetime.now(timezone.utc) - timedelta(hours=1)

    repo.record_checkin(p_hash=p_hash, timestamp=t1)
    repo.record_checkin(p_hash=p_hash, timestamp=t2)
    last = repo.get_last_checkin(p_hash)
    assert last is not None
    # In Firestore we just overwrite the same document "last_checkin"
    assert abs((last.timestamp - t2).total_seconds()) < 1


def test_notification_log_dedupes_by_phone_and_last_checkin_and_status():
    db = MockFirestore()
    _, p_hash = secure_phone_identity(TEST_PHONE)
    last_checkin_at = datetime.now(timezone.utc) - timedelta(days=3)
    log_repo = NotificationLogRepository(db)

    assert log_repo.has_sent(p_hash=p_hash, last_checkin_at=last_checkin_at, status="NOTIFIED") is False
    log_repo.record_sent(p_hash=p_hash, last_checkin_at=last_checkin_at, status="NOTIFIED")
    assert log_repo.has_sent(p_hash=p_hash, last_checkin_at=last_checkin_at, status="NOTIFIED") is True
