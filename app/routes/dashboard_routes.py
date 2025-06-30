"""
Dashboard Routes - MVC Pattern Implementation
"""

from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import pandas as pd

from app.controllers.dashboard_controller import DashboardController
from app.models.schemas import BaseResponse, User
from app.core.database import get_analyzer
from app.core.data_analyzer import ExcaliburDataAnalyzer
from app.middleware.auth_middleware import get_current_user, get_chef_or_admin_user, get_admin_user

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")

# Initialize controller
dashboard_controller = DashboardController()


# View Routes (Templates)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Main dashboard page."""
    # Determine user role display
    role_display = {
        "admin": "Administrateur",
        "chef": "Chef de Production",
        "user": "Utilisateur Standard"
    }.get(current_user.role, "Utilisateur Standard")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_role": role_display,
        "user_permissions": {
            "is_admin": current_user.role == "admin",
            "is_chef_or_admin": current_user.role in ["admin", "chef"],
            "can_manage_users": current_user.role == "admin",
            "can_export": current_user.role in ["admin", "chef"],
            "can_view_analytics": True
        }
    })


@router.get("/of", response_class=HTMLResponse)
async def of_management(request: Request, current_user: User = Depends(get_current_user)):
    """OF Management page."""
    # Determine user role display
    role_display = {
        "admin": "Administrateur",
        "chef": "Chef de Production",
        "user": "Utilisateur Standard"
    }.get(current_user.role, "Utilisateur Standard")

    return templates.TemplateResponse("of_management.html", {
        "request": request,
        "user": current_user,
        "user_role": role_display,
        "user_permissions": {
            "is_admin": current_user.role == "admin",
            "is_chef_or_admin": current_user.role in ["admin", "chef"],
            "can_manage_users": current_user.role == "admin",
            "can_export": current_user.role in ["admin", "chef"],
            "can_view_analytics": True
        }
    })


