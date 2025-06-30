"""
Production Management Routes - Core ERP Production APIs
Handles production orders, manufacturing processes, and production analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, List
from datetime import datetime, date, timedelta
import pandas as pd

from app.core.database import get_analyzer
from app.models.schemas import BaseResponse
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/production", tags=["Production Management"])


@router.get("/orders", response_model=BaseResponse)
async def get_production_orders(
    status: Optional[str] = Query(None, description="Order status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)"),
    priority: Optional[int] = Query(None, description="Priority level (1-5)"),
    sector: Optional[str] = Query(None, description="Production sector"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    client: Optional[str] = Query(None, description="Client filter"),
    product_family: Optional[str] = Query(None, description="Product family"),
    overdue_only: bool = Query(False, description="Show only overdue orders"),
    limit: Optional[int] = Query(100, description="Maximum number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get production orders with comprehensive filtering options."""
    try:
        # Build filters
        filters = {}
        if status:
            filters['statut_filter'] = status
        if date_from:
            filters['date_debut'] = date_from
        if date_to:
            filters['date_fin'] = date_to
        if client:
            filters['client_filter'] = client
        if product_family:
            filters['famille_filter'] = product_family

        # Get data from analyzer
        data = analyzer.get_of_data(**filters)
        
        # Apply additional filters
        if overdue_only:
            today = datetime.now().date()
            data = data[data['LANCEMENT_AU_PLUS_TARD'] < today.strftime('%Y-%m-%d')]
        
        if priority:
            data = data[data.get('PRIORITE', 0) == priority]
            
        if sector:
            data = data[data.get('SECTEUR', '') == sector]
        
        # Limit results
        if limit:
            data = data.head(limit)

        # Calculate metrics
        total_orders = len(data)
        overdue_count = len(data[data['LANCEMENT_AU_PLUS_TARD'] < datetime.now().strftime('%Y-%m-%d')]) if not data.empty else 0
        avg_progress = data['Avancement_PROD'].mean() * 100 if not data.empty else 0

        return BaseResponse(
            success=True,
            data={
                "orders": data.to_dict('records') if not data.empty else [],
                "metrics": {
                    "total_orders": total_orders,
                    "overdue_count": overdue_count,
                    "avg_progress": round(avg_progress, 2),
                    "completion_rate": round((data['Avancement_PROD'] == 1.0).sum() / len(data) * 100, 2) if not data.empty else 0
                },
                "filters_applied": filters
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting production orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving production orders: {str(e)}")


@router.get("/orders/{order_id}", response_model=BaseResponse)
async def get_production_order_details(
    order_id: str,
    analyzer=Depends(get_analyzer)
):
    """Get detailed information for a specific production order."""
    try:
        # Get all data and filter by order ID
        data = analyzer.get_of_data()
        order_data = data[data['NUMERO_OFDA'] == order_id]
        
        if order_data.empty:
            raise HTTPException(status_code=404, detail=f"Production order {order_id} not found")
        
        order = order_data.iloc[0].to_dict()
        
        # Add calculated fields
        order['days_since_launch'] = (datetime.now().date() - datetime.strptime(order.get('LANCEMENT_AU_PLUS_TARD', '2024-01-01'), '%Y-%m-%d').date()).days
        order['is_overdue'] = order['days_since_launch'] > 0
        order['completion_percentage'] = round(order.get('Avancement_PROD', 0) * 100, 2)
        
        return BaseResponse(success=True, data=order)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting order details for {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving order details: {str(e)}")


@router.get("/capacity", response_model=BaseResponse)
async def get_production_capacity(
    sector: Optional[str] = Query(None, description="Production sector"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    analyzer=Depends(get_analyzer)
):
    """Get production capacity analysis by sector."""
    try:
        # Get production data
        filters = {}
        if date_from:
            filters['date_debut'] = date_from
        if date_to:
            filters['date_fin'] = date_to
            
        data = analyzer.get_of_data(**filters)
        
        if data.empty:
            return BaseResponse(success=True, data={"sectors": [], "total_capacity": 0})
        
        # Group by sector
        if sector:
            data = data[data.get('SECTEUR', '') == sector]
        
        sector_analysis = data.groupby(data.get('SECTEUR', 'Unknown')).agg({
            'NUMERO_OFDA': 'count',
            'QUANTITE_DEMANDEE': 'sum',
            'CUMUL_ENTREES': 'sum',
            'DUREE_PREVUE': 'sum',
            'CUMUL_TEMPS_PASSES': 'sum',
            'Avancement_PROD': 'mean'
        }).round(2)
        
        sectors = []
        for sector_name, row in sector_analysis.iterrows():
            sectors.append({
                "sector": sector_name,
                "active_orders": int(row['NUMERO_OFDA']),
                "total_quantity_demanded": int(row['QUANTITE_DEMANDEE']),
                "total_quantity_produced": int(row['CUMUL_ENTREES']),
                "total_planned_hours": float(row['DUREE_PREVUE']),
                "total_actual_hours": float(row['CUMUL_TEMPS_PASSES']),
                "avg_completion": round(row['Avancement_PROD'] * 100, 2),
                "efficiency": round((row['DUREE_PREVUE'] / row['CUMUL_TEMPS_PASSES'] * 100) if row['CUMUL_TEMPS_PASSES'] > 0 else 0, 2)
            })
        
        return BaseResponse(
            success=True,
            data={
                "sectors": sectors,
                "total_capacity": {
                    "total_orders": len(data),
                    "total_planned_hours": float(data['DUREE_PREVUE'].sum()),
                    "total_actual_hours": float(data['CUMUL_TEMPS_PASSES'].sum()),
                    "overall_efficiency": round((data['DUREE_PREVUE'].sum() / data['CUMUL_TEMPS_PASSES'].sum() * 100) if data['CUMUL_TEMPS_PASSES'].sum() > 0 else 0, 2)
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting production capacity: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving production capacity: {str(e)}")


@router.get("/performance", response_model=BaseResponse)
async def get_production_performance(
    period: str = Query("week", description="Analysis period (day, week, month, quarter)"),
    sector: Optional[str] = Query(None, description="Production sector"),
    analyzer=Depends(get_analyzer)
):
    """Get production performance metrics and trends."""
    try:
        # Calculate date range based on period
        today = datetime.now().date()
        if period == "day":
            date_from = today.strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
        elif period == "week":
            date_from = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
        elif period == "month":
            date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
        elif period == "quarter":
            date_from = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Use: day, week, month, quarter")
        
        # Get data
        data = analyzer.get_of_data(date_debut=date_from, date_fin=date_to)
        
        if sector:
            data = data[data.get('SECTEUR', '') == sector]
        
        if data.empty:
            return BaseResponse(success=True, data={"performance": {}, "trends": []})
        
        # Calculate performance metrics
        performance = {
            "period": period,
            "date_range": {"from": date_from, "to": date_to},
            "total_orders": len(data),
            "completed_orders": len(data[data['Avancement_PROD'] >= 1.0]),
            "avg_completion_rate": round(data['Avancement_PROD'].mean() * 100, 2),
            "avg_efficiency": round(data.get('EFFICACITE', pd.Series([0])).mean() * 100, 2),
            "overdue_orders": len(data[data['LANCEMENT_AU_PLUS_TARD'] < today.strftime('%Y-%m-%d')]),
            "on_time_delivery": round((len(data[data['LANCEMENT_AU_PLUS_TARD'] >= today.strftime('%Y-%m-%d')]) / len(data) * 100) if len(data) > 0 else 0, 2)
        }
        
        return BaseResponse(
            success=True,
            data={
                "performance": performance,
                "sector_filter": sector,
                "data_points": len(data)
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting production performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving production performance: {str(e)}")


@router.post("/orders/{order_id}/update-status", response_model=BaseResponse)
async def update_production_order_status(
    order_id: str,
    status: str = Body(..., description="New status"),
    notes: Optional[str] = Body(None, description="Update notes"),
    analyzer=Depends(get_analyzer)
):
    """Update production order status (simulation - would need database write access)."""
    try:
        # Validate status
        valid_statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED", "ON_HOLD"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Check if order exists
        data = analyzer.get_of_data()
        order_exists = not data[data['NUMERO_OFDA'] == order_id].empty
        
        if not order_exists:
            raise HTTPException(status_code=404, detail=f"Production order {order_id} not found")
        
        # Simulate update (in real implementation, this would update the database)
        update_record = {
            "order_id": order_id,
            "old_status": "IN_PROGRESS",  # Would get from database
            "new_status": status,
            "updated_at": datetime.now().isoformat(),
            "notes": notes,
            "updated_by": "system"  # Would get from authentication
        }
        
        app_logger.info(f"Production order {order_id} status updated to {status}")
        
        return BaseResponse(
            success=True,
            message=f"Production order {order_id} status updated successfully",
            data=update_record
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error updating order status for {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")
