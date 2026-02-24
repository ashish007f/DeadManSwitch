from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.schema import Base, User, CheckIn, NotificationLog
from app.repositories.checkin_repo import CheckInRepository
from app.repositories.notification_repo import NotificationLogRepository


def _make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_record_checkin_upserts_and_keeps_only_one_row():
    db = _make_db()
    try:
        user = User(phone_number="5550001111", display_name="Test", verified=1)
        db.add(user)
        db.commit()
        db.refresh(user)

        repo = CheckInRepository(db)
        t1 = datetime.utcnow() - timedelta(hours=2)
        t2 = datetime.utcnow() - timedelta(hours=1)

        repo.record_checkin(phone=user.phone_number, timestamp=t1)
        repo.record_checkin(phone=user.phone_number, timestamp=t2)

        rows = db.query(CheckIn).filter(CheckIn.user_id == user.id).all()
        assert len(rows) == 1
        assert abs((rows[0].timestamp - t2).total_seconds()) < 1
    finally:
        db.close()


def test_notification_log_dedupes_by_user_and_last_checkin_and_status():
    db = _make_db()
    try:
        user = User(phone_number="5550002222", display_name="Test", verified=1)
        db.add(user)
        db.commit()
        db.refresh(user)

        last_checkin_at = datetime.utcnow() - timedelta(days=3)
        log_repo = NotificationLogRepository(db)

        assert log_repo.has_sent(user_id=user.id, last_checkin_at=last_checkin_at, status="NOTIFIED") is False
        log_repo.record_sent(user_id=user.id, last_checkin_at=last_checkin_at, status="NOTIFIED")
        assert log_repo.has_sent(user_id=user.id, last_checkin_at=last_checkin_at, status="NOTIFIED") is True

        # sanity check storage
        assert db.query(NotificationLog).count() == 1
    finally:
        db.close()

