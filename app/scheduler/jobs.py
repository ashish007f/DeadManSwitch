"""
Background scheduler for check-in monitoring.

Runs periodic checks to evaluate status and log changes.
Designed for future notification adapters.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.database import SessionLocal
from app.services.checkin_service import CheckInService
from app.domain.status import CheckInStatus


class CheckInScheduler:
    """Background scheduler for check-in status monitoring"""
    
    def __init__(self, check_interval_minutes: int = 1):
        self.scheduler = BackgroundScheduler()
        self.check_interval_minutes = check_interval_minutes
        self._last_status: Optional[CheckInStatus] = None
    
    def start(self):
        """Start the background scheduler"""
        try:
            self.scheduler.add_job(
                self._check_status,
                "interval",
                minutes=self.check_interval_minutes,
                id="check_checkin_status",
                replace_existing=True,
            )
            self.scheduler.start()
            print(f"✓ Scheduler started (checks every {self.check_interval_minutes} minute(s))")
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
            current_status = service.compute_current_status()
            
            # Log status change
            if current_status != self._last_status:
                timestamp = datetime.utcnow().isoformat()
                print(f"[{timestamp}] Status changed: {self._last_status} → {current_status}")
                self._last_status = current_status
                
                # If we enter NOTIFIED state, trigger notification adapters
                if current_status == CheckInStatus.NOTIFIED:
                    try:
                        self._notify_status_change(current_status)
                    except Exception as e:
                        print(f"⚠ Notification hook error: {e}")
            
        except Exception as e:
            print(f"⚠ Scheduler error: {e}")
        finally:
            db.close()
    
    def _notify_status_change(self, status: CheckInStatus):
        """
        Hook for future notification adapters.
        
        Example extensibility:
        - EmailNotifier.send(status)
        - WhatsAppNotifier.send(status)
        - SlackNotifier.send(status)
        """
        # Minimal notifier: read settings + instructions and print intended notifications.
        db = SessionLocal()
        try:
            service = CheckInService(db)
            settings = service.get_settings()
            instructions = service.get_instructions()

            contacts = settings.contacts or []
            print(f"🔔 Notifying {len(contacts)} contacts about status {status}")
            for c in contacts:
                print(f" - Would notify: {c}")

            if instructions.content:
                print("📄 Instructions to send:")
                print(instructions.content)

            # Real implementations would call external adapters here.
        except Exception as e:
            print(f"⚠ Failed to run notifier: {e}")
        finally:
            db.close()


# Global scheduler instance
_scheduler = CheckInScheduler()


def start_scheduler():
    """Start the global scheduler"""
    _scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    _scheduler.stop()
