# Application de Suivi du Temps de Production - Excalibur ERP (FastAPI)

## Description

Cette application FastAPI moderne permet de suivre et analyser les temps de production en se connectant directement à la base de données Excalibur ERP. Elle offre une API REST complète et une interface web responsive pour visualiser les ordres de fabrication (OF), leurs avancements et identifier les alertes de dépassement de temps.

**🚀 Version FastAPI** : Application refactorisée de Streamlit vers FastAPI pour une meilleure scalabilité, performance et facilité de déploiement. Fonctionne entièrement avec la base de données Excalibur ERP, sans dépendance aux fichiers Excel externes.

## Fonctionnalités

### 📊 Tableau de Bord Principal

- **Métriques en temps réel** : Total OF, OF en cours, avancement moyen production, alertes temps
- **Sélection d'intervalle** : Filtrage par dates de début et fin

### 📋 Gestion des Données

- **Affichage tabulaire** des ordres de fabrication
- **Filtres supplémentaires** : Par produit, par alerte, nombre d'enregistrements
- **Export CSV** des données filtrées
- **Calculs SQL natifs** :
  - Avancement Production = Cumul Entrées / Quantité Demandée
  - Avancement Temps = Cumul Temps Passés / Durée Prévue
  - Alertes automatiques si Avancement Temps > 100%
  - Efficacité = Temps Prévu / Temps Passé
  - Temps unitaires basés sur l'historique

### 📈 Analyses Graphiques

- **Vue d'ensemble** : Répartition des statuts et distribution des avancements
- **Scatter Plot** : Avancement Production vs Temps avec ligne de référence
- **Analyse des alertes** : Identification des OF en retard
- **Top 10 des retards** : Visualisation des OF les plus en retard

### 📄 Rapports

- **Rapport de synthèse** automatique avec statistiques clés
- **Export du rapport** en format texte
- **Identification des OF critiques**
- **Analyse par famille technique**
- **Recommandations automatiques**

### ⚙️ Analyse de Charge de Travail (Nouveau)

- **Calcul dynamique** de la charge par secteur
- **Taux de charge** en temps réel
- **Répartition des ressources** par qualification
- **Visualisation graphique** des charges

### 📋 Gestion du Backlog (Nouveau)

- **Identification automatique** des OF en retard
- **Système de priorités** (Urgent/Prioritaire/Normal)
- **Calcul du temps restant** estimé
- **Filtrage par client** et priorité

### 👥 Gestion du Personnel (Nouveau)

- **Liste du personnel actif** avec qualifications
- **Coefficients d'efficacité** par qualification
- **Analyse des compétences** disponibles
- **Répartition des qualifications**

## Installation et Lancement

### Méthode 1 : Script automatique (Recommandé)

```bash
python run_fastapi.py
```

### Méthode 2 : Installation manuelle

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application FastAPI
python main.py
# ou
uvicorn main:app --host 0.0.0.0 --port 80 --reload
```

### Méthode 3 : Utilisation directe d'uvicorn

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement avec uvicorn
uvicorn main:app --reload
```

## Accès à l'Application

Une fois lancée, l'application est accessible via :

- **Dashboard Principal** : http://0.0.0.0:80
- **Documentation API (Swagger)** : http://0.0.0.0:80/docs
- **Documentation Alternative (ReDoc)** : http://0.0.0.0:80/redoc

## 🛠️ Utilitaires de Maintenance

### Monitoring de l'Application

```bash
# Vérification ponctuelle de l'état
python monitor_app.py

# Monitoring continu (toutes les 60 secondes)
python monitor_app.py --continuous

# Monitoring avec intervalle personnalisé
python monitor_app.py --continuous --interval 30

# Monitoring d'une instance distante
python monitor_app.py --url http://production-server:80
```

### Sauvegarde de Configuration

```bash
# Créer une sauvegarde complète
python backup_config.py

# Lister les sauvegardes disponibles
python backup_config.py --list

# Nettoyer les anciennes sauvegardes (garder les 3 plus récentes)
python backup_config.py --cleanup 3
```

### Déploiement en Production

