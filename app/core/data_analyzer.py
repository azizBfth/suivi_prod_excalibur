"""
Data Analyzer - Simplified implementation for MVC pattern
"""

import pandas as pd
import pyodbc
from typing import Optional, Dict, Any
from app.core.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import warnings


class ExcaliburDataAnalyzer:
    """Simplified data analyzer for production tracking."""

    def __init__(self):
        """Initialize the analyzer with database connection."""
        self.settings = get_settings()
        self.connection = None
        self.engine = None  # SQLAlchemy engine
        self._sample_data = None  # Cache for sample data
        self._of_da_columns = None  # Cache for OF_DA columns
        self._histo_of_da_columns = None  # Cache for HISTO_OF_DA columns
        self._connect()
    
    def _connect(self):
        """Establish database connection with SQLAlchemy."""
        try:
            # First establish pyodbc connection
            connection_string = (
                f"DRIVER={{SQL Anywhere 17}};"
                f"SERVER={self.settings.db_server_name};"
                f"HOST={self.settings.db_host};"
                f"DATABASE={self.settings.db_database_name};"
                f"UID={self.settings.db_uid};"
                f"PWD={self.settings.db_pwd};"
                f"CHARSET=UTF-8;"
            )
            self.connection = pyodbc.connect(connection_string)
            print("✅ PyODBC database connection established successfully")

            # Create SQLAlchemy engine using the same connection parameters
            # Use a simpler approach: create engine from the pyodbc connection string
            sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={connection_string.replace(';', '%3B').replace('=', '%3D').replace('{', '%7B').replace('}', '%7D').replace(' ', '+')}"

            # Alternative: Try direct SQL Anywhere URL format
            try:
                # Create SQLAlchemy engine
                self.engine = create_engine(
                    sqlalchemy_url,
                    echo=False,  # Set to True for SQL debugging
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections every hour
                )

                # Test the SQLAlchemy connection
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()

                print("✅ SQLAlchemy database connection established successfully")

            except Exception as sqlalchemy_error:
                print(f"⚠️ SQLAlchemy connection failed, will use pyodbc with warning suppression: {sqlalchemy_error}")
                self.engine = None
                # We'll suppress warnings in execute_query instead

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.connection = None
            self.engine = None
    
    def _close_connection(self):
        """Close database connections."""
        if self.engine:
            try:
                self.engine.dispose()
            except:
                pass
            self.engine = None

        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

    def _check_table_columns(self, table_name: str) -> list:
        """Check what columns exist in a specific table."""
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            # Use a query that gets table structure without data
            cursor.execute(f'SELECT * FROM "gpao"."{table_name}" WHERE 1=0')
            columns = [column[0] for column in cursor.description]
            cursor.close()
            print(f"✅ Found {len(columns)} columns in {table_name}: {columns}")
            return columns
        except Exception as e:
            print(f"❌ Error checking {table_name} columns: {e}")
            return []

    def _get_available_columns(self):
        """Get available columns for both tables and cache them."""
        if self._of_da_columns is None:
            self._of_da_columns = self._check_table_columns("OF_DA")
        if self._histo_of_da_columns is None:
            self._histo_of_da_columns = self._check_table_columns("HISTO_OF_DA")

        return self._of_da_columns, self._histo_of_da_columns
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute SQL query and return DataFrame with proper warning suppression."""
        # Try SQLAlchemy first if available
        if self.engine:
            try:
                # Suppress pandas SQLAlchemy warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

                    if params:
                        # Convert tuple params to dict for SQLAlchemy
                        if isinstance(params, tuple):
                            # Create numbered parameters for SQLAlchemy
                            param_dict = {f"param_{i}": param for i, param in enumerate(params)}
                            # Replace ? placeholders with :param_0, :param_1, etc.
                            sqlalchemy_query = query
                            for i in range(len(params)):
                                sqlalchemy_query = sqlalchemy_query.replace("?", f":param_{i}", 1)
                            return pd.read_sql(text(sqlalchemy_query), self.engine, params=param_dict)
                        else:
                            return pd.read_sql(text(query), self.engine, params=params)
                    else:
                        return pd.read_sql(text(query), self.engine)

            except Exception as e:
                print(f"❌ SQLAlchemy query execution failed: {e}")
                # Fall back to pyodbc

        # Fall back to pyodbc connection with warning suppression
        if not self.connection:
            print("No connection available, attempting to reconnect...")
            self._connect()
            if not self.connection:
                print("Failed to establish connection")
                return pd.DataFrame()

        try:
            # Suppress pandas warnings about pyodbc connections
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")
                warnings.filterwarnings("ignore", message=".*Other DBAPI2 objects are not tested.*")

                if params:
                    return pd.read_sql(query, self.connection, params=params)
                else:
                    return pd.read_sql(query, self.connection)

        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            # Try to reconnect once
            print("🔄 Attempting to reconnect...")
            self._connect()
            if self.connection:
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")
                        warnings.filterwarnings("ignore", message=".*Other DBAPI2 objects are not tested.*")

                        if params:
                            return pd.read_sql(query, self.connection, params=params)
                        else:
                            return pd.read_sql(query, self.connection)
                except Exception as e2:
                    print(f"❌ Query execution failed after reconnect: {e2}")
            return pd.DataFrame()
    
    def get_of_data(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get OF data with filters including historical unit time calculations."""
        # Enhanced query with proper historical unit time calculations from HISTO_OF_DA
        # Including all useful ERP fields: LANCE_LE, DISPO_DEMANDE, DATA_CLOTURE
        query = """
        SELECT
            ofda.NUMERO_OFDA,
            ofda.PRODUIT,
            ofda.STATUT,
            ofda.LANCEMENT_AU_PLUS_TARD,
            ofda.QUANTITE_DEMANDEE,
            ofda.CUMUL_ENTREES,
            ofda.DUREE_PREVUE,
            ofda.CUMUL_TEMPS_PASSES,
            ofda.AFFAIRE,
            ofda.DESIGNATION,
            ofda.LANCE_LE,
            ofda.DISPO_DEMANDEE AS DISPO_DEMANDE,
            NULL AS DATA_CLOTURE,
            COALESCE(ofda.CATEGORIE, 'Non définie') AS FAMILLE_TECHNIQUE,
            COALESCE(ofda.CLIENT, 'Non défini') AS CLIENT,
            'Non défini' AS SECTEUR,
            0 AS PRIORITE,
            'Non défini' AS RESPONSABLE,
            COALESCE(hist_avg.TEMPS_UNITAIRE_MOYEN, 0) AS TEMPS_UNITAIRE_HISTORIQUE,
            'ACTIVE' AS DATA_SOURCE,
            CASE
                WHEN ofda.STATUT IN ('T', 'A') THEN 'COMPLETED'
                ELSE 'IN_PROGRESS'
            END AS COMPLETION_STATUS,
            CASE
                WHEN ofda.QUANTITE_DEMANDEE > 0
                THEN CAST(ofda.CUMUL_ENTREES AS FLOAT) / CAST(ofda.QUANTITE_DEMANDEE AS FLOAT)
                ELSE 0
            END AS Avancement_PROD,
            CASE
                WHEN ofda.DUREE_PREVUE > 0
                THEN CAST(ofda.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(ofda.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps,
            CASE
                WHEN ofda.DUREE_PREVUE > 0 AND ofda.CUMUL_TEMPS_PASSES > ofda.DUREE_PREVUE
                THEN 1
                ELSE 0
            END AS Alerte_temps,
            ofda.DUREE_PREVUE AS DUREE_ESTIMEE_HISTORIQUE,
            CASE
                WHEN ofda.DUREE_PREVUE > 0
                THEN CAST(ofda.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(ofda.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps_historique
        FROM gpao.OF_DA AS ofda
        LEFT JOIN (
            SELECT
                HISTO.PRODUIT,
                HISTO.CATEGORIE,
                AVG(CASE
                    WHEN HISTO.CUMUL_ENTREES > 0
                    THEN CAST(HISTO.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(HISTO.CUMUL_ENTREES AS FLOAT)
                    ELSE 0
                END) AS TEMPS_UNITAIRE_MOYEN
            FROM gpao.HISTO_OF_DA HISTO
            WHERE HISTO.CUMUL_ENTREES > 0 AND HISTO.CUMUL_TEMPS_PASSES > 0
            GROUP BY HISTO.PRODUIT, HISTO.CATEGORIE
        ) hist_avg ON ofda.PRODUIT = hist_avg.PRODUIT AND ofda.CATEGORIE = hist_avg.CATEGORIE
        WHERE ofda.NUMERO_OFDA LIKE 'F%'
        """

        params = []

        if statut_filter:
            query += " AND ofda.STATUT = ?"
            params.append(statut_filter)

        if date_debut:
            query += " AND ofda.LANCEMENT_AU_PLUS_TARD >= ?"
            params.append(date_debut)

        if date_fin:
            query += " AND ofda.LANCEMENT_AU_PLUS_TARD <= ?"
            params.append(date_fin)

        if famille_filter:
            query += " AND COALESCE(ofda.CATEGORIE, 'Non définie') = ?"
            params.append(famille_filter)

        if client_filter:
            query += " AND COALESCE(ofda.CLIENT, 'Non défini') = ?"
            params.append(client_filter)

        query += " ORDER BY ofda.LANCEMENT_AU_PLUS_TARD DESC"

        df = self.execute_query(query, tuple(params) if params else None)

        # If database query fails, provide sample data for testing filters
        if df.empty and not hasattr(self, '_sample_data_created'):
            print("Database query returned empty, creating sample data for testing...")
            df = self._create_sample_data()
            self._sample_data_created = True
            print(f"Created sample data with {len(df)} records")

            # Apply filters to sample data
            print(f"Applying filters to {len(df)} sample records...")
            if statut_filter:
                df = df[df['STATUT'] == statut_filter]
                print(f"Applied status filter '{statut_filter}': {len(df)} records remaining")
            if famille_filter:
                df = df[df['FAMILLE_TECHNIQUE'] == famille_filter]
                print(f"Applied family filter '{famille_filter}': {len(df)} records remaining")
            if client_filter:
                df = df[df['CLIENT'] == client_filter]
                print(f"Applied client filter '{client_filter}': {len(df)} records remaining")
            if date_debut:
                df = df[df['LANCEMENT_AU_PLUS_TARD'] >= date_debut]
                print(f"Applied start date filter '{date_debut}': {len(df)} records remaining")
            if date_fin:
                df = df[df['LANCEMENT_AU_PLUS_TARD'] <= date_fin]
                print(f"Applied end date filter '{date_fin}': {len(df)} records remaining")

        if not df.empty:
            # Add calculated columns
            df['Avancement_PROD'] = df.apply(
                lambda row: row['CUMUL_ENTREES'] / row['QUANTITE_DEMANDEE']
                if row['QUANTITE_DEMANDEE'] and row['QUANTITE_DEMANDEE'] != 0 else 0,
                axis=1
            )

            df['Avancement_temps'] = df.apply(
                lambda row: row['CUMUL_TEMPS_PASSES'] / row['DUREE_PREVUE']
                if row['DUREE_PREVUE'] and row['DUREE_PREVUE'] != 0 else 0,
                axis=1
            )

            # Add alert column (simple logic: time advancement > production advancement)
            df['Alerte_temps'] = df['Avancement_temps'] > df['Avancement_PROD']

            # Add missing columns for consistency
            if 'DATA_SOURCE' not in df.columns:
                df['DATA_SOURCE'] = 'ACTIVE'
            if 'COMPLETION_STATUS' not in df.columns:
                df['COMPLETION_STATUS'] = df['STATUT'].apply(
                    lambda x: 'COMPLETED' if x in ['T', 'A'] else 'IN_PROGRESS'
                )

            # Apply alert filter if specified
            if alerte_filter:
                df = df[df['Alerte_temps'] == True]

            # Add week number
            df['SEMAINE'] = pd.to_datetime(df['LANCEMENT_AU_PLUS_TARD'], errors='coerce').dt.isocalendar().week

            # Add efficiency calculation (more realistic)
            df['EFFICACITE'] = df.apply(
                lambda row: row['Avancement_PROD'] / row['Avancement_temps']
                if row['Avancement_temps'] and row['Avancement_temps'] != 0 else 1.0,
                axis=1
            )

        return df

    def _create_sample_data(self) -> pd.DataFrame:
        """Create sample data for testing when database is not available."""
        import random
        from datetime import datetime, timedelta

        # Sample data for testing filters
        sample_data = []
        familles = ['Mécanique', 'Électronique', 'Assemblage', 'Usinage', 'Soudure']
        clients = ['Client A', 'Client B', 'Client C', 'Client D', 'Client E']
        statuts = ['C', 'T', 'A']

        base_date = datetime.now()

        for i in range(50):
            # Generate random dates within the last 6 months
            days_offset = random.randint(-180, 30)
            launch_date = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')

            quantite_demandee = random.randint(10, 1000)
            cumul_entrees = random.randint(0, quantite_demandee)
            duree_prevue = random.randint(10, 200)
            cumul_temps_passes = random.randint(0, int(duree_prevue * 1.5))

            sample_data.append({
                'NUMERO_OFDA': f'F{1000 + i:04d}',
                'PRODUIT': f'PROD_{i:03d}',
                'STATUT': random.choice(statuts),
                'LANCEMENT_AU_PLUS_TARD': launch_date,
                'QUANTITE_DEMANDEE': quantite_demandee,
                'CUMUL_ENTREES': cumul_entrees,
                'DUREE_PREVUE': duree_prevue,
                'CUMUL_TEMPS_PASSES': cumul_temps_passes,
                'AFFAIRE': f'AFF_{i:03d}',
                'DESIGNATION': f'Produit de test {i}',
                'LANCE_LE': launch_date,
                'DISPO_DEMANDE': (base_date + timedelta(days=days_offset + random.randint(5, 30))).strftime('%Y-%m-%d'),
                'DATA_CLOTURE': (base_date + timedelta(days=days_offset + random.randint(30, 60))).strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                'FAMILLE_TECHNIQUE': random.choice(familles),
                'CLIENT': random.choice(clients),
                'SECTEUR': random.choice(['USINAGE', 'ASSEMBLAGE', 'CONTROLE', 'EXPEDITION']),
                'PRIORITE': random.randint(1, 5),
                'RESPONSABLE': random.choice(['Resp_A', 'Resp_B', 'Resp_C'])
            })

        return pd.DataFrame(sample_data)
    def get_histo_of_data(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """Get historical OF data from HISTO_OF_DA table. All records are considered completed."""
        query = """
        SELECT
            histo.NUMERO_OFDA,
            histo.PRODUIT,
            histo.STATUT,
            histo.LANCEMENT_AU_PLUS_TARD,
            histo.QUANTITE_DEMANDEE,
            histo.CUMUL_ENTREES,
            histo.DUREE_PREVUE,
            histo.CUMUL_TEMPS_PASSES,
            histo.AFFAIRE,
            histo.DESIGNATION,
            histo.LANCE_LE,
            histo.DISPO_DEMANDEE AS DISPO_DEMANDE,
            histo.DATE_CLOTURE AS DATA_CLOTURE,
            COALESCE(histo.CATEGORIE, 'Non définie') AS FAMILLE_TECHNIQUE,
            COALESCE(histo.CLIENT, 'Non défini') AS CLIENT,
            'Non défini' AS SECTEUR,
            0 AS PRIORITE,
            'Non défini' AS RESPONSABLE,
            CASE
                WHEN histo.CUMUL_ENTREES > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.CUMUL_ENTREES AS FLOAT)
                ELSE 0
            END AS TEMPS_UNITAIRE_HISTORIQUE,
            'HISTORICAL' AS DATA_SOURCE,
            'COMPLETED' AS COMPLETION_STATUS,
            CASE
                WHEN histo.QUANTITE_DEMANDEE > 0
                THEN CAST(histo.CUMUL_ENTREES AS FLOAT) / CAST(histo.QUANTITE_DEMANDEE AS FLOAT)
                ELSE 0
            END AS Avancement_PROD,
            CASE
                WHEN histo.DUREE_PREVUE > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps,
            0 AS Alerte_temps,
            histo.DUREE_PREVUE AS DUREE_ESTIMEE_HISTORIQUE,
            CASE
                WHEN histo.DUREE_PREVUE > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps_historique
        FROM gpao.HISTO_OF_DA AS histo
        WHERE histo.NUMERO_OFDA LIKE 'F%'
        """

        params = []

        if date_debut:
            # For historical data, filter by DATE_CLOTURE (completion date)
            query += " AND histo.DATE_CLOTURE >= ?"
            params.append(date_debut)

        if date_fin:
            # For historical data, filter by DATE_CLOTURE (completion date)
            query += " AND histo.DATE_CLOTURE <= ?"
            params.append(date_fin)

        if famille_filter:
            query += " AND COALESCE(histo.CATEGORIE, 'Non définie') = ?"
            params.append(famille_filter)

        if client_filter:
            query += " AND COALESCE(histo.CLIENT, 'Non défini') = ?"
            params.append(client_filter)

        query += " ORDER BY histo.LANCEMENT_AU_PLUS_TARD DESC"

        df = self.execute_query(query, tuple(params) if params else None)
        return df if df is not None else pd.DataFrame()

    def get_combined_of_data(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None,
        include_historical: bool = True
    ) -> pd.DataFrame:
        """Get combined OF data from both active and historical tables using LANCE_LE for date filtering."""
        # Get active data using LANCE_LE for filtering
        active_data = self.get_of_data_with_lance_le_filter(
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            famille_filter=famille_filter,
            client_filter=client_filter,
            alerte_filter=alerte_filter
        )

        if not include_historical:
            return active_data

        # Get historical data using LANCE_LE for filtering (not DATE_CLOTURE for combined view)
        historical_data = self.get_histo_of_data_with_lance_le_filter(
            date_debut=date_debut,
            date_fin=date_fin,
            famille_filter=famille_filter,
            client_filter=client_filter
        )

        # Combine the data (columns should now be consistent)
        if not active_data.empty and not historical_data.empty:
            # Ensure both DataFrames have data before concatenation
            combined_data = pd.concat([active_data, historical_data], ignore_index=True)
        elif not active_data.empty:
            combined_data = active_data
        elif not historical_data.empty:
            combined_data = historical_data
        else:
            combined_data = pd.DataFrame()

        return combined_data

    def get_of_data_with_lance_le_filter(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        statut_filter: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None,
        alerte_filter: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get OF data with filters using LANCE_LE field for date filtering (for combined view)."""
        # Same query as get_of_data but with LANCE_LE filtering
        query = """
        SELECT
            ofda.NUMERO_OFDA,
            ofda.PRODUIT,
            ofda.STATUT,
            ofda.LANCEMENT_AU_PLUS_TARD,
            ofda.QUANTITE_DEMANDEE,
            ofda.CUMUL_ENTREES,
            ofda.DUREE_PREVUE,
            ofda.CUMUL_TEMPS_PASSES,
            ofda.AFFAIRE,
            ofda.DESIGNATION,
            ofda.LANCE_LE,
            ofda.DISPO_DEMANDEE AS DISPO_DEMANDE,
            NULL AS DATA_CLOTURE,
            COALESCE(ofda.CATEGORIE, 'Non définie') AS FAMILLE_TECHNIQUE,
            COALESCE(ofda.CLIENT, 'Non défini') AS CLIENT,
            'Non défini' AS SECTEUR,
            0 AS PRIORITE,
            'Non défini' AS RESPONSABLE,
            COALESCE(hist_avg.TEMPS_UNITAIRE_MOYEN, 0) AS TEMPS_UNITAIRE_HISTORIQUE,
            'ACTIVE' AS DATA_SOURCE,
            CASE
                WHEN ofda.STATUT IN ('T', 'A') THEN 'COMPLETED'
                ELSE 'IN_PROGRESS'
            END AS COMPLETION_STATUS,
            CASE
                WHEN ofda.QUANTITE_DEMANDEE > 0
                THEN CAST(ofda.CUMUL_ENTREES AS FLOAT) / CAST(ofda.QUANTITE_DEMANDEE AS FLOAT)
                ELSE 0
            END AS Avancement_PROD,
            CASE
                WHEN ofda.DUREE_PREVUE > 0
                THEN CAST(ofda.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(ofda.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps,
            CASE
                WHEN ofda.DUREE_PREVUE > 0 AND ofda.CUMUL_TEMPS_PASSES > ofda.DUREE_PREVUE
                THEN 1
                ELSE 0
            END AS Alerte_temps,
            ofda.DUREE_PREVUE AS DUREE_ESTIMEE_HISTORIQUE,
            CASE
                WHEN ofda.DUREE_PREVUE > 0
                THEN CAST(ofda.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(ofda.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps_historique
        FROM gpao.OF_DA AS ofda
        LEFT JOIN (
            SELECT
                HISTO.PRODUIT,
                HISTO.CATEGORIE,
                AVG(CASE
                    WHEN HISTO.CUMUL_ENTREES > 0
                    THEN CAST(HISTO.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(HISTO.CUMUL_ENTREES AS FLOAT)
                    ELSE 0
                END) AS TEMPS_UNITAIRE_MOYEN
            FROM gpao.HISTO_OF_DA HISTO
            WHERE HISTO.CUMUL_ENTREES > 0 AND HISTO.CUMUL_TEMPS_PASSES > 0
            GROUP BY HISTO.PRODUIT, HISTO.CATEGORIE
        ) hist_avg ON ofda.PRODUIT = hist_avg.PRODUIT AND ofda.CATEGORIE = hist_avg.CATEGORIE
        WHERE ofda.NUMERO_OFDA LIKE 'F%'
        """

        params = []

        # Use LANCE_LE for date filtering in combined view
        if date_debut:
            query += " AND ofda.LANCE_LE >= ?"
            params.append(date_debut)

        if date_fin:
            query += " AND ofda.LANCE_LE <= ?"
            params.append(date_fin)

        if statut_filter:
            query += " AND ofda.STATUT = ?"
            params.append(statut_filter)

        if famille_filter:
            query += " AND COALESCE(ofda.CATEGORIE, 'Non définie') = ?"
            params.append(famille_filter)

        if client_filter:
            query += " AND COALESCE(ofda.CLIENT, 'Non défini') = ?"
            params.append(client_filter)

        query += " ORDER BY ofda.LANCEMENT_AU_PLUS_TARD DESC"

        df = self.execute_query(query, tuple(params) if params else None)

        if df is None or df.empty:
            return pd.DataFrame()

        # Apply alert filter if specified
        if alerte_filter is not None:
            if alerte_filter:
                df = df[df['Alerte_temps'] == 1]
            else:
                df = df[df['Alerte_temps'] == 0]

        return df

    def get_histo_of_data_with_lance_le_filter(
        self,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        famille_filter: Optional[str] = None,
        client_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """Get historical OF data using LANCE_LE field for date filtering (for combined view)."""
        query = """
        SELECT
            histo.NUMERO_OFDA,
            histo.PRODUIT,
            histo.STATUT,
            histo.LANCEMENT_AU_PLUS_TARD,
            histo.QUANTITE_DEMANDEE,
            histo.CUMUL_ENTREES,
            histo.DUREE_PREVUE,
            histo.CUMUL_TEMPS_PASSES,
            histo.AFFAIRE,
            histo.DESIGNATION,
            histo.LANCE_LE,
            histo.DISPO_DEMANDEE AS DISPO_DEMANDE,
            histo.DATE_CLOTURE AS DATA_CLOTURE,
            COALESCE(histo.CATEGORIE, 'Non définie') AS FAMILLE_TECHNIQUE,
            COALESCE(histo.CLIENT, 'Non défini') AS CLIENT,
            'Non défini' AS SECTEUR,
            0 AS PRIORITE,
            'Non défini' AS RESPONSABLE,
            CASE
                WHEN histo.CUMUL_ENTREES > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.CUMUL_ENTREES AS FLOAT)
                ELSE 0
            END AS TEMPS_UNITAIRE_HISTORIQUE,
            'HISTORICAL' AS DATA_SOURCE,
            'COMPLETED' AS COMPLETION_STATUS,
            CASE
                WHEN histo.QUANTITE_DEMANDEE > 0
                THEN CAST(histo.CUMUL_ENTREES AS FLOAT) / CAST(histo.QUANTITE_DEMANDEE AS FLOAT)
                ELSE 0
            END AS Avancement_PROD,
            CASE
                WHEN histo.DUREE_PREVUE > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps,
            0 AS Alerte_temps,
            histo.DUREE_PREVUE AS DUREE_ESTIMEE_HISTORIQUE,
            CASE
                WHEN histo.DUREE_PREVUE > 0
                THEN CAST(histo.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(histo.DUREE_PREVUE AS FLOAT)
                ELSE 0
            END AS Avancement_temps_historique
        FROM gpao.HISTO_OF_DA AS histo
        WHERE histo.NUMERO_OFDA LIKE 'F%'
        """

        params = []

        # Use LANCE_LE for date filtering in combined view
        if date_debut:
            query += " AND histo.LANCE_LE >= ?"
            params.append(date_debut)

        if date_fin:
            query += " AND histo.LANCE_LE <= ?"
            params.append(date_fin)

        if famille_filter:
            query += " AND COALESCE(histo.CATEGORIE, 'Non définie') = ?"
            params.append(famille_filter)

        if client_filter:
            query += " AND COALESCE(histo.CLIENT, 'Non défini') = ?"
            params.append(client_filter)

        query += " ORDER BY histo.LANCEMENT_AU_PLUS_TARD DESC"

        df = self.execute_query(query, tuple(params) if params else None)
        return df if df is not None else pd.DataFrame()

    def get_historical_analysis(self, date_debut: str, date_fin: str) -> Dict[str, Any]:
        """Get historical analysis comparing current performance with historical data."""
        try:
            # Get current OF data with historical calculations
            current_data = self.get_of_data(date_debut=date_debut, date_fin=date_fin)

            # Get historical data for comparison
            historical_data = self.get_histo_of_data(date_debut=date_debut, date_fin=date_fin)

            if current_data.empty and historical_data.empty:
                return {
                    'success': False,
                    'message': 'No data available for historical analysis',
                    'data': {}
                }

            # Calculate historical performance metrics
            historical_metrics = {
                'total_current_orders': len(current_data) if not current_data.empty else 0,
                'total_historical_orders': len(historical_data) if not historical_data.empty else 0,
                'orders_with_historical_data': len(current_data[current_data['TEMPS_UNITAIRE_HISTORIQUE'] > 0]) if not current_data.empty else 0,
                'avg_historical_unit_time': current_data['TEMPS_UNITAIRE_HISTORIQUE'].mean() if not current_data.empty else 0,
                'historical_completion_rate': 100.0 if not historical_data.empty else 0.0,  # All HISTO_OF_DA records are completed
                'current_avg_advancement': current_data['Avancement_PROD'].mean() * 100 if not current_data.empty else 0,
                'historical_avg_advancement': 100.0 if not historical_data.empty else 0.0,  # All historical orders are 100% complete
            }

            # Group by product family for detailed analysis
            family_analysis = {}
            if not current_data.empty:
                family_analysis = current_data.groupby('FAMILLE_TECHNIQUE').agg({
                    'TEMPS_UNITAIRE_HISTORIQUE': 'mean',
                    'Avancement_PROD': 'mean',
                    'Avancement_temps': 'mean',
                    'NUMERO_OFDA': 'count'
                }).round(3).to_dict('index')

            # Historical family analysis
            historical_family_analysis = {}
            if not historical_data.empty:
                historical_family_analysis = historical_data.groupby('FAMILLE_TECHNIQUE').agg({
                    'TEMPS_UNITAIRE_HISTORIQUE': 'mean',
                    'Avancement_PROD': 'mean',
                    'Avancement_temps': 'mean',
                    'NUMERO_OFDA': 'count'
                }).round(3).to_dict('index')

            # Top performing current products
            top_current_performers = []
            if not current_data.empty:
                top_current_performers = current_data.nlargest(10, 'Avancement_PROD')[
                    ['NUMERO_OFDA', 'PRODUIT', 'DESIGNATION', 'Avancement_PROD', 'FAMILLE_TECHNIQUE']
                ].to_dict('records')

            # Sample of completed historical orders
            historical_sample = []
            if not historical_data.empty:
                historical_sample = historical_data.head(10)[
                    ['NUMERO_OFDA', 'PRODUIT', 'DESIGNATION', 'COMPLETION_STATUS', 'FAMILLE_TECHNIQUE']
                ].to_dict('records')

            return {
                'success': True,
                'data': {
                    'metrics': historical_metrics,
                    'current_family_analysis': family_analysis,
                    'historical_family_analysis': historical_family_analysis,
                    'top_current_performers': top_current_performers,
                    'historical_sample': historical_sample,
                    'current_data': current_data.to_dict('records') if not current_data.empty else [],
                    'historical_data': historical_data.to_dict('records') if not historical_data.empty else []
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error in historical analysis: {str(e)}',
                'data': {}
            }
    def get_charge_data(self) -> pd.DataFrame:
        """Get workload data."""
        # Return empty DataFrame for now - can be implemented later
        return pd.DataFrame({
            'SECTEUR': [],
            'NB_OPERATEURS': [],
            'NB_HEURES_DISPONIBLES_SEMAINE': []
        })
    
    def get_backlog_data(self) -> pd.DataFrame:
        """Get backlog data."""
        # Return empty DataFrame for now - can be implemented later
        return pd.DataFrame({
            'NUMERO_OFDA': [],
            'PRIORITE': [],
            'DATE_PREVUE': []
        })
    
    def get_personnel_data(self) -> pd.DataFrame:
        """Get personnel data."""
        # Return empty DataFrame for now - can be implemented later
        return pd.DataFrame({
            'NOM': [],
            'QUALIFICATION': [],
            'SECTEUR': []
        })
    
    def get_comprehensive_of_data(
        self,
        date_debut: str,
        date_fin: str,
        statut_filter: Optional[str] = None,
        include_historical: bool = True
    ) -> pd.DataFrame:
        """Get comprehensive OF data for the specified period, including historical data."""
        return self.get_combined_of_data(
            date_debut=date_debut,
            date_fin=date_fin,
            statut_filter=statut_filter,
            include_historical=include_historical
        )
    
    def get_dashboard_data(
        self, 
        date_debut: str, 
        date_fin: str, 
        statut_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get dashboard data."""
        main_of_data = self.get_comprehensive_of_data(date_debut, date_fin, statut_filter)
        charge_data = self.get_charge_data()
        backlog_data = self.get_backlog_data()
        personnel_data = self.get_personnel_data()
        
        return {
            'main_of_data': main_of_data,
            'charge_data': charge_data,
            'backlog_data': backlog_data,
            'personnel_data': personnel_data
        }
