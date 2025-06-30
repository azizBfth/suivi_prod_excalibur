"""
Production order notification service for automatic email triggers.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

import logging

# Setup logger
app_logger = logging.getLogger(__name__)
from app.services.email_service import EmailService
from app.core.data_analyzer import ExcaliburDataAnalyzer


class ProductionNotificationService:
    """Service for managing production order email notifications."""
    
    def __init__(self):
        self.email_service = EmailService()
        self.last_check_time = None
        self.sent_notifications = {}  # Track sent notifications to avoid duplicates
    
    async def check_and_send_overdue_notifications(self, analyzer: ExcaliburDataAnalyzer) -> int:
        """Check for overdue orders and send notifications."""
        try:
            # Get current orders
            current_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            data = analyzer.get_comprehensive_of_data(start_date, current_date, 'C')
            
            if data is None or data.empty:
                app_logger.debug("No production order data available for overdue check")
                return 0
            
            # Find overdue orders
            today = datetime.now().date()
            overdue_orders = []
            
            for _, order in data.iterrows():
                try:
                    due_date_str = order.get('LANCEMENT_AU_PLUS_TARD', '')
                    if not due_date_str:
                        continue
                    
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    days_overdue = (today - due_date).days
                    
                    # Only consider orders that are actually overdue and not completed
                    if days_overdue > 0 and order.get('Avancement_PROD', 0) < 1.0:
                        order_id = order.get('NUMERO_OFDA', '')
                        
                        # Check if we already sent notification for this order today
                        notification_key = f"overdue_{order_id}_{current_date}"
                        if notification_key not in self.sent_notifications:
                            overdue_orders.append(order.to_dict())
                            self.sent_notifications[notification_key] = datetime.now()
                
                except Exception as e:
                    app_logger.warning(f"Error processing order for overdue check: {e}")
                    continue
            
            # Send notifications for overdue orders
            notifications_sent = 0
            for order_data in overdue_orders:
                try:
                    success = await self.email_service.send_production_order_notification(
                        order_data=order_data,
                        notification_type='overdue'
                    )
                    
                    if success:
                        notifications_sent += 1
                        app_logger.info(f"Overdue notification sent for order {order_data.get('NUMERO_OFDA')}")
                    
                except Exception as e:
                    app_logger.error(f"Failed to send overdue notification for order {order_data.get('NUMERO_OFDA')}: {e}")
            
            if notifications_sent > 0:
                app_logger.info(f"Sent {notifications_sent} overdue order notifications")
            
            return notifications_sent
            
        except Exception as e:
            app_logger.error(f"Error checking overdue orders: {e}", exc_info=True)
            return 0
    
    async def check_and_send_completion_notifications(self, analyzer: ExcaliburDataAnalyzer) -> int:
        """Check for recently completed orders and send notifications."""
        try:
            # Get historical data (completed orders)
            current_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Check last 24 hours
            
            # Get completed orders from historical data
            historical_data = analyzer.get_comprehensive_of_data(start_date, current_date, 'H')
            
            if historical_data is None or historical_data.empty:
                app_logger.debug("No completed orders found for notification")
                return 0
            
            notifications_sent = 0
            
            for _, order in historical_data.iterrows():
                try:
                    order_id = order.get('NUMERO_OFDA', '')
                    
                    # Check if we already sent completion notification for this order
                    notification_key = f"completion_{order_id}"
                    if notification_key not in self.sent_notifications:
                        
                        # Send completion notification
                        success = await self.email_service.send_production_order_notification(
                            order_data=order.to_dict(),
                            notification_type='completion'
                        )
                        
                        if success:
                            notifications_sent += 1
                            self.sent_notifications[notification_key] = datetime.now()
                            app_logger.info(f"Completion notification sent for order {order_id}")
                
                except Exception as e:
                    app_logger.error(f"Failed to send completion notification for order {order.get('NUMERO_OFDA')}: {e}")
            
            if notifications_sent > 0:
                app_logger.info(f"Sent {notifications_sent} completion notifications")
            
            return notifications_sent
            
        except Exception as e:
            app_logger.error(f"Error checking completed orders: {e}", exc_info=True)
            return 0
    
    async def check_and_send_urgent_notifications(self, analyzer: ExcaliburDataAnalyzer) -> int:
        """Check for orders requiring urgent attention and send notifications."""
        try:
            # Get current orders
            current_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            data = analyzer.get_comprehensive_of_data(start_date, current_date, 'C')
            
            if data is None or data.empty:
                return 0
            
            urgent_orders = []
            today = datetime.now().date()
            
            for _, order in data.iterrows():
                try:
                    order_id = order.get('NUMERO_OFDA', '')
                    due_date_str = order.get('LANCEMENT_AU_PLUS_TARD', '')
                    progress = order.get('Avancement_PROD', 0)
                    
                    if not due_date_str:
                        continue
                    
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    days_until_due = (due_date - today).days
                    
                    # Identify urgent conditions
                    urgency_reasons = []
                    
                    # Due in 1-2 days with low progress
                    if 0 <= days_until_due <= 2 and progress < 0.7:
                        urgency_reasons.append(f"Échéance dans {days_until_due} jour(s) avec seulement {progress*100:.1f}% d'avancement")
                    
                    # Very low progress on orders that should be further along
                    if days_until_due <= 5 and progress < 0.3:
                        urgency_reasons.append(f"Avancement très faible ({progress*100:.1f}%) pour une échéance proche")
                    
                    # Stalled orders (no progress in recent period - would need historical comparison)
                    if progress > 0 and progress < 0.9 and days_until_due <= 3:
                        urgency_reasons.append("Ordre proche de l'échéance nécessitant une attention immédiate")
                    
                    if urgency_reasons:
                        # Check if we already sent urgent notification for this order today
                        notification_key = f"urgent_{order_id}_{current_date}"
                        if notification_key not in self.sent_notifications:
                            order_dict = order.to_dict()
                            order_dict['urgency_reason'] = '; '.join(urgency_reasons)
                            urgent_orders.append(order_dict)
                            self.sent_notifications[notification_key] = datetime.now()
                
                except Exception as e:
                    app_logger.warning(f"Error processing order for urgent check: {e}")
                    continue
            
            # Send urgent notifications
            notifications_sent = 0
            for order_data in urgent_orders:
                try:
                    success = await self.email_service.send_production_order_notification(
                        order_data=order_data,
                        notification_type='urgent'
                    )
                    
                    if success:
                        notifications_sent += 1
                        app_logger.info(f"Urgent notification sent for order {order_data.get('NUMERO_OFDA')}")
                
                except Exception as e:
                    app_logger.error(f"Failed to send urgent notification for order {order_data.get('NUMERO_OFDA')}: {e}")
            
            if notifications_sent > 0:
                app_logger.info(f"Sent {notifications_sent} urgent order notifications")
            
            return notifications_sent
            
        except Exception as e:
            app_logger.error(f"Error checking urgent orders: {e}", exc_info=True)
            return 0
    
    async def send_daily_summary(self, analyzer: ExcaliburDataAnalyzer) -> bool:
        """Send daily production summary email."""
        try:
            # Get current date data
            current_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Get current and historical data
            current_data = analyzer.get_comprehensive_of_data(start_date, current_date, 'C')
            historical_data = analyzer.get_comprehensive_of_data(start_date, current_date, 'H')
            
            # Calculate summary metrics
            total_orders = len(current_data) if current_data is not None and not current_data.empty else 0
            completed_orders = len(historical_data) if historical_data is not None and not historical_data.empty else 0
            
            overdue_count = 0
            in_progress_count = 0
            avg_progress = 0
            
            if current_data is not None and not current_data.empty:
                today = datetime.now().date()
                
                for _, order in current_data.iterrows():
                    try:
                        due_date_str = order.get('LANCEMENT_AU_PLUS_TARD', '')
                        progress = order.get('Avancement_PROD', 0)
                        
                        if due_date_str:
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                            if due_date < today and progress < 1.0:
                                overdue_count += 1
                        
                        if 0 < progress < 1.0:
                            in_progress_count += 1
                    
                    except Exception:
                        continue
                
                avg_progress = current_data['Avancement_PROD'].mean() * 100 if 'Avancement_PROD' in current_data.columns else 0
            
            summary_data = {
                'date': current_date,
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'overdue_orders': overdue_count,
                'in_progress_orders': in_progress_count,
                'avg_progress': avg_progress
            }
            
            # Send daily summary email
            success = await self.email_service.send_daily_production_summary(summary_data)
            
            if success:
                app_logger.info(f"Daily production summary sent for {current_date}")
            
            return success
            
        except Exception as e:
            app_logger.error(f"Error sending daily summary: {e}", exc_info=True)
            return False
    
    def cleanup_old_notifications(self, days_to_keep: int = 7):
        """Clean up old notification records to prevent memory buildup."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Remove old notification records
            keys_to_remove = [
                key for key, timestamp in self.sent_notifications.items()
                if timestamp < cutoff_date
            ]
            
            for key in keys_to_remove:
                del self.sent_notifications[key]
            
            if keys_to_remove:
                app_logger.debug(f"Cleaned up {len(keys_to_remove)} old notification records")
                
        except Exception as e:
            app_logger.error(f"Error cleaning up notifications: {e}", exc_info=True)


# Global instance
production_notification_service = ProductionNotificationService()
