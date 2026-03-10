import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .base import NotificationAdapter
from ..models import NotificationRecipient, NotificationMessage, StatusChangeEvent

class SMTPNotificationAdapter(NotificationAdapter):
    """Notification adapter for sending emails via SMTP (e.g. Gmail)"""
    
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender = os.getenv("SMTP_SENDER")

    def send(self, recipient: NotificationRecipient, message: NotificationMessage, event: StatusChangeEvent) -> bool:
        if not all([self.user, self.password, recipient.address]):
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient.address
            msg['Subject'] = message.subject
            
            msg.attach(MIMEText(message.body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls() # Secure connection
                server.login(self.user, self.password)
                server.send_message(msg)
                
            return True
        except Exception as e:
            print(f"❌ SMTP Error: {e}")
            return False
