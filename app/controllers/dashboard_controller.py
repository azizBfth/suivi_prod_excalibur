"""
Dashboard Controller - Business logic for dashboard operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
from app.core.database import get_analyzer
from app.models.schemas import DashboardResponse, KPIData


class DashboardController:
    """Controller for dashboard business logic"""

    def __init__(self):
        pass
    
    def get_dashboard_data(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get complete dashboard data with filters"""
        try:
            # Get OF data with filters
            of_data = analyzer.get_of_data(
                date_debut=date_debut,
                date_fin=date_fin,
                statut_filter=statut_filter,
                famille_filter=famille_filter,
                client_filter=client_filter,
                alerte_filter=alerte_filter
            )

            # Calculate KPIs
            kpis = self._calculate_kpis(of_data)

            # Get additional data
            charge_data = analyzer.get_charge_data()
            backlog_data = analyzer.get_backlog_data()

            return {
                "main_of": of_data.to_dict('records') if not of_data.empty else [],
                "of_data": of_data.to_dict('records') if not of_data.empty else [],  # Keep both for compatibility
                "kpis": kpis,
                "charge_data": charge_data.to_dict('records') if not charge_data.empty else [],
                "backlog_data": backlog_data.to_dict('records') if not backlog_data.empty else [],
                "filters_applied": {
                    "date_debut": date_debut,
                    "date_fin": date_fin,
                    "statut_filter": statut_filter,
                    "famille_filter": famille_filter,
                    "client_filter": client_filter,
                    "alerte_filter": alerte_filter
                }
            }

        except Exception as e:
            raise Exception(f"Error getting dashboard data: {str(e)}")
    
    def get_kpis(self, analyzer) -> Dict[str, Any]:
        """Get KPI data only"""
        try:
            of_data = analyzer.get_of_data()
            return self._calculate_kpis(of_data)
        except Exception as e:
            raise Exception(f"Error calculating KPIs: {str(e)}")

    def get_filter_options(self, analyzer) -> Dict[str, Any]:
        """Get available filter options - simplified to only return date range information"""
        try:
            # Get all data without any filters to get date range
            of_data = analyzer.get_of_data()

            if of_data.empty:
                print("No data available, returning empty filter options")
                return {
                    "date_range": {"min": None, "max": None},
                    "total_records": 0
                }

            # Get date range from actual data
            date_range = {"min": None, "max": None}
            if 'LANCEMENT_AU_PLUS_TARD' in of_data.columns:
                dates = pd.to_datetime(of_data['LANCEMENT_AU_PLUS_TARD'], errors='coerce').dropna()
                if not dates.empty:
                    date_range = {
                        "min": dates.min().strftime('%Y-%m-%d'),
                        "max": dates.max().strftime('%Y-%m-%d')
                    }

            filter_options = {
                "date_range": date_range,
                "total_records": len(of_data),
                "message": "Only date range filtering is available"
            }

            print(f"Generated simplified filter options: {filter_options['total_records']} total records")
            return filter_options

        except Exception as e:
            print(f"Error getting filter options: {str(e)}")
            # Return empty options on error - let frontend handle gracefully
            return {
                "date_range": {"min": None, "max": None},
                "total_records": 0,
                "error": str(e)
            }
    
    def _calculate_kpis(self, of_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate KPIs from OF data"""
        if of_data.empty:
            return {
                "total_of": 0,
                "of_en_cours": 0,
                "of_termines": 0,
                "of_arretes": 0,
                "avg_prod": 0.0,
                "avg_temps": 0.0,
                "alertes": 0,
                "efficacite": 0.0
            }
        
        total_of = len(of_data)
        of_en_cours = len(of_data[of_data['STATUT'] == 'C'])
        of_termines = len(of_data[of_data['STATUT'] == 'T'])
        of_arretes = len(of_data[of_data['STATUT'] == 'A'])
        
        # Calculate averages
        avg_prod = of_data['Avancement_PROD'].mean() * 100 if 'Avancement_PROD' in of_data.columns else 0.0
        avg_temps = of_data['Avancement_temps'].mean() * 100 if 'Avancement_temps' in of_data.columns else 0.0
        
        # Count alerts
        alertes = len(of_data[of_data.get('Alerte_temps', False) == True])
        
        # Calculate efficiency
        efficacite = of_data['EFFICACITE'].mean() if 'EFFICACITE' in of_data.columns else 0.0
        
        return {
            "total_of": total_of,
            "of_en_cours": of_en_cours,
            "of_termines": of_termines,
            "of_arretes": of_arretes,
            "avg_prod": round(avg_prod, 1),
            "avg_temps": round(avg_temps, 1),
            "alertes": alertes,
            "efficacite": round(efficacite, 2)
        }
