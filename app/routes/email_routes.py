"""
Simplified email notification routes for automatic alerts and production notifications.
No dashboard interface - only essential automatic functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.schemas import BaseResponse
from app.services.email_service import EmailService
from app.services.production_notification_service import production_notification_service
import logging

# Setup logger
app_logger = logging.getLogger(__name__)
from app.core.database import get_analyzer

router = APIRouter(prefix="/api/email", tags=["Email Notifications"])


class ProductionOrderNotificationRequest(BaseModel):
    """Request model for production order notification."""
    order_id: str
    notification_type: str  # overdue, completion, status_change, urgent
    recipients: Optional[List[str]] = None
    custom_message: Optional[str] = None


class ManualAlertRequest(BaseModel):
    """Request model for manual alert."""
    title: str
    message: str
    severity: str = "medium"  # low, medium, high, critical
    alert_type: str = "general"
    send_email: bool = True


# Basic status endpoint for monitoring
@router.get("/status", response_model=BaseResponse)
async def get_email_service_status():
    """Get basic email service status for monitoring."""
    try:
        email_service = EmailService()
        
        return BaseResponse(
            success=True,
            data={
                "configured": email_service.is_configured(),
                "recipients_count": len(email_service.alert_recipients),
                "from_email": email_service.from_email
            },
            message="Email service status retrieved"
        )
        
    except Exception as e:
        app_logger.error(f"Error getting email service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving email service status: {str(e)}")


# Manual production order notification
@router.post("/production-order/notify", response_model=BaseResponse)
async def send_production_order_notification(
    request: ProductionOrderNotificationRequest,
    analyzer=Depends(get_analyzer)
):
    """Send production order notification email (for manual triggers)."""
    try:
        # Get order data
        data = analyzer.get_of_data()
        order_data = data[data['NUMERO_OFDA'] == request.order_id]
        
        if order_data.empty:
            raise HTTPException(status_code=404, detail=f"Production order {request.order_id} not found")
        
        order = order_data.iloc[0].to_dict()
        
        # Add custom message if provided
        if request.custom_message:
            order['custom_message'] = request.custom_message
        
        # Send notification
        email_service = EmailService()
        success = await email_service.send_production_order_notification(
            order_data=order,
            notification_type=request.notification_type,
            recipients=request.recipients
        )
        
        # Log the manual notification
        app_logger.info(f"Manual production order notification sent: {request.order_id} - {request.notification_type}")
        
        return BaseResponse(
            success=success,
            data={
                "order_id": request.order_id,
                "notification_type": request.notification_type,
                "timestamp": datetime.now().isoformat()
            },
            message="Notification sent" if success else "Failed to send notification"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error sending production order notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending production order notification: {str(e)}")


# Automatic notification triggers
@router.post("/production/check-overdue", response_model=BaseResponse)
async def check_overdue_orders(
    background_tasks: BackgroundTasks,
    analyzer=Depends(get_analyzer)
):
    """Manually trigger overdue order check and send notifications."""
    try:
        background_tasks.add_task(
            production_notification_service.check_and_send_overdue_notifications,
            analyzer
        )
        
        app_logger.info("Manual overdue order check initiated")
        
        return BaseResponse(
            success=True,
            data={"message": "Overdue check initiated", "timestamp": datetime.now().isoformat()},
            message="Overdue order check started"
        )

    except Exception as e:
        app_logger.error(f"Error initiating overdue check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error initiating overdue check: {str(e)}")


@router.post("/production/check-urgent", response_model=BaseResponse)
async def check_urgent_orders(
    background_tasks: BackgroundTasks,
    analyzer=Depends(get_analyzer)
):
    """Manually trigger urgent order check and send notifications."""
    try:
        background_tasks.add_task(
            production_notification_service.check_and_send_urgent_notifications,
            analyzer
        )
        
        app_logger.info("Manual urgent order check initiated")
        
        return BaseResponse(
            success=True,
            data={"message": "Urgent check initiated", "timestamp": datetime.now().isoformat()},
            message="Urgent order check started"
        )

    except Exception as e:
        app_logger.error(f"Error initiating urgent check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error initiating urgent check: {str(e)}")


@router.post("/production/send-daily-summary", response_model=BaseResponse)
async def send_daily_summary(
    background_tasks: BackgroundTasks,
    analyzer=Depends(get_analyzer)
):
    """Manually trigger daily production summary email."""
    try:
        background_tasks.add_task(
            production_notification_service.send_daily_summary,
            analyzer
        )
        
        app_logger.info("Manual daily summary generation initiated")
        
        return BaseResponse(
            success=True,
            data={"message": "Daily summary initiated", "timestamp": datetime.now().isoformat()},
            message="Daily summary generation started"
        )

    except Exception as e:
        app_logger.error(f"Error initiating daily summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error initiating daily summary: {str(e)}")


@router.get("/production/notification-status", response_model=BaseResponse)
async def get_notification_status():
    """Get production notification service status for monitoring."""
    try:
        status_data = {
            "service_active": True,
            "email_configured": production_notification_service.email_service.is_configured(),
            "last_check": production_notification_service.last_check_time.isoformat() if production_notification_service.last_check_time else None,
            "notifications_sent": len(production_notification_service.sent_notifications)
        }

        return BaseResponse(
            success=True,
            data=status_data,
            message="Notification status retrieved"
        )

    except Exception as e:
        app_logger.error(f"Error getting notification status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving notification status: {str(e)}")


# Manual alert endpoint for creating custom alerts
@router.post("/alerts/create", response_model=BaseResponse)
async def create_manual_alert(request: ManualAlertRequest):
    """Create and send a manual alert notification."""
    try:
        from app.services.alert_service import alert_service
        
        # Create manual alert
        await alert_service.create_manual_alert(
            title=request.title,
            message=request.message,
            severity=request.severity,
            alert_type=request.alert_type,
            send_email=request.send_email
        )
        
        app_logger.info(f"Manual alert created: {request.title}")
        
        return BaseResponse(
            success=True,
            data={
                "title": request.title,
                "severity": request.severity,
                "email_sent": request.send_email,
                "timestamp": datetime.now().isoformat()
            },
            message="Manual alert created and sent"
        )
        
    except Exception as e:
        app_logger.error(f"Error creating manual alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating manual alert: {str(e)}")
