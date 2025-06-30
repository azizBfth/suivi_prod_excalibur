"""
Data Service - Centralized data access layer
"""

from typing import Optional, Dict, Any
import pandas as pd
from app.core.database import get_analyzer


class DataService:
    """Service for data access operations"""
    
    def __init__(self):
        self.analyzer = get_analyzer()
    
    def get_of_data(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get OF data with filters"""
        return self.analyzer.get_of_data(
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            alerte_filter=alerte_filter
        )
    
    def get_charge_data(self) -> pd.DataFrame:
        """Get charge/workload data"""
        return self.analyzer.get_charge_data()
    
    def get_backlog_data(self) -> pd.DataFrame:
        """Get backlog data"""
        return self.analyzer.get_backlog_data()
    
    def get_personnel_data(self) -> pd.DataFrame:
        """Get personnel data"""
        return self.analyzer.get_personnel_data()
    
    def execute_custom_query(self, query: str) -> pd.DataFrame:
        """Execute custom SQL query"""
        return self.analyzer.execute_query(query)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Try a simple query to test connection
            result = self.analyzer.execute_query("SELECT 1 as test")
            return not result.empty
        except Exception:
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        try:
            # Test connection
            is_connected = self.test_connection()
            
            return {
                "connected": is_connected,
                "analyzer_type": type(self.analyzer).__name__,
                "status": "healthy" if is_connected else "disconnected"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "status": "error"
            }
