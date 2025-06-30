"""
Database connection utilities and dependencies.
"""

import pyodbc
from typing import Optional
from fastapi import HTTPException
from app.core.data_analyzer import ExcaliburDataAnalyzer
from app.core.config import get_settings

# Global analyzer instance
_analyzer: Optional[ExcaliburDataAnalyzer] = None


def get_db_connection():
    """
    Get database connection using the same pattern as your of_routes.py example.
    This function mimics the pattern you showed in your constructor example.
    """
    settings = get_settings()
    
    if not all([settings.db_uid, settings.db_pwd, settings.db_host, 
                settings.db_server_name, settings.db_database_name]):
        raise ValueError("Database connection parameters missing in .env")
    
    connection_string = (
        f"DRIVER={{SQL Anywhere 17}};"
        f"SERVER={settings.db_server_name};"
        f"HOST={settings.db_host};"
        f"DATABASE={settings.db_database_name};"
        f"UID={settings.db_uid};"
        f"PWD={settings.db_pwd};"
        f"CHARSET=UTF-8;"
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )


def init_analyzer() -> Optional[ExcaliburDataAnalyzer]:
    """Initialize the data analyzer instance."""
    global _analyzer
    try:
        _analyzer = ExcaliburDataAnalyzer()
        return _analyzer
    except Exception as e:
        print(f"Failed to initialize analyzer: {e}")
        _analyzer = None
        return None


def get_analyzer() -> ExcaliburDataAnalyzer:
    """
    Dependency to get the analyzer instance.
    This is used as a FastAPI dependency.
    """
    if _analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available. Please check configuration."
        )
    return _analyzer


def cleanup_analyzer() -> None:
    """Cleanup the analyzer instance."""
    global _analyzer
    if _analyzer:
        try:
            _analyzer._close_connection()
        except:
            pass  # Ignore errors when closing
        _analyzer = None
