"""
SQLAlchemy ORM schema definitions.

Minimal schema focused on core functionality.
"""

from sqlalchemy import Column, Integer, DateTime, String, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class OTP(Base):
    """OTP storage for phone verification"""
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Integer, default=0)  # 0=unused, 1=verified


class Settings(Base):
    """Application settings (check-in interval, etc.)"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    # per-user settings
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    checkin_interval_hours = Column(Integer, default=48)
    # How long after being MISSED before entering GRACE_PERIOD (hours)
    missed_buffer_hours = Column(Integer, default=1)
    # Grace period after missed buffer before notifying (hours)
    grace_period_hours = Column(Integer, default=24)
    # JSON/text-encoded contacts for trusted people (future: separate table)
    contacts = Column(Text, nullable=True)


class CheckIn(Base):
    """Recorded check-in timestamps"""
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class Instructions(Base):
    """Instructions for trusted contacts"""
    __tablename__ = "instructions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User table - phone number based with OTP"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    display_name = Column(String(256), nullable=True)
    verified = Column(Integer, default=0)  # 0=unverified, 1=verified


class NotificationLog(Base):
    """Tracks sent notifications to prevent duplicate sends per missed-cycle."""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # The last check-in timestamp that this notification corresponds to.
    # If the user checks in again, last_checkin_at changes and we can notify again if needed.
    last_checkin_at = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False)  # e.g. NOTIFIED

    notified_at = Column(DateTime, default=datetime.utcnow, nullable=False)


Index("ix_notification_logs_user_checkin_status", NotificationLog.user_id, NotificationLog.last_checkin_at, NotificationLog.status)


def init_db():
    """Create all tables if they don't exist."""
    from app.db.database import engine
    Base.metadata.create_all(bind=engine)