Consultez le fichier `DEPLOYMENT_CHECKLIST.md` pour une liste complète des étapes de déploiement et de configuration en production.

- **Health Check** : http://0.0.0.0:80/api/health

## Configuration

### Base de Données (Seule source de données)

L'application se connecte automatiquement à la base de données Excalibur avec les paramètres :

- **Serveur** : 192.168.1.200:2638
- **Base** : excalib
- **Utilisateur** : gpao
- **Mot de passe** : flat

### Tables Utilisées

L'application accède directement aux tables suivantes :

- **OF_DA** : Ordres de fabrication principaux
- **HISTO_OF_DA** : Historique des OF pour calculs de temps unitaires
- **SALARIES** : Personnel actif et qualifications
- **Autres tables** : Selon les besoins de jointure

## Structure des Données

### Colonnes Principales

- **NUMERO_OFDA** : Numéro de l'ordre de fabrication
- **PRODUIT** : Référence du produit
- **STATUT** : Statut de l'OF (C/T/A)
- **LANCEMENT_AU_PLUS_TARD** : Date de lancement prévue
- **QUANTITE_DEMANDEE** : Quantité à produire
- **CUMUL_ENTREES** : Quantité déjà produite
- **DUREE_PREVUE** : Temps de production prévu
- **CUMUL_TEMPS_PASSES** : Temps déjà passé

### Calculs Automatiques

- **Avancement_PROD** : Pourcentage de production réalisée
- **Avancement_temps** : Pourcentage de temps consommé
- **Alerte_temps** : Indicateur de dépassement (True/False)
- **SEMAINE** : Semaine de lancement calculée automatiquement

## Utilisation

### 1. Sélection des Critères

- Choisir les dates de début et fin dans la barre latérale
- Sélectionner le statut des OF à analyser
- Cliquer sur "🔍 Rechercher"

### 2. Analyse des Données

- **Onglet Données** : Consulter le tableau détaillé avec filtres
- **Onglet Graphiques** : Visualiser les analyses graphiques
- **Onglet Rapport** : Lire le rapport de synthèse

### 3. Export des Résultats

- **CSV** : Télécharger les données filtrées
- **Rapport** : Télécharger le rapport de synthèse

## Indicateurs Clés

### 🟢 Statuts Normaux

- Avancement temps ≤ 100%
- Production en cours normale

### 🔴 Alertes

- ⚠️ Avancement temps > 100% (dépassement)
- OF en retard de production

### 📊 Métriques de Performance

- **Taux de respect des délais** : % OF sans dépassement temps
- **Efficacité production** : Ratio avancement production/temps
- **Charge de travail** : Répartition des OF par statut

## Architecture FastAPI

### Structure du Projet

```
├── main.py                 # Application FastAPI principale
├── analyse_donnees.py      # Module d'analyse des données (inchangé)
├── templates/
│   └── dashboard.html      # Template HTML du dashboard
├── static/
│   └── dashboard.js        # JavaScript pour l'interface
├── requirements.txt        # Dépendances Python
├── run_fastapi.py         # Script de lancement
└── README.md              # Documentation
```

### API Endpoints

- **GET /** : Dashboard principal (HTML)
- **GET /api/dashboard-data** : Données complètes du dashboard
- **GET /api/of-data** : Données des ordres de fabrication avec filtres
- **GET /api/report** : Génération de rapport textuel
- **GET /api/export/csv** : Export des données en CSV
- **GET /api/filters/options** : Options disponibles pour les filtres
- **GET /api/stats/summary** : Statistiques de synthèse
- **GET /api/health** : Vérification de l'état de l'application

## Dépendances

- **FastAPI** : Framework web moderne et rapide
- **Uvicorn** : Serveur ASGI pour FastAPI
- **Jinja2** : Moteur de templates
- **Pandas** : Manipulation des données
- **Plotly** : Graphiques interactifs (côté client)
- **PyODBC** : Connexion base de données
- **Python-dotenv** : Gestion des variables d'environnement

## Évolutions Futures

- Alertes en temps réel
- Notifications par email
- Intégration avec d'autres modules ERP
- Analyses prédictives
- Dashboard mobile
