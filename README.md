# Projet_GMQ710
 Cartographie interactive de l’accessibilité aux transports urbains à Sherbrooke

## Objectif du projet

Ce projet vise à analyser l’accessibilité aux transports publics (réseau d’autobus) dans la ville de Sherbrooke à l’aide d’une approche géospatiale intégrée.
L’objectif est d’identifier les zones urbaines desservies et non desservies par le réseau de transport collectif de la Société de Transport de Sherbrooke(STS), à partir d’analyses spatiales et de leur visualisation dans une application cartographique interactive.

Le projet repose sur une approche hybride combinant une base de données spatiale (PostGIS) et Python, afin d’assurer à la fois de bonnes performances pour les calculs spatiaux et une grande flexibilité pour la visualisation et l’interaction utilisateur.

| **Source**                                          | **Type** | **Format**          | **Utilité**                                                                               |
| --------------------------------------------------- | -------- | ------------------- | ----------------------------------------------------------------------------------------- |
| Données Québec – GTFS                               | Vecteur  | Shapefile / GeoJSON | Informations sur les lignes et réseaux d’autobus pour évaluer la couverture du territoire https://www.donneesquebec.ca/recherche/dataset/transport-sts |
| Données Québec – Arrêts de bus                      | Vecteur  | Shapefile / GeoJSON | Localisation des arrêts utilisée pour créer les zones de desserte (buffers) https://www.donneesquebec.ca/recherche/dataset/transport-sts              |
| Ville de Sherbrooke – Zonage habitation / activités | Vecteur  | Shapefile / GeoJSON | Répartition des zones urbaines pour analyser la desserte du réseau       https://donneesouvertes-sherbrooke.opendata.arcgis.com/search?q=adresse                     |

Toutes les données géospatiales sont intégrées et stockées dans une base de données PostgreSQL/PostGIS.

## Approche méthodologique

L’analyse est réalisée à l’aide d’une architecture hybride PostGIS et Python sous pgAdmin et Vs code, structurée comme suit :

1. **Base de données spatiale (PostGIS) avec pgAdmin**
   
La base de données constitue le cœur du système d’analyse spatiale et permet
   * Le stockage des couches géographiques (lignes de bus, arrêts, adresses)
   * La gestion des systèmes de coordonnées
   * La réalisation des opérations spatiales directement en SQL, notamment :
       * création de zones tampons (ST_Buffer)
       * fusion de géométries (ST_Union)
       * calculs de proximité (ST_DWithin)
       * requêtes spatiales optimisées

Cette approche permet de réduire considérablement les temps de calcul pour les opérations géospatiales complexes.


2. **Traitement et orchestration avec Python**

Python est utilisé comme couche de contrôle et de traitement applicatif.

  * Communication avec la base de données via SQLAlchemy
  * Exécution de requêtes spatiales SQL
  * Récupération et conversion des résultats avec GeoPandas
  * Calcul et formatage des indicateurs statistiques
  * Exposition des résultats via une API développée avec Flask

3. **Visualisation cartographique interactive**

Notre application web permet d’explorer les résultats de manière interactive.

  * Affichage des couches spatiales (lignes, arrêts, buffers, et heatmap)
  * Visualisation des zones non desservies
  * Génération dynamique de statistiques d’accessibilité
  * Interaction utilisateur (paramètres de distance sur le buffer des arrets, activation/désactivation des couches)

La cartographie repose sur Leaflet et des bibliothèques JavaScript associées notamment heatmap et clustering.

## Résultats produits

  * Carte interactive de l’accessibilité aux transports urbains
  * Zones tampons de desserte des lignes et des arrêts
  * Identification des adresses non desservies
  * Statistiques synthétiques :
     * nombre total d’arrêts
     * nombre total d’adresses
     * nombre et pourcentage d’adresses desservies
     * nombre d’adresses non desservies
       
## Outils et technologies

### Langages

* Python
* SQL(PostGIS)
* HTML/JavaScript

### Bibliothèques et logiciels

* PostgreSQL / PostGIS
* GeoPandas
* SQLAlchemy
* Flask
* Leaflet

## Membre du groupe

* **Toudasida Evrard Konkobo**
* **Abdoul Rahim Yanogo**
