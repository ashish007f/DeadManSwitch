from datetime import datetime, timedelta, timezone

from app.domain.status import compute_status, hours_until_due, CheckInStatus


def test_compute_status_transitions_and_hours():
    interval = 48

    # SAFE: elapsed << 0.8 * interval (0.8*48 = 38.4)
    last_safe = datetime.now(timezone.utc) - timedelta(hours=10)
    assert compute_status(last_safe, interval) == CheckInStatus.SAFE
    h = hours_until_due(last_safe, interval)
    # expected ~38 hours remaining (allow 1-hour tolerance)
    assert h > 37 and h < 39

    # DUE_SOON: elapsed between 0.8*interval and interval
    last_due_soon = datetime.now(timezone.utc) - timedelta(hours=40)
    assert compute_status(last_due_soon, interval) == CheckInStatus.DUE_SOON

    # MISSED: elapsed >= interval but < interval + missed_buffer (default missed_buffer=1)
    last_missed = datetime.now(timezone.utc) - timedelta(hours=48.5)
    assert compute_status(last_missed, interval) == CheckInStatus.MISSED

    # GRACE_PERIOD: elapsed >= interval + missed_buffer but < interval+missed_buffer+grace (default grace=24)
    last_grace = datetime.now(timezone.utc) - timedelta(hours=50)
    assert compute_status(last_grace, interval) == CheckInStatus.GRACE_PERIOD
    # hours until due (notify) should be positive and roughly grace remaining
    remaining = hours_until_due(last_grace, interval)
    # notify_at = interval + missed_buffer + grace = 48 +1 +24 = 73
    # elapsed ~50 -> remaining ~23
    assert remaining > 22 and remaining < 24.5

    # NOTIFIED: elapsed >= interval + missed_buffer + grace_period
    last_notified = datetime.now(timezone.utc) - timedelta(hours=80)
    assert compute_status(last_notified, interval) == CheckInStatus.NOTIFIED


def test_no_last_checkin_behaviour():
    # When there's no last checkin, compute_status should return MISSED and hours_until_due 0.0
    assert compute_status(None, 24) == CheckInStatus.MISSED
    assert hours_until_due(None, 24) == 0.0
