"""
Quality Management Routes - ERP Quality Control APIs
Handles quality inspections, defect tracking, and quality analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta

from app.core.database import get_analyzer
from app.models.schemas import BaseResponse
import logging

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quality", tags=["Quality Management"])


@router.get("/inspections", response_model=BaseResponse)
async def get_quality_inspections(
    order_id: Optional[str] = Query(None, description="Production order ID"),
    product_code: Optional[str] = Query(None, description="Product code"),
    status: Optional[str] = Query(None, description="Inspection status (PENDING, PASSED, FAILED, IN_PROGRESS)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    inspector: Optional[str] = Query(None, description="Inspector name"),
    limit: Optional[int] = Query(50, description="Maximum number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get quality inspection records."""
    try:
        # Get production data to base inspections on
        filters = {}
        if date_from:
            filters['date_debut'] = date_from
        if date_to:
            filters['date_fin'] = date_to
            
        production_data = analyzer.get_of_data(**filters)
        
        inspections = []
        
        if not production_data.empty:
            inspectors = ["John Quality", "Sarah Inspector", "Mike Checker", "Lisa Validator"]
            
            for _, order in production_data.iterrows():
                # Generate multiple inspection points per order
                inspection_points = ["Incoming Materials", "In-Process", "Final Inspection", "Pre-Shipment"]
                
                for point in inspection_points:
                    # Simulate inspection based on production progress
                    if order['Avancement_PROD'] > 0.2:  # Only create inspections for started orders
                        inspection_status = "PASSED"
                        if order['Avancement_PROD'] < 0.5:
                            inspection_status = "IN_PROGRESS"
                        elif hash(f"{order['NUMERO_OFDA']}{point}") % 10 == 0:  # 10% failure rate
                            inspection_status = "FAILED"
                        
                        inspection = {
                            "inspection_id": f"QI_{order['NUMERO_OFDA']}_{point.replace(' ', '_').upper()}",
                            "order_id": order['NUMERO_OFDA'],
                            "product_code": order['PRODUIT'],
                            "product_name": order['DESIGNATION'],
                            "inspection_point": point,
                            "status": inspection_status,
                            "inspector": inspectors[hash(order['NUMERO_OFDA']) % len(inspectors)],
                            "inspection_date": order['LANCEMENT_AU_PLUS_TARD'],
                            "completion_date": order['LANCEMENT_AU_PLUS_TARD'] if inspection_status == "PASSED" else None,
                            "defects_found": 0 if inspection_status == "PASSED" else (1 if inspection_status == "FAILED" else None),
                            "quality_score": 95 if inspection_status == "PASSED" else (75 if inspection_status == "FAILED" else None),
                            "notes": f"Quality inspection for {point.lower()}",
                            "corrective_actions": ["Rework required"] if inspection_status == "FAILED" else []
                        }
                        
                        # Apply filters
                        if order_id and order_id != inspection["order_id"]:
                            continue
                        if product_code and product_code not in inspection["product_code"]:
                            continue
                        if status and status != inspection["status"]:
                            continue
                        if inspector and inspector not in inspection["inspector"]:
                            continue
                        
                        inspections.append(inspection)
        
        # Sort by inspection date (newest first)
        inspections.sort(key=lambda x: x["inspection_date"], reverse=True)
        
        # Limit results
        if limit:
            inspections = inspections[:limit]
        
        # Calculate metrics
        total_inspections = len(inspections)
        passed_inspections = len([i for i in inspections if i["status"] == "PASSED"])
        failed_inspections = len([i for i in inspections if i["status"] == "FAILED"])
        pass_rate = round(passed_inspections / total_inspections * 100, 2) if total_inspections > 0 else 0
        
        return BaseResponse(
            success=True,
            data={
                "inspections": inspections,
                "metrics": {
                    "total_inspections": total_inspections,
                    "passed_inspections": passed_inspections,
                    "failed_inspections": failed_inspections,
                    "pass_rate": pass_rate,
                    "avg_quality_score": round(sum([i["quality_score"] for i in inspections if i["quality_score"]]) / len([i for i in inspections if i["quality_score"]]), 2) if inspections else 0
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting quality inspections: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving quality inspections: {str(e)}")


@router.get("/defects", response_model=BaseResponse)
async def get_defect_tracking(
    severity: Optional[str] = Query(None, description="Defect severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    category: Optional[str] = Query(None, description="Defect category"),
    status: Optional[str] = Query(None, description="Defect status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(50, description="Maximum number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get defect tracking records."""
    try:
        # Get production data to base defects on
        production_data = analyzer.get_of_data()
        
        defects = []
        defect_categories = ["Dimensional", "Surface Finish", "Material", "Assembly", "Functional"]
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        if not production_data.empty:
            for _, order in production_data.iterrows():
                # Generate defects for orders with quality issues (simulate 15% defect rate)
                if hash(order['NUMERO_OFDA']) % 7 == 0:  # ~15% of orders have defects
                    num_defects = 1 + (hash(order['NUMERO_OFDA']) % 3)  # 1-3 defects per problematic order
                    
                    for i in range(num_defects):
                        defect_severity = severities[hash(f"{order['NUMERO_OFDA']}{i}") % len(severities)]
                        defect_category = defect_categories[hash(f"{order['NUMERO_OFDA']}{i}") % len(defect_categories)]
                        
                        defect = {
                            "defect_id": f"DEF_{order['NUMERO_OFDA']}_{i+1:03d}",
                            "order_id": order['NUMERO_OFDA'],
                            "product_code": order['PRODUIT'],
                            "product_name": order['DESIGNATION'],
                            "category": defect_category,
                            "severity": defect_severity,
                            "status": "RESOLVED" if order['Avancement_PROD'] > 0.8 else "OPEN",
                            "description": f"{defect_category} issue detected in {order['PRODUIT']}",
                            "detected_date": order['LANCEMENT_AU_PLUS_TARD'],
                            "detected_by": "Quality Inspector",
                            "assigned_to": "Production Team",
                            "resolution_date": order['LANCEMENT_AU_PLUS_TARD'] if order['Avancement_PROD'] > 0.8 else None,
                            "root_cause": f"Process variation in {defect_category.lower()}",
                            "corrective_action": f"Adjust {defect_category.lower()} parameters",
                            "cost_impact": 100 * (1 + severities.index(defect_severity)),  # Cost based on severity
                            "recurrence_risk": "LOW" if defect_severity in ["LOW", "MEDIUM"] else "MEDIUM"
                        }
                        
                        # Apply filters
                        if severity and severity != defect["severity"]:
                            continue
                        if category and category != defect["category"]:
                            continue
                        if status and status != defect["status"]:
                            continue
                        if date_from and defect["detected_date"] < date_from:
                            continue
                        if date_to and defect["detected_date"] > date_to:
                            continue
                        
                        defects.append(defect)
        
        # Sort by severity and date
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        defects.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["detected_date"]), reverse=True)
        
        # Limit results
        if limit:
            defects = defects[:limit]
        
        # Calculate metrics
        total_defects = len(defects)
        open_defects = len([d for d in defects if d["status"] in ["OPEN", "IN_PROGRESS"]])
        critical_defects = len([d for d in defects if d["severity"] == "CRITICAL"])
        total_cost_impact = sum([d["cost_impact"] for d in defects])
        
        return BaseResponse(
            success=True,
            data={
                "defects": defects,
                "metrics": {
                    "total_defects": total_defects,
                    "open_defects": open_defects,
                    "critical_defects": critical_defects,
                    "resolution_rate": round((total_defects - open_defects) / total_defects * 100, 2) if total_defects > 0 else 0,
                    "total_cost_impact": total_cost_impact,
                    "avg_resolution_time": "2.5 days"  # Simulated
                }
            }
        )
    except Exception as e:
        app_logger.error(f"Error getting defect tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving defect tracking: {str(e)}")


@router.get("/metrics", response_model=BaseResponse)
async def get_quality_metrics(
    period: str = Query("month", description="Analysis period (week, month, quarter)"),
    product_family: Optional[str] = Query(None, description="Product family filter"),
    analyzer=Depends(get_analyzer)
):
    """Get quality metrics and KPIs."""
    try:
        # Calculate date range
        today = datetime.now().date()
        if period == "week":
            date_from = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == "month":
            date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        elif period == "quarter":
            date_from = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Use: week, month, quarter")
        
        date_to = today.strftime('%Y-%m-%d')
        
        # Get production data
        production_data = analyzer.get_of_data(date_debut=date_from, date_fin=date_to)
        
        if product_family:
            production_data = production_data[production_data.get('FAMILLE_TECHNIQUE', '') == product_family]
        
        # Calculate quality metrics
        total_orders = len(production_data) if not production_data.empty else 0
        
        # Simulate quality metrics based on production data
        quality_metrics = {
            "period": period,
            "date_range": {"from": date_from, "to": date_to},
            "product_family_filter": product_family,
            "first_pass_yield": 92.5,  # Simulated
            "defect_rate": 2.8,        # Simulated
            "customer_satisfaction": 4.3,  # Simulated (out of 5)
            "cost_of_quality": 45000,  # Simulated
            "inspection_efficiency": 88.7,  # Simulated
            "supplier_quality_rating": 94.2,  # Simulated
            "quality_trends": {
                "first_pass_yield_trend": "+1.2%",
                "defect_rate_trend": "-0.5%",
                "customer_satisfaction_trend": "+0.1"
            },
            "top_defect_categories": [
                {"category": "Dimensional", "count": 15, "percentage": 35.7},
                {"category": "Surface Finish", "count": 12, "percentage": 28.6},
                {"category": "Material", "count": 8, "percentage": 19.0},
                {"category": "Assembly", "count": 5, "percentage": 11.9},
                {"category": "Functional", "count": 2, "percentage": 4.8}
            ],
            "quality_by_product": []
        }
        
        # Calculate quality by product if we have production data
        if not production_data.empty:
            product_quality = production_data.groupby('PRODUIT').agg({
                'NUMERO_OFDA': 'count',
                'Avancement_PROD': 'mean'
            }).reset_index()
            
            for _, row in product_quality.iterrows():
                # Simulate quality score based on production progress
                quality_score = 85 + (row['Avancement_PROD'] * 10)  # Higher progress = better quality
                
                quality_metrics["quality_by_product"].append({
                    "product_code": row['PRODUIT'],
                    "order_count": int(row['NUMERO_OFDA']),
                    "quality_score": round(quality_score, 1),
                    "defect_rate": round(max(0, 5 - quality_score/20), 2),
                    "first_pass_yield": round(min(100, quality_score + 5), 1)
                })
        
        return BaseResponse(
            success=True,
            data=quality_metrics
        )
    except Exception as e:
        app_logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving quality metrics: {str(e)}")


@router.post("/inspections", response_model=BaseResponse)
async def create_quality_inspection(
    order_id: str = Body(..., description="Production order ID"),
    inspection_point: str = Body(..., description="Inspection point"),
    inspector: str = Body(..., description="Inspector name"),
    notes: Optional[str] = Body(None, description="Inspection notes"),
    analyzer=Depends(get_analyzer)
):
    """Create a new quality inspection record."""
    try:
        # Validate order exists
        production_data = analyzer.get_of_data()
        order_exists = not production_data[production_data['NUMERO_OFDA'] == order_id].empty
        
        if not order_exists:
            raise HTTPException(status_code=404, detail=f"Production order {order_id} not found")
        
        # Create inspection record
        inspection_id = f"QI_{order_id}_{inspection_point.replace(' ', '_').upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        inspection_record = {
            "inspection_id": inspection_id,
            "order_id": order_id,
            "inspection_point": inspection_point,
            "status": "PENDING",
            "inspector": inspector,
            "created_date": datetime.now().isoformat(),
            "notes": notes,
            "quality_score": None,
            "defects_found": None
        }
        
        app_logger.info(f"Quality inspection created: {inspection_id}")
        
        return BaseResponse(
            success=True,
            message=f"Quality inspection {inspection_id} created successfully",
            data=inspection_record
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error creating quality inspection: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating quality inspection: {str(e)}")


@router.put("/inspections/{inspection_id}", response_model=BaseResponse)
async def update_quality_inspection(
    inspection_id: str,
    status: str = Body(..., description="Inspection status"),
    quality_score: Optional[float] = Body(None, description="Quality score (0-100)"),
    defects_found: Optional[int] = Body(None, description="Number of defects found"),
    notes: Optional[str] = Body(None, description="Updated notes"),
    analyzer=Depends(get_analyzer)
):
    """Update quality inspection results."""
    try:
        # Validate status
        valid_statuses = ["PENDING", "IN_PROGRESS", "PASSED", "FAILED", "CANCELLED"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate quality score
        if quality_score is not None and (quality_score < 0 or quality_score > 100):
            raise HTTPException(status_code=400, detail="Quality score must be between 0 and 100")
        
        # Update inspection record (simulation)
        updated_inspection = {
            "inspection_id": inspection_id,
            "status": status,
            "quality_score": quality_score,
            "defects_found": defects_found,
            "notes": notes,
            "updated_date": datetime.now().isoformat(),
            "updated_by": "system"  # Would get from authentication
        }
        
        app_logger.info(f"Quality inspection updated: {inspection_id} -> {status}")
        
        return BaseResponse(
            success=True,
            message=f"Quality inspection {inspection_id} updated successfully",
            data=updated_inspection
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error updating quality inspection {inspection_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating quality inspection: {str(e)}")


@router.get("/compliance", response_model=BaseResponse)
async def get_compliance_status(
    standard: Optional[str] = Query(None, description="Quality standard (ISO9001, ISO14001, etc.)"),
    analyzer=Depends(get_analyzer)
):
    """Get quality compliance status and audit information."""
    try:
        # Simulate compliance data
        compliance_data = {
            "overall_compliance_score": 94.2,
            "last_audit_date": "2024-05-15",
            "next_audit_date": "2024-11-15",
            "compliance_standards": [
                {
                    "standard": "ISO 9001:2015",
                    "compliance_score": 96.5,
                    "status": "COMPLIANT",
                    "last_assessment": "2024-05-15",
                    "findings": 2,
                    "corrective_actions": 1
                },
                {
                    "standard": "ISO 14001:2015",
                    "compliance_score": 91.8,
                    "status": "COMPLIANT",
                    "last_assessment": "2024-04-20",
                    "findings": 3,
                    "corrective_actions": 2
                },
                {
                    "standard": "OHSAS 18001",
                    "compliance_score": 94.3,
                    "status": "COMPLIANT",
                    "last_assessment": "2024-03-10",
                    "findings": 1,
                    "corrective_actions": 0
                }
            ],
            "audit_findings": [
                {
                    "finding_id": "AUD_2024_001",
                    "standard": "ISO 9001:2015",
                    "severity": "MINOR",
                    "description": "Documentation update required for quality procedures",
                    "status": "CLOSED",
                    "due_date": "2024-06-30"
                },
                {
                    "finding_id": "AUD_2024_002",
                    "standard": "ISO 14001:2015",
                    "severity": "MAJOR",
                    "description": "Environmental monitoring frequency needs improvement",
                    "status": "OPEN",
                    "due_date": "2024-07-15"
                }
            ],
            "certification_status": {
                "iso_9001": {"status": "ACTIVE", "expiry": "2025-12-31"},
                "iso_14001": {"status": "ACTIVE", "expiry": "2025-08-15"},
                "ohsas_18001": {"status": "ACTIVE", "expiry": "2025-10-20"}
            }
        }
        
        # Filter by standard if specified
        if standard:
            filtered_standards = [s for s in compliance_data["compliance_standards"] if s["standard"].startswith(standard)]
            if not filtered_standards:
                raise HTTPException(status_code=404, detail=f"Standard {standard} not found")
            
            compliance_data["compliance_standards"] = filtered_standards
            compliance_data["audit_findings"] = [f for f in compliance_data["audit_findings"] if f["standard"].startswith(standard)]
        
        return BaseResponse(
            success=True,
            data=compliance_data
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving compliance status: {str(e)}")