# Unified dashboard route - uses the updated unified_view.html template
@router.get("/unified", response_class=HTMLResponse)
async def unified_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Unified dashboard combining dashboard and OF management views."""
    # Determine user role display
    role_display = {
        "admin": "Administrateur",
        "chef": "Chef de Production",
        "user": "Utilisateur Standard"
    }.get(current_user.role, "Utilisateur Standard")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_role": role_display,
        "user_permissions": {
            "is_admin": current_user.role == "admin",
            "is_chef_or_admin": current_user.role in ["admin", "chef"],
            "can_manage_users": current_user.role == "admin",
            "can_export": current_user.role in ["admin", "chef"],
            "can_view_analytics": True
        }
    })


@router.get("/api/config", response_model=BaseResponse)
async def get_configuration(current_user: User = Depends(get_current_user)):
    """Get dynamic configuration for the unified dashboard."""
    try:
        # This would typically come from a database or configuration service
        # For now, return default configuration that can be customized
        config_data = {
            "dateDefaults": {
                "defaultRangeDays": 7,
                "maxHistoryYears": 2,
            },
            "display": {
                "maxTableRows": 100,  # Increased from default
                "maxOverdueItems": 15,  # Increased from default
                "urgentThresholdDays": 5,  # Reduced from default (more sensitive)
            },
            "labels": {
                "totalOrders": "Commandes totales",
                "inProgress": "En cours",
                "completed": "Terminées",
                "stopped": "Arrêtées",
                "alerts": "Alertes actives",
                "pendingOrders": "Commandes en attente",
                "urgentOrders": "Commandes urgentes",
                "activeOrders": "Commandes actives",
                "overdueOrders": "Commandes en retard",
                "noDataFound": "Aucune donnée disponible",
                "noOrdersFound": "Aucune commande trouvée",
                "noOverdueOrders": "Aucune commande en retard trouvée",
                "loadingData": "Chargement des données...",
                "efficiency": "Efficacité de la production",
                "avgProduction": "Production moyenne",
                "avgTime": "Temps moyen",
                "completionRate": "Taux d'achèvement"
            }
        }
        return BaseResponse(success=True, data=config_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching configuration: {str(e)}")


# API Routes (Data)
@router.get("/api/dashboard-data", response_model=BaseResponse)
async def get_dashboard_data(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter (C/T/A)"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    alerte_filter: Optional[bool] = Query(None, description="Alert filter"),
    current_user: User = Depends(get_current_user),
    analyzer=Depends(get_analyzer)
):
    """Get all dashboard data including KPIs and detailed information."""
    try:
        data = dashboard_controller.get_dashboard_data(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            alerte_filter=alerte_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


@router.get("/api/kpis", response_model=BaseResponse)
async def get_kpis(current_user: User = Depends(get_current_user), analyzer=Depends(get_analyzer)):
    """Get KPIs only for dashboard widgets."""
    try:
        kpis = dashboard_controller.get_kpis(analyzer)
        return BaseResponse(success=True, data={"kpis": kpis})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPIs: {str(e)}")


@router.get("/api/filters/options", response_model=BaseResponse)
async def get_filter_options(current_user: User = Depends(get_current_user), analyzer=Depends(get_analyzer)):
    """Get available filter options for dropdowns."""
    try:
        options = dashboard_controller.get_filter_options(analyzer)
        return BaseResponse(success=True, data={"options": options})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter options: {str(e)}")


@router.get("/api/historical-analysis")
async def get_historical_analysis(
    date_debut: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_fin: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    analyzer: ExcaliburDataAnalyzer = Depends(get_analyzer)
):
    """Get historical performance analysis comparing current data with historical benchmarks."""
    try:
        historical_data = analyzer.get_historical_analysis(date_debut, date_fin)

        if not historical_data['success']:
            raise HTTPException(status_code=404, detail=historical_data['message'])

        return BaseResponse(
            success=True,
            message="Historical analysis retrieved successfully",
            data=historical_data['data']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical analysis failed: {str(e)}")


@router.get("/api/config", response_model=BaseResponse)
async def get_configuration(current_user: User = Depends(get_current_user)):
    """Get application configuration and settings."""
    try:
        from app.core.config import get_settings
        settings = get_settings()

        config_data = {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "features": {
                "alerts": True,
                "export": True,
                "analytics": True,
                "user_management": current_user.username == "admin"
            },
            "ui_settings": {
                "refresh_interval": 30000,  # 30 seconds
                "max_records_per_page": 100,
                "default_date_range": 30  # days
            }
        }

        return BaseResponse(
            success=True,
            message="Configuration retrieved successfully",
            data=config_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")


@router.get("/api/kpis", response_model=BaseResponse)
async def get_kpis(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    current_user: User = Depends(get_current_user),
    analyzer=Depends(get_analyzer)
):
    """Get Key Performance Indicators (KPIs) for the dashboard."""
    try:
        # Get OF data
        of_data = analyzer.get_of_data()
        histo_data = analyzer.get_histo_data()

        kpis = {
            "total_orders": 0,
            "active_orders": 0,
            "completed_orders": 0,
            "overdue_orders": 0,
            "efficiency_rate": 0.0,
            "completion_rate": 0.0
        }

        if of_data is not None and not of_data.empty:
            # Apply filters
            filtered_data = of_data.copy()

            if date_debut:
                try:
                    date_debut_dt = pd.to_datetime(date_debut)
                    if 'DATE_CREATION' in filtered_data.columns:
                        filtered_data = filtered_data[pd.to_datetime(filtered_data['DATE_CREATION']) >= date_debut_dt]
                except:
                    pass

            if date_fin:
                try:
                    date_fin_dt = pd.to_datetime(date_fin)
                    if 'DATE_CREATION' in filtered_data.columns:
                        filtered_data = filtered_data[pd.to_datetime(filtered_data['DATE_CREATION']) <= date_fin_dt]
                except:
                    pass

            if statut_filter and 'STATUT' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['STATUT'] == statut_filter]

            if famille_filter and 'FAMILLE_TECHNIQUE' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['FAMILLE_TECHNIQUE'] == famille_filter]

            if client_filter and 'CLIENT' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['CLIENT'] == client_filter]

            # Calculate KPIs
            kpis["total_orders"] = len(filtered_data)

            if 'STATUT' in filtered_data.columns:
                kpis["active_orders"] = len(filtered_data[filtered_data['STATUT'] == 'C'])
                kpis["completed_orders"] = len(filtered_data[filtered_data['STATUT'] == 'T'])

            # Calculate completion rate
            if kpis["total_orders"] > 0:
                kpis["completion_rate"] = (kpis["completed_orders"] / kpis["total_orders"]) * 100

        # Add historical data if available
        if histo_data is not None and not histo_data.empty:
            kpis["historical_records"] = len(histo_data)

        return BaseResponse(
            success=True,
            message="KPIs retrieved successfully",
            data=kpis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving KPIs: {str(e)}")



