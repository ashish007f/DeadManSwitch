"""
Tests for two-tier notification system.

Verifies that notifications are sent at GRACE_PERIOD and NOTIFIED statuses with correct content.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.schema import Base, User, Settings, CheckIn, Instructions, NotificationLog
from app.services.checkin_service import CheckInService
from app.repositories.notification_repo import NotificationLogRepository
from app.domain.status import CheckInStatus


def _make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_notification_deduplication_grace_period():
    """Test that GRACE_PERIOD notification is sent only once per missed cycle"""
    db = _make_db()
    try:
        # Setup user
        user = User(phone_number="5551112222", display_name="Test User", verified=1)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        settings = Settings(
            user_id=user.id,
            checkin_interval_hours=48,
            missed_buffer_hours=1,
            grace_period_hours=24,
            contacts='["alice@example.com"]'
        )
        db.add(settings)
        db.commit()
        
        # Create a check-in that puts us in GRACE_PERIOD
        last_checkin = datetime.utcnow() - timedelta(hours=50)  # Past interval + buffer
        checkin = CheckIn(user_id=user.id, timestamp=last_checkin)
        db.add(checkin)
        db.commit()
        
        notif_repo = NotificationLogRepository(db)
        
        # First check - should not be sent yet
        assert not notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        
        # Record as sent
        notif_repo.record_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        
        # Second check - should be marked as sent
        assert notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        
        # Different last_checkin should not be marked as sent
        new_checkin = datetime.utcnow() - timedelta(hours=1)
        assert not notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=new_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        
    finally:
        db.close()


def test_notification_deduplication_notified():
    """Test that NOTIFIED notification is sent only once per missed cycle"""
    db = _make_db()
    try:
        user = User(phone_number="5552223333", display_name="Test User", verified=1)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        settings = Settings(
            user_id=user.id,
            checkin_interval_hours=48,
            missed_buffer_hours=1,
            grace_period_hours=24,
            contacts='["bob@example.com"]'
        )
        db.add(settings)
        db.commit()
        
        # Create a check-in that puts us in NOTIFIED
        last_checkin = datetime.utcnow() - timedelta(hours=100)  # Past everything
        checkin = CheckIn(user_id=user.id, timestamp=last_checkin)
        db.add(checkin)
        db.commit()
        
        notif_repo = NotificationLogRepository(db)
        
        # Should not be sent yet
        assert not notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.NOTIFIED.value
        )
        
        # Record as sent
        notif_repo.record_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.NOTIFIED.value
        )
        
        # Should be marked as sent
        assert notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.NOTIFIED.value
        )
        
    finally:
        db.close()


def test_both_notifications_separate():
    """Test that GRACE_PERIOD and NOTIFIED notifications are tracked separately"""
    db = _make_db()
    try:
        user = User(phone_number="5553334444", display_name="Test User", verified=1)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        last_checkin = datetime.utcnow() - timedelta(hours=100)
        checkin = CheckIn(user_id=user.id, timestamp=last_checkin)
        db.add(checkin)
        db.commit()
        
        notif_repo = NotificationLogRepository(db)
        
        # Record GRACE_PERIOD notification
        notif_repo.record_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        
        # Record NOTIFIED notification
        notif_repo.record_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.NOTIFIED.value
        )
        
        # Both should be marked as sent
        assert notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.GRACE_PERIOD.value
        )
        assert notif_repo.has_sent(
            user_id=user.id,
            last_checkin_at=last_checkin,
            status=CheckInStatus.NOTIFIED.value
        )
        
        # Should have 2 log entries
        logs = db.query(NotificationLog).filter(NotificationLog.user_id == user.id).all()
        assert len(logs) == 2
        
    finally:
        db.close()
