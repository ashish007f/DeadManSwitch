"""
Background scheduler for check-in monitoring using Firestore.

Runs periodic checks to evaluate status and log changes.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from datetime import datetime, timezone
from typing import Optional
from google.cloud import firestore

from app.db.database import get_firestore_client
from app.services.checkin_service import CheckInService
from app.domain.status import CheckInStatus
from app.repositories.notification_repo import NotificationLogRepository
from app.notifications.adapters.console import ConsoleNotificationAdapter
from app.notifications.adapters.fcm import FCMNotificationAdapter
from app.notifications.adapters.smtp import SMTPNotificationAdapter
from app.notifications.models import (
    NotificationMessage,
    NotificationRecipient,
    StatusChangeEvent,
)

# Silence APScheduler info/success logs
logging.getLogger('apscheduler').setLevel(logging.WARNING)

class CheckInScheduler:
    """Background scheduler for check-in status monitoring using Firestore"""
    
    def __init__(self, check_interval_hrs: float = 0.0166): # 1 minute
        self.scheduler = BackgroundScheduler()
        self.check_interval_hours = check_interval_hrs
        self._last_status_by_phone: dict[str, CheckInStatus] = {}
        # Phase 2: pluggable adapter registry
        self._adapter_by_channel = {
            "email": SMTPNotificationAdapter(),
            "sms": ConsoleNotificationAdapter(),
            "whatsapp": ConsoleNotificationAdapter(),
            "push": FCMNotificationAdapter(),
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
        db = get_firestore_client()
        try:
            service = CheckInService(db)
            notif_repo = NotificationLogRepository(db)

            # Iterate over all users in Firestore
            users_ref = db.collection("users")
            for user_doc in users_ref.stream():
                user_data = user_doc.to_dict()
                p_hash = user_data.get("phone_hash")
                if not p_hash:
                    continue
                
                # Try to get raw phone for email bodies
                from app.domain.encryption import decrypt_data
                raw_phone = decrypt_data(user_data.get("encrypted_phone")) or p_hash
                    
                status_resp = service.get_status(p_hash=p_hash)
                current_status = status_resp.status

                prev_status = self._last_status_by_phone.get(p_hash)
                if prev_status != current_status:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    print(f"[{timestamp}] [{raw_phone}] Status changed: {prev_status} → {current_status}")
                    self._last_status_by_phone[p_hash] = current_status

                if status_resp.last_checkin is None:
                    continue

                # Reminders to the user themselves
                for reminder_status in (CheckInStatus.DUE_SOON, CheckInStatus.MISSED):
                    if current_status != reminder_status:
                        continue
                    
                    already_reminded = notif_repo.has_sent(
                        p_hash=p_hash,
                        last_checkin_at=status_resp.last_checkin,
                        status=f"REMINDER_{reminder_status.value}",
                    )
                    
                    if not already_reminded:
                        try:
                            self._send_self_reminder(
                                p_hash=p_hash,
                                raw_phone=raw_phone,
                                fcm_token=user_data.get("fcm_token"),
                                status=reminder_status,
                                hours_until_due=status_resp.hours_until_due,
                                last_checkin_at=status_resp.last_checkin,
                            )
                            notif_repo.record_sent(
                                p_hash=p_hash,
                                last_checkin_at=status_resp.last_checkin,
                                status=f"REMINDER_{reminder_status.value}",
                            )
                        except Exception as e:
                            print(f"⚠ Reminder error for {p_hash}: {e}")

                # Escalation notifications
                for notify_status in (CheckInStatus.GRACE_PERIOD, CheckInStatus.NOTIFIED):
                    if current_status != notify_status:
                        continue
                    already_sent = notif_repo.has_sent(
                        p_hash=p_hash,
                        last_checkin_at=status_resp.last_checkin,
                        status=notify_status.value,
                    )
                    if not already_sent:
                        try:
                            self._notify_user(
                                service=service,
                                p_hash=p_hash,
                                raw_phone=raw_phone,
                                status=notify_status,
                                last_checkin_at=status_resp.last_checkin,
                            )
                            notif_repo.record_sent(
                                p_hash=p_hash,
                                last_checkin_at=status_resp.last_checkin,
                                status=notify_status.value,
                            )
                        except Exception as e:
                            print(f"⚠ Notification error for {raw_phone}: {e}")
            
        except Exception as e:
            print(f"⚠ Scheduler error: {e}")
    
    def _send_self_reminder(
        self,
        p_hash: str,
        raw_phone: str,
        fcm_token: Optional[str],
        status: CheckInStatus,
        hours_until_due: float,
        last_checkin_at: datetime,
    ):
        """Send a reminder to the user themselves"""
        if status == CheckInStatus.DUE_SOON:
            message = NotificationMessage(
                subject="Check-in Reminder",
                body=f"Hey! Your SAFE check-in for {raw_phone} is due in {abs(hours_until_due):.1f} hours. Please check in now to stay SAFE.",
            )
        else:  # MISSED
            message = NotificationMessage(
                subject="URGENT: Check-in Overdue",
                body=f"URGENT: You missed your check-in for {raw_phone}! Please check in immediately to prevent your trusted contacts from being alerted.",
            )

        print(f"📱 Sending self-reminder to {raw_phone} (status={status})")
        
        event = StatusChangeEvent(
            user_phone=raw_phone,
            new_status=status,
            last_checkin_at=last_checkin_at,
            created_at=datetime.now(timezone.utc),
        )

        if fcm_token:
            push_recipient = NotificationRecipient(channel="push", address=fcm_token)
            push_adapter = self._adapter_by_channel.get("push")
            if push_adapter:
                push_adapter.send(recipient=push_recipient, message=message, event=event)

        sms_recipient = NotificationRecipient(channel="sms", address=raw_phone)
        sms_adapter = self._adapter_by_channel.get("sms", ConsoleNotificationAdapter())
        sms_adapter.send(recipient=sms_recipient, message=message, event=event)

    def _notify_user(
        self,
        *,
        service: CheckInService,
        p_hash: str,
        raw_phone: str,
        status: CheckInStatus,
        last_checkin_at: datetime,
    ) -> None:
        settings = service.get_settings(p_hash=p_hash)
        instructions = service.get_instructions(p_hash=p_hash)

        recipients: list[NotificationRecipient] = []
        for addr in settings.contacts or []:
            recipients.append(NotificationRecipient(channel="email", address=addr))

        deduped: list[NotificationRecipient] = []
        seen: set[tuple[str, str]] = set()
        for r in recipients:
            key = (r.channel, r.address)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        event = StatusChangeEvent(
            user_phone=raw_phone,
            new_status=status,
            last_checkin_at=last_checkin_at,
            created_at=datetime.now(timezone.utc),
            instructions=instructions.content,
        )

        if status == CheckInStatus.GRACE_PERIOD:
            message = NotificationMessage(
                subject="Please check on this person — missed check-in",
                body="\n".join([
                    "I'mGood — Check-in reminder",
                    "",
                    f"The person associated with {raw_phone} has not checked in within their expected interval.",
                    "",
                    "Please call or check on them to ensure they are okay.",
                    "",
                    f"Last check-in (UTC): {last_checkin_at.isoformat()}",
                ]),
            )
        else:
            message = NotificationMessage(
                subject="I'mGood — Important: instructions and sensitive information",
                body="\n".join([
                    "I'mGood — Instructions for trusted contacts",
                    "",
                    f"The person associated with {raw_phone} has not checked in for an extended period.",
                    "The following information was provided for use by family members.",
                    "",
                    "--- Instructions and sensitive information ---",
                    "",
                    (instructions.content or "(No instructions provided)"),
                    "",
                    "---",
                    "",
                    f"Last check-in (UTC): {last_checkin_at.isoformat()}",
                ]),
            )

        print(f"🔔 Notifying {len(deduped)} recipients for {raw_phone} (status={status})")
        for r in deduped:
            adapter = self._adapter_by_channel.get(r.channel, ConsoleNotificationAdapter())
            adapter.send(recipient=r, message=message, event=event)


_scheduler = CheckInScheduler()

def start_scheduler():
    _scheduler.start()

def stop_scheduler():
    _scheduler.stop()
