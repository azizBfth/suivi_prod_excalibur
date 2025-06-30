"""
Alert Service for creating and managing production alerts.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.email_service import EmailService

# Setup logger
app_logger = logging.getLogger(__name__)


class AlertService:
    """Alert service for creating and managing production alerts."""

    def __init__(self):
        """Initialize alert service."""
        self.alerts = []
        self.email_service = EmailService()
    
    async def create_manual_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        alert_type: str = "general",
        send_email: bool = True
    ) -> bool:
        """Create a manual alert."""
        try:
            alert = {
                "title": title,
                "message": message,
                "severity": severity,
                "alert_type": alert_type,
                "timestamp": datetime.now(),
                "email_sent": False
            }

            self.alerts.append(alert)
            app_logger.info(f"Manual alert created: {title} - {severity}")

            # Send email notification if requested
            if send_email:
                email_subject = f"🔔 Production Alert: {title}"
                email_body = self._create_alert_email_body(title, message, severity, alert_type)

                email_sent = await self.email_service.send_alert_email(
                    subject=email_subject,
                    message=email_body
                )

                alert["email_sent"] = email_sent
                if email_sent:
                    app_logger.info(f"Alert email sent successfully: {title}")
                else:
                    app_logger.warning(f"Failed to send alert email: {title}")

            return True

        except Exception as e:
            app_logger.error(f"Error creating manual alert: {e}")
            return False

    async def create_production_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        alert_data: Optional[Dict[str, Any]] = None,
        send_email: bool = True
    ) -> bool:
        """Create a production-related alert."""
        try:
            alert = {
                "title": title,
                "message": message,
                "severity": severity,
                "alert_type": "production",
                "timestamp": datetime.now(),
                "alert_data": alert_data or {},
                "email_sent": False
            }

            self.alerts.append(alert)
            app_logger.info(f"Production alert created: {title} - {severity}")

            # Send email notification if requested
            if send_email:
                email_subject = f"🏭 Production Alert: {title}"
                email_body = self._create_production_alert_email_body(title, message, severity, alert_data)

                email_sent = await self.email_service.send_alert_email(
                    subject=email_subject,
                    message=email_body
                )

                alert["email_sent"] = email_sent
                if email_sent:
                    app_logger.info(f"Production alert email sent successfully: {title}")
                else:
                    app_logger.warning(f"Failed to send production alert email: {title}")

            return True

        except Exception as e:
            app_logger.error(f"Error creating production alert: {e}")
            return False

    def _create_alert_email_body(self, title: str, message: str, severity: str, alert_type: str) -> str:
        """Create HTML email body for general alerts."""
        severity_colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545"
        }

        color = severity_colors.get(severity, "#6c757d")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: {color};">🔔 Production Alert</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{title}</h3>
                    <p><strong>Severity:</strong> <span style="color: {color}; text-transform: uppercase;">{severity}</span></p>
                    <p><strong>Type:</strong> {alert_type}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                </div>
                <div style="background-color: #ffffff; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px;">
                    <h4>Details:</h4>
                    <p>{message}</p>
                </div>
                <hr style="margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated alert from the Production Tracking System.
                </p>
            </div>
        </body>
        </html>
        """

    def _create_production_alert_email_body(self, title: str, message: str, severity: str, alert_data: Optional[Dict[str, Any]]) -> str:
        """Create HTML email body for production alerts."""
        severity_colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545"
        }

        color = severity_colors.get(severity, "#6c757d")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build additional data section
        additional_info = ""
        if alert_data:
            additional_info = "<h4>Additional Information:</h4><ul>"
            for key, value in alert_data.items():
                additional_info += f"<li><strong>{key}:</strong> {value}</li>"
            additional_info += "</ul>"

        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: {color};">🏭 Production Alert</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{title}</h3>
                    <p><strong>Severity:</strong> <span style="color: {color}; text-transform: uppercase;">{severity}</span></p>
                    <p><strong>Type:</strong> Production</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                </div>
                <div style="background-color: #ffffff; padding: 20px; border: 1px solid #dee2e6; border-radius: 5px;">
                    <h4>Alert Details:</h4>
                    <p>{message}</p>
                    {additional_info}
                </div>
                <hr style="margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated production alert from the Production Tracking System.
                </p>
            </div>
        </body>
        </html>
        """


# Create a global instance for use across the application
alert_service = AlertService()


# Global instance
alert_service = AlertService()
