"""
Alert management routes for system alerts and notifications.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import pandas as pd

from app.models.schemas import BaseResponse, User
from app.middleware.auth_middleware import get_current_user
from app.core.database import get_analyzer

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


class AlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "medium"  # low, medium, high, critical
    category: str = "general"  # general, production, system, quality


class AlertResponse(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    category: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool = False
    is_acknowledged: bool = False


class AlertStats(BaseModel):
    total_alerts: int
    unresolved_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int


# In-memory alert storage (in production, use a database)
alerts_storage = []
alert_counter = 0


def generate_alert_id() -> str:
    """Generate a unique alert ID."""
    global alert_counter
    alert_counter += 1
    return f"alert_{alert_counter}_{int(datetime.now().timestamp())}"


async def create_system_alert(title: str, message: str, severity: str = "medium", category: str = "system") -> dict:
    """Create a system alert with email notification."""
    from app.services.alert_service import alert_service

    alert_id = generate_alert_id()
    alert = {
        "id": alert_id,
        "title": title,
        "message": message,
        "severity": severity,
        "category": category,
        "created_at": datetime.now(),
        "resolved_at": None,
        "acknowledged_at": None,
        "is_resolved": False,
        "is_acknowledged": False
    }
    alerts_storage.append(alert)

    # Send email notification for high and critical alerts
    if severity in ["high", "critical"]:
        try:
            await alert_service.create_production_alert(
                title=title,
                message=message,
                severity=severity,
                alert_data={"category": category, "alert_id": alert_id},
                send_email=True
            )
        except Exception as e:
            app_logger.error(f"Failed to send email for alert {alert_id}: {e}")

    return alert


@router.get("/", response_model=BaseResponse)
async def get_alerts(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get all alerts with optional filtering."""
    try:
        filtered_alerts = alerts_storage.copy()
        
        # Apply filters
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity]
        
        if category:
            filtered_alerts = [a for a in filtered_alerts if a["category"] == category]
        
        if resolved is not None:
            filtered_alerts = [a for a in filtered_alerts if a["is_resolved"] == resolved]
        
        # Sort by creation date (newest first)
        filtered_alerts.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply limit
        filtered_alerts = filtered_alerts[:limit]
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(filtered_alerts)} alerts",
            data=filtered_alerts
        )
    except Exception as e:
        app_logger.error(f"Error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")


@router.get("/history", response_model=BaseResponse)
async def get_alert_history(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get alert history for the specified number of days."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        historical_alerts = [
            alert for alert in alerts_storage
            if alert["created_at"] >= cutoff_date
        ]
        
        # Sort by creation date (newest first)
        historical_alerts.sort(key=lambda x: x["created_at"], reverse=True)
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(historical_alerts)} alerts from the last {days} days",
            data=historical_alerts
        )
    except Exception as e:
        app_logger.error(f"Error retrieving alert history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alert history: {str(e)}")


