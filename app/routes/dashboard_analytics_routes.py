"""
Dashboard Analytics Routes
Specialized endpoints for different dashboard analytical views
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.core.database import get_analyzer
from app.controllers.dashboard_analytics_controller import DashboardAnalyticsController
from app.models.schemas import BaseResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Analytics"])

# Initialize controller
dashboard_controller = DashboardAnalyticsController()

@router.get("/overview", response_model=BaseResponse)
async def get_overview_dashboard(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    include_historical: bool = Query(False, description="Include historical data"),
    apply_date_range: bool = Query(True, description="Apply date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Get overview dashboard with general KPIs and summary metrics."""
    try:
        data = dashboard_controller.get_overview_dashboard(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            include_historical=include_historical,
            apply_date_range=apply_date_range
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading overview dashboard: {str(e)}")


@router.get("/status-analysis", response_model=BaseResponse)
async def get_status_analysis(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    include_historical: bool = Query(False, description="Include historical data"),
    apply_date_range: bool = Query(True, description="Apply date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Get status analysis with dynamic status loading and transitions."""
    try:
        data = dashboard_controller.get_status_analysis(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            famille_filter=famille_filter,
            client_filter=client_filter,
            include_historical=include_historical,
            apply_date_range=apply_date_range
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading status analysis: {str(e)}")


@router.get("/performance-analytics", response_model=BaseResponse)
async def get_performance_analytics(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    include_historical: bool = Query(False, description="Include historical data"),
    apply_date_range: bool = Query(True, description="Apply date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Get performance analytics with unit time comparisons and advancement metrics."""
    try:
        data = dashboard_controller.get_performance_analytics(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            include_historical=include_historical,
            apply_date_range=apply_date_range
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading performance analytics: {str(e)}")


@router.get("/data-source-comparison", response_model=BaseResponse)
async def get_data_source_comparison(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    apply_date_range: bool = Query(True, description="Apply date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Get data source comparison between OF_DA and HISTO_OF_DA tables."""
    try:
        data = dashboard_controller.get_data_source_comparison(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            famille_filter=famille_filter,
            client_filter=client_filter,
            apply_date_range=apply_date_range
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data source comparison: {str(e)}")


@router.get("/export/{tab_name}", response_model=BaseResponse)
async def export_dashboard_data(
    tab_name: str,
    format: str = Query("csv", description="Export format (csv)"),
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    include_historical: bool = Query(False, description="Include historical data"),
    apply_date_range: bool = Query(True, description="Apply date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Export dashboard data for specific tab."""
    try:
        data = dashboard_controller.export_dashboard_data(
            tab_name=tab_name,
            format=format,
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            include_historical=include_historical,
            apply_date_range=apply_date_range
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting dashboard data: {str(e)}")


@router.get("/dynamic-statuses", response_model=BaseResponse)
async def get_dynamic_statuses(
    include_historical: bool = Query(False, description="Include historical data"),
    analyzer=Depends(get_analyzer)
):
    """Get all unique status values that exist in the data."""
    try:
        data = dashboard_controller.get_dynamic_statuses(
            analyzer=analyzer,
            include_historical=include_historical
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dynamic statuses: {str(e)}")
