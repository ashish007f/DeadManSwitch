"""
Check-in status computation logic.

Pure domain logic - zero dependencies on FastAPI, DB, or external services.
"""

from enum import Enum
from datetime import datetime, timedelta


class CheckInStatus(str, Enum):
    """Check-in health status"""
    SAFE = "SAFE"
    DUE_SOON = "DUE_SOON"
    MISSED = "MISSED"
    GRACE_PERIOD = "GRACE_PERIOD"
    NOTIFIED = "NOTIFIED"


def compute_status(
    last_checkin: datetime | None,
    interval_hours: int,
    missed_buffer_hours: int = 1,
    grace_period_hours: int = 24,
) -> CheckInStatus:
    """
    Compute check-in status based on last check-in time and interval.

    Status lifecycle (from healthy to escalation):
    - SAFE: elapsed < 0.8 * interval
    - DUE_SOON: elapsed is between 0.8 * interval and interval
    - MISSED: elapsed >= interval but still within the "missed buffer"
    - GRACE_PERIOD: elapsed is after the missed buffer but before the grace period ends
    - NOTIFIED: elapsed has exceeded interval + missed_buffer + grace_period

    Args:
        last_checkin: UTC timestamp of last check-in, or None
        interval_hours: Expected check-in interval in hours
        missed_buffer_hours: Extra buffer hours after interval before entering grace
        grace_period_hours: Grace period hours after missed buffer before notifying

    Returns:
        CheckInStatus enum value
    """
    if last_checkin is None:
        return CheckInStatus.MISSED

    now = datetime.utcnow()
    elapsed_hours = (now - last_checkin).total_seconds() / 3600

    threshold_safe = 0.8 * interval_hours
    threshold_due_soon = interval_hours
    threshold_missed_end = interval_hours + missed_buffer_hours
    threshold_grace_end = threshold_missed_end + grace_period_hours

    if elapsed_hours < threshold_safe:
        return CheckInStatus.SAFE
    elif elapsed_hours < threshold_due_soon:
        return CheckInStatus.DUE_SOON
    elif elapsed_hours < threshold_missed_end:
        return CheckInStatus.MISSED
    elif elapsed_hours < threshold_grace_end:
        return CheckInStatus.GRACE_PERIOD
    else:
        return CheckInStatus.NOTIFIED


def hours_until_due(
    last_checkin: datetime | None,
    interval_hours: int,
    missed_buffer_hours: int = 1,
    grace_period_hours: int = 24,
) -> float:
    """
    Calculate hours remaining until check-in is due.
    
    Returns negative if already overdue.
    
    Args:
        last_checkin: UTC timestamp of last check-in, or None
        interval_hours: Expected check-in interval in hours
        
    Returns:
        Hours remaining (negative if overdue)
    """
    if last_checkin is None:
        return 0.0

    now = datetime.utcnow()
    elapsed_hours = (now - last_checkin).total_seconds() / 3600

    # If not yet due, show hours until interval
    if elapsed_hours < interval_hours:
        return interval_hours - elapsed_hours

    # If missed or in grace, show hours until notification
    notify_at = interval_hours + missed_buffer_hours + grace_period_hours
    return notify_at - elapsed_hours
