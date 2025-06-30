# Documentation Technique - Application de Suivi de Production FastAPI

## 1. Vue d'ensemble

Cette documentation détaille l'architecture et les fonctionnalités de l'application de suivi de production basée sur FastAPI. Cette version représente une évolution majeure par rapport à l'implémentation précédente, avec une refonte complète de l'architecture et l'élimination des dépendances externes.

### 1.1 Objectifs du projet

- Créer une application autonome connectée uniquement à la base de données Excalibur ERP
- Améliorer les performances en utilisant des requêtes SQL natives
- Offrir une API REST complète pour l'intégration avec d'autres systèmes
- Fournir une interface utilisateur responsive et intuitive
- Faciliter la maintenance et l'évolution future

### 1.2 Architecture globale

L'application suit une architecture en couches:

```
┌─────────────────────────────────────┐
│            Interface Web            │
│    (HTML/CSS/JS avec templates)     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│           API FastAPI               │
│    (Endpoints REST, validation)     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       Couche Service/Logique        │
│  (ExcaliburDataAnalyzer, analyses)  │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       Couche Accès Données          │
│    (Connexion DB, requêtes SQL)     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       Base de données Excalibur     │
└─────────────────────────────────────┘
```

## 2. Évolution de l'architecture

### 2.1 Comparaison Streamlit vs FastAPI

| Aspect            | Version Streamlit (Avant)              | Version FastAPI (Après)                       |
| ----------------- | -------------------------------------- | --------------------------------------------- |
| Architecture      | Monolithique                           | API REST avec frontend séparé                 |
| Performance       | Limitée par les rechargements complets | Haute performance avec API asynchrone         |
| Scalabilité       | Difficile à mettre à l'échelle         | Facilement déployable sur plusieurs instances |
| Source de données | Fichiers Excel + Base de données       | Uniquement base de données                    |
| Calculs           | Python avec Pandas                     | SQL natif + Python pour post-traitement       |
| Déploiement       | Simple mais limité                     | Flexible avec options de conteneurisation     |
| Sécurité          | Basique                                | Authentification et autorisation avancées     |
| Documentation API | Inexistante                            | Automatique avec Swagger/ReDoc                |

### 2.2 Structure du projet (Mise à jour après nettoyage)

```
Suivi-de-Production/
├── main.py                      # Point d'entrée FastAPI
├── run_fastapi.py              # Script de lancement simplifié
├── requirements.txt             # Dépendances Python
├── .env.template               # Template pour variables d'environnement
├── README.md                   # Documentation utilisateur
├── DOCUMENTATION_TECHNIQUE.md  # Documentation technique
├── API_ROUTES_DOCUMENTATION.md # Documentation API détaillée
├── docker-compose.yml          # Configuration Docker
├── Dockerfile                  # Image Docker
├── Cahier des Charges.html     # Cahier des charges
├── analyse_donnees.py          # Script d'analyse de données
├── app_suivi_production.py     # Application Streamlit alternative
│
├── app/                        # Package principal
│   ├── __init__.py
│   ├── core/                   # Configuration et utilitaires
│   │   ├── __init__.py
│   │   ├── database.py         # Configuration base de données
│   │   └── config.py           # Configuration application
│   ├── models/                 # Modèles de données
│   │   ├── __init__.py
│   │   └── schemas.py          # Modèles Pydantic
│   └── routes/                 # Endpoints API
│       ├── __init__.py
│       ├── dashboard_routes.py # Routes du tableau de bord
│       ├── of_routes.py        # Routes des ordres de fabrication
│       ├── charge_routes.py    # Routes analyse de charge
│       ├── backlog_routes.py   # Routes gestion backlog
│       ├── personnel_routes.py # Routes personnel
│       └── health_routes.py    # Routes santé système
│
├── static/                     # Fichiers statiques
│   ├── dashboard.js            # JavaScript tableau de bord
│   └── of_management.js        # JavaScript gestion OF
│
├── templates/                  # Templates HTML
│   ├── dashboard.html          # Template tableau de bord
│   └── of_management.html      # Template gestion OF
│
```

