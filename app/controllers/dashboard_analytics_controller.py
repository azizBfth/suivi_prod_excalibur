"""
Dashboard Analytics Controller
Handles specialized dashboard analytical views and data processing
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import csv
import io


class DashboardAnalyticsController:
    """Controller for dashboard analytics operations"""

    def get_overview_dashboard(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        include_historical: bool = False,
        apply_date_range: bool = True
    ) -> Dict[str, Any]:
        """Get overview dashboard with general KPIs and summary metrics."""
        try:
            # Get combined data based on settings
            if include_historical:
                if apply_date_range:
                    # Apply date range filter
                    data = analyzer.get_combined_of_data(
                        date_debut=date_debut,
                        date_fin=date_fin,
                        statut_filter=statut_filter,
                        famille_filter=famille_filter,
                        client_filter=client_filter,
                        include_historical=True
                    )
                else:
                    # Load all data then filter
                    data = analyzer.get_combined_of_data(
                        statut_filter=statut_filter,
                        famille_filter=famille_filter,
                        client_filter=client_filter,
                        include_historical=True
                    )
            else:
                # Only active data
                data = analyzer.get_of_data(
                    date_debut=date_debut if apply_date_range else None,
                    date_fin=date_fin if apply_date_range else None,
                    statut_filter=statut_filter,
                    famille_filter=famille_filter,
                    client_filter=client_filter
                )

            if data.empty:
                return self._empty_overview_response()

            # Calculate KPIs
            kpis = self._calculate_overview_kpis(data)
            
            # Get status distribution
            status_distribution = self._get_status_distribution(data)
            
            # Get family breakdown
            family_breakdown = self._get_family_breakdown(data)
            
            # Get recent activity
            recent_activity = self._get_recent_activity(data)
            
            # Get alerts and warnings
            alerts = self._get_overview_alerts(data)

            return {
                "kpis": kpis,
                "status_distribution": status_distribution,
                "family_breakdown": family_breakdown,
                "recent_activity": recent_activity,
                "alerts": alerts,
                "data_summary": {
                    "total_records": len(data),
                    "date_range": {
                        "start": date_debut,
                        "end": date_fin,
                        "applied": apply_date_range
                    },
                    "filters_applied": {
                        "status": statut_filter,
                        "family": famille_filter,
                        "client": client_filter,
                        "historical": include_historical
                    }
                }
            }

        except Exception as e:
            raise Exception(f"Error generating overview dashboard: {str(e)}")

    def get_status_analysis(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        include_historical: bool = False,
        apply_date_range: bool = True
    ) -> Dict[str, Any]:
        """Get status analysis with dynamic status loading and transitions."""
        try:
            # Get dynamic statuses
            dynamic_statuses = self.get_dynamic_statuses(analyzer, include_historical)
            
            # Get data for analysis
            if include_historical:
                if apply_date_range:
                    active_data = analyzer.get_of_data(
                        date_debut=date_debut,
                        date_fin=date_fin,
                        famille_filter=famille_filter,
                        client_filter=client_filter
                    )
                    historical_data = analyzer.get_histo_of_data(
                        date_debut=date_debut,
                        date_fin=date_fin,
                        famille_filter=famille_filter,
                        client_filter=client_filter
                    )
                else:
                    active_data = analyzer.get_of_data(
                        famille_filter=famille_filter,
                        client_filter=client_filter
                    )
                    historical_data = analyzer.get_histo_of_data(
                        famille_filter=famille_filter,
                        client_filter=client_filter
                    )
            else:
                active_data = analyzer.get_of_data(
                    date_debut=date_debut if apply_date_range else None,
                    date_fin=date_fin if apply_date_range else None,
                    famille_filter=famille_filter,
                    client_filter=client_filter
                )
                historical_data = pd.DataFrame()

            # Analyze status distributions
            status_analysis = self._analyze_status_distributions(active_data, historical_data, dynamic_statuses)
            
            # Analyze status transitions (if date range allows)
            status_transitions = self._analyze_status_transitions(active_data, date_debut, date_fin)
            
            # Get status trends over time
            status_trends = self._get_status_trends(active_data, historical_data, apply_date_range)

            return {
                "dynamic_statuses": dynamic_statuses,
                "status_analysis": status_analysis,
                "status_transitions": status_transitions,
                "status_trends": status_trends,
                "data_summary": {
                    "active_records": len(active_data) if not active_data.empty else 0,
                    "historical_records": len(historical_data) if not historical_data.empty else 0,
                    "include_historical": include_historical,
                    "apply_date_range": apply_date_range
                }
            }

        except Exception as e:
            raise Exception(f"Error generating status analysis: {str(e)}")

    def get_performance_analytics(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        include_historical: bool = False,
        apply_date_range: bool = True
    ) -> Dict[str, Any]:
        """Get performance analytics with unit time comparisons and advancement metrics."""
        try:
            # Get current period data
            current_data = analyzer.get_of_data(
                date_debut=date_debut if apply_date_range else None,
                date_fin=date_fin if apply_date_range else None,
                statut_filter=statut_filter,
                famille_filter=famille_filter,
                client_filter=client_filter
            )
            
            # Get historical data for comparison
            historical_data = analyzer.get_histo_of_data(
                date_debut=date_debut if apply_date_range else None,
                date_fin=date_fin if apply_date_range else None,
                famille_filter=famille_filter,
                client_filter=client_filter
            )
            
            # Calculate unit time comparisons
            unit_time_analysis = self._analyze_unit_times(current_data, historical_data)
            
            # Calculate advancement metrics
            advancement_metrics = self._calculate_advancement_metrics(current_data, historical_data)
            
            # Get efficiency trends
            efficiency_trends = self._get_efficiency_trends(current_data, historical_data)
            
            # Performance by family
            family_performance = self._analyze_family_performance(current_data, historical_data)

            return {
                "unit_time_analysis": unit_time_analysis,
                "advancement_metrics": advancement_metrics,
                "efficiency_trends": efficiency_trends,
                "family_performance": family_performance,
                "data_summary": {
                    "current_period_records": len(current_data) if not current_data.empty else 0,
                    "historical_records": len(historical_data) if not historical_data.empty else 0,
                    "include_historical": include_historical,
                    "apply_date_range": apply_date_range
                }
            }

        except Exception as e:
            raise Exception(f"Error generating performance analytics: {str(e)}")

    def get_data_source_comparison(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        apply_date_range: bool = True
    ) -> Dict[str, Any]:
        """Get data source comparison between OF_DA and HISTO_OF_DA tables."""
        try:
            # Get OF_DA data
            of_da_data = analyzer.get_of_data(
                date_debut=date_debut if apply_date_range else None,
                date_fin=date_fin if apply_date_range else None,
                famille_filter=famille_filter,
                client_filter=client_filter
            )
            
            # Get HISTO_OF_DA data
            histo_of_da_data = analyzer.get_histo_of_data(
                date_debut=date_debut if apply_date_range else None,
                date_fin=date_fin if apply_date_range else None,
                famille_filter=famille_filter,
                client_filter=client_filter
            )
            
            # Analyze OF_DA metrics
            of_da_metrics = self._analyze_table_metrics(of_da_data, "OF_DA")
            
            # Analyze HISTO_OF_DA metrics
            histo_of_da_metrics = self._analyze_table_metrics(histo_of_da_data, "HISTO_OF_DA")
            
            # Data quality indicators
            data_quality = self._analyze_data_quality(of_da_data, histo_of_da_data)
            
            # Table-specific insights
            table_insights = self._get_table_insights(of_da_data, histo_of_da_data)

            return {
                "of_da_metrics": of_da_metrics,
                "histo_of_da_metrics": histo_of_da_metrics,
                "data_quality": data_quality,
                "table_insights": table_insights,
                "comparison_summary": {
                    "of_da_records": len(of_da_data) if not of_da_data.empty else 0,
                    "histo_of_da_records": len(histo_of_da_data) if not histo_of_da_data.empty else 0,
                    "total_records": (len(of_da_data) if not of_da_data.empty else 0) + 
                                   (len(histo_of_da_data) if not histo_of_da_data.empty else 0),
                    "apply_date_range": apply_date_range
                }
            }

        except Exception as e:
            raise Exception(f"Error generating data source comparison: {str(e)}")

    def get_dynamic_statuses(self, analyzer, include_historical: bool = False) -> Dict[str, Any]:
        """Get all unique status values that exist in the data."""
        try:
            # Get unique statuses from OF_DA
            of_da_statuses = analyzer.execute_query(
                "SELECT DISTINCT STATUT FROM gpao.OF_DA WHERE NUMERO_OFDA LIKE 'F%' AND STATUT IS NOT NULL"
            )
            
            active_statuses = []
            if of_da_statuses is not None and not of_da_statuses.empty:
                active_statuses = of_da_statuses['STATUT'].tolist()
            
            historical_statuses = []
            if include_historical:
                # Get unique statuses from HISTO_OF_DA
                histo_statuses = analyzer.execute_query(
                    "SELECT DISTINCT STATUT FROM gpao.HISTO_OF_DA WHERE NUMERO_OFDA LIKE 'F%' AND STATUT IS NOT NULL"
                )
                if histo_statuses is not None and not histo_statuses.empty:
                    historical_statuses = histo_statuses['STATUT'].tolist()
            
            # Combine and deduplicate
            all_statuses = list(set(active_statuses + historical_statuses))
            
            return {
                "active_statuses": active_statuses,
                "historical_statuses": historical_statuses,
                "all_statuses": all_statuses,
                "status_descriptions": self._get_status_descriptions(all_statuses)
            }

        except Exception as e:
            raise Exception(f"Error getting dynamic statuses: {str(e)}")

    def export_dashboard_data(
        self,
        tab_name: str,
        format: str,
        analyzer,
        **kwargs
    ) -> Dict[str, Any]:
        """Export dashboard data for specific tab."""
        try:
            # Get data based on tab
            if tab_name == "overview":
                data = self.get_overview_dashboard(analyzer, **kwargs)
            elif tab_name == "status-analysis":
                data = self.get_status_analysis(analyzer, **kwargs)
            elif tab_name == "performance-analytics":
                data = self.get_performance_analytics(analyzer, **kwargs)
            elif tab_name == "data-source-comparison":
                data = self.get_data_source_comparison(analyzer, **kwargs)
            else:
                raise ValueError(f"Unknown tab name: {tab_name}")
            
            # Export based on format
            if format.lower() == "csv":
                return self._export_to_csv(data, tab_name)
            elif format.lower() == "pdf":
                return self._export_to_pdf(data, tab_name)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            raise Exception(f"Error exporting dashboard data: {str(e)}")

    # Helper methods for data analysis
    def _empty_overview_response(self) -> Dict[str, Any]:
        """Return empty overview response structure."""
        return {
            "kpis": {},
            "status_distribution": {},
            "family_breakdown": {},
            "recent_activity": [],
            "alerts": [],
            "data_summary": {"total_records": 0}
        }

    def _calculate_overview_kpis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overview KPIs from data."""
        if data.empty:
            return {}

        total_orders = len(data)

        # Status-based counts
        active_orders = len(data[data.get('DATA_SOURCE', '') == 'ACTIVE']) if 'DATA_SOURCE' in data.columns else 0
        historical_orders = len(data[data.get('DATA_SOURCE', '') == 'HISTORICAL']) if 'DATA_SOURCE' in data.columns else 0
        completed_orders = len(data[data.get('COMPLETION_STATUS', '') == 'COMPLETED']) if 'COMPLETION_STATUS' in data.columns else 0

        # Production metrics
        total_quantity_demanded = data['QUANTITE_DEMANDEE'].sum() if 'QUANTITE_DEMANDEE' in data.columns else 0
        total_quantity_produced = data['CUMUL_ENTREES'].sum() if 'CUMUL_ENTREES' in data.columns else 0
        avg_advancement = data['Avancement_PROD'].mean() * 100 if 'Avancement_PROD' in data.columns else 0

        # Time metrics
        avg_unit_time = data['TEMPS_UNITAIRE_HISTORIQUE'].mean() if 'TEMPS_UNITAIRE_HISTORIQUE' in data.columns else 0
        total_time_spent = data['CUMUL_TEMPS_PASSES'].sum() if 'CUMUL_TEMPS_PASSES' in data.columns else 0

        # Alerts
        alerts_count = len(data[data.get('Alerte_temps', 0) == 1]) if 'Alerte_temps' in data.columns else 0

        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "historical_orders": historical_orders,
            "completed_orders": completed_orders,
            "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0,
            "total_quantity_demanded": total_quantity_demanded,
            "total_quantity_produced": total_quantity_produced,
            "production_rate": (total_quantity_produced / total_quantity_demanded * 100) if total_quantity_demanded > 0 else 0,
            "avg_advancement": avg_advancement,
            "avg_unit_time": avg_unit_time,
            "total_time_spent": total_time_spent,
            "alerts_count": alerts_count,
            "alert_rate": (alerts_count / total_orders * 100) if total_orders > 0 else 0
        }

    def _get_status_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get status distribution from data."""
        if data.empty or 'STATUT' not in data.columns:
            return {}

        status_counts = data['STATUT'].value_counts().to_dict()
        total = len(data)

        status_percentages = {status: (count / total * 100) for status, count in status_counts.items()}

        return {
            "counts": status_counts,
            "percentages": status_percentages,
            "total": total
        }

    def _get_family_breakdown(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get family breakdown from data."""
        if data.empty or 'FAMILLE_TECHNIQUE' not in data.columns:
            return {}

        family_stats = data.groupby('FAMILLE_TECHNIQUE').agg({
            'NUMERO_OFDA': 'count',
            'Avancement_PROD': 'mean',
            'TEMPS_UNITAIRE_HISTORIQUE': 'mean'
        }).round(3)

        return family_stats.to_dict('index')

    def _get_recent_activity(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get recent activity from data."""
        if data.empty or 'LANCEMENT_AU_PLUS_TARD' not in data.columns:
            return []

        # Sort by launch date and get recent items
        recent_data = data.sort_values('LANCEMENT_AU_PLUS_TARD', ascending=False).head(10)

        return recent_data[['NUMERO_OFDA', 'PRODUIT', 'STATUT', 'LANCEMENT_AU_PLUS_TARD', 'Avancement_PROD']].to_dict('records')

    def _get_overview_alerts(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get alerts and warnings from data."""
        alerts = []

        if data.empty:
            return alerts

        # Time alerts
        if 'Alerte_temps' in data.columns:
            time_alerts = data[data['Alerte_temps'] == 1]
            if not time_alerts.empty:
                alerts.append({
                    "type": "time_overrun",
                    "severity": "warning",
                    "count": len(time_alerts),
                    "message": f"{len(time_alerts)} commandes dépassent le temps prévu"
                })

        # Low advancement alerts
        if 'Avancement_PROD' in data.columns:
            low_advancement = data[data['Avancement_PROD'] < 0.3]  # Less than 30%
            if not low_advancement.empty:
                alerts.append({
                    "type": "low_advancement",
                    "severity": "info",
                    "count": len(low_advancement),
                    "message": f"{len(low_advancement)} commandes avec avancement faible (<30%)"
                })

        return alerts

    def _analyze_status_distributions(self, active_data: pd.DataFrame, historical_data: pd.DataFrame, dynamic_statuses: Dict) -> Dict[str, Any]:
        """Analyze status distributions between active and historical data."""
        analysis = {
            "active_distribution": {},
            "historical_distribution": {},
            "comparison": {}
        }

        # Active data distribution
        if not active_data.empty and 'STATUT' in active_data.columns:
            active_counts = active_data['STATUT'].value_counts().to_dict()
            active_total = len(active_data)
            analysis["active_distribution"] = {
                "counts": active_counts,
                "percentages": {status: (count / active_total * 100) for status, count in active_counts.items()},
                "total": active_total
            }

        # Historical data distribution (all are completed)
        if not historical_data.empty:
            historical_total = len(historical_data)
            analysis["historical_distribution"] = {
                "counts": {"COMPLETED": historical_total},
                "percentages": {"COMPLETED": 100.0},
                "total": historical_total,
                "note": "All HISTO_OF_DA records are considered completed"
            }

        return analysis

    def _analyze_status_transitions(self, data: pd.DataFrame, date_debut: Optional[str], date_fin: Optional[str]) -> Dict[str, Any]:
        """Analyze status transitions over time."""
        # This would require historical tracking of status changes
        # For now, return basic transition analysis
        return {
            "transitions_available": False,
            "note": "Status transition tracking requires historical status change data",
            "current_status_summary": self._get_status_distribution(data)
        }

    def _get_status_trends(self, active_data: pd.DataFrame, historical_data: pd.DataFrame, apply_date_range: bool) -> Dict[str, Any]:
        """Get status trends over time."""
        trends = {
            "active_trends": {},
            "historical_completion_trend": {},
            "combined_trends": {}
        }

        # Basic trend analysis based on available data
        if not active_data.empty and 'LANCEMENT_AU_PLUS_TARD' in active_data.columns:
            # Group by date and status
            try:
                active_data['LANCEMENT_AU_PLUS_TARD'] = pd.to_datetime(active_data['LANCEMENT_AU_PLUS_TARD'], errors='coerce')
                daily_trends = active_data.groupby([active_data['LANCEMENT_AU_PLUS_TARD'].dt.date, 'STATUT']).size().unstack(fill_value=0)
                trends["active_trends"] = daily_trends.to_dict('index') if not daily_trends.empty else {}
            except Exception:
                trends["active_trends"] = {}

        return trends

    def _analyze_unit_times(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze unit time comparisons."""
        analysis = {
            "current_avg_unit_time": 0,
            "historical_avg_unit_time": 0,
            "comparison": {},
            "by_family": {}
        }

        # Current data unit times
        if not current_data.empty and 'TEMPS_UNITAIRE_HISTORIQUE' in current_data.columns:
            analysis["current_avg_unit_time"] = current_data['TEMPS_UNITAIRE_HISTORIQUE'].mean()

        # Historical data unit times
        if not historical_data.empty and 'TEMPS_UNITAIRE_HISTORIQUE' in historical_data.columns:
            analysis["historical_avg_unit_time"] = historical_data['TEMPS_UNITAIRE_HISTORIQUE'].mean()

        # Comparison
        if analysis["current_avg_unit_time"] > 0 and analysis["historical_avg_unit_time"] > 0:
            analysis["comparison"] = {
                "difference": analysis["current_avg_unit_time"] - analysis["historical_avg_unit_time"],
                "percentage_change": ((analysis["current_avg_unit_time"] - analysis["historical_avg_unit_time"]) / analysis["historical_avg_unit_time"]) * 100
            }

        return analysis

    def _calculate_advancement_metrics(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate advancement metrics."""
        metrics = {
            "current_metrics": {},
            "historical_metrics": {},
            "comparison": {}
        }

        # Current advancement metrics
        if not current_data.empty:
            if 'Avancement_PROD' in current_data.columns:
                metrics["current_metrics"]["avg_production_advancement"] = current_data['Avancement_PROD'].mean() * 100
                metrics["current_metrics"]["production_advancement_distribution"] = {
                    "0-25%": len(current_data[current_data['Avancement_PROD'] <= 0.25]),
                    "25-50%": len(current_data[(current_data['Avancement_PROD'] > 0.25) & (current_data['Avancement_PROD'] <= 0.5)]),
                    "50-75%": len(current_data[(current_data['Avancement_PROD'] > 0.5) & (current_data['Avancement_PROD'] <= 0.75)]),
                    "75-100%": len(current_data[current_data['Avancement_PROD'] > 0.75])
                }

            if 'Avancement_temps' in current_data.columns:
                metrics["current_metrics"]["avg_time_advancement"] = current_data['Avancement_temps'].mean() * 100

        # Historical metrics (all completed)
        if not historical_data.empty:
            metrics["historical_metrics"]["completion_rate"] = 100.0
            metrics["historical_metrics"]["total_completed"] = len(historical_data)
            if 'TEMPS_UNITAIRE_HISTORIQUE' in historical_data.columns:
                metrics["historical_metrics"]["avg_unit_time"] = historical_data['TEMPS_UNITAIRE_HISTORIQUE'].mean()

        return metrics

    def _get_efficiency_trends(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Get efficiency trends."""
        trends = {
            "current_efficiency": {},
            "historical_efficiency": {},
            "trends": {}
        }

        # Current efficiency calculations
        if not current_data.empty:
            if 'Avancement_PROD' in current_data.columns and 'Avancement_temps' in current_data.columns:
                # Calculate efficiency as production advancement vs time advancement
                efficiency_data = current_data[
                    (current_data['Avancement_temps'] > 0) &
                    (current_data['Avancement_PROD'].notna()) &
                    (current_data['Avancement_temps'].notna())
                ].copy()

                if not efficiency_data.empty:
                    efficiency_data['efficiency_ratio'] = efficiency_data['Avancement_PROD'] / efficiency_data['Avancement_temps']
                    trends["current_efficiency"]["avg_efficiency"] = efficiency_data['efficiency_ratio'].mean()
                    trends["current_efficiency"]["efficiency_distribution"] = {
                        "below_50%": len(efficiency_data[efficiency_data['efficiency_ratio'] < 0.5]),
                        "50-80%": len(efficiency_data[(efficiency_data['efficiency_ratio'] >= 0.5) & (efficiency_data['efficiency_ratio'] < 0.8)]),
                        "80-100%": len(efficiency_data[(efficiency_data['efficiency_ratio'] >= 0.8) & (efficiency_data['efficiency_ratio'] <= 1.0)]),
                        "above_100%": len(efficiency_data[efficiency_data['efficiency_ratio'] > 1.0])
                    }

        # Historical efficiency (all completed, so 100% production advancement)
        if not historical_data.empty:
            trends["historical_efficiency"]["completion_rate"] = 100.0
            trends["historical_efficiency"]["note"] = "All historical records are completed orders"

        return trends

    def _analyze_family_performance(self, current_data: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by product family."""
        performance = {
            "current_family_performance": {},
            "historical_family_performance": {},
            "family_comparison": {}
        }

        # Current family performance
        if not current_data.empty and 'FAMILLE_TECHNIQUE' in current_data.columns:
            current_family_stats = current_data.groupby('FAMILLE_TECHNIQUE').agg({
                'NUMERO_OFDA': 'count',
                'Avancement_PROD': 'mean',
                'Avancement_temps': 'mean',
                'TEMPS_UNITAIRE_HISTORIQUE': 'mean'
            }).round(3)
            performance["current_family_performance"] = current_family_stats.to_dict('index')

        # Historical family performance
        if not historical_data.empty and 'FAMILLE_TECHNIQUE' in historical_data.columns:
            historical_family_stats = historical_data.groupby('FAMILLE_TECHNIQUE').agg({
                'NUMERO_OFDA': 'count',
                'TEMPS_UNITAIRE_HISTORIQUE': 'mean'
            }).round(3)
            performance["historical_family_performance"] = historical_family_stats.to_dict('index')

        return performance

    def _analyze_table_metrics(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Analyze metrics for a specific table."""
        if data.empty:
            return {"table_name": table_name, "record_count": 0, "metrics": {}}

        metrics = {
            "table_name": table_name,
            "record_count": len(data),
            "date_range": {},
            "status_distribution": {},
            "family_distribution": {},
            "data_completeness": {}
        }

        # Date range analysis
        if 'LANCEMENT_AU_PLUS_TARD' in data.columns:
            try:
                dates = pd.to_datetime(data['LANCEMENT_AU_PLUS_TARD'], errors='coerce')
                valid_dates = dates.dropna()
                if not valid_dates.empty:
                    metrics["date_range"] = {
                        "earliest": valid_dates.min().strftime('%Y-%m-%d'),
                        "latest": valid_dates.max().strftime('%Y-%m-%d'),
                        "span_days": (valid_dates.max() - valid_dates.min()).days
                    }
            except Exception:
                pass

        # Status distribution
        if 'STATUT' in data.columns:
            status_counts = data['STATUT'].value_counts().to_dict()
            metrics["status_distribution"] = status_counts

        # Family distribution
        if 'FAMILLE_TECHNIQUE' in data.columns:
            family_counts = data['FAMILLE_TECHNIQUE'].value_counts().to_dict()
            metrics["family_distribution"] = family_counts

        # Data completeness
        total_records = len(data)
        completeness = {}
        for column in ['PRODUIT', 'QUANTITE_DEMANDEE', 'CUMUL_ENTREES', 'DUREE_PREVUE']:
            if column in data.columns:
                non_null_count = data[column].notna().sum()
                completeness[column] = {
                    "complete_records": non_null_count,
                    "completeness_percentage": (non_null_count / total_records * 100) if total_records > 0 else 0
                }
        metrics["data_completeness"] = completeness

        return metrics

    def _analyze_data_quality(self, of_da_data: pd.DataFrame, histo_of_da_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality indicators."""
        quality = {
            "of_da_quality": {},
            "histo_of_da_quality": {},
            "comparison": {}
        }

        # OF_DA quality indicators
        if not of_da_data.empty:
            quality["of_da_quality"] = self._calculate_quality_indicators(of_da_data, "OF_DA")

        # HISTO_OF_DA quality indicators
        if not histo_of_da_data.empty:
            quality["histo_of_da_quality"] = self._calculate_quality_indicators(histo_of_da_data, "HISTO_OF_DA")

        return quality

    def _calculate_quality_indicators(self, data: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Calculate quality indicators for a dataset."""
        if data.empty:
            return {}

        total_records = len(data)
        indicators = {
            "total_records": total_records,
            "missing_data": {},
            "data_consistency": {},
            "value_ranges": {}
        }

        # Missing data analysis
        for column in data.columns:
            missing_count = data[column].isna().sum()
            indicators["missing_data"][column] = {
                "missing_count": missing_count,
                "missing_percentage": (missing_count / total_records * 100) if total_records > 0 else 0
            }

        # Data consistency checks
        if 'QUANTITE_DEMANDEE' in data.columns and 'CUMUL_ENTREES' in data.columns:
            # Check for logical inconsistencies
            over_production = data[data['CUMUL_ENTREES'] > data['QUANTITE_DEMANDEE']]
            indicators["data_consistency"]["over_production_count"] = len(over_production)

        if 'DUREE_PREVUE' in data.columns and 'CUMUL_TEMPS_PASSES' in data.columns:
            # Check for time overruns
            time_overruns = data[data['CUMUL_TEMPS_PASSES'] > data['DUREE_PREVUE']]
            indicators["data_consistency"]["time_overrun_count"] = len(time_overruns)

        return indicators

    def _get_table_insights(self, of_da_data: pd.DataFrame, histo_of_da_data: pd.DataFrame) -> Dict[str, Any]:
        """Get table-specific insights and patterns."""
        insights = {
            "of_da_insights": [],
            "histo_of_da_insights": [],
            "cross_table_insights": []
        }

        # OF_DA insights
        if not of_da_data.empty:
            insights["of_da_insights"].append({
                "type": "status_insight",
                "message": f"OF_DA contains {len(of_da_data)} active production orders"
            })

            if 'STATUT' in of_da_data.columns:
                status_counts = of_da_data['STATUT'].value_counts()
                most_common_status = status_counts.index[0] if not status_counts.empty else "Unknown"
                insights["of_da_insights"].append({
                    "type": "status_distribution",
                    "message": f"Most common status in OF_DA: {most_common_status} ({status_counts.iloc[0]} orders)"
                })

        # HISTO_OF_DA insights
        if not histo_of_da_data.empty:
            insights["histo_of_da_insights"].append({
                "type": "completion_insight",
                "message": f"HISTO_OF_DA contains {len(histo_of_da_data)} completed orders (all considered finished)"
            })

            if 'TEMPS_UNITAIRE_HISTORIQUE' in histo_of_da_data.columns:
                avg_unit_time = histo_of_da_data['TEMPS_UNITAIRE_HISTORIQUE'].mean()
                insights["histo_of_da_insights"].append({
                    "type": "performance_insight",
                    "message": f"Average historical unit time: {avg_unit_time:.2f} hours"
                })

        # Cross-table insights
        if not of_da_data.empty and not histo_of_da_data.empty:
            total_orders = len(of_da_data) + len(histo_of_da_data)
            completion_rate = (len(histo_of_da_data) / total_orders * 100) if total_orders > 0 else 0
            insights["cross_table_insights"].append({
                "type": "completion_rate",
                "message": f"Overall completion rate: {completion_rate:.1f}% ({len(histo_of_da_data)} completed out of {total_orders} total orders)"
            })

        return insights

    def _get_status_descriptions(self, statuses: List[str]) -> Dict[str, str]:
        """Get human-readable descriptions for status codes."""
        descriptions = {
            'C': 'En Cours',
            'T': 'Terminé',
            'A': 'Arrêté',
            'P': 'Planifié',
            'S': 'Suspendu',
            'F': 'Fini',
            'X': 'Annulé'
        }

        return {status: descriptions.get(status, f"Statut {status}") for status in statuses}

    def _export_to_csv(self, data: Dict[str, Any], tab_name: str) -> Dict[str, Any]:
        """Export data to CSV format."""
        try:
            # Convert data to CSV-friendly format
            csv_data = self._flatten_data_for_export(data)

            # Create CSV content
            output = io.StringIO()
            if csv_data:
                writer = csv.DictWriter(output, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)

            return {
                "format": "csv",
                "filename": f"dashboard_{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content": output.getvalue(),
                "size": len(output.getvalue())
            }
        except Exception as e:
            raise Exception(f"Error exporting to CSV: {str(e)}")

    def _export_to_pdf(self, data: Dict[str, Any], tab_name: str) -> Dict[str, Any]:
        """Export data to PDF format - DISABLED."""
        raise Exception("PDF export is not available")

    def _flatten_data_for_export(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested data structure for CSV export."""
        flattened = []

        # Extract key metrics and flatten them
        if 'kpis' in data:
            for key, value in data['kpis'].items():
                flattened.append({"metric": key, "value": value, "category": "KPI"})

        if 'data_summary' in data:
            for key, value in data['data_summary'].items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flattened.append({"metric": f"{key}_{sub_key}", "value": sub_value, "category": "Summary"})
                else:
                    flattened.append({"metric": key, "value": value, "category": "Summary"})

        return flattened
