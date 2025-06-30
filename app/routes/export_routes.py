"""
Export routes for data export functionality (CSV, Excel, TXT).
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import pandas as pd
import io
import csv
import logging

from app.models.schemas import BaseResponse, User
from app.middleware.auth_middleware import get_current_user, get_res_or_admin_user
from app.core.database import get_analyzer

# Setup logger
app_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["Export"])


def create_csv_response(data: pd.DataFrame, filename: str) -> StreamingResponse:
    """Create a CSV response from DataFrame."""
    output = io.StringIO()
    data.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response


def create_excel_response(data: pd.DataFrame, filename: str) -> StreamingResponse:
    """Create an Excel response from DataFrame."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Data')
    output.seek(0)
    
    response = StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response


@router.get("/csv")
async def export_csv(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    table: str = Query("of", description="Table to export (of, histo, all)"),
    current_user: User = Depends(get_res_or_admin_user),  # Require res or admin privileges
    analyzer=Depends(get_analyzer)
):
    """Export data to CSV format."""
    try:
        # Get data based on table parameter
        if table == "of":
            data = analyzer.get_of_data()
        elif table == "histo":
            data = analyzer.get_histo_of_data()
        elif table == "all":
            of_data = analyzer.get_of_data()
            histo_data = analyzer.get_histo_of_data()
            data = pd.concat([of_data, histo_data], ignore_index=True)
        else:
            raise HTTPException(status_code=400, detail="Invalid table parameter")
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Apply filters
        if date_debut:
            try:
                date_debut_dt = pd.to_datetime(date_debut)
                if 'DATE_CREATION' in data.columns:
                    data = data[pd.to_datetime(data['DATE_CREATION']) >= date_debut_dt]
            except:
                pass
        
        if date_fin:
            try:
                date_fin_dt = pd.to_datetime(date_fin)
                if 'DATE_CREATION' in data.columns:
                    data = data[pd.to_datetime(data['DATE_CREATION']) <= date_fin_dt]
            except:
                pass
        
        if statut_filter and 'STATUT' in data.columns:
            data = data[data['STATUT'] == statut_filter]
        
        if famille_filter and 'FAMILLE_TECHNIQUE' in data.columns:
            data = data[data['FAMILLE_TECHNIQUE'] == famille_filter]
        
        if client_filter and 'CLIENT' in data.columns:
            data = data[data['CLIENT'] == client_filter]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{table}_{timestamp}.csv"
        
        app_logger.info(f"CSV export requested by user {current_user.username}: {filename}")
        
        return create_csv_response(data, filename)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")


@router.get("/excel")
async def export_excel(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    table: str = Query("of", description="Table to export (of, histo, all)"),
    current_user: User = Depends(get_res_or_admin_user),  # Require res or admin privileges
    analyzer=Depends(get_analyzer)
):
    """Export data to Excel format."""
    try:
        # Get data based on table parameter
        if table == "of":
            data = analyzer.get_of_data()
        elif table == "histo":
            data = analyzer.get_histo_of_data()
        elif table == "all":
            of_data = analyzer.get_of_data()
            histo_data = analyzer.get_histo_of_data()
            data = pd.concat([of_data, histo_data], ignore_index=True)
        else:
            raise HTTPException(status_code=400, detail="Invalid table parameter")
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Apply filters (same as CSV)
        if date_debut:
            try:
                date_debut_dt = pd.to_datetime(date_debut)
                if 'DATE_CREATION' in data.columns:
                    data = data[pd.to_datetime(data['DATE_CREATION']) >= date_debut_dt]
            except:
                pass
        
        if date_fin:
            try:
                date_fin_dt = pd.to_datetime(date_fin)
                if 'DATE_CREATION' in data.columns:
                    data = data[pd.to_datetime(data['DATE_CREATION']) <= date_fin_dt]
            except:
                pass
        
        if statut_filter and 'STATUT' in data.columns:
            data = data[data['STATUT'] == statut_filter]
        
        if famille_filter and 'FAMILLE_TECHNIQUE' in data.columns:
            data = data[data['FAMILLE_TECHNIQUE'] == famille_filter]
        
        if client_filter and 'CLIENT' in data.columns:
            data = data[data['CLIENT'] == client_filter]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{table}_{timestamp}.xlsx"
        
        app_logger.info(f"Excel export requested by user {current_user.username}: {filename}")
        
        return create_excel_response(data, filename)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")


