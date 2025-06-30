"""
Email templates for production order notifications.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class EmailTemplateManager:
    """Manager for email templates."""
    
    def __init__(self):
        self.base_style = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .order-info { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .order-details { margin: 20px 0; }
            .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
            .detail-label { font-weight: bold; color: #495057; }
            .detail-value { color: #212529; }
            .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; }
            .btn { display: inline-block; padding: 10px 20px; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
            .progress-bar { width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }
            .progress-fill { height: 100%; background-color: #28a745; transition: width 0.3s ease; }
            .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .status-pending { background-color: #ffc107; color: #212529; }
            .status-progress { background-color: #17a2b8; color: white; }
            .status-completed { background-color: #28a745; color: white; }
            .status-overdue { background-color: #dc3545; color: white; }
            .alert-box { padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid; }
            .alert-warning { background-color: #fff3cd; border-color: #ffc107; color: #856404; }
            .alert-danger { background-color: #f8d7da; border-color: #dc3545; color: #721c24; }
            .alert-success { background-color: #d4edda; border-color: #28a745; color: #155724; }
            .alert-info { background-color: #d1ecf1; border-color: #17a2b8; color: #0c5460; }
        """
    
    def get_overdue_order_template(self, order_data: Dict[str, Any], custom_message: Optional[str] = None) -> tuple[str, str]:
        """Generate overdue order email template."""
        order_number = order_data.get('NUMERO_OFDA', 'N/A')
        product_name = order_data.get('DESIGNATION_PRODUIT', 'N/A')
        client = order_data.get('NOM_CLIENT', 'N/A')
        due_date = order_data.get('LANCEMENT_AU_PLUS_TARD', 'N/A')
        progress = round(order_data.get('Avancement_PROD', 0) * 100, 1)
        
        # Calculate days overdue
        try:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            days_overdue = (datetime.now().date() - due_date_obj).days
        except:
            days_overdue = 0
        
        subject = f"🚨 URGENT - Ordre de Production en Retard: {order_number}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ordre de Production en Retard</title>
            <style>{self.base_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #dc3545;">
                    <h1>🚨 ORDRE DE PRODUCTION EN RETARD</h1>
                </div>
                
                <div class="content">
                    <div class="alert-box alert-danger">
                        <h3>⚠️ Action Immédiate Requise</h3>
                        <p><strong>L'ordre de production {order_number} est en retard de {days_overdue} jour(s).</strong></p>
                        {f'<p><em>{custom_message}</em></p>' if custom_message else ''}
                    </div>
                    
                    <div class="order-details">
                        <h3>Détails de l'Ordre</h3>
                        <div class="detail-row">
                            <span class="detail-label">Numéro d'Ordre:</span>
                            <span class="detail-value"><strong>{order_number}</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Produit:</span>
                            <span class="detail-value">{product_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Client:</span>
                            <span class="detail-value">{client}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date d'Échéance:</span>
                            <span class="detail-value"><span class="status-badge status-overdue">{due_date}</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Jours de Retard:</span>
                            <span class="detail-value"><strong style="color: #dc3545;">{days_overdue} jour(s)</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Avancement:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {progress}%; background-color: {'#dc3545' if progress < 50 else '#ffc107' if progress < 80 else '#28a745'};"></div>
                                </div>
                                {progress}%
                            </span>
                        </div>
                    </div>
                    
                    <div class="alert-box alert-warning">
                        <h4>Actions Recommandées:</h4>
                        <ul>
                            <li>Vérifier la disponibilité des ressources</li>
                            <li>Contacter l'équipe de production</li>
                            <li>Évaluer l'impact sur les autres commandes</li>
                            <li>Informer le client si nécessaire</li>
                            <li>Mettre à jour le planning de production</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="btn" style="background-color: #dc3545;">Voir les Détails</a>
                        <a href="#" class="btn" style="background-color: #6c757d;">Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Cette notification a été générée automatiquement par le Système de Suivi de Production Excalibur ERP.</p>
                    <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, body
    
    def get_completion_template(self, order_data: Dict[str, Any], custom_message: Optional[str] = None) -> tuple[str, str]:
        """Generate order completion email template."""
        order_number = order_data.get('NUMERO_OFDA', 'N/A')
        product_name = order_data.get('DESIGNATION_PRODUIT', 'N/A')
        client = order_data.get('NOM_CLIENT', 'N/A')
        completion_date = datetime.now().strftime('%Y-%m-%d')
        
        subject = f"✅ Ordre de Production Terminé: {order_number}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ordre de Production Terminé</title>
            <style>{self.base_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #28a745;">
                    <h1>✅ ORDRE DE PRODUCTION TERMINÉ</h1>
                </div>
                
                <div class="content">
                    <div class="alert-box alert-success">
                        <h3>🎉 Félicitations!</h3>
                        <p><strong>L'ordre de production {order_number} a été terminé avec succès.</strong></p>
                        {f'<p><em>{custom_message}</em></p>' if custom_message else ''}
                    </div>
                    
                    <div class="order-details">
                        <h3>Détails de l'Ordre Terminé</h3>
                        <div class="detail-row">
                            <span class="detail-label">Numéro d'Ordre:</span>
                            <span class="detail-value"><strong>{order_number}</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Produit:</span>
                            <span class="detail-value">{product_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Client:</span>
                            <span class="detail-value">{client}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date de Terminaison:</span>
                            <span class="detail-value"><span class="status-badge status-completed">{completion_date}</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Statut:</span>
                            <span class="detail-value"><span class="status-badge status-completed">TERMINÉ</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Avancement:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: 100%; background-color: #28a745;"></div>
                                </div>
                                100%
                            </span>
                        </div>
                    </div>
                    
                    <div class="alert-box alert-info">
                        <h4>Prochaines Étapes:</h4>
                        <ul>
                            <li>Contrôle qualité final</li>
                            <li>Préparation pour l'expédition</li>
                            <li>Notification au client</li>
                            <li>Mise à jour des stocks</li>
                            <li>Archivage de la documentation</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="btn" style="background-color: #28a745;">Voir les Détails</a>
                        <a href="#" class="btn" style="background-color: #17a2b8;">Rapport de Production</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Cette notification a été générée automatiquement par le Système de Suivi de Production Excalibur ERP.</p>
                    <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, body
    
    def get_status_change_template(self, order_data: Dict[str, Any], old_status: str, new_status: str, custom_message: Optional[str] = None) -> tuple[str, str]:
        """Generate status change email template."""
        order_number = order_data.get('NUMERO_OFDA', 'N/A')
        product_name = order_data.get('DESIGNATION_PRODUIT', 'N/A')
        client = order_data.get('NOM_CLIENT', 'N/A')
        progress = round(order_data.get('Avancement_PROD', 0) * 100, 1)
        
        subject = f"📋 Changement de Statut: {order_number} - {old_status} → {new_status}"
        
        # Determine status colors and messages
        status_info = {
            'PENDING': {'color': '#ffc107', 'text': 'EN ATTENTE', 'class': 'status-pending'},
            'IN_PROGRESS': {'color': '#17a2b8', 'text': 'EN COURS', 'class': 'status-progress'},
            'COMPLETED': {'color': '#28a745', 'text': 'TERMINÉ', 'class': 'status-completed'},
            'ON_HOLD': {'color': '#6c757d', 'text': 'EN PAUSE', 'class': 'status-pending'},
            'CANCELLED': {'color': '#dc3545', 'text': 'ANNULÉ', 'class': 'status-overdue'}
        }
        
        old_info = status_info.get(old_status, {'color': '#6c757d', 'text': old_status, 'class': 'status-pending'})
        new_info = status_info.get(new_status, {'color': '#6c757d', 'text': new_status, 'class': 'status-pending'})
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Changement de Statut</title>
            <style>{self.base_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: {new_info['color']};">
                    <h1>📋 CHANGEMENT DE STATUT</h1>
                </div>
                
                <div class="content">
                    <div class="alert-box alert-info">
                        <h3>📋 Mise à Jour du Statut</h3>
                        <p><strong>Le statut de l'ordre de production {order_number} a été modifié.</strong></p>
                        <p>
                            <span class="status-badge {old_info['class']}">{old_info['text']}</span>
                            →
                            <span class="status-badge {new_info['class']}">{new_info['text']}</span>
                        </p>
                        {f'<p><em>{custom_message}</em></p>' if custom_message else ''}
                    </div>
                    
                    <div class="order-details">
                        <h3>Détails de l'Ordre</h3>
                        <div class="detail-row">
                            <span class="detail-label">Numéro d'Ordre:</span>
                            <span class="detail-value"><strong>{order_number}</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Produit:</span>
                            <span class="detail-value">{product_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Client:</span>
                            <span class="detail-value">{client}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Ancien Statut:</span>
                            <span class="detail-value"><span class="status-badge {old_info['class']}">{old_info['text']}</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Nouveau Statut:</span>
                            <span class="detail-value"><span class="status-badge {new_info['class']}">{new_info['text']}</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Avancement:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {progress}%;"></div>
                                </div>
                                {progress}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date de Modification:</span>
                            <span class="detail-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="btn" style="background-color: {new_info['color']};">Voir les Détails</a>
                        <a href="#" class="btn" style="background-color: #6c757d;">Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Cette notification a été générée automatiquement par le Système de Suivi de Production Excalibur ERP.</p>
                    <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, body

    def get_urgent_order_template(self, order_data: Dict[str, Any], urgency_reason: str, custom_message: Optional[str] = None) -> tuple[str, str]:
        """Generate urgent order email template."""
        order_number = order_data.get('NUMERO_OFDA', 'N/A')
        product_name = order_data.get('DESIGNATION_PRODUIT', 'N/A')
        client = order_data.get('NOM_CLIENT', 'N/A')
        due_date = order_data.get('LANCEMENT_AU_PLUS_TARD', 'N/A')
        progress = round(order_data.get('Avancement_PROD', 0) * 100, 1)

        subject = f"⚠️ URGENT - Attention Immédiate Requise: {order_number}"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ordre de Production Urgent</title>
            <style>{self.base_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #fd7e14;">
                    <h1>⚠️ ORDRE DE PRODUCTION URGENT</h1>
                </div>

                <div class="content">
                    <div class="alert-box alert-warning">
                        <h3>⚠️ Attention Immédiate Requise</h3>
                        <p><strong>L'ordre de production {order_number} nécessite une attention urgente.</strong></p>
                        <p><strong>Raison:</strong> {urgency_reason}</p>
                        {f'<p><em>{custom_message}</em></p>' if custom_message else ''}
                    </div>

                    <div class="order-details">
                        <h3>Détails de l'Ordre Urgent</h3>
                        <div class="detail-row">
                            <span class="detail-label">Numéro d'Ordre:</span>
                            <span class="detail-value"><strong>{order_number}</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Produit:</span>
                            <span class="detail-value">{product_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Client:</span>
                            <span class="detail-value">{client}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Date d'Échéance:</span>
                            <span class="detail-value">{due_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Niveau d'Urgence:</span>
                            <span class="detail-value"><span class="status-badge" style="background-color: #fd7e14; color: white;">URGENT</span></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Avancement:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {progress}%; background-color: #fd7e14;"></div>
                                </div>
                                {progress}%
                            </span>
                        </div>
                    </div>

                    <div class="alert-box alert-danger">
                        <h4>Actions Immédiates Requises:</h4>
                        <ul>
                            <li>Contacter immédiatement l'équipe de production</li>
                            <li>Vérifier la disponibilité des ressources critiques</li>
                            <li>Évaluer les options d'accélération</li>
                            <li>Informer la direction si nécessaire</li>
                            <li>Mettre à jour le statut dans les 2 heures</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="btn" style="background-color: #fd7e14;">Action Immédiate</a>
                        <a href="#" class="btn" style="background-color: #dc3545;">Escalader</a>
                    </div>
                </div>

                <div class="footer">
                    <p>Cette notification urgente a été générée automatiquement par le Système de Suivi de Production Excalibur ERP.</p>
                    <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return subject, body

    def get_daily_summary_template(self, summary_data: Dict[str, Any]) -> tuple[str, str]:
        """Generate daily production summary email template."""
        date = summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_orders = summary_data.get('total_orders', 0)
        completed_orders = summary_data.get('completed_orders', 0)
        overdue_orders = summary_data.get('overdue_orders', 0)
        in_progress_orders = summary_data.get('in_progress_orders', 0)
        avg_progress = summary_data.get('avg_progress', 0)

        subject = f"📊 Résumé Quotidien de Production - {date}"

        # Calculate completion rate
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

        # Determine overall status color
        if overdue_orders > 0:
            status_color = "#dc3545"
            status_text = "Attention Requise"
            status_icon = "⚠️"
        elif completion_rate >= 80:
            status_color = "#28a745"
            status_text = "Excellent"
            status_icon = "✅"
        elif completion_rate >= 60:
            status_color = "#ffc107"
            status_text = "Satisfaisant"
            status_icon = "📊"
        else:
            status_color = "#fd7e14"
            status_text = "À Améliorer"
            status_icon = "📈"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Résumé Quotidien de Production</title>
            <style>
                {self.base_style}
                .metric-card {{ background-color: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid; }}
                .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
                .metric-label {{ color: #6c757d; font-size: 0.9em; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: {status_color};">
                    <h1>{status_icon} RÉSUMÉ QUOTIDIEN DE PRODUCTION</h1>
                    <p>{date}</p>
                </div>

                <div class="content">
                    <div class="alert-box alert-info">
                        <h3>📊 Statut Général: {status_text}</h3>
                        <p>Résumé de l'activité de production pour la journée du {date}.</p>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric-card" style="border-left-color: #17a2b8;">
                            <div class="metric-value" style="color: #17a2b8;">{total_orders}</div>
                            <div class="metric-label">Total des Ordres</div>
                        </div>

                        <div class="metric-card" style="border-left-color: #28a745;">
                            <div class="metric-value" style="color: #28a745;">{completed_orders}</div>
                            <div class="metric-label">Ordres Terminés</div>
                        </div>

                        <div class="metric-card" style="border-left-color: #ffc107;">
                            <div class="metric-value" style="color: #ffc107;">{in_progress_orders}</div>
                            <div class="metric-label">En Cours</div>
                        </div>

                        <div class="metric-card" style="border-left-color: #dc3545;">
                            <div class="metric-value" style="color: #dc3545;">{overdue_orders}</div>
                            <div class="metric-label">En Retard</div>
                        </div>
                    </div>

                    <div class="order-details">
                        <h3>Indicateurs de Performance</h3>
                        <div class="detail-row">
                            <span class="detail-label">Taux de Completion:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {completion_rate}%; background-color: {status_color};"></div>
                                </div>
                                {completion_rate:.1f}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Avancement Moyen:</span>
                            <span class="detail-value">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {avg_progress}%;"></div>
                                </div>
                                {avg_progress:.1f}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Statut Général:</span>
                            <span class="detail-value"><span class="status-badge" style="background-color: {status_color}; color: white;">{status_text}</span></span>
                        </div>
                    </div>

                    {f'''
                    <div class="alert-box alert-danger">
                        <h4>⚠️ Ordres en Retard Détectés</h4>
                        <p>Il y a {overdue_orders} ordre(s) en retard qui nécessitent une attention immédiate.</p>
                    </div>
                    ''' if overdue_orders > 0 else ''}

                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="btn" style="background-color: {status_color};">Voir le Dashboard</a>
                        <a href="#" class="btn" style="background-color: #6c757d;">Rapport Détaillé</a>
                    </div>
                </div>

                <div class="footer">
                    <p>Ce résumé a été généré automatiquement par le Système de Suivi de Production Excalibur ERP.</p>
                    <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return subject, body