@router.post("/check", response_model=BaseResponse)
async def check_alerts(
    background_tasks: BackgroundTasks,
    analyzer=Depends(get_analyzer),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger alert checking for production issues."""
    try:
        # Check for production issues and create alerts
        background_tasks.add_task(check_production_alerts, analyzer)
        
        return BaseResponse(
            success=True,
            message="Alert check initiated in background",
            data={"status": "checking"}
        )
    except Exception as e:
        app_logger.error(f"Error initiating alert check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initiating alert check: {str(e)}")


@router.post("/{alert_id}/resolve", response_model=BaseResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Resolve a specific alert."""
    try:
        alert = next((a for a in alerts_storage if a["id"] == alert_id), None)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        alert["is_resolved"] = True
        alert["resolved_at"] = datetime.now()
        
        app_logger.info(f"Alert {alert_id} resolved by user {current_user.username}")
        
        return BaseResponse(
            success=True,
            message=f"Alert {alert_id} resolved successfully",
            data=alert
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


@router.post("/resolve-multiple", response_model=BaseResponse)
async def resolve_multiple_alerts(
    alert_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Resolve multiple alerts at once."""
    try:
        resolved_alerts = []
        not_found_alerts = []
        
        for alert_id in alert_ids:
            alert = next((a for a in alerts_storage if a["id"] == alert_id), None)
            
            if alert:
                alert["is_resolved"] = True
                alert["resolved_at"] = datetime.now()
                resolved_alerts.append(alert_id)
            else:
                not_found_alerts.append(alert_id)
        
        app_logger.info(f"Resolved {len(resolved_alerts)} alerts by user {current_user.username}")
        
        return BaseResponse(
            success=True,
            message=f"Resolved {len(resolved_alerts)} alerts",
            data={
                "resolved": resolved_alerts,
                "not_found": not_found_alerts
            }
        )
    except Exception as e:
        app_logger.error(f"Error resolving multiple alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resolving multiple alerts: {str(e)}")


@router.post("/{alert_id}/acknowledge", response_model=BaseResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge a specific alert."""
    try:
        alert = next((a for a in alerts_storage if a["id"] == alert_id), None)

        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        alert["is_acknowledged"] = True
        alert["acknowledged_at"] = datetime.now()

        app_logger.info(f"Alert {alert_id} acknowledged by user {current_user.username}")

        return BaseResponse(
            success=True,
            message=f"Alert {alert_id} acknowledged successfully",
            data=alert
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error acknowledging alert: {str(e)}")


@router.get("/stats", response_model=BaseResponse)
async def get_basic_alert_stats(current_user: User = Depends(get_current_user)):
    """Get basic alert statistics."""
    try:
        total_alerts = len(alerts_storage)
        unresolved_alerts = len([a for a in alerts_storage if not a["is_resolved"]])

        severity_counts = {
            "critical": len([a for a in alerts_storage if a["severity"] == "critical"]),
            "high": len([a for a in alerts_storage if a["severity"] == "high"]),
            "medium": len([a for a in alerts_storage if a["severity"] == "medium"]),
            "low": len([a for a in alerts_storage if a["severity"] == "low"])
        }

        stats = {
            "total_alerts": total_alerts,
            "unresolved_alerts": unresolved_alerts,
            "critical_alerts": severity_counts["critical"],
            "high_alerts": severity_counts["high"],
            "medium_alerts": severity_counts["medium"],
            "low_alerts": severity_counts["low"]
        }

        return BaseResponse(
            success=True,
            message="Alert statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        app_logger.error(f"Error retrieving alert stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alert stats: {str(e)}")


@router.post("/stats", response_model=BaseResponse)
async def get_alert_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get detailed alert statistics for a specific time period."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        period_alerts = [
            alert for alert in alerts_storage
            if alert["created_at"] >= cutoff_date
        ]

        total_alerts = len(period_alerts)
        unresolved_alerts = len([a for a in period_alerts if not a["is_resolved"]])
        acknowledged_alerts = len([a for a in period_alerts if a["is_acknowledged"]])

        severity_counts = {
            "critical": len([a for a in period_alerts if a["severity"] == "critical"]),
            "high": len([a for a in period_alerts if a["severity"] == "high"]),
            "medium": len([a for a in period_alerts if a["severity"] == "medium"]),
            "low": len([a for a in period_alerts if a["severity"] == "low"])
        }

        category_counts = {}
        for alert in period_alerts:
            category = alert["category"]
            category_counts[category] = category_counts.get(category, 0) + 1

        stats = {
            "period_days": days,
            "total_alerts": total_alerts,
            "unresolved_alerts": unresolved_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "resolution_rate": (total_alerts - unresolved_alerts) / total_alerts * 100 if total_alerts > 0 else 0
        }

        return BaseResponse(
            success=True,
            message=f"Alert statistics for the last {days} days retrieved successfully",
            data=stats
        )
    except Exception as e:
        app_logger.error(f"Error retrieving detailed alert stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving detailed alert stats: {str(e)}")


@router.post("/test/manual", response_model=BaseResponse)
async def create_manual_alert(
    alert_request: AlertRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a manual alert for testing purposes."""
    try:
        alert = create_system_alert(
            title=alert_request.title,
            message=alert_request.message,
            severity=alert_request.severity,
            category=alert_request.category
        )

        app_logger.info(f"Manual alert created by user {current_user.username}: {alert['id']}")

        return BaseResponse(
            success=True,
            message="Manual alert created successfully",
            data=alert
        )
    except Exception as e:
        app_logger.error(f"Error creating manual alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating manual alert: {str(e)}")


@router.get("/test/options", response_model=BaseResponse)
async def get_alert_test_options(current_user: User = Depends(get_current_user)):
    """Get available options for alert testing."""
    try:
        options = {
            "severities": ["low", "medium", "high", "critical"],
            "categories": ["general", "production", "system", "quality", "inventory", "planning"],
            "sample_alerts": [
                {
                    "title": "Production Delay",
                    "message": "Order OF-2024-001 is behind schedule by 2 hours",
                    "severity": "high",
                    "category": "production"
                },
                {
                    "title": "System Performance",
                    "message": "Database response time is above normal threshold",
                    "severity": "medium",
                    "category": "system"
                },
                {
                    "title": "Quality Issue",
                    "message": "Defect rate exceeded 5% threshold in production line A",
                    "severity": "critical",
                    "category": "quality"
                }
            ]
        }

        return BaseResponse(
            success=True,
            message="Alert test options retrieved successfully",
            data=options
        )
    except Exception as e:
        app_logger.error(f"Error retrieving alert test options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alert test options: {str(e)}")


@router.post("/test/send", response_model=BaseResponse)
async def send_test_alert(
    title: str = "Test Alert",
    message: str = "This is a test alert from the production system",
    severity: str = "medium",
    send_email: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Send a test alert to verify the alert system is working."""
    try:
        from app.services.alert_service import alert_service

        # Create test alert
        success = await alert_service.create_manual_alert(
            title=title,
            message=message,
            severity=severity,
            alert_type="test",
            send_email=send_email
        )

        if success:
            return BaseResponse(
                success=True,
                message="Test alert sent successfully",
                data={
                    "title": title,
                    "severity": severity,
                    "email_sent": send_email,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create test alert")

    except Exception as e:
        app_logger.error(f"Error sending test alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending test alert: {str(e)}")


async def check_production_alerts(analyzer):
    """Background task to check for production-related alerts."""
    try:
        # Get current OF data
        of_data = analyzer.get_of_data()

        if of_data is not None and not of_data.empty:
            current_time = datetime.now()
            alerts_created = 0

            # 1. Check for time overrun alerts (Alerte_temps)
            if 'Alerte_temps' in of_data.columns:
                time_alerts = of_data[of_data['Alerte_temps'] == 1]
                if not time_alerts.empty:
                    await create_system_alert(
                        title="Time Overrun Alert",
                        message=f"{len(time_alerts)} orders are exceeding planned time",
                        severity="high",
                        category="production"
                    )
                    alerts_created += 1

            # 2. Check for low advancement alerts
            if 'Avancement_PROD' in of_data.columns:
                low_advancement = of_data[of_data['Avancement_PROD'] < 0.3]
                if not low_advancement.empty:
                    await create_system_alert(
                        title="Low Advancement Alert",
                        message=f"{len(low_advancement)} orders have less than 30% advancement",
                        severity="medium",
                        category="production"
                    )
                    alerts_created += 1

            # 3. Check for overdue orders (past LANCEMENT_AU_PLUS_TARD date)
            if 'LANCEMENT_AU_PLUS_TARD' in of_data.columns:
                try:
                    of_data['LANCEMENT_AU_PLUS_TARD_DATE'] = pd.to_datetime(of_data['LANCEMENT_AU_PLUS_TARD'], errors='coerce')
                    overdue_orders = of_data[
                        (of_data['LANCEMENT_AU_PLUS_TARD_DATE'].notna()) &
                        (of_data['LANCEMENT_AU_PLUS_TARD_DATE'] < current_time) &
                        (of_data['STATUT'] != 'T')  # Not terminated
                    ]
                    if not overdue_orders.empty:
                        await create_system_alert(
                            title="Overdue Orders Alert",
                            message=f"{len(overdue_orders)} orders are past their deadline",
                            severity="critical",
                            category="production"
                        )
                        alerts_created += 1
                except Exception as e:
                    app_logger.warning(f"Error checking overdue orders: {e}")

            # 4. Check for efficiency issues (time advancement > production advancement)
            if 'Avancement_temps' in of_data.columns and 'Avancement_PROD' in of_data.columns:
                efficiency_issues = of_data[
                    (of_data['Avancement_temps'] > of_data['Avancement_PROD']) &
                    (of_data['Avancement_temps'] > 0.5)  # Only for orders with significant time spent
                ]
                if not efficiency_issues.empty:
                    await create_system_alert(
                        title="Efficiency Issues Alert",
                        message=f"{len(efficiency_issues)} orders show efficiency concerns",
                        severity="medium",
                        category="production"
                    )
                    alerts_created += 1

            app_logger.info(f"Production alert check completed - {alerts_created} alerts created")

    except Exception as e:
        app_logger.error(f"Error in production alert check: {str(e)}")
        create_system_alert(
            title="Alert Check Failed",
            message=f"Failed to check production alerts: {str(e)}",
            severity="medium",
            category="system"
        )