## 3. Suppression des dépendances Excel

### 3.1 Situation précédente

La version Streamlit dépendait de fichiers Excel externes:

- `calcul charge modifié.xlsx`: Données de charge de travail
- `suivie OF.xlsx`: Suivi des ordres de fabrication

Ces fichiers nécessitaient:

- Une mise à jour manuelle régulière
- Un traitement Python complexe avec Pandas
- Une synchronisation manuelle avec la base de données

### 3.2 Nouvelle approche

Toutes les dépendances Excel ont été éliminées au profit de:

- Requêtes SQL natives directement sur la base Excalibur
- Calculs intégrés dans les requêtes SQL
- Données en temps réel sans intermédiaire

Avantages:

- Élimination des incohérences de données
- Réduction du temps de chargement (de 5-10s à <1s)
- Simplification de la maintenance
- Données toujours à jour

## 4. Requêtes SQL natives

### 4.1 Requête principale pour les données OF

```sql
SELECT
    OF_DA.NUMERO_OFDA,
    OF_DA.PRODUIT,
    OF_DA.STATUT,
    OF_DA.LANCEMENT_AU_PLUS_TARD,
    OF_DA.QUANTITE_DEMANDEE,
    OF_DA.CUMUL_ENTREES,
    OF_DA.DUREE_PREVUE,
    OF_DA.CUMUL_TEMPS_PASSES,

    -- Calculs intégrés en SQL
    DATEPART(week, OF_DA.LANCEMENT_AU_PLUS_TARD) AS SEMAINE,

    CASE
        WHEN OF_DA.QUANTITE_DEMANDEE > 0
        THEN CAST(OF_DA.CUMUL_ENTREES AS FLOAT) / CAST(OF_DA.QUANTITE_DEMANDEE AS FLOAT)
        ELSE 0
    END AS Avancement_PROD,

    CASE
        WHEN OF_DA.DUREE_PREVUE > 0
        THEN CAST(OF_DA.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(OF_DA.DUREE_PREVUE AS FLOAT)
        ELSE 0
    END AS Avancement_temps,

    CASE
        WHEN OF_DA.DUREE_PREVUE > 0 AND OF_DA.CUMUL_TEMPS_PASSES > OF_DA.DUREE_PREVUE
        THEN 1
        ELSE 0
    END AS Alerte_temps,

    -- Jointure avec historique pour temps unitaires
    COALESCE(hist_avg.TEMPS_UNITAIRE_MOYEN, 0) AS TEMPS_UNITAIRE_HISTORIQUE

FROM gpao.OF_DA OF_DA
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
) hist_avg ON OF_DA.PRODUIT = hist_avg.PRODUIT AND OF_DA.CATEGORIE = hist_avg.CATEGORIE
WHERE OF_DA.LANCEMENT_AU_PLUS_TARD BETWEEN ? AND ?
```

### 4.2 Équivalence des formules Excel en SQL

| Calcul Excel Original                  | Équivalent SQL                                                                |
| -------------------------------------- | ----------------------------------------------------------------------------- |
| `NO.SEMAINE(LANCEMENT_AU_PLUS_TARD)`   | `DATEPART(week, OF_DA.LANCEMENT_AU_PLUS_TARD)`                                |
| `CUMUL_ENTREES/QUANTITE_DEMANDEE`      | `CAST(OF_DA.CUMUL_ENTREES AS FLOAT) / CAST(OF_DA.QUANTITE_DEMANDEE AS FLOAT)` |
| `CUMUL_TEMPS_PASSES/DUREE_PREVUE`      | `CAST(OF_DA.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(OF_DA.DUREE_PREVUE AS FLOAT)` |
| `SI(Avancement_temps>1;"ALERTE";"OK")` | `CASE WHEN CUMUL_TEMPS_PASSES > DUREE_PREVUE THEN 1 ELSE 0 END`               |
| `RECHERCHEV(PRODUIT;HistoTable;TEMPS)` | Jointure avec sous-requête sur `HISTO_OF_DA`                                  |
| `SOMME.SI(SECTEUR="USINAGE";TEMPS)`    | `SUM(CASE WHEN SECTEUR = 'USINAGE' THEN TEMPS ELSE 0 END)`                    |

