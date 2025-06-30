"""
Email Service for production notifications and alerts.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.config import get_settings

# Setup logger
app_logger = logging.getLogger(__name__)


class EmailService:
    """Email service for production notifications and alerts."""

    def __init__(self):
        """Initialize email service with settings."""
        self.settings = get_settings()
        self.smtp_host = getattr(self.settings, 'smtp_host', None)
        self.smtp_port = getattr(self.settings, 'smtp_port', 587)
        self.smtp_user = getattr(self.settings, 'smtp_user', None)
        self.smtp_password = getattr(self.settings, 'smtp_password', None)
        self.from_email = getattr(self.settings, 'from_email', 'noreply@example.com')

        # Parse alert recipients
        recipients_str = getattr(self.settings, 'alert_email_recipients', '')
        self.alert_recipients = [email.strip() for email in recipients_str.split(',') if email.strip()] if recipients_str else []

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.smtp_host and
            self.smtp_user and
            self.smtp_password and
            self.from_email and
            self.alert_recipients
        )
    
    async def send_production_order_notification(
        self,
        order_data: Dict[str, Any],
        notification_type: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """Send production order notification email."""
        try:
            if not self.is_configured():
                app_logger.warning("Email service not configured - logging notification instead")
                app_logger.info(f"Email notification (not configured): {notification_type} for order {order_data.get('NUMERO_OFDA', 'Unknown')}")
                return True

            # Use provided recipients or default alert recipients
            to_emails = recipients or self.alert_recipients
            if not to_emails:
                app_logger.warning("No recipients configured for email notifications")
                return False

            # Create email content based on notification type
            subject, body = self._create_production_notification_content(order_data, notification_type)

            # Send email
            return self._send_email(to_emails, subject, body)

        except Exception as e:
            app_logger.error(f"Error sending production order notification: {e}")
            return False
    
    async def send_alert_email(
        self,
        subject: str,
        message: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """Send alert email."""
        try:
            if not self.is_configured():
                app_logger.warning("Email service not configured - logging alert instead")
                app_logger.info(f"Email alert (not configured): {subject}")
                return True

            # Use provided recipients or default alert recipients
            to_emails = recipients or self.alert_recipients
            if not to_emails:
                app_logger.warning("No recipients configured for alert emails")
                return False

            # Send email
            return self._send_email(to_emails, subject, message)

        except Exception as e:
            app_logger.error(f"Error sending alert email: {e}")
            return False

    def _send_email(self, to_emails: List[str], subject: str, body: str) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # Add body to email
            msg.attach(MIMEText(body, 'html'))

            # Create SMTP session
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                # Try STARTTLS if supported
                try:
                    server.starttls()  # Enable security
                    app_logger.info("STARTTLS enabled for email connection")
                except Exception as e:
                    app_logger.warning(f"STARTTLS not supported or failed: {e}")
                    # Continue without STARTTLS for servers that don't support it

                # Login if credentials are provided
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                # Send email
                text = msg.as_string()
                server.sendmail(self.from_email, to_emails, text)

            app_logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to send email: {e}")
            return False

    def _create_production_notification_content(self, order_data: Dict[str, Any], notification_type: str) -> tuple:
        """Create email content for production notifications."""
        order_id = order_data.get('NUMERO_OFDA', 'Unknown')
        client = order_data.get('CLIENT', 'Unknown')
        famille = order_data.get('FAMILLE_TECHNIQUE', 'Unknown')
        advancement = order_data.get('Avancement_PROD', 0) * 100

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if notification_type == 'overdue':
            subject = f"🚨 Production Alert: Overdue Order {order_id}"
            body = f"""
            <html>
            <body>
                <h2>Production Alert: Overdue Order</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Client:</strong> {client}</p>
                <p><strong>Family:</strong> {famille}</p>
                <p><strong>Advancement:</strong> {advancement:.1f}%</p>
                <p><strong>Status:</strong> Overdue</p>
                <p><strong>Alert Time:</strong> {timestamp}</p>
                <hr>
                <p>This order has passed its deadline and requires immediate attention.</p>
            </body>
            </html>
            """
        elif notification_type == 'urgent':
            urgency_reason = order_data.get('urgency_reason', 'Requires immediate attention')
            subject = f"⚠️ Production Alert: Urgent Order {order_id}"
            body = f"""
            <html>
            <body>
                <h2>Production Alert: Urgent Order</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Client:</strong> {client}</p>
                <p><strong>Family:</strong> {famille}</p>
                <p><strong>Advancement:</strong> {advancement:.1f}%</p>
                <p><strong>Urgency Reason:</strong> {urgency_reason}</p>
                <p><strong>Alert Time:</strong> {timestamp}</p>
                <hr>
                <p>This order requires urgent attention to meet its deadline.</p>
            </body>
            </html>
            """
        elif notification_type == 'completion':
            subject = f"✅ Production Update: Order {order_id} Completed"
            body = f"""
            <html>
            <body>
                <h2>Production Update: Order Completed</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Client:</strong> {client}</p>
                <p><strong>Family:</strong> {famille}</p>
                <p><strong>Completion Time:</strong> {timestamp}</p>
                <hr>
                <p>This order has been successfully completed.</p>
            </body>
            </html>
            """
        else:
            subject = f"📋 Production Update: Order {order_id}"
            body = f"""
            <html>
            <body>
                <h2>Production Update</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Client:</strong> {client}</p>
                <p><strong>Family:</strong> {famille}</p>
                <p><strong>Advancement:</strong> {advancement:.1f}%</p>
                <p><strong>Update Time:</strong> {timestamp}</p>
                <hr>
                <p>Production status update for your reference.</p>
            </body>
            </html>
            """

        return subject, body
