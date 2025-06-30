"""
OF (Orders of Fabrication) Controller - Business logic for OF operations
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from app.core.database import get_analyzer


class OFController:
    """Controller for OF business logic"""

    def __init__(self):
        pass

    def _clean_dataframe_for_json(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame data for JSON serialization compatibility."""
        if df.empty:
            return df

        # Create a copy to avoid modifying the original
        cleaned_df = df.copy()

        # Replace NaN, inf, and -inf with None/0 for JSON compatibility
        cleaned_df = cleaned_df.replace([float('inf'), float('-inf')], 0)
        cleaned_df = cleaned_df.fillna(0).infer_objects(copy=False)

        # Convert all numeric columns to safe types
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype in ['float64', 'float32']:
                try:
                    # Check if the column should be integer
                    if col in ['QUANTITE_DEMANDEE', 'CUMUL_ENTREES', 'DUREE_PREVUE', 'CUMUL_TEMPS_PASSES', 'PRIORITE']:
                        # Convert to int, but handle large floats safely
                        numeric_col = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
                        # Clip values to safe integer range to avoid overflow
                        numeric_col = numeric_col.clip(-2147483647, 2147483647)
                        cleaned_df[col] = numeric_col.astype(int)
                    else:
                        # Keep as float but ensure it's finite and round to reasonable precision
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0.0)
                        cleaned_df[col] = cleaned_df[col].round(6)  # Limit precision to avoid serialization issues
                except (ValueError, OverflowError, TypeError):
                    # If conversion fails, set to 0
                    cleaned_df[col] = 0

            elif cleaned_df[col].dtype == 'bool':
                # Ensure boolean columns are proper booleans
                try:
                    cleaned_df[col] = cleaned_df[col].astype(bool)
                except (ValueError, TypeError):
                    cleaned_df[col] = False

            elif cleaned_df[col].dtype == 'object':
                # Handle string columns - replace None with empty string
                cleaned_df[col] = cleaned_df[col].fillna('')

        return cleaned_df
    
    def get_all_of(self, analyzer, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get all OF data"""
        try:
            of_data = analyzer.get_of_data()

            if limit and not of_data.empty:
                of_data = of_data.head(limit)

            # Clean data for JSON serialization
            of_data = self._clean_dataframe_for_json(of_data)

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data)
            }

        except Exception as e:
            raise Exception(f"Error getting all OF: {str(e)}")

    def get_current_ofs(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current/active OF data from of_da table with specialized filtering"""
        try:
            # Get active OF data with filters
            of_data = analyzer.get_of_data(
                date_debut=date_debut,
                date_fin=date_fin,
                statut_filter=statut_filter,
                famille_filter=famille_filter,
                client_filter=client_filter
            )

            # Calculate KPIs specific to current OFs
            total_active = len(of_data)
            in_progress = len(of_data[of_data['STATUT'] == 'C']) if not of_data.empty else 0
            overdue_count = 0
            avg_progress = 0.0

            if not of_data.empty:
                # Calculate overdue orders (where current date > LANCEMENT_AU_PLUS_TARD)
                from datetime import datetime
                today = datetime.now().date()
                if 'LANCEMENT_AU_PLUS_TARD' in of_data.columns:
                    overdue_count = len(of_data[
                        pd.to_datetime(of_data['LANCEMENT_AU_PLUS_TARD'], errors='coerce').dt.date < today
                    ])

                # Calculate average progress
                if 'QUANTITE_DEMANDEE' in of_data.columns and 'CUMUL_ENTREES' in of_data.columns:
                    progress_data = of_data[
                        (of_data['QUANTITE_DEMANDEE'] > 0) &
                        (of_data['CUMUL_ENTREES'].notna())
                    ]
                    if not progress_data.empty:
                        avg_progress = (progress_data['CUMUL_ENTREES'] / progress_data['QUANTITE_DEMANDEE'] * 100).mean()

            # Clean data for JSON serialization
            of_data = self._clean_dataframe_for_json(of_data)

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": total_active,
                "kpis": {
                    "total_active": total_active,
                    "in_progress": in_progress,
                    "overdue_count": overdue_count,
                    "avg_progress": round(avg_progress, 2)
                }
            }

        except Exception as e:
            raise Exception(f"Error getting current OFs: {str(e)}")

    def get_of_en_cours(self, analyzer, date_debut=None, date_fin=None, statut_filter=None, famille_filter=None, client_filter=None) -> Dict[str, Any]:
        """Get OF currently in progress"""
        try:
            # Default to status 'C' (en cours) if no status filter provided
            if statut_filter is None:
                statut_filter = 'C'

            of_data = analyzer.get_of_data(
                date_debut=date_debut,
                date_fin=date_fin,
                statut_filter=statut_filter,
                famille_filter=famille_filter,
                client_filter=client_filter
            )

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data)
            }

        except Exception as e:
            raise Exception(f"Error getting OF en cours: {str(e)}")

    def get_of_histo(self, analyzer) -> Dict[str, Any]:
        """Get historical OF data (completed and stopped from both active and historical tables)"""
        try:
            # Get completed and stopped OF from active table
            of_termines = analyzer.get_of_data(statut_filter='T')
            of_arretes = analyzer.get_of_data(statut_filter='A')

            # Get all historical data from HISTO_OF_DA (all are considered completed)
            of_historical = analyzer.get_histo_of_data()

            # Combine all historical data
            historical_data_list = []

            if not of_termines.empty:
                historical_data_list.append(of_termines)
            if not of_arretes.empty:
                historical_data_list.append(of_arretes)
            if not of_historical.empty:
                historical_data_list.append(of_historical)

            if historical_data_list:
                # Filter out empty DataFrames before concatenation
                non_empty_data = [df for df in historical_data_list if not df.empty]
                if non_empty_data:
                    of_data = pd.concat(non_empty_data, ignore_index=True)
                else:
                    of_data = pd.DataFrame()
            else:
                of_data = pd.DataFrame()

            # Sort by date if available
            if not of_data.empty and 'LANCEMENT_AU_PLUS_TARD' in of_data.columns:
                of_data = of_data.sort_values('LANCEMENT_AU_PLUS_TARD', ascending=False)

            # Clean data for JSON serialization
            if not of_data.empty:
                of_data = self._clean_dataframe_for_json(of_data)

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data),
                "sources": {
                    "active_completed": len(of_termines) if not of_termines.empty else 0,
                    "active_stopped": len(of_arretes) if not of_arretes.empty else 0,
                    "historical": len(of_historical) if not of_historical.empty else 0
                }
            }

        except Exception as e:
            raise Exception(f"Error getting OF historique: {str(e)}")

    def get_completed_orders(self, analyzer, date_debut: Optional[str] = None, date_fin: Optional[str] = None) -> Dict[str, Any]:
        """Get all completed orders from HISTO_OF_DA table (all records are considered completed)"""
        try:
            # Get all historical data from HISTO_OF_DA - all are completed by definition
            of_data = analyzer.get_histo_of_data(
                date_debut=date_debut,
                date_fin=date_fin
            )

            # Sort by date if available
            if not of_data.empty and 'LANCEMENT_AU_PLUS_TARD' in of_data.columns:
                try:
                    of_data['LANCEMENT_AU_PLUS_TARD'] = pd.to_datetime(
                        of_data['LANCEMENT_AU_PLUS_TARD'],
                        errors='coerce'
                    )
                    of_data = of_data.sort_values('LANCEMENT_AU_PLUS_TARD', ascending=False, na_position='last')
                    of_data['LANCEMENT_AU_PLUS_TARD'] = of_data['LANCEMENT_AU_PLUS_TARD'].dt.strftime('%Y-%m-%d')
                except Exception as sort_error:
                    print(f"Warning: Could not sort by date: {sort_error}")

            # Clean data for JSON serialization
            if not of_data.empty:
                of_data = self._clean_dataframe_for_json(of_data)

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data),
                "data_source": "HISTO_OF_DA",
                "completion_status": "ALL_COMPLETED"
            }

        except Exception as e:
            raise Exception(f"Error getting completed orders: {str(e)}")

    def get_of_by_status(self, analyzer, status: str) -> Dict[str, Any]:
        """Get OF by specific status"""
        try:
            # Validate status
            valid_statuses = ['C', 'T', 'A']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

            of_data = analyzer.get_of_data(statut_filter=status)

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data),
                "status": status
            }

        except Exception as e:
            raise Exception(f"Error getting OF by status {status}: {str(e)}")

    def get_of_with_filters(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None,
        limit: Optional[int] = None,
        include_historical: bool = False
    ) -> Dict[str, Any]:
        """Get OF data with comprehensive filters, optionally including historical data"""
        try:
            if include_historical:
                # Use combined data approach
                of_data = analyzer.get_combined_of_data(
                    date_debut=date_debut,
                    date_fin=date_fin,
                    statut_filter=statut_filter,
                    famille_filter=famille_filter,
                    client_filter=client_filter,
                    alerte_filter=alerte_filter,
                    include_historical=True
                )
            else:
                # Use only active data
                of_data = analyzer.get_of_data(
                    date_debut=date_debut,
                    date_fin=date_fin,
                    statut_filter=statut_filter,
                    famille_filter=famille_filter,
                    client_filter=client_filter,
                    alerte_filter=alerte_filter
                )

            if limit and not of_data.empty:
                of_data = of_data.head(limit)

            # Count data sources if historical data is included
            source_counts = {}
            if include_historical and not of_data.empty and 'DATA_SOURCE' in of_data.columns:
                source_counts = of_data['DATA_SOURCE'].value_counts().to_dict()

            return {
                "of_list": of_data.to_dict('records') if not of_data.empty else [],
                "count": len(of_data),
                "source_counts": source_counts,
                "filters_applied": {
                    "date_debut": date_debut,
                    "date_fin": date_fin,
                    "statut_filter": statut_filter,
                    "famille_filter": famille_filter,
                    "client_filter": client_filter,
                    "alerte_filter": alerte_filter,
                    "limit": limit,
                    "include_historical": include_historical
                }
            }

        except Exception as e:
            raise Exception(f"Error getting filtered OF: {str(e)}")

    def get_of_statistics(self, analyzer) -> Dict[str, Any]:
        """Get OF statistics summary"""
        try:
            of_data = analyzer.get_of_data()

            if of_data.empty:
                return {
                    "total": 0,
                    "by_status": {"C": 0, "T": 0, "A": 0},
                    "avg_advancement": {"production": 0.0, "time": 0.0},
                    "alerts_count": 0
                }

            # Count by status
            status_counts = of_data['STATUT'].value_counts().to_dict()
            by_status = {
                "C": status_counts.get('C', 0),
                "T": status_counts.get('T', 0),
                "A": status_counts.get('A', 0)
            }

            # Calculate averages
            avg_prod = of_data['Avancement_PROD'].mean() * 100 if 'Avancement_PROD' in of_data.columns else 0.0
            avg_temps = of_data['Avancement_temps'].mean() * 100 if 'Avancement_temps' in of_data.columns else 0.0

            # Count alerts
            alerts_count = len(of_data[of_data.get('Alerte_temps', False) == True])

            return {
                "total": len(of_data),
                "by_status": by_status,
                "avg_advancement": {
                    "production": round(avg_prod, 1),
                    "time": round(avg_temps, 1)
                },
                "alerts_count": alerts_count
            }

        except Exception as e:
            raise Exception(f"Error getting OF statistics: {str(e)}")

    def get_history_ofs(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get historical/completed OF data from histo_of_da table with specialized filtering"""
        try:
            # Get historical data with filters (applies to DATA_CLOTURE)
            of_historical = analyzer.get_histo_of_data(
                date_debut=date_debut,
                date_fin=date_fin,
                famille_filter=famille_filter,
                client_filter=client_filter
            )

            # Apply status filter if provided (though all HISTO_OF_DA records are considered completed)
            if statut_filter and not of_historical.empty:
                of_historical = of_historical[of_historical['STATUT'] == statut_filter]

            # Calculate KPIs specific to historical OFs
            total_completed = len(of_historical)
            completion_rate = 100.0  # All records in HISTO_OF_DA are completed
            avg_completion_time = 0.0
            recently_completed = 0

            if not of_historical.empty:
                # Calculate recently completed (last 7 days)
                from datetime import datetime, timedelta
                import pandas as pd
                seven_days_ago = datetime.now().date() - timedelta(days=7)
                if 'DATA_CLOTURE' in of_historical.columns:
                    try:
                        # Convert DATA_CLOTURE to datetime and then to date for comparison
                        data_cloture_dates = pd.to_datetime(of_historical['DATA_CLOTURE'], errors='coerce')
                        # Filter out NaT values and convert to date
                        valid_dates = data_cloture_dates.dropna()
                        if not valid_dates.empty:
                            # Create boolean mask for date comparison
                            date_mask = data_cloture_dates.dt.date >= seven_days_ago
                            recent_completions = of_historical[date_mask.fillna(False)]
                            recently_completed = len(recent_completions)
                    except Exception as e:
                        print(f"Warning: Error processing DATA_CLOTURE dates: {e}")
                        recently_completed = 0

                # Calculate average completion time if we have both start and end dates
                if 'LANCE_LE' in of_historical.columns and 'DATA_CLOTURE' in of_historical.columns:
                    completion_times = pd.to_datetime(of_historical['DATA_CLOTURE'], errors='coerce') - \
                                     pd.to_datetime(of_historical['LANCE_LE'], errors='coerce')
                    valid_times = completion_times.dropna()
                    if not valid_times.empty:
                        avg_completion_time = valid_times.dt.days.mean()

            return {
                "of_list": of_historical.to_dict('records') if not of_historical.empty else [],
                "count": total_completed,
                "kpis": {
                    "total_completed": total_completed,
                    "completion_rate": completion_rate,
                    "avg_completion_time": round(avg_completion_time, 1),
                    "recently_completed": recently_completed
                }
            }

        except Exception as e:
            raise Exception(f"Error getting history OFs: {str(e)}")

    def get_all_ofs_combined(
        self,
        analyzer,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get combined view of all OF data from both of_da and histo_of_da tables"""
        try:
            # Use the existing combined data method from analyzer
            combined_data = analyzer.get_combined_of_data(
                date_debut=date_debut,
                date_fin=date_fin,
                statut_filter=statut_filter,
                famille_filter=famille_filter,
                client_filter=client_filter,
                include_historical=True
            )

            if limit and not combined_data.empty:
                combined_data = combined_data.head(limit)

            # Calculate combined KPIs
            total_ofs = len(combined_data)
            active_count = 0
            completed_count = 0
            overall_performance = 0.0

            if not combined_data.empty:
                # Count by data source
                if 'DATA_SOURCE' in combined_data.columns:
                    source_counts = combined_data['DATA_SOURCE'].value_counts().to_dict()
                    active_count = source_counts.get('ACTIVE', 0)
                    completed_count = source_counts.get('HISTORICAL', 0)

                # Calculate overall performance metric
                if 'QUANTITE_DEMANDEE' in combined_data.columns and 'CUMUL_ENTREES' in combined_data.columns:
                    performance_data = combined_data[
                        (combined_data['QUANTITE_DEMANDEE'] > 0) &
                        (combined_data['CUMUL_ENTREES'].notna())
                    ]
                    if not performance_data.empty:
                        overall_performance = (performance_data['CUMUL_ENTREES'] / performance_data['QUANTITE_DEMANDEE'] * 100).mean()

            # Clean data for JSON serialization using the existing method
            combined_data = self._clean_dataframe_for_json(combined_data)

            return {
                "of_list": combined_data.to_dict('records') if not combined_data.empty else [],
                "count": total_ofs,
                "kpis": {
                    "total_ofs": int(total_ofs),
                    "active_vs_completed_ratio": f"{int(active_count)}:{int(completed_count)}",
                    "overall_performance": float(round(overall_performance, 2)) if np.isfinite(overall_performance) else 0.0,
                    "active_count": int(active_count),
                    "completed_count": int(completed_count)
                }
            }

        except Exception as e:
            raise Exception(f"Error getting combined OFs: {str(e)}")