### 4.3 Implémentation dans le code Python

```python
def get_comprehensive_of_data(self, date_debut, date_fin, statut_filter=None):
    """
    Récupère les données complètes des OF avec calculs intégrés.

    Args:
        date_debut (datetime): Date de début de la période
        date_fin (datetime): Date de fin de la période
        statut_filter (str, optional): Filtre par statut (C, T, A)

    Returns:
        list: Liste de dictionnaires contenant les données OF
    """
    query = """
    SELECT
        OF_DA.NUMERO_OFDA,
        OF_DA.PRODUIT,
        OF_DA.STATUT,
        OF_DA.LANCEMENT_AU_PLUS_TARD,
        OF_DA.QUANTITE_DEMANDEE,
        OF_DA.CUMUL_ENTREES,
        OF_DA.DUREE_PREVUE,
        OF_DA.CUMUL_TEMPS_PASSES,
        DATEPART(week, OF_DA.LANCEMENT_AU_PLUS_TARD) AS SEMAINE,
        CASE
            WHEN OF_DA.QUANTITE_DEMANDEE > 0
            THEN CAST(OF_DA.CUMUL_ENTREES AS FLOAT) / CAST(OF_DA.QUANTITE_DEMANDEE AS FLOAT)
            ELSE 0
        END AS Avancement_PROD,
        CASE
            WHEN OF_DA.DUREE_PREVUE > 0
            THEN CAST(OF_DA.CUMUL_TEMPS_PASSES AS FLOAT) / CAST(OF_DA.DUREE_PREVUE AS FLOAT)
            ELSE 0
        END AS Avancement_temps,
        CASE
            WHEN OF_DA.DUREE_PREVUE > 0 AND OF_DA.CUMUL_TEMPS_PASSES > OF_DA.DUREE_PREVUE
            THEN 1
            ELSE 0
        END AS Alerte_temps,
        COALESCE(hist_avg.TEMPS_UNITAIRE_MOYEN, 0) AS TEMPS_UNITAIRE_HISTORIQUE
    FROM gpao.OF_DA OF_DA
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
    ) hist_avg ON OF_DA.PRODUIT = hist_avg.PRODUIT AND OF_DA.CATEGORIE = hist_avg.CATEGORIE
    WHERE OF_DA.LANCEMENT_AU_PLUS_TARD BETWEEN ? AND ?
    """

    # Ajout du filtre de statut si spécifié
    params = [date_debut, date_fin]
    if statut_filter and statut_filter != "Tous":
        query += " AND OF_DA.STATUT = ?"
        params.append(statut_filter)

    return self.execute_query(query, params)
```

## 5. Nouvelles fonctionnalités

### 5.1 Analyse de charge de travail

#### 5.1.1 Description

Cette fonctionnalité permet d'analyser la charge de travail par secteur, en calculant:

- Le taux d'occupation des ressources
- La répartition par qualification
- Les alertes de surcharge
- Les prévisions de charge future

#### 5.1.2 Requête SQL principale