@router.get("/txt-resume")
async def export_txt_resume(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    analyzer=Depends(get_analyzer)
):
    """Export a text summary of production data."""
    try:
        # Get data
        of_data = analyzer.get_of_data()
        histo_data = analyzer.get_histo_of_data()
        
        if (of_data is None or of_data.empty) and (histo_data is None or histo_data.empty):
            raise HTTPException(status_code=404, detail="No data found")
        
        # Generate summary text
        summary_lines = []
        summary_lines.append("=== RÉSUMÉ DE PRODUCTION ===")
        summary_lines.append(f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        summary_lines.append(f"Utilisateur: {current_user.username}")
        summary_lines.append("")
        
        # OF data summary
        if of_data is not None and not of_data.empty:
            summary_lines.append("--- ORDRES DE FABRICATION EN COURS ---")
            summary_lines.append(f"Nombre total d'OF: {len(of_data)}")
            
            if 'STATUT' in of_data.columns:
                status_counts = of_data['STATUT'].value_counts()
                for status, count in status_counts.items():
                    summary_lines.append(f"  - {status}: {count}")
            
            summary_lines.append("")
        
        # Historical data summary
        if histo_data is not None and not histo_data.empty:
            summary_lines.append("--- HISTORIQUE DE PRODUCTION ---")
            summary_lines.append(f"Nombre total d'enregistrements: {len(histo_data)}")
            summary_lines.append("")
        
        # Additional statistics
        summary_lines.append("--- STATISTIQUES GÉNÉRALES ---")
        total_records = 0
        if of_data is not None:
            total_records += len(of_data)
        if histo_data is not None:
            total_records += len(histo_data)
        
        summary_lines.append(f"Total des enregistrements: {total_records}")
        summary_lines.append("")
        summary_lines.append("=== FIN DU RÉSUMÉ ===")
        
        # Create response
        summary_text = "\n".join(summary_lines)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_production_{timestamp}.txt"
        
        app_logger.info(f"TXT resume export requested by user {current_user.username}: {filename}")
        
        response = Response(
            content=summary_text.encode('utf-8'),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting TXT resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting TXT resume: {str(e)}")


@router.get("/summary", response_model=BaseResponse)
async def get_export_summary(
    current_user: User = Depends(get_res_or_admin_user),  # Require res or admin privileges
    analyzer=Depends(get_analyzer)
):
    """Get summary information about available data for export."""
    try:
        summary = {}
        
        # OF data summary
        of_data = analyzer.get_of_data()
        if of_data is not None and not of_data.empty:
            summary["of_data"] = {
                "total_records": len(of_data),
                "columns": list(of_data.columns),
                "date_range": {
                    "start": of_data['DATE_CREATION'].min() if 'DATE_CREATION' in of_data.columns else None,
                    "end": of_data['DATE_CREATION'].max() if 'DATE_CREATION' in of_data.columns else None
                } if 'DATE_CREATION' in of_data.columns else None
            }
        
        # Historical data summary
        histo_data = analyzer.get_histo_of_data()
        if histo_data is not None and not histo_data.empty:
            summary["histo_data"] = {
                "total_records": len(histo_data),
                "columns": list(histo_data.columns),
                "date_range": {
                    "start": histo_data['DATE_CREATION'].min() if 'DATE_CREATION' in histo_data.columns else None,
                    "end": histo_data['DATE_CREATION'].max() if 'DATE_CREATION' in histo_data.columns else None
                } if 'DATE_CREATION' in histo_data.columns else None
            }
        
        # Export formats available
        summary["available_formats"] = ["csv", "excel", "txt"]
        summary["last_updated"] = datetime.now().isoformat()
        
        return BaseResponse(
            success=True,
            message="Export summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        app_logger.error(f"Error getting export summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting export summary: {str(e)}")


@router.post("/validate", response_model=BaseResponse)
async def validate_export_request(
    table: str,
    format: str,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    analyzer=Depends(get_analyzer)
):
    """Validate an export request before processing."""
    try:
        # Validate table parameter
        valid_tables = ["of", "histo", "all"]
        if table not in valid_tables:
            return BaseResponse(
                success=False,
                message=f"Invalid table parameter. Must be one of: {', '.join(valid_tables)}",
                data={"valid_tables": valid_tables}
            )

        # Validate format parameter
        valid_formats = ["csv", "excel", "txt"]
        if format not in valid_formats:
            return BaseResponse(
                success=False,
                message=f"Invalid format parameter. Must be one of: {', '.join(valid_formats)}",
                data={"valid_formats": valid_formats}
            )

        # Validate date range
        if date_debut and date_fin:
            try:
                debut_dt = pd.to_datetime(date_debut)
                fin_dt = pd.to_datetime(date_fin)
                if debut_dt > fin_dt:
                    return BaseResponse(
                        success=False,
                        message="Start date must be before end date",
                        data={"date_debut": date_debut, "date_fin": date_fin}
                    )
            except:
                return BaseResponse(
                    success=False,
                    message="Invalid date format. Use YYYY-MM-DD",
                    data={"date_debut": date_debut, "date_fin": date_fin}
                )

        # Check data availability
        data_available = False
        estimated_records = 0

        if table == "of":
            of_data = analyzer.get_of_data()
            if of_data is not None and not of_data.empty:
                data_available = True
                estimated_records = len(of_data)
        elif table == "histo":
            histo_data = analyzer.get_histo_of_data()
            if histo_data is not None and not histo_data.empty:
                data_available = True
                estimated_records = len(histo_data)
        elif table == "all":
            of_data = analyzer.get_of_data()
            histo_data = analyzer.get_histo_of_data()
            if (of_data is not None and not of_data.empty) or (histo_data is not None and not histo_data.empty):
                data_available = True
                estimated_records = (len(of_data) if of_data is not None else 0) + (len(histo_data) if histo_data is not None else 0)

        if not data_available:
            return BaseResponse(
                success=False,
                message="No data available for export",
                data={"table": table, "estimated_records": 0}
            )

        return BaseResponse(
            success=True,
            message="Export request is valid",
            data={
                "table": table,
                "format": format,
                "estimated_records": estimated_records,
                "data_available": data_available
            }
        )

    except Exception as e:
        app_logger.error(f"Error validating export request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating export request: {str(e)}")


@router.get("/dashboard")
async def export_dashboard_data(
    format: str = Query("csv", description="Export format (csv, excel)"),
    current_user: User = Depends(get_res_or_admin_user),  # Require res or admin privileges
    analyzer=Depends(get_analyzer)
):
    """Export dashboard data in specified format."""
    try:
        # Get dashboard data
        dashboard_data = {}

        # Get OF data
        of_data = analyzer.get_of_data()
        if of_data is not None and not of_data.empty:
            dashboard_data["of_data"] = of_data

        # Get historical data
        histo_data = analyzer.get_histo_of_data()
        if histo_data is not None and not histo_data.empty:
            dashboard_data["histo_data"] = histo_data

        if not dashboard_data:
            raise HTTPException(status_code=404, detail="No dashboard data available")

        # Combine all data for export
        all_data = []
        for table_name, data in dashboard_data.items():
            data_copy = data.copy()
            data_copy['source_table'] = table_name
            all_data.append(data_copy)

        combined_data = pd.concat(all_data, ignore_index=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format.lower() == "excel":
            filename = f"dashboard_export_{timestamp}.xlsx"
            return create_excel_response(combined_data, filename)
        else:  # Default to CSV
            filename = f"dashboard_export_{timestamp}.csv"
            return create_csv_response(combined_data, filename)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting dashboard data: {str(e)}")


@router.get("/comprehensive-csv")
async def export_comprehensive_csv(
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - frontend format"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - frontend format"),
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - backend format"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - backend format"),
    current_user: User = Depends(get_res_or_admin_user),
    analyzer=Depends(get_analyzer)
):
    """Export comprehensive CSV with all 3 dashboard tabs, proper labels, separators, and summary tables."""
    try:
        # Handle both parameter naming conventions
        start_date = date_debut or dateDebut
        end_date = date_fin or dateFin

        app_logger.info(f"Comprehensive CSV export requested by user {current_user.username} with date range: {start_date} to {end_date}")

        # Get data for all three tabs with date filtering
        of_en_cours_data = analyzer.get_of_data_with_lance_le_filter(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else analyzer.get_of_data()

        of_histo_data = analyzer.get_histo_of_data(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else analyzer.get_histo_of_data()

        of_combined_data = analyzer.get_combined_of_data(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else None

        # If combined data is not available, create it from individual datasets
        if of_combined_data is None or of_combined_data.empty:
            data_frames = []
            if of_en_cours_data is not None and not of_en_cours_data.empty:
                data_frames.append(of_en_cours_data)
            if of_histo_data is not None and not of_histo_data.empty:
                data_frames.append(of_histo_data)
            of_combined_data = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

        # Create comprehensive CSV content
        output = io.StringIO()

        # Write header with export information
        output.write("=== EXPORT COMPLET DU TABLEAU DE BORD DE PRODUCTION ===\n")
        output.write(f"Date d'export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"Utilisateur: {current_user.username}\n")
        if start_date or end_date:
            output.write(f"Période filtrée: {start_date or 'Début'} à {end_date or 'Fin'}\n")
        else:
            output.write("Période: Toutes les données\n")
        output.write("\n")

        # Tab 1: OF En Cours
        output.write("=== ONGLET 1: OF EN COURS (OF_DA) ===\n")
        if of_en_cours_data is not None and not of_en_cours_data.empty:
            output.write(f"Nombre d'enregistrements: {len(of_en_cours_data)}\n")
            output.write("Colonnes: N° OF, Produit, Désignation, Client, Famille, Statut, Avanc. Prod, Avanc. Temps, Efficacité\n")
            output.write("\n")

            # Select and rename columns for export
            export_cols = ['NUMERO_OFDA', 'PRODUIT', 'DESIGNATION', 'CLIENT', 'FAMILLE_TECHNIQUE',
                          'STATUT', 'Avancement_PROD', 'Avancement_temps', 'EFFICACITE']
            available_cols = [col for col in export_cols if col in of_en_cours_data.columns]

            if available_cols:
                of_en_cours_export = of_en_cours_data[available_cols].copy()
                of_en_cours_export.to_csv(output, index=False, lineterminator='\n')
            else:
                output.write("Aucune donnée disponible pour cet onglet\n")
        else:
            output.write("Aucune donnée disponible pour cet onglet\n")

        output.write("\n" + "="*80 + "\n\n")

        # Tab 2: OF Historique
        output.write("=== ONGLET 2: OF HISTORIQUE (HISTO_OF_DA) ===\n")
        if of_histo_data is not None and not of_histo_data.empty:
            output.write(f"Nombre d'enregistrements: {len(of_histo_data)}\n")
            output.write("Colonnes: N° OF, Produit, Client, Date Fin, Durée, Efficacité\n")
            output.write("\n")

            # Select and rename columns for export
            export_cols = ['NUMERO_OFDA', 'PRODUIT', 'CLIENT', 'DATE_FIN', 'DUREE_TOTALE', 'EFFICACITE']
            available_cols = [col for col in export_cols if col in of_histo_data.columns]

            if available_cols:
                of_histo_export = of_histo_data[available_cols].copy()
                of_histo_export.to_csv(output, index=False, lineterminator='\n')
            else:
                output.write("Aucune donnée disponible pour cet onglet\n")
        else:
            output.write("Aucune donnée disponible pour cet onglet\n")

        output.write("\n" + "="*80 + "\n\n")

        # Tab 3: Vue Combinée
        output.write("=== ONGLET 3: VUE COMBINÉE (TOUS LES OF) ===\n")
        if of_combined_data is not None and not of_combined_data.empty:
            output.write(f"Nombre d'enregistrements: {len(of_combined_data)}\n")
            output.write("Colonnes: N° OF, Produit, Client, Statut, Avanc. Prod, Avanc. Temps, Efficacité\n")
            output.write("\n")

            # Select and rename columns for export
            export_cols = ['NUMERO_OFDA', 'PRODUIT', 'CLIENT', 'STATUT',
                          'Avancement_PROD', 'Avancement_temps', 'EFFICACITE']
            available_cols = [col for col in export_cols if col in of_combined_data.columns]

            if available_cols:
                of_combined_export = of_combined_data[available_cols].copy()
                of_combined_export.to_csv(output, index=False, lineterminator='\n')
            else:
                output.write("Aucune donnée disponible pour cet onglet\n")
        else:
            output.write("Aucune donnée disponible pour cet onglet\n")

        output.write("\n" + "="*80 + "\n\n")

        # Summary Table
        output.write("=== TABLEAU RÉCAPITULATIF ===\n")
        output.write("Onglet,Nombre d'enregistrements,Description\n")

        en_cours_count = len(of_en_cours_data) if of_en_cours_data is not None and not of_en_cours_data.empty else 0
        histo_count = len(of_histo_data) if of_histo_data is not None and not of_histo_data.empty else 0
        combined_count = len(of_combined_data) if of_combined_data is not None and not of_combined_data.empty else 0

        output.write(f"OF En Cours,{en_cours_count},Ordres de fabrication en cours de production\n")
        output.write(f"OF Historique,{histo_count},Ordres de fabrication terminés\n")
        output.write(f"Vue Combinée,{combined_count},Tous les ordres de fabrication (en cours + terminés)\n")
        output.write(f"TOTAL UNIQUE,{combined_count},Nombre total d'OF uniques dans la vue combinée\n")

        output.write("\n=== FIN DE L'EXPORT ===\n")

        # Create response
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_complet_dashboard_{timestamp}.csv"

        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

        app_logger.info(f"Comprehensive CSV export completed: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting comprehensive CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting comprehensive CSV: {str(e)}")


@router.get("/comprehensive-txt")
async def export_comprehensive_txt(
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - frontend format"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - frontend format"),
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - backend format"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - backend format"),
    current_user: User = Depends(get_res_or_admin_user),
    analyzer=Depends(get_analyzer)
):
    """Export comprehensive TXT detailed report with all dashboard data, KPIs, and analysis."""
    try:
        # Handle both parameter naming conventions
        start_date = date_debut or dateDebut
        end_date = date_fin or dateFin

        app_logger.info(f"Comprehensive TXT export requested by user {current_user.username} with date range: {start_date} to {end_date}")

        # Get data for all three tabs with date filtering
        of_en_cours_data = analyzer.get_of_data_with_lance_le_filter(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else analyzer.get_of_data()

        of_histo_data = analyzer.get_histo_of_data(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else analyzer.get_histo_of_data()

        of_combined_data = analyzer.get_combined_of_data(
            date_debut=start_date,
            date_fin=end_date
        ) if start_date or end_date else None

        # If combined data is not available, create it from individual datasets
        if of_combined_data is None or of_combined_data.empty:
            data_frames = []
            if of_en_cours_data is not None and not of_en_cours_data.empty:
                data_frames.append(of_en_cours_data)
            if of_histo_data is not None and not of_histo_data.empty:
                data_frames.append(of_histo_data)
            of_combined_data = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

        # Build comprehensive report
        report_lines = []

        # Header
        report_lines.extend([
            "=" * 100,
            "RAPPORT DÉTAILLÉ DU TABLEAU DE BORD DE PRODUCTION",
            "=" * 100,
            f"Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Généré par: {current_user.username}",
            f"Période analysée: {start_date or 'Début'} à {end_date or 'Fin'}" if start_date or end_date else "Période: Toutes les données",
            "",
        ])

        # Executive Summary
        en_cours_count = len(of_en_cours_data) if of_en_cours_data is not None and not of_en_cours_data.empty else 0
        histo_count = len(of_histo_data) if of_histo_data is not None and not of_histo_data.empty else 0
        combined_count = len(of_combined_data) if of_combined_data is not None and not of_combined_data.empty else 0

        report_lines.extend([
            "RÉSUMÉ EXÉCUTIF",
            "-" * 50,
            f"• Total OF en cours: {en_cours_count:,}",
            f"• Total OF terminés: {histo_count:,}",
            f"• Total OF (vue combinée): {combined_count:,}",
            "",
        ])

        # Calculate KPIs if data is available
        if of_combined_data is not None and not of_combined_data.empty:
            try:
                # Calculate efficiency statistics
                if 'EFFICACITE' in of_combined_data.columns:
                    efficacite_data = pd.to_numeric(of_combined_data['EFFICACITE'], errors='coerce').dropna()
                    if not efficacite_data.empty:
                        avg_efficacite = efficacite_data.mean()
                        min_efficacite = efficacite_data.min()
                        max_efficacite = efficacite_data.max()

                        report_lines.extend([
                            "INDICATEURS DE PERFORMANCE",
                            "-" * 50,
                            f"• Efficacité moyenne: {avg_efficacite:.1f}%",
                            f"• Efficacité minimale: {min_efficacite:.1f}%",
                            f"• Efficacité maximale: {max_efficacite:.1f}%",
                            "",
                        ])

                # Status distribution
                if 'STATUT' in of_combined_data.columns:
                    status_counts = of_combined_data['STATUT'].value_counts()
                    report_lines.extend([
                        "RÉPARTITION PAR STATUT",
                        "-" * 50,
                    ])
                    for status, count in status_counts.items():
                        percentage = (count / len(of_combined_data)) * 100
                        report_lines.append(f"• {status}: {count:,} ({percentage:.1f}%)")
                    report_lines.append("")

                # Family distribution
                if 'FAMILLE_TECHNIQUE' in of_combined_data.columns:
                    family_counts = of_combined_data['FAMILLE_TECHNIQUE'].value_counts().head(10)
                    report_lines.extend([
                        "TOP 10 FAMILLES TECHNIQUES",
                        "-" * 50,
                    ])
                    for family, count in family_counts.items():
                        percentage = (count / len(of_combined_data)) * 100
                        report_lines.append(f"• {family}: {count:,} ({percentage:.1f}%)")
                    report_lines.append("")

                # Client distribution
                if 'CLIENT' in of_combined_data.columns:
                    client_counts = of_combined_data['CLIENT'].value_counts().head(10)
                    report_lines.extend([
                        "TOP 10 CLIENTS",
                        "-" * 50,
                    ])
                    for client, count in client_counts.items():
                        percentage = (count / len(of_combined_data)) * 100
                        report_lines.append(f"• {client}: {count:,} ({percentage:.1f}%)")
                    report_lines.append("")

            except Exception as e:
                report_lines.extend([
                    "INDICATEURS DE PERFORMANCE",
                    "-" * 50,
                    f"Erreur lors du calcul des KPIs: {str(e)}",
                    "",
                ])

        # Detailed sections for each tab
        report_lines.extend([
            "=" * 100,
            "DÉTAIL PAR ONGLET",
            "=" * 100,
            "",
        ])

        # OF En Cours details
        report_lines.extend([
            "1. OF EN COURS (OF_DA)",
            "-" * 50,
            f"Nombre d'enregistrements: {en_cours_count:,}",
            "Description: Ordres de fabrication actuellement en cours de production",
        ])

        if of_en_cours_data is not None and not of_en_cours_data.empty:
            # Show sample records
            sample_size = min(5, len(of_en_cours_data))
            report_lines.extend([
                f"Échantillon ({sample_size} premiers enregistrements):",
                "",
            ])

            for i in range(sample_size):
                row = of_en_cours_data.iloc[i]
                numero = row.get('NUMERO_OFDA', 'N/A')
                produit = row.get('PRODUIT', 'N/A')
                client = row.get('CLIENT', 'N/A')
                statut = row.get('STATUT', 'N/A')
                efficacite = row.get('EFFICACITE', 'N/A')

                report_lines.append(f"  • OF {numero}: {produit} - Client: {client} - Statut: {statut} - Efficacité: {efficacite}%")

        report_lines.extend(["", ""])

        # OF Historique details
        report_lines.extend([
            "2. OF HISTORIQUE (HISTO_OF_DA)",
            "-" * 50,
            f"Nombre d'enregistrements: {histo_count:,}",
            "Description: Ordres de fabrication terminés et archivés",
        ])

        if of_histo_data is not None and not of_histo_data.empty:
            # Show sample records
            sample_size = min(5, len(of_histo_data))
            report_lines.extend([
                f"Échantillon ({sample_size} premiers enregistrements):",
                "",
            ])

            for i in range(sample_size):
                row = of_histo_data.iloc[i]
                numero = row.get('NUMERO_OFDA', 'N/A')
                produit = row.get('PRODUIT', 'N/A')
                client = row.get('CLIENT', 'N/A')
                date_fin = row.get('DATE_FIN', 'N/A')
                efficacite = row.get('EFFICACITE', 'N/A')

                report_lines.append(f"  • OF {numero}: {produit} - Client: {client} - Terminé: {date_fin} - Efficacité: {efficacite}%")

        report_lines.extend(["", ""])

        # Vue Combinée details
        report_lines.extend([
            "3. VUE COMBINÉE (TOUS LES OF)",
            "-" * 50,
            f"Nombre d'enregistrements: {combined_count:,}",
            "Description: Vue consolidée de tous les ordres de fabrication",
            "",
        ])

        # Footer
        report_lines.extend([
            "=" * 100,
            "FIN DU RAPPORT",
            "=" * 100,
            f"Rapport généré le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}",
            "Système de Suivi de Production - Excalibur ERP",
        ])

        # Create response
        report_text = "\n".join(report_lines)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rapport_detaille_production_{timestamp}.txt"

        response = Response(
            content=report_text.encode('utf-8'),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

        app_logger.info(f"Comprehensive TXT export completed: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting comprehensive TXT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting comprehensive TXT: {str(e)}")


@router.get("/tab/{tab_name}")
async def export_tab_data(
    tab_name: str,
    format: str = Query("csv", description="Export format (csv, excel)"),
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - frontend format"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - frontend format"),
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - backend format"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - backend format"),
    current_user: User = Depends(get_res_or_admin_user),  # Require res or admin privileges
    analyzer=Depends(get_analyzer)
):
    """Export data for a specific tab with date filtering support."""
    try:
        # Handle both parameter naming conventions
        start_date = date_debut or dateDebut
        end_date = date_fin or dateFin

        # Map tab names to data sources
        tab_mapping = {
            "en_cours": "of",
            "histo": "histo",
            "all": "all",
            "of-en-cours": "of",
            "of-historique": "histo",
            "of-combined": "all",
            "overview": "all",
            "status_analysis": "of",
            "performance": "all"
        }

        if tab_name not in tab_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid tab name: {tab_name}")

        table_type = tab_mapping[tab_name]

        # Get data based on tab with date filtering
        if table_type == "of":
            data = analyzer.get_of_data_with_lance_le_filter(
                date_debut=start_date,
                date_fin=end_date
            ) if start_date or end_date else analyzer.get_of_data()
        elif table_type == "histo":
            data = analyzer.get_histo_of_data(
                date_debut=start_date,
                date_fin=end_date
            ) if start_date or end_date else analyzer.get_histo_of_data()
        elif table_type == "all":
            data = analyzer.get_combined_of_data(
                date_debut=start_date,
                date_fin=end_date
            ) if start_date or end_date else None

            # If combined data is not available, create it from individual datasets
            if data is None or data.empty:
                of_data = analyzer.get_of_data_with_lance_le_filter(
                    date_debut=start_date,
                    date_fin=end_date
                ) if start_date or end_date else analyzer.get_of_data()

                histo_data = analyzer.get_histo_of_data(
                    date_debut=start_date,
                    date_fin=end_date
                ) if start_date or end_date else analyzer.get_histo_of_data()

                data_frames = []
                if of_data is not None and not of_data.empty:
                    data_frames.append(of_data)
                if histo_data is not None and not histo_data.empty:
                    data_frames.append(histo_data)
                data = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for tab: {tab_name}")

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else ""

        if format.lower() == "excel":
            filename = f"{tab_name}_export{date_suffix}_{timestamp}.xlsx"
            return create_excel_response(data, filename)
        else:  # Default to CSV
            filename = f"{tab_name}_export{date_suffix}_{timestamp}.csv"
            return create_csv_response(data, filename)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error exporting tab data for {tab_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting tab data: {str(e)}")
