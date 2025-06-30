"""
Planning & Scheduling Routes - ERP Production Planning APIs
Handles production scheduling, resource planning, and capacity management
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
import pandas as pd

from app.core.database import get_analyzer
from app.models.schemas import BaseResponse
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/planning", tags=["Planning & Scheduling"])


@router.get("/schedule", response_model=BaseResponse)
async def get_production_schedule(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sector: Optional[str] = Query(None, description="Production sector"),
    view_type: str = Query("week", description="Schedule view (day, week, month)"),
    analyzer=Depends(get_analyzer)
):
    """Get production schedule with timeline view."""
    try:
        # Set default date range based on view type
        today = datetime.now().date()
        if not date_from:
            if view_type == "day":
                date_from = today.strftime('%Y-%m-%d')
            elif view_type == "week":
                date_from = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            elif view_type == "month":
                date_from = today.replace(day=1).strftime('%Y-%m-%d')
            else:
                date_from = today.strftime('%Y-%m-%d')
        
        if not date_to:
            if view_type == "day":
                date_to = today.strftime('%Y-%m-%d')
            elif view_type == "week":
                date_to = (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')
            elif view_type == "month":
                next_month = today.replace(day=28) + timedelta(days=4)
                date_to = (next_month - timedelta(days=next_month.day)).strftime('%Y-%m-%d')
            else:
                date_to = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get production data
        filters = {'date_debut': date_from, 'date_fin': date_to}
        if sector:
            filters['secteur_filter'] = sector
            
        production_data = analyzer.get_of_data(**filters)
        
        # Build schedule timeline
        schedule_items = []
        
        if not production_data.empty:
            for _, order in production_data.iterrows():
                # Calculate schedule dates
                try:
                    start_date = datetime.strptime(order['LANCEMENT_AU_PLUS_TARD'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    start_date = datetime.now().date()
                
                # Estimate duration based on planned hours (assume 8 hours per day)
                duration_days = max(1, int(order.get('DUREE_PREVUE', 8) / 8))
                end_date = start_date + timedelta(days=duration_days)
                
                schedule_item = {
                    "order_id": order['NUMERO_OFDA'],
                    "product": order['PRODUIT'],
                    "product_name": order['DESIGNATION'],
                    "sector": order.get('SECTEUR', 'Unknown'),
                    "priority": order.get('PRIORITE', 1),
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d'),
                    "duration_days": duration_days,
                    "planned_hours": float(order.get('DUREE_PREVUE', 0)),
                    "actual_hours": float(order.get('CUMUL_TEMPS_PASSES', 0)),
                    "progress": round(order.get('Avancement_PROD', 0) * 100, 2),
                    "status": order['STATUT'],
                    "is_overdue": start_date < today,
                    "resource_requirements": {
                        "operators": max(1, int(order.get('DUREE_PREVUE', 8) / 40)),  # Estimate operators needed
                        "machines": ["MACHINE_A", "MACHINE_B"],  # Simulated
                        "materials": f"Materials for {order['PRODUIT']}"
                    }
                }
                schedule_items.append(schedule_item)
        
        # Sort by start date and priority
        schedule_items.sort(key=lambda x: (x['start_date'], -x['priority']))
        
        # Calculate schedule metrics
        total_orders = len(schedule_items)
        overdue_orders = len([item for item in schedule_items if item['is_overdue']])
        avg_progress = sum([item['progress'] for item in schedule_items]) / len(schedule_items) if schedule_items else 0
        
        return BaseResponse(
            success=True,
            data={
                "schedule": schedule_items,
                "view_config": {
                    "view_type": view_type,
                    "date_from": date_from,
                    "date_to": date_to,
                    "sector_filter": sector
                },
                "metrics": {
                    "total_orders": total_orders,
                    "overdue_orders": overdue_orders,
                    "avg_progress": round(avg_progress, 2),
                    "schedule_efficiency": round((total_orders - overdue_orders) / total_orders * 100, 2) if total_orders > 0 else 0
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting production schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving production schedule: {str(e)}")


@router.get("/capacity-planning", response_model=BaseResponse)
async def get_capacity_planning(
    period: str = Query("month", description="Planning period (week, month, quarter)"),
    sector: Optional[str] = Query(None, description="Production sector"),
    analyzer=Depends(get_analyzer)
):
    """Get capacity planning analysis and recommendations."""
    try:
        # Calculate date range
        today = datetime.now().date()
        if period == "week":
            date_from = today.strftime('%Y-%m-%d')
            date_to = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == "month":
            date_from = today.strftime('%Y-%m-%d')
            date_to = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        elif period == "quarter":
            date_from = today.strftime('%Y-%m-%d')
            date_to = (today + timedelta(days=90)).strftime('%Y-%m-%d')
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Use: week, month, quarter")
        
        # Get production data
        production_data = analyzer.get_of_data(date_debut=date_from, date_fin=date_to)
        
        if sector:
            production_data = production_data[production_data.get('SECTEUR', '') == sector]
        
        # Calculate capacity metrics
        capacity_analysis = {
            "period": period,
            "date_range": {"from": date_from, "to": date_to},
            "total_capacity_hours": 2000,  # Simulated total available hours
            "planned_hours": float(production_data['DUREE_PREVUE'].sum()) if not production_data.empty else 0,
            "actual_hours": float(production_data['CUMUL_TEMPS_PASSES'].sum()) if not production_data.empty else 0,
            "capacity_utilization": 0,
            "efficiency_rate": 0,
            "bottlenecks": [],
            "recommendations": []
        }
        
        if capacity_analysis["total_capacity_hours"] > 0:
            capacity_analysis["capacity_utilization"] = round(
                capacity_analysis["planned_hours"] / capacity_analysis["total_capacity_hours"] * 100, 2
            )
        
        if capacity_analysis["planned_hours"] > 0:
            capacity_analysis["efficiency_rate"] = round(
                capacity_analysis["planned_hours"] / capacity_analysis["actual_hours"] * 100, 2
            ) if capacity_analysis["actual_hours"] > 0 else 0
        
        # Identify bottlenecks (simulated)
        if not production_data.empty:
            sector_workload = production_data.groupby(production_data.get('SECTEUR', 'Unknown'))['DUREE_PREVUE'].sum()
            
            for sector_name, workload in sector_workload.items():
                if workload > 500:  # Threshold for bottleneck
                    capacity_analysis["bottlenecks"].append({
                        "sector": sector_name,
                        "workload_hours": float(workload),
                        "capacity_exceeded": round((workload - 500) / 500 * 100, 2),
                        "severity": "high" if workload > 800 else "medium"
                    })
        
        # Generate recommendations
        recommendations = []
        
        if capacity_analysis["capacity_utilization"] > 90:
            recommendations.append({
                "type": "capacity",
                "priority": "high",
                "title": "Capacity Overload",
                "description": "Consider adding overtime or additional resources",
                "impact": "Potential delays in production schedule"
            })
        elif capacity_analysis["capacity_utilization"] < 60:
            recommendations.append({
                "type": "optimization",
                "priority": "medium",
                "title": "Underutilized Capacity",
                "description": "Consider taking on additional orders or reducing resources",
                "impact": "Opportunity for increased revenue or cost reduction"
            })
        
        if capacity_analysis["efficiency_rate"] < 80:
            recommendations.append({
                "type": "efficiency",
                "priority": "medium",
                "title": "Low Efficiency",
                "description": "Review processes and training to improve efficiency",
                "impact": "Potential for significant time savings"
            })
        
        capacity_analysis["recommendations"] = recommendations
        
        return BaseResponse(
            success=True,
            data=capacity_analysis
        )
    except Exception as e:
        app_logger.error(f"Error getting capacity planning: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving capacity planning: {str(e)}")


@router.get("/resource-allocation", response_model=BaseResponse)
async def get_resource_allocation(
    resource_type: Optional[str] = Query(None, description="Resource type (operators, machines, materials)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    analyzer=Depends(get_analyzer)
):
    """Get resource allocation analysis."""
    try:
        # Set default date range
        if not date_from:
            date_from = datetime.now().date().strftime('%Y-%m-%d')
        if not date_to:
            date_to = (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get production data
        production_data = analyzer.get_of_data(date_debut=date_from, date_fin=date_to)
        
        resource_allocation = {
            "date_range": {"from": date_from, "to": date_to},
            "operators": [],
            "machines": [],
            "materials": [],
            "allocation_summary": {}
        }
        
        if not production_data.empty:
            # Simulate operator allocation
            operators = [
                {"id": "OP001", "name": "John Smith", "sector": "Assembly", "skill_level": 3},
                {"id": "OP002", "name": "Jane Doe", "sector": "Machining", "skill_level": 4},
                {"id": "OP003", "name": "Bob Wilson", "sector": "Quality", "skill_level": 5},
                {"id": "OP004", "name": "Alice Brown", "sector": "Assembly", "skill_level": 2}
            ]
            
            for operator in operators:
                # Calculate workload based on production orders
                sector_orders = production_data[production_data.get('SECTEUR', '') == operator['sector']]
                workload_hours = float(sector_orders['DUREE_PREVUE'].sum()) / len(operators) if not sector_orders.empty else 0
                
                resource_allocation["operators"].append({
                    **operator,
                    "allocated_hours": round(workload_hours, 2),
                    "utilization": round(min(100, workload_hours / 40 * 100), 2),  # Assuming 40h/week
                    "assigned_orders": sector_orders['NUMERO_OFDA'].tolist() if not sector_orders.empty else [],
                    "availability": "available" if workload_hours < 35 else "overloaded"
                })
            
            # Simulate machine allocation
            machines = [
                {"id": "MACH001", "name": "CNC Machine A", "sector": "Machining", "capacity": 24},
                {"id": "MACH002", "name": "Assembly Line 1", "sector": "Assembly", "capacity": 16},
                {"id": "MACH003", "name": "Quality Station", "sector": "Quality", "capacity": 8}
            ]
            
            for machine in machines:
                sector_orders = production_data[production_data.get('SECTEUR', '') == machine['sector']]
                required_hours = float(sector_orders['DUREE_PREVUE'].sum()) if not sector_orders.empty else 0
                
                resource_allocation["machines"].append({
                    **machine,
                    "allocated_hours": round(required_hours, 2),
                    "utilization": round(min(100, required_hours / machine['capacity'] * 100), 2),
                    "assigned_orders": sector_orders['NUMERO_OFDA'].tolist() if not sector_orders.empty else [],
                    "status": "available" if required_hours < machine['capacity'] * 0.8 else "overloaded"
                })
        
        # Filter by resource type if specified
        if resource_type:
            if resource_type not in ["operators", "machines", "materials"]:
                raise HTTPException(status_code=400, detail="Invalid resource_type. Use: operators, machines, materials")
            
            filtered_data = {
                "date_range": resource_allocation["date_range"],
                resource_type: resource_allocation[resource_type],
                "allocation_summary": resource_allocation["allocation_summary"]
            }
            return BaseResponse(success=True, data=filtered_data)
        
        # Calculate allocation summary
        resource_allocation["allocation_summary"] = {
            "total_operators": len(resource_allocation["operators"]),
            "available_operators": len([op for op in resource_allocation["operators"] if op["availability"] == "available"]),
            "total_machines": len(resource_allocation["machines"]),
            "available_machines": len([m for m in resource_allocation["machines"] if m["status"] == "available"]),
            "avg_operator_utilization": round(sum([op["utilization"] for op in resource_allocation["operators"]]) / len(resource_allocation["operators"]), 2) if resource_allocation["operators"] else 0,
            "avg_machine_utilization": round(sum([m["utilization"] for m in resource_allocation["machines"]]) / len(resource_allocation["machines"]), 2) if resource_allocation["machines"] else 0
        }
        
        return BaseResponse(success=True, data=resource_allocation)
    except Exception as e:
        app_logger.error(f"Error getting resource allocation: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving resource allocation: {str(e)}")


@router.post("/optimize-schedule", response_model=BaseResponse)
async def optimize_schedule(
    optimization_criteria: str = Body(..., description="Optimization criteria (time, cost, resource)"),
    constraints: Dict = Body(..., description="Optimization constraints"),
    analyzer=Depends(get_analyzer)
):
    """Optimize production schedule based on criteria and constraints."""
    try:
        # Validate optimization criteria
        valid_criteria = ["time", "cost", "resource"]
        if optimization_criteria not in valid_criteria:
            raise HTTPException(status_code=400, detail=f"Invalid criteria. Use: {valid_criteria}")
        
        # Get current production data
        production_data = analyzer.get_of_data()
        
        if production_data.empty:
            return BaseResponse(success=True, data={"optimized_schedule": [], "improvements": {}})
        
        # Simulate schedule optimization
        optimized_orders = []
        
        for _, order in production_data.iterrows():
            # Apply optimization logic based on criteria
            if optimization_criteria == "time":
                # Prioritize by due date and duration
                priority_score = order.get('PRIORITE', 1) * 2 + (5 - min(5, order.get('DUREE_PREVUE', 0) / 10))
            elif optimization_criteria == "cost":
                # Prioritize by cost efficiency
                priority_score = order.get('PRIORITE', 1) + (order.get('QUANTITE_DEMANDEE', 0) / 100)
            else:  # resource
                # Prioritize by resource availability
                priority_score = order.get('PRIORITE', 1) + (3 if order.get('SECTEUR', '') == 'Assembly' else 1)
            
            optimized_order = {
                "order_id": order['NUMERO_OFDA'],
                "product": order['PRODUIT'],
                "original_priority": order.get('PRIORITE', 1),
                "optimized_priority": round(priority_score, 2),
                "original_start_date": order['LANCEMENT_AU_PLUS_TARD'],
                "optimized_start_date": order['LANCEMENT_AU_PLUS_TARD'],  # Would be recalculated
                "estimated_completion": order['LANCEMENT_AU_PLUS_TARD'],  # Would be recalculated
                "resource_allocation": {
                    "sector": order.get('SECTEUR', 'Unknown'),
                    "estimated_hours": float(order.get('DUREE_PREVUE', 0))
                }
            }
            optimized_orders.append(optimized_order)
        
        # Sort by optimized priority
        optimized_orders.sort(key=lambda x: x['optimized_priority'], reverse=True)
        
        # Calculate improvements
        improvements = {
            "optimization_criteria": optimization_criteria,
            "total_orders_optimized": len(optimized_orders),
            "estimated_time_savings": "15%",  # Simulated
            "estimated_cost_savings": "8%",   # Simulated
            "resource_efficiency_gain": "12%", # Simulated
            "constraints_applied": constraints
        }
        
        app_logger.info(f"Schedule optimization completed with criteria: {optimization_criteria}")
        
        return BaseResponse(
            success=True,
            message="Schedule optimization completed successfully",
            data={
                "optimized_schedule": optimized_orders,
                "improvements": improvements,
                "optimization_timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error optimizing schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing schedule: {str(e)}")


@router.get("/workload-forecast", response_model=BaseResponse)
async def get_workload_forecast(
    forecast_days: int = Query(30, description="Number of days to forecast"),
    sector: Optional[str] = Query(None, description="Production sector"),
    analyzer=Depends(get_analyzer)
):
    """Get workload forecast for production planning."""
    try:
        # Get historical data for forecasting
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=forecast_days * 2)  # Get historical data for pattern analysis
        
        production_data = analyzer.get_of_data(
            date_debut=start_date.strftime('%Y-%m-%d'),
            date_fin=end_date.strftime('%Y-%m-%d')
        )
        
        if sector:
            production_data = production_data[production_data.get('SECTEUR', '') == sector]
        
        # Generate forecast data (simplified simulation)
        forecast_data = []
        
        for i in range(forecast_days):
            forecast_date = end_date + timedelta(days=i)
            
            # Simulate workload based on historical patterns
            base_workload = 40 + (i % 7) * 5  # Weekly pattern
            seasonal_factor = 1 + 0.1 * (i % 30) / 30  # Monthly variation
            random_factor = 0.9 + (hash(str(forecast_date)) % 20) / 100  # Pseudo-random variation
            
            forecasted_workload = base_workload * seasonal_factor * random_factor
            
            forecast_data.append({
                "date": forecast_date.strftime('%Y-%m-%d'),
                "forecasted_workload_hours": round(forecasted_workload, 2),
                "confidence_level": max(60, 95 - i),  # Decreasing confidence over time
                "capacity_utilization": round(min(100, forecasted_workload / 50 * 100), 2),
                "recommended_actions": []
            })
            
            # Add recommendations based on workload
            if forecasted_workload > 45:
                forecast_data[-1]["recommended_actions"].append("Consider overtime or additional resources")
            elif forecasted_workload < 25:
                forecast_data[-1]["recommended_actions"].append("Opportunity for additional orders")
        
        # Calculate forecast summary
        avg_workload = sum([day["forecasted_workload_hours"] for day in forecast_data]) / len(forecast_data)
        peak_workload = max([day["forecasted_workload_hours"] for day in forecast_data])
        low_workload = min([day["forecasted_workload_hours"] for day in forecast_data])
        
        forecast_summary = {
            "forecast_period_days": forecast_days,
            "avg_daily_workload": round(avg_workload, 2),
            "peak_workload": round(peak_workload, 2),
            "low_workload": round(low_workload, 2),
            "workload_variance": round(peak_workload - low_workload, 2),
            "high_utilization_days": len([day for day in forecast_data if day["capacity_utilization"] > 80]),
            "sector_filter": sector
        }
        
        return BaseResponse(
            success=True,
            data={
                "forecast": forecast_data,
                "summary": forecast_summary,
                "generated_at": datetime.now().isoformat()
            }
        )
    except Exception as e:
        app_logger.error(f"Error generating workload forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating workload forecast: {str(e)}")