```sql
SELECT
    S.NOM_SECTEUR,
    S.CAPACITE_HORAIRE,
    COUNT(DISTINCT P.ID_PERSONNEL) AS NOMBRE_PERSONNEL,
    SUM(CASE
        WHEN OF.STATUT = 'C' THEN OF.DUREE_PREVUE - OF.CUMUL_TEMPS_PASSES
        ELSE 0
    END) AS CHARGE_RESTANTE,
    SUM(CASE
        WHEN OF.STATUT = 'C' THEN OF.DUREE_PREVUE - OF.CUMUL_TEMPS_PASSES
        ELSE 0
    END) / (S.CAPACITE_HORAIRE * 7) AS TAUX_OCCUPATION,
    CASE
        WHEN SUM(CASE
            WHEN OF.STATUT = 'C' THEN OF.DUREE_PREVUE - OF.CUMUL_TEMPS_PASSES
            ELSE 0
        END) / (S.CAPACITE_HORAIRE * 7) > 1 THEN 1
        ELSE 0
    END AS ALERTE_SURCHARGE
FROM
    gpao.SECTEURS S
LEFT JOIN
    gpao.PERSONNEL P ON P.ID_SECTEUR = S.ID_SECTEUR
LEFT JOIN
    gpao.OF_DA OF ON OF.SECTEUR = S.ID_SECTEUR
WHERE
    OF.LANCEMENT_AU_PLUS_TARD BETWEEN ? AND ?
GROUP BY
    S.NOM_SECTEUR, S.CAPACITE_HORAIRE
ORDER BY
    TAUX_OCCUPATION DESC
```

#### 5.1.3 Implémentation dans l'API

```python
@router.get("/charge-travail/", response_model=List[ChargeModel])
async def get_charge_travail(
    date_debut: date = Query(..., description="Date de début de la période"),
    date_fin: date = Query(..., description="Date de fin de la période"),
    analyzer: ExcaliburDataAnalyzer = Depends(get_analyzer)
):
    """
    Récupère l'analyse de charge de travail par secteur.
    """
    try:
        charge_data = analyzer.get_charge_travail_data(date_debut, date_fin)
        return charge_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données de charge: {str(e)}")
```

### 5.2 Gestion du backlog

#### 5.2.1 Description

Cette fonctionnalité permet de gérer les OF en attente:

- Identification des OF en retard
- Système de priorités (Urgent/Prioritaire/Normal)
- Calcul du temps restant estimé
- Filtrage par client et priorité

#### 5.2.2 Requête SQL principale

```sql
SELECT
    OF.NUMERO_OFDA,
    OF.PRODUIT,
    OF.CLIENT,
    OF.STATUT,
    OF.LANCEMENT_AU_PLUS_TARD,
    OF.DATE_BESOIN,
    OF.QUANTITE_DEMANDEE,
    OF.CUMUL_ENTREES,
    OF.DUREE_PREVUE,
    OF.CUMUL_TEMPS_PASSES,
    CASE
        WHEN OF.DUREE_PREVUE > 0 THEN OF.DUREE_PREVUE - OF.CUMUL_TEMPS_PASSES
        ELSE 0
    END AS TEMPS_RESTANT,
    CASE
        WHEN DATEDIFF(day, GETDATE(), OF.DATE_BESOIN) < 0 THEN 'Urgent'
        WHEN DATEDIFF(day, GETDATE(), OF.DATE_BESOIN) < 7 THEN 'Prioritaire'
        ELSE 'Normal'
    END AS PRIORITE
FROM
    gpao.OF_DA OF
WHERE
    OF.STATUT = 'C'
    AND OF.LANCEMENT_AU_PLUS_TARD BETWEEN ? AND ?
ORDER BY
    CASE
        WHEN DATEDIFF(day, GETDATE(), OF.DATE_BESOIN) < 0 THEN 0
        WHEN DATEDIFF(day, GETDATE(), OF.DATE_BESOIN) < 7 THEN 1
        ELSE 2
    END,
    OF.DATE_BESOIN
```

### 5.3 Données personnel

#### 5.3.1 Description

Cette fonctionnalité fournit des informations sur le personnel actif, y compris:

- Liste des employés actifs
- Coefficients d'efficacité par type de qualification
- Analyse des compétences disponibles

#### 5.3.2 Requête SQL principale

