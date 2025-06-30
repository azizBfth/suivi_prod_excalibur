"""
Inventory Management Routes - ERP Inventory & Stock APIs
Handles stock levels, material requirements, and inventory analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_analyzer
from app.models.schemas import BaseResponse
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inventory", tags=["Inventory Management"])


@router.get("/stock-levels", response_model=BaseResponse)
async def get_stock_levels(
    product_code: Optional[str] = Query(None, description="Product code filter"),
    category: Optional[str] = Query(None, description="Product category"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    location: Optional[str] = Query(None, description="Storage location"),
    limit: Optional[int] = Query(100, description="Maximum number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get current stock levels for all products."""
    try:
        # Get production data to calculate stock requirements
        production_data = analyzer.get_of_data()
        
        # Simulate stock data based on production requirements
        stock_items = []
        
        if not production_data.empty:
            # Group by product to calculate stock needs
            product_summary = production_data.groupby('PRODUIT').agg({
                'QUANTITE_DEMANDEE': 'sum',
                'CUMUL_ENTREES': 'sum',
                'FAMILLE_TECHNIQUE': 'first'
            }).reset_index()
            
            for _, row in product_summary.iterrows():
                # Simulate stock levels
                required_qty = int(row['QUANTITE_DEMANDEE'])
                produced_qty = int(row['CUMUL_ENTREES'])
                remaining_need = max(0, required_qty - produced_qty)
                
                # Simulate current stock (would come from inventory database)
                simulated_stock = max(0, remaining_need + (remaining_need * 0.2))  # 20% buffer
                
                stock_item = {
                    "product_code": row['PRODUIT'],
                    "product_name": f"Product {row['PRODUIT']}",
                    "category": row['FAMILLE_TECHNIQUE'],
                    "current_stock": int(simulated_stock),
                    "required_stock": required_qty,
                    "available_stock": int(simulated_stock),
                    "reserved_stock": produced_qty,
                    "reorder_level": max(10, int(required_qty * 0.1)),
                    "stock_status": "OK" if simulated_stock > required_qty * 0.1 else "LOW",
                    "location": "WAREHOUSE_A",
                    "last_updated": datetime.now().isoformat()
                }
                
                # Apply filters
                if product_code and product_code not in stock_item["product_code"]:
                    continue
                if category and category != stock_item["category"]:
                    continue
                if location and location != stock_item["location"]:
                    continue
                if low_stock_only and stock_item["stock_status"] != "LOW":
                    continue
                
                stock_items.append(stock_item)
        
        # Limit results
        if limit:
            stock_items = stock_items[:limit]
        
        # Calculate summary metrics
        total_items = len(stock_items)
        low_stock_items = len([item for item in stock_items if item["stock_status"] == "LOW"])
        total_value = sum([item["current_stock"] * 10 for item in stock_items])  # Simulate value
        
        return BaseResponse(
            success=True,
            data={
                "stock_items": stock_items,
                "summary": {
                    "total_items": total_items,
                    "low_stock_items": low_stock_items,
                    "total_inventory_value": total_value,
                    "stock_turnover_rate": 85.5  # Simulated
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting stock levels: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stock levels: {str(e)}")


@router.get("/material-requirements", response_model=BaseResponse)
async def get_material_requirements(
    order_id: Optional[str] = Query(None, description="Production order ID"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    analyzer=Depends(get_analyzer)
):
    """Get material requirements for production orders."""
    try:
        # Get production data
        filters = {}
        if date_from:
            filters['date_debut'] = date_from
        if date_to:
            filters['date_fin'] = date_to
            
        production_data = analyzer.get_of_data(**filters)
        
        if order_id:
            production_data = production_data[production_data['NUMERO_OFDA'] == order_id]
        
        if production_data.empty:
            return BaseResponse(success=True, data={"requirements": [], "summary": {}})
        
        # Calculate material requirements
        requirements = []
        
        for _, order in production_data.iterrows():
            # Simulate material requirements for each order
            base_materials = [
                {"material": "Steel Sheet", "unit": "kg", "rate": 2.5},
                {"material": "Aluminum Rod", "unit": "m", "rate": 1.2},
                {"material": "Plastic Component", "unit": "pcs", "rate": 3.0},
                {"material": "Electronic Module", "unit": "pcs", "rate": 1.0}
            ]
            
            for material in base_materials:
                required_qty = order['QUANTITE_DEMANDEE'] * material["rate"]
                allocated_qty = order['CUMUL_ENTREES'] * material["rate"]
                
                requirement = {
                    "order_id": order['NUMERO_OFDA'],
                    "product": order['PRODUIT'],
                    "material_code": f"MAT_{material['material'].replace(' ', '_').upper()}",
                    "material_name": material['material'],
                    "required_quantity": round(required_qty, 2),
                    "allocated_quantity": round(allocated_qty, 2),
                    "remaining_quantity": round(required_qty - allocated_qty, 2),
                    "unit": material['unit'],
                    "due_date": order['LANCEMENT_AU_PLUS_TARD'],
                    "priority": order.get('PRIORITE', 1),
                    "status": "ALLOCATED" if allocated_qty >= required_qty else "PENDING"
                }
                requirements.append(requirement)
        
        # Calculate summary
        total_requirements = len(requirements)
        pending_requirements = len([r for r in requirements if r["status"] == "PENDING"])
        
        return BaseResponse(
            success=True,
            data={
                "requirements": requirements,
                "summary": {
                    "total_requirements": total_requirements,
                    "pending_requirements": pending_requirements,
                    "allocation_rate": round((total_requirements - pending_requirements) / total_requirements * 100, 2) if total_requirements > 0 else 0
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting material requirements: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving material requirements: {str(e)}")


@router.get("/movements", response_model=BaseResponse)
async def get_inventory_movements(
    movement_type: Optional[str] = Query(None, description="Movement type (IN, OUT, TRANSFER, ADJUSTMENT)"),
    product_code: Optional[str] = Query(None, description="Product code filter"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Maximum number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get inventory movement history."""
    try:
        # Get production data to simulate movements
        production_data = analyzer.get_of_data()
        
        movements = []
        
        if not production_data.empty:
            for _, order in production_data.iterrows():
                # Simulate inventory movements based on production
                if order['CUMUL_ENTREES'] > 0:
                    # Raw material OUT movement
                    movements.append({
                        "movement_id": f"MOV_{order['NUMERO_OFDA']}_OUT",
                        "movement_type": "OUT",
                        "product_code": f"RAW_{order['PRODUIT']}",
                        "product_name": f"Raw Material for {order['PRODUIT']}",
                        "quantity": int(order['CUMUL_ENTREES'] * 2.5),  # Simulate raw material consumption
                        "unit": "kg",
                        "reference": order['NUMERO_OFDA'],
                        "location_from": "WAREHOUSE_A",
                        "location_to": "PRODUCTION",
                        "movement_date": order['LANCEMENT_AU_PLUS_TARD'],
                        "created_by": "SYSTEM",
                        "notes": f"Material consumption for production order {order['NUMERO_OFDA']}"
                    })
                    
                    # Finished product IN movement
                    movements.append({
                        "movement_id": f"MOV_{order['NUMERO_OFDA']}_IN",
                        "movement_type": "IN",
                        "product_code": order['PRODUIT'],
                        "product_name": order['DESIGNATION'],
                        "quantity": int(order['CUMUL_ENTREES']),
                        "unit": "pcs",
                        "reference": order['NUMERO_OFDA'],
                        "location_from": "PRODUCTION",
                        "location_to": "WAREHOUSE_B",
                        "movement_date": order['LANCEMENT_AU_PLUS_TARD'],
                        "created_by": "SYSTEM",
                        "notes": f"Production completion for order {order['NUMERO_OFDA']}"
                    })
        
        # Apply filters
        if movement_type:
            movements = [m for m in movements if m["movement_type"] == movement_type]
        if product_code:
            movements = [m for m in movements if product_code in m["product_code"]]
        if date_from:
            movements = [m for m in movements if m["movement_date"] >= date_from]
        if date_to:
            movements = [m for m in movements if m["movement_date"] <= date_to]
        
        # Sort by date (newest first)
        movements.sort(key=lambda x: x["movement_date"], reverse=True)
        
        # Limit results
        if limit:
            movements = movements[:limit]
        
        # Calculate summary
        in_movements = len([m for m in movements if m["movement_type"] == "IN"])
        out_movements = len([m for m in movements if m["movement_type"] == "OUT"])
        
        return BaseResponse(
            success=True,
            data={
                "movements": movements,
                "summary": {
                    "total_movements": len(movements),
                    "in_movements": in_movements,
                    "out_movements": out_movements,
                    "date_range": {"from": date_from, "to": date_to}
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting inventory movements: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving inventory movements: {str(e)}")


@router.get("/analytics", response_model=BaseResponse)
async def get_inventory_analytics(
    period: str = Query("month", description="Analysis period (week, month, quarter)"),
    category: Optional[str] = Query(None, description="Product category filter"),
    analyzer=Depends(get_analyzer)
):
    """Get inventory analytics and insights."""
    try:
        # Get production data for analytics
        production_data = analyzer.get_of_data()
        
        if production_data.empty:
            return BaseResponse(success=True, data={"analytics": {}, "insights": []})
        
        # Calculate analytics based on production data
        analytics = {
            "period": period,
            "inventory_turnover": 4.2,  # Simulated
            "stock_accuracy": 96.5,     # Simulated
            "carrying_cost": 125000,    # Simulated
            "stockout_incidents": 3,    # Simulated
            "top_moving_products": [],
            "slow_moving_products": [],
            "category_analysis": {}
        }
        
        # Analyze by product
        if not production_data.empty:
            product_analysis = production_data.groupby('PRODUIT').agg({
                'QUANTITE_DEMANDEE': 'sum',
                'CUMUL_ENTREES': 'sum',
                'FAMILLE_TECHNIQUE': 'first'
            }).reset_index()
            
            # Top moving products
            top_products = product_analysis.nlargest(5, 'CUMUL_ENTREES')
            analytics["top_moving_products"] = [
                {
                    "product_code": row['PRODUIT'],
                    "category": row['FAMILLE_TECHNIQUE'],
                    "total_movement": int(row['CUMUL_ENTREES']),
                    "demand": int(row['QUANTITE_DEMANDEE'])
                }
                for _, row in top_products.iterrows()
            ]
            
            # Category analysis
            category_analysis = production_data.groupby('FAMILLE_TECHNIQUE').agg({
                'QUANTITE_DEMANDEE': 'sum',
                'CUMUL_ENTREES': 'sum',
                'NUMERO_OFDA': 'count'
            }).to_dict('index')
            
            analytics["category_analysis"] = {
                cat: {
                    "total_demand": int(data['QUANTITE_DEMANDEE']),
                    "total_produced": int(data['CUMUL_ENTREES']),
                    "order_count": int(data['NUMERO_OFDA']),
                    "fulfillment_rate": round(data['CUMUL_ENTREES'] / data['QUANTITE_DEMANDEE'] * 100, 2) if data['QUANTITE_DEMANDEE'] > 0 else 0
                }
                for cat, data in category_analysis.items()
            }
        
        # Generate insights
        insights = [
            {
                "type": "optimization",
                "title": "Stock Optimization Opportunity",
                "message": "Consider reducing safety stock for fast-moving items to improve cash flow",
                "impact": "medium",
                "category": "cost_reduction"
            },
            {
                "type": "alert",
                "title": "Low Stock Alert",
                "message": "3 items are below reorder level and need immediate attention",
                "impact": "high",
                "category": "stock_management"
            },
            {
                "type": "trend",
                "title": "Seasonal Pattern Detected",
                "message": "Inventory turnover increases by 15% during this period historically",
                "impact": "low",
                "category": "forecasting"
            }
        ]
        
        return BaseResponse(
            success=True,
            data={
                "analytics": analytics,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting inventory analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving inventory analytics: {str(e)}")


@router.post("/adjust-stock", response_model=BaseResponse)
async def adjust_stock(
    product_code: str = Body(..., description="Product code"),
    adjustment_quantity: float = Body(..., description="Adjustment quantity (positive for increase, negative for decrease)"),
    reason: str = Body(..., description="Reason for adjustment"),
    notes: Optional[str] = Body(None, description="Additional notes"),
    analyzer=Depends(get_analyzer)
):
    """Adjust stock levels (simulation - would need database write access)."""
    try:
        # Validate product exists
        production_data = analyzer.get_of_data()
        product_exists = not production_data[production_data['PRODUIT'] == product_code].empty
        
        if not product_exists:
            raise HTTPException(status_code=404, detail=f"Product {product_code} not found")
        
        # Simulate stock adjustment
        adjustment_record = {
            "adjustment_id": f"ADJ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "product_code": product_code,
            "adjustment_quantity": adjustment_quantity,
            "reason": reason,
            "notes": notes,
            "adjusted_at": datetime.now().isoformat(),
            "adjusted_by": "system",  # Would get from authentication
            "previous_stock": 100,  # Simulated
            "new_stock": 100 + adjustment_quantity  # Simulated
        }
        
        app_logger.info(f"Stock adjustment for {product_code}: {adjustment_quantity}")
        
        return BaseResponse(
            success=True,
            message=f"Stock adjusted successfully for product {product_code}",
            data=adjustment_record
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error adjusting stock for {product_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adjusting stock: {str(e)}")
