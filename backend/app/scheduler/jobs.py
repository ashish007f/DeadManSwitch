"""
Background scheduler for check-in monitoring.

Runs periodic checks to evaluate status and log changes.
Designed for future notification adapters.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from datetime import datetime
from typing import Optional

from app.db.database import SessionLocal
from app.services.checkin_service import CheckInService
from app.domain.status import CheckInStatus
from app.db.schema import User
from app.repositories.notification_repo import NotificationLogRepository
from app.notifications.adapters.console import ConsoleNotificationAdapter
from app.notifications.models import (
    NotificationMessage,
    NotificationRecipient,
    StatusChangeEvent,
)


class CheckInScheduler:
    """Background scheduler for check-in status monitoring"""
    
    def __init__(self, check_interval_hrs: float = 0.0166): # 1 minute
        self.scheduler = BackgroundScheduler()
        self.check_interval_hours = check_interval_hrs
        self._last_status_by_user: dict[int, CheckInStatus] = {}
        # Phase 2: pluggable adapter registry (currently console for all channels)
        self._adapter_by_channel = {
            "email": ConsoleNotificationAdapter(),
            "sms": ConsoleNotificationAdapter(),
            "whatsapp": ConsoleNotificationAdapter(),
        }
    
    def start(self):
        """Start the background scheduler"""
        try:
            self.scheduler.add_job(
                self._check_status,
                "interval",
                hours=self.check_interval_hours,
                id="check_checkin_status",
                replace_existing=True,
            )
            self.scheduler.start()
            print(f"✓ Scheduler started (checks every {self.check_interval_hours} hour(s))")
        except SchedulerAlreadyRunningError:
            print("⚠ Scheduler already running")
    
    def stop(self):
        """Stop the background scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("✓ Scheduler stopped")
    
    def _check_status(self):
        """Periodic check-in status evaluation"""
        db = SessionLocal()
        try:
            service = CheckInService(db)
            notif_repo = NotificationLogRepository(db)

            users: list[User] = db.query(User).all()
            for user in users:
                phone = user.phone_number
                status_resp = service.get_status(phone=phone)
                current_status = status_resp.status

                prev_status = self._last_status_by_user.get(user.id)
                if prev_status != current_status:
                    timestamp = datetime.utcnow().isoformat()
                    print(f"[{timestamp}] [{phone}] Status changed: {prev_status} → {current_status}")
                    self._last_status_by_user[user.id] = current_status

                # Two-tier notifications per missed cycle (keyed by last_checkin timestamp):
                # 1. GRACE_PERIOD: simple "please check on this person" (no sensitive info)
                # 2. NOTIFIED: full message with instructions (sensitive info for family)
                if status_resp.last_checkin is None:
                    continue

                # Reminders to the user themselves
                for reminder_status in (CheckInStatus.DUE_SOON, CheckInStatus.MISSED):
                    if current_status != reminder_status:
                        continue
                    
                    already_reminded = notif_repo.has_sent(
                        user_id=user.id,
                        last_checkin_at=status_resp.last_checkin,
                        status=f"REMINDER_{reminder_status.value}",
                    )
                    
                    if not already_reminded:
                        try:
                            self._send_self_reminder(
                                phone=phone,
                                status=reminder_status,
                                hours_until_due=status_resp.hours_until_due,
                                last_checkin_at=status_resp.last_checkin,
                            )
                            notif_repo.record_sent(
                                user_id=user.id,
                                last_checkin_at=status_resp.last_checkin,
                                status=f"REMINDER_{reminder_status.value}",
                            )
                        except Exception as e:
                            print(f"⚠ Reminder error for {phone}: {e}")

                # Two-tier notifications per missed cycle (keyed by last_checkin timestamp):
                # 1. GRACE_PERIOD: simple "please check on this person" (no sensitive info)
                # 2. NOTIFIED: full message with instructions (sensitive info for family)
                for notify_status in (CheckInStatus.GRACE_PERIOD, CheckInStatus.NOTIFIED):
                    if current_status != notify_status:
                        continue
                    already_sent = notif_repo.has_sent(
                        user_id=user.id,
                        last_checkin_at=status_resp.last_checkin,
                        status=notify_status.value,
                    )
                    if not already_sent:
                        try:
                            self._notify_user(
                                service=service,
                                phone=phone,
                                status=notify_status,
                                last_checkin_at=status_resp.last_checkin,
                            )
                            notif_repo.record_sent(
                                user_id=user.id,
                                last_checkin_at=status_resp.last_checkin,
                                status=notify_status.value,
                            )
                        except Exception as e:
                            print(f"⚠ Notification error for {phone}: {e}")
            
        except Exception as e:
            print(f"⚠ Scheduler error: {e}")
        finally:
            db.close()
    
    def _send_self_reminder(
        self,
        phone: str,
        status: CheckInStatus,
        hours_until_due: float,
        last_checkin_at: datetime,
    ):
        """Send a reminder to the user themselves via SMS"""
        recipient = NotificationRecipient(channel="sms", address=phone)

        if status == CheckInStatus.DUE_SOON:
            message = NotificationMessage(
                subject="Check-in Reminder",
                body=f"Hey! Your SAFE check-in is due in {abs(hours_until_due):.1f} hours. Please check in now to stay SAFE.",
            )
        else:  # MISSED
            message = NotificationMessage(
                subject="URGENT: Check-in Overdue",
                body=f"URGENT: You missed your check-in! Please check in immediately to prevent your trusted contacts from being alerted.",
            )

        print(f"📱 Sending self-reminder to {phone} (status={status})")
        adapter = self._adapter_by_channel.get("sms", ConsoleNotificationAdapter())

        event = StatusChangeEvent(
            user_phone=phone,
            new_status=status,
            last_checkin_at=last_checkin_at,
            created_at=datetime.utcnow(),
        )
        adapter.send(recipient=recipient, message=message, event=event)

    def _notify_user(
        self,
        *,
        service: CheckInService,
        phone: str,
        status: CheckInStatus,
        last_checkin_at: datetime,
    ) -> None:
        settings = service.get_settings(phone=phone)
        instructions = service.get_instructions(phone=phone)

        recipients: list[NotificationRecipient] = []

        # Contacts live in settings.contacts as simple strings
        for addr in settings.contacts or []:
            recipients.append(NotificationRecipient(channel="email", address=addr))

        # De-dupe recipients by (channel,address)
        deduped: list[NotificationRecipient] = []
        seen: set[tuple[str, str]] = set()
        for r in recipients:
            key = (r.channel, r.address)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        event = StatusChangeEvent(
            user_phone=phone,
            new_status=status,
            last_checkin_at=last_checkin_at,
            created_at=datetime.utcnow(),
            instructions=instructions.content,
        )

        if status == CheckInStatus.GRACE_PERIOD:
            # First notification: simple "please check on this person" — no sensitive info
            message = NotificationMessage(
                subject="Please check on this person — missed check-in",
                body="\n".join(
                    [
                        "Dead-Man Switch — Check-in reminder",
                        "",
                        f"The person associated with {phone} has not checked in within their expected interval.",
                        "",
                        "Please call or check on them to ensure they are okay.",
                        "",
                        f"Last check-in (UTC): {last_checkin_at.isoformat()}",
                    ]
                ),
            )
        else:
            # Second notification (NOTIFIED): full message with instructions — sensitive info
            message = NotificationMessage(
                subject="Dead-Man Switch — Important: instructions and sensitive information",
                body="\n".join(
                    [
                        "Dead-Man Switch — Instructions for trusted contacts",
                        "",
                        f"The person associated with {phone} has not checked in for an extended period.",
                        "The following information was provided for use by family members.",
                        "",
                        "--- Instructions and sensitive information ---",
                        "",
                        (instructions.content or "(No instructions provided)"),
                        "",
                        "---",
                        "",
                        f"Last check-in (UTC): {last_checkin_at.isoformat()}",
                    ]
                ),
            )

        print(f"🔔 Notifying {len(deduped)} recipients for {phone} (status={status})")
        for r in deduped:
            adapter = self._adapter_by_channel.get(r.channel, ConsoleNotificationAdapter())
            adapter.send(recipient=r, message=message, event=event)


# Global scheduler instance
_scheduler = CheckInScheduler()


def start_scheduler():
    """Start the global scheduler"""
    _scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    _scheduler.stop()