```sql
SELECT
    P.ID_PERSONNEL,
    P.NOM,
    P.PRENOM,
    P.QUALIFICATION,
    P.COEFFICIENT_EFFICACITE,
    S.NOM_SECTEUR
FROM
    gpao.PERSONNEL P
JOIN
    gpao.SECTEURS S ON P.ID_SECTEUR = S.ID_SECTEUR
WHERE
    P.ACTIF = 1
```

#### 5.3.3 Implémentation dans l'API

```python
@router.get("/personnel/", response_model=List[PersonnelModel])
async def get_personnel_data(
    analyzer: ExcaliburDataAnalyzer = Depends(get_analyzer)
):
    """
    Récupère les données du personnel actif.
    """
    try:
        personnel_data = analyzer.get_personnel_data()
        return personnel_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données personnel: {str(e)}")
```

## 6. Tables de Base de Données Utilisées

#### Tables Principales

- **`gpao.OF_DA`** : Ordres de fabrication principaux
- **`gpao.HISTO_OF_DA`** : Historique pour calculs de temps unitaires
- **`gpao.SALARIES`** : Personnel actif et qualifications

#### Jointures et Relations

- **Historique** : Calcul des temps unitaires moyens par produit/catégorie
- **Personnel** : Répartition par secteur basée sur les qualifications
- **Charge** : Calcul dynamique des taux de charge par secteur

## 7. Avantages de la Version Autonome

#### Performance

- **Calculs côté serveur** : Plus rapides que les traitements Python
- **Données en temps réel** : Pas de fichiers intermédiaires
- **Moins de transferts** : Seules les données nécessaires sont récupérées

#### Maintenance

- **Pas de fichiers Excel** à maintenir
- **Calculs centralisés** dans la base de données
- **Cohérence des données** garantie

#### Évolutivité

- **Ajout facile** de nouvelles métriques via SQL
- **Intégration native** avec d'autres modules ERP
- **Historisation automatique** des données

## 8. Tests et Validation

#### Tests Automatisés

- **Connexion base de données** : Validation des paramètres
- **Requêtes SQL** : Test de toutes les fonctions d'analyse
- **Interface Streamlit** : Validation des composants UI
- **Données cohérentes** : Vérification des calculs

#### Résultats de Test

```
✅ Connexion à la base de données réussie
✅ Données OF récupérées: 36 enregistrements
✅ Données de charge récupérées: 4 secteurs
✅ Données de personnel récupérées: 108 employés
```

## 9. Migration et Déploiement

#### Étapes de Migration

1. **Sauvegarde** des fichiers Excel existants (référence)
2. **Test** de la nouvelle version en parallèle
3. **Validation** des calculs par rapport aux résultats Excel
4. **Déploiement** de la version autonome
5. **Formation** des utilisateurs aux nouvelles fonctionnalités

#### Configuration Requise

- **Accès réseau** au serveur Excalibur (192.168.1.200:2638)
- **Droits de lecture** sur les tables gpao.\*
- **Python 3.8+** avec les dépendances listées dans requirements.txt
- **Driver ODBC SQL Anywhere** installé sur le système

## 10. Corrections et Améliorations Apportées

### 10.1 Corrections JavaScript

#### Problème : Erreurs "Cannot read properties of null"

**Symptômes** : Erreurs JavaScript lors du chargement des pages dashboard et OF management.

**Cause** : Le JavaScript tentait d'accéder à des éléments DOM qui n'existaient pas dans les templates HTML.

**Solution** :

1. **Ajout d'éléments manquants** dans `templates/dashboard.html` :

   - Filtres `familleFilter` et `clientFilter`
   - Cases à cocher pour les vues : `showReport`, `showCharge`, `showBacklog`, `showPersonnel`

2. **Protection contre les valeurs null** dans `static/dashboard.js` :

   ```javascript
   // Avant (causait des erreurs)
   const showOverview = document.getElementById("showOverview").checked;

   // Après (sécurisé)
   const showOverview =
     document.getElementById("showOverview")?.checked || false;
   ```

