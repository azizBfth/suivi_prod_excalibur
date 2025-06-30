"""
Pydantic schemas for request/response models
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field


# Base response model
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


# OF (Order of Fabrication) models
class OFItem(BaseModel):
    NUMERO_OFDA: Optional[str] = None
    PRODUIT: Optional[str] = None
    STATUT: Optional[str] = None
    LANCEMENT_AU_PLUS_TARD: Optional[str] = None
    QUANTITE_DEMANDEE: Optional[int] = None
    CUMUL_ENTREES: Optional[int] = None
    DUREE_PREVUE: Optional[int] = None
    CUMUL_TEMPS_PASSES: Optional[int] = None
    AFFAIRE: Optional[str] = None
    DESIGNATION: Optional[str] = None
    LANCE_LE: Optional[str] = None
    DISPO_DEMANDE: Optional[str] = None  # Date de disponibilité demandée
    DATA_CLOTURE: Optional[str] = None  # Date de clôture
    FAMILLE_TECHNIQUE: Optional[str] = None
    CLIENT: Optional[str] = None
    SECTEUR: Optional[str] = None  # Secteur de production
    PRIORITE: Optional[int] = None  # Priorité de l'ordre
    RESPONSABLE: Optional[str] = None  # Responsable de l'ordre
    Avancement_PROD: Optional[float] = None
    Avancement_temps: Optional[float] = None
    Alerte_temps: Optional[bool] = None
    SEMAINE: Optional[int] = None
    EFFICACITE: Optional[float] = None
    DATA_SOURCE: Optional[str] = None  # 'ACTIVE' or 'HISTORICAL'
    COMPLETION_STATUS: Optional[str] = None  # 'COMPLETED', 'IN_PROGRESS'
    TEMPS_UNITAIRE_HISTORIQUE: Optional[float] = None


class OFResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = None


class OFListResponse(BaseResponse):
    data: Optional[List[OFItem]] = None


# KPI models
class KPIData(BaseModel):
    total_of: int = 0
    of_en_cours: int = 0
    of_termines: int = 0
    of_arretes: int = 0
    avg_prod: float = 0.0
    avg_temps: float = 0.0
    alertes: int = 0
    efficacite: float = 0.0


# Dashboard models
class DashboardData(BaseModel):
    of_data: List[OFItem] = []
    kpis: KPIData
    charge_data: List[Dict[str, Any]] = []
    backlog_data: List[Dict[str, Any]] = []
    filters_applied: Dict[str, Any] = {}


class DashboardResponse(BaseResponse):
    data: Optional[DashboardData] = None


# Filter models
class FilterOptions(BaseModel):
    familles: List[str] = []
    clients: List[str] = []


class FilterOptionsResponse(BaseResponse):
    data: Optional[FilterOptions] = None


# Health check models
class HealthStatus(BaseModel):
    status: str = "healthy"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    database_connected: bool = True
    version: str = "2.0.0"


class HealthResponse(BaseResponse):
    data: Optional[HealthStatus] = None


# Export models
class ExportRequest(BaseModel):
    format: str = Field(default="csv", description="Export format (csv, excel)")
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    statut_filter: Optional[str] = None
    famille_filter: Optional[str] = None
    client_filter: Optional[str] = None


# Statistics models
class OFStatistics(BaseModel):
    total: int = 0
    by_status: Dict[str, int] = {"C": 0, "T": 0, "A": 0}
    avg_advancement: Dict[str, float] = {"production": 0.0, "time": 0.0}
    alerts_count: int = 0


class StatisticsResponse(BaseResponse):
    data: Optional[OFStatistics] = None


# Query parameters models
class OFQueryParams(BaseModel):
    date_debut: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_fin: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    statut_filter: Optional[str] = Field(None, description="Status filter (C/T/A)")
    famille_filter: Optional[str] = Field(None, description="Family filter")
    client_filter: Optional[str] = Field(None, description="Client filter")
    alerte_filter: Optional[bool] = Field(None, description="Alert filter")
    limit: Optional[int] = Field(None, description="Limit number of results")


# Authentication models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=4, max_length=100, description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    username: Optional[str] = None
 
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    role: str = "user"  # "admin", "res", "user"
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UserInDB(User):
    hashed_password: str


class LoginResponse(BaseResponse):
    data: Optional[Token] = None


class UserResponse(BaseResponse):
    data: Optional[User] = None


# Error models
class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
