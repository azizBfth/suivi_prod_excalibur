"""
OF Routes - MVC Pattern Implementation
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.controllers.of_controller import OFController
from app.models.schemas import BaseResponse
from app.core.database import get_analyzer

router = APIRouter(prefix="/api/of", tags=["Orders of Fabrication"])

# Initialize controller
of_controller = OFController()


@router.get("/current", response_model=BaseResponse)
async def get_current_ofs(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - applies to LANCE_LE"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - applies to LANCE_LE"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    enable_date_filter: bool = Query(False, description="Enable date range filter"),
    analyzer=Depends(get_analyzer)
):
    """Get current/active OF data from of_da table."""
    try:
        data = of_controller.get_current_ofs(
            analyzer=analyzer,
            date_debut=date_debut if enable_date_filter else None,
            date_fin=date_fin if enable_date_filter else None,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des OF actuels : {str(e)}")


@router.get("/en_cours", response_model=BaseResponse)
async def get_of_en_cours(
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - applies to LANCEMENT_AU_PLUS_TARD"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - applies to LANCEMENT_AU_PLUS_TARD"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    analyzer=Depends(get_analyzer)
):
    """Get OF currently in progress."""
    try:
        data = of_controller.get_of_en_cours(
            analyzer=analyzer,
            date_debut=dateDebut,
            date_fin=dateFin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OF en cours: {str(e)}")


@router.get("/history", response_model=BaseResponse)
async def get_history_ofs(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - applies to DATA_CLOTURE"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - applies to DATA_CLOTURE"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    enable_date_filter: bool = Query(True, description="Enable date range filter (default: True for history)"),
    analyzer=Depends(get_analyzer)
):
    """Get historical/completed OF data from histo_of_da table."""
    try:
        data = of_controller.get_history_ofs(
            analyzer=analyzer,
            date_debut=date_debut if enable_date_filter else None,
            date_fin=date_fin if enable_date_filter else None,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique des OF : {str(e)}")


@router.get("/histo", response_model=BaseResponse)
async def get_of_histo(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - applies to DATE_CLOTURE"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - applies to DATE_CLOTURE"),
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - alias for date_debut"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - alias for date_fin"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    alerts_only: bool = Query(False, description="Show only alerts"),
    retard_filter: bool = Query(False, description="Show only delayed orders"),
    analyzer=Depends(get_analyzer)
):
    """Get historical OF data from HISTO_OF_DA table filtered by DATE_CLOTURE (completion date)."""
    try:
        # Handle both parameter naming conventions
        start_date = date_debut or dateDebut
        end_date = date_fin or dateFin

        # Use the history_ofs method which properly filters by DATE_CLOTURE
        data = of_controller.get_history_ofs(
            analyzer=analyzer,
            date_debut=start_date,
            date_fin=end_date,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OF historique: {str(e)}")


@router.get("/completed", response_model=BaseResponse)
async def get_completed_orders(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    analyzer=Depends(get_analyzer)
):
    """Get all completed orders from HISTO_OF_DA table (all records are considered completed)."""
    try:
        data = of_controller.get_completed_orders(analyzer, date_debut=date_debut, date_fin=date_fin)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des OF terminés : {str(e)}")


@router.get("/all-ofs", response_model=BaseResponse)
async def get_all_ofs_combined(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - applies to LANCE_LE"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - applies to LANCE_LE"),
    dateDebut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) - alias for date_debut"),
    dateFin: Optional[str] = Query(None, description="End date (YYYY-MM-DD) - alias for date_fin"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    enable_date_filter: bool = Query(True, description="Enable date range filter (default: True)"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get combined view of all OF data from both of_da and histo_of_da tables filtered by LANCE_LE (launch date)."""
    try:
        # Handle both parameter naming conventions
        start_date = date_debut or dateDebut
        end_date = date_fin or dateFin

        # Always enable date filtering when dates are provided
        should_filter = enable_date_filter or (start_date is not None) or (end_date is not None)

        data = of_controller.get_all_ofs_combined(
            analyzer=analyzer,
            date_debut=start_date if should_filter else None,
            date_fin=end_date if should_filter else None,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            limit=limit
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de tous les OF : {str(e)}")


@router.get("/all", response_model=BaseResponse)
async def get_all_of(
    limit: Optional[int] = Query(None, description="Limit number of results"),
    analyzer=Depends(get_analyzer)
):
    """Get all OF data."""
    try:
        data = of_controller.get_all_of(analyzer, limit=limit)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all OF: {str(e)}")


@router.get("/filtered", response_model=BaseResponse)
async def get_filtered_of_data(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter (C/T/A)"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    alerte_filter: Optional[bool] = Query(None, description="Alert filter"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    include_historical: bool = Query(False, description="Include historical data from HISTO_OF_DA"),
    analyzer=Depends(get_analyzer)
):
    """Get filtered OF data with comprehensive filters, optionally including historical data."""
    try:
        data = of_controller.get_of_with_filters(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            alerte_filter=alerte_filter,
            limit=limit,
            include_historical=include_historical
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filtered OF data: {str(e)}")


@router.get("/by_status/{status}", response_model=BaseResponse)
async def get_of_by_status(status: str, analyzer=Depends(get_analyzer)):
    """Get OF data by specific status."""
    try:
        data = of_controller.get_of_by_status(analyzer, status)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OF by status {status}: {str(e)}")


@router.get("/statistics", response_model=BaseResponse)
async def get_of_statistics(analyzer=Depends(get_analyzer)):
    """Get OF statistics summary."""
    try:
        data = of_controller.get_of_statistics(analyzer)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OF statistics: {str(e)}")


# Add missing endpoints for API compatibility
@router.get("/historical", response_model=BaseResponse)
async def get_historical_ofs(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    analyzer=Depends(get_analyzer)
):
    """Get historical OF data - alias for /history endpoint."""
    try:
        data = of_controller.get_history_ofs(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving historical OF data: {str(e)}")


@router.get("/combined", response_model=BaseResponse)
async def get_combined_ofs(
    date_debut: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_fin: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    statut_filter: Optional[str] = Query(None, description="Status filter"),
    famille_filter: Optional[str] = Query(None, description="Family filter"),
    client_filter: Optional[str] = Query(None, description="Client filter"),
    analyzer=Depends(get_analyzer)
):
    """Get combined OF data - alias for /all-ofs endpoint."""
    try:
        data = of_controller.get_all_ofs_combined(
            analyzer=analyzer,
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter
        )
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving combined OF data: {str(e)}")


@router.get("/analytics", response_model=BaseResponse)
async def get_of_analytics(analyzer=Depends(get_analyzer)):
    """Get OF analytics and insights."""
    try:
        data = of_controller.get_of_statistics(analyzer)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving OF analytics: {str(e)}")


@router.get("/summary", response_model=BaseResponse)
async def get_of_summary(analyzer=Depends(get_analyzer)):
    """Get OF summary - alias for statistics."""
    try:
        data = of_controller.get_of_statistics(analyzer)
        return BaseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving OF summary: {str(e)}")


@router.get("/fields-info", response_model=BaseResponse)
async def get_of_fields_info():
    """Get comprehensive information about all available OF fields and their usage in the ERP system."""
    try:
        fields_info = {
            "core_fields": {
                "NUMERO_OFDA": {
                    "description": "Numéro unique de l'ordre de fabrication",
                    "type": "string",
                    "usage": "Identifiant principal pour le suivi",
                    "example": "F001234"
                },
                "PRODUIT": {
                    "description": "Code/référence du produit à fabriquer",
                    "type": "string",
                    "usage": "Identification du produit dans le catalogue",
                    "example": "PROD_001"
                },
                "STATUT": {
                    "description": "Statut actuel de l'ordre de fabrication",
                    "type": "string",
                    "usage": "Suivi de l'état d'avancement (C=En cours, T=Terminé, A=Arrêté)",
                    "values": ["C", "T", "A"]
                }
            },
            "date_fields": {
                "LANCEMENT_AU_PLUS_TARD": {
                    "description": "Date limite de lancement de la production",
                    "type": "date",
                    "usage": "Planification et respect des délais",
                    "format": "YYYY-MM-DD"
                },
                "LANCE_LE": {
                    "description": "Date effective de lancement de l'ordre",
                    "type": "date",
                    "usage": "Suivi du démarrage réel de la production",
                    "format": "YYYY-MM-DD"
                },
                "DISPO_DEMANDE": {
                    "description": "Date de disponibilité demandée par le client",
                    "type": "date",
                    "usage": "Gestion des engagements clients et priorités",
                    "format": "YYYY-MM-DD"
                },
                "DATA_CLOTURE": {
                    "description": "Date de clôture/finalisation de l'ordre",
                    "type": "date",
                    "usage": "Suivi de la finalisation complète de l'ordre",
                    "format": "YYYY-MM-DD"
                }
            },
            "production_fields": {
                "QUANTITE_DEMANDEE": {
                    "description": "Quantité totale à produire",
                    "type": "numeric",
                    "usage": "Calcul des avancements et planification",
                    "unit": "unités"
                },
                "CUMUL_ENTREES": {
                    "description": "Quantité déjà produite/entrée en stock",
                    "type": "numeric",
                    "usage": "Calcul de l'avancement production",
                    "unit": "unités"
                },
                "DUREE_PREVUE": {
                    "description": "Temps de production prévu",
                    "type": "numeric",
                    "usage": "Planification et calcul d'avancement temps",
                    "unit": "heures"
                },
                "CUMUL_TEMPS_PASSES": {
                    "description": "Temps déjà consommé sur l'ordre",
                    "type": "numeric",
                    "usage": "Suivi de la consommation temps réelle",
                    "unit": "heures"
                }
            },
            "organizational_fields": {
                "AFFAIRE": {
                    "description": "Numéro d'affaire/projet associé",
                    "type": "string",
                    "usage": "Regroupement par projet ou contrat",
                    "example": "AFF_001"
                },
                "CLIENT": {
                    "description": "Client final ou donneur d'ordre",
                    "type": "string",
                    "usage": "Suivi par client et reporting commercial",
                    "example": "Client ABC"
                },
                "SECTEUR": {
                    "description": "Secteur de production responsable",
                    "type": "string",
                    "usage": "Répartition de charge et planification",
                    "values": ["USINAGE", "ASSEMBLAGE", "CONTROLE", "EXPEDITION"]
                },
                "RESPONSABLE": {
                    "description": "Responsable de l'ordre de fabrication",
                    "type": "string",
                    "usage": "Suivi des responsabilités et escalade",
                    "example": "Resp_Production_A"
                },
                "PRIORITE": {
                    "description": "Niveau de priorité de l'ordre",
                    "type": "integer",
                    "usage": "Ordonnancement et gestion des urgences",
                    "range": "1-5 (1=Très faible, 5=Critique)"
                }
            },
            "classification_fields": {
                "FAMILLE_TECHNIQUE": {
                    "description": "Famille technique/catégorie du produit",
                    "type": "string",
                    "usage": "Analyse par famille et optimisation processus",
                    "example": "Mécanique, Électronique"
                },
                "DESIGNATION": {
                    "description": "Désignation complète du produit",
                    "type": "string",
                    "usage": "Description détaillée pour identification",
                    "example": "Pièce mécanique type A"
                }
            },
            "calculated_fields": {
                "Avancement_PROD": {
                    "description": "Pourcentage d'avancement production",
                    "type": "percentage",
                    "usage": "Suivi visuel de l'avancement",
                    "calculation": "CUMUL_ENTREES / QUANTITE_DEMANDEE * 100"
                },
                "Avancement_temps": {
                    "description": "Pourcentage d'avancement temps",
                    "type": "percentage",
                    "usage": "Détection des dépassements temps",
                    "calculation": "CUMUL_TEMPS_PASSES / DUREE_PREVUE * 100"
                },
                "Alerte_temps": {
                    "description": "Indicateur de dépassement temps",
                    "type": "boolean",
                    "usage": "Alerte automatique sur les retards",
                    "condition": "CUMUL_TEMPS_PASSES > DUREE_PREVUE"
                },
                "TEMPS_UNITAIRE_HISTORIQUE": {
                    "description": "Temps unitaire moyen historique pour ce produit",
                    "type": "numeric",
                    "usage": "Amélioration des estimations futures",
                    "source": "Calculé depuis HISTO_OF_DA"
                }
            },
            "system_fields": {
                "DATA_SOURCE": {
                    "description": "Source des données",
                    "type": "string",
                    "usage": "Distinction entre données actives et historiques",
                    "values": ["ACTIVE", "HISTORICAL"]
                },
                "COMPLETION_STATUS": {
                    "description": "Statut de finalisation",
                    "type": "string",
                    "usage": "Suivi du cycle de vie complet",
                    "values": ["COMPLETED", "IN_PROGRESS"]
                }
            }
        }

        return BaseResponse(
            success=True,
            data={
                "fields_info": fields_info,
                "total_fields": sum(len(category) for category in fields_info.values()),
                "usage_recommendations": {
                    "dashboard_priority": ["NUMERO_OFDA", "PRODUIT", "STATUT", "Avancement_PROD", "Alerte_temps"],
                    "planning_priority": ["LANCEMENT_AU_PLUS_TARD", "DISPO_DEMANDE", "PRIORITE", "SECTEUR"],
                    "production_tracking": ["CUMUL_ENTREES", "CUMUL_TEMPS_PASSES", "Avancement_PROD", "Avancement_temps"],
                    "client_reporting": ["CLIENT", "AFFAIRE", "DESIGNATION", "DATA_CLOTURE"],
                    "historical_analysis": ["TEMPS_UNITAIRE_HISTORIQUE", "DATA_SOURCE", "COMPLETION_STATUS"]
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fields information: {str(e)}")