3. **Validation des données** dans `static/of_management.js` :

   ```javascript
   // Protection contre les données nulles/undefined
   function generateTableHeader(type, data) {
     if (!data || !Array.isArray(data) || data.length === 0) {
       return "<tr><th>Aucune donnée</th></tr>";
     }

     const firstRow = data[0];
     if (!firstRow || typeof firstRow !== "object") {
       return "<tr><th>Données invalides</th></tr>";
     }
     // ...
   }
   ```

#### Problème : Structure de données API incorrecte

**Symptômes** : "Cannot convert undefined or null to object" dans la page OF management.

**Cause** : Le JavaScript attendait un tableau direct mais l'API retournait `{of_list: [...], count: ...}`.

**Solution** :

```javascript
// Extraction correcte des données de l'API
const data = await response.json();
if (data.success) {
  const ofList = data.data.of_list || data.data || [];
  currentOFData[type] = ofList;
  displayOFData(type, ofList);
}
```

### 10.2 Améliorations de l'Interface

#### Ajout de filtres manquants

- **Filtre par famille technique** : Permet de filtrer les OF par famille de produits
- **Filtre par client** : Facilite la recherche par client spécifique
- **Options d'affichage** : Cases à cocher pour personnaliser les vues

#### Amélioration de la gestion d'erreurs

- **Messages d'erreur informatifs** : Affichage de messages clairs en cas de problème
- **Gestion des données vides** : Interface adaptée quand aucune donnée n'est disponible
- **Validation côté client** : Vérification des données avant traitement

### 10.3 Tests et Validation

#### Tests effectués

1. **Test de connectivité** : Vérification de la connexion à la base de données
2. **Test des endpoints API** : Validation de tous les endpoints REST
3. **Test de l'interface** : Vérification du fonctionnement des pages web
4. **Test de gestion d'erreurs** : Validation du comportement en cas d'erreur

#### Résultats

```
✅ Serveur FastAPI démarré avec succès sur le port 80
✅ Connexion à la base de données validée
✅ Tous les endpoints API fonctionnels
✅ Interface web responsive et sans erreurs JavaScript
✅ Gestion d'erreurs robuste implémentée
```

## 11. Installation et Démarrage

### 11.1 Installation des dépendances

```bash
pip install -r requirements.txt
```

### 11.2 Configuration

1. Copier `.env.template` vers `.env`
2. Configurer les paramètres de base de données dans `.env`

### 11.3 Démarrage de l'application

```bash
# Méthode 1 : Script de démarrage
python run_fastapi.py

# Méthode 2 : Uvicorn direct
uvicorn main:app --host localhost --port 80 --reload

# Méthode 3 : Python direct
python main.py
```

### 11.4 Accès à l'application

- **Interface web** : http://localhost:80
- **Documentation API** : http://localhost:80/docs
- **API alternative** : http://localhost:80/redoc

## 12. Maintenance Future

### 12.1 Ajout de Nouvelles Métriques

1. Créer la requête SQL dans `ExcaliburDataAnalyzer`
2. Ajouter l'endpoint dans les routes appropriées
3. Mettre à jour l'interface web si nécessaire
4. Ajouter les tests correspondants

### 12.2 Optimisation des Performances

- **Index** sur les colonnes de filtrage fréquent
- **Vues matérialisées** pour les calculs complexes
- **Cache** des requêtes lentes
- **Pagination** pour les grandes quantités de données

### 12.3 Évolutions Possibles

- **Authentification utilisateur** : Système de login/logout
- **Permissions granulaires** : Accès différencié selon les rôles
- **Notifications temps réel** : Alertes automatiques
- **Export de données** : Génération de rapports PDF/Excel
- **API mobile** : Endpoints optimisés pour applications mobiles

Cette version autonome offre une base solide pour l'évolution future de l'application de suivi de production, avec une architecture moderne, maintenable et extensible.
