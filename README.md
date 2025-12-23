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
| Ville de Sherbrooke – Zonage habitation / activités | Vecteur  | Shapefile / GeoJSON | Répartition des zones urbaines pour analyser la desserte du réseau   https://donneesouvertes-sherbrooke.opendata.arcgis.com/search?q=adresse                     |



## Approche méthodologique

L’analyse est réalisée en Python sous Visual Studio Code (VS Code). Elle comprend :

1. **Chargement et prétraitement des données**

   * Lecture des données géospatiales (Shapefile / GeoJSON) via GeoPandas
   * Harmonisation des projections et qualité des géométries

2. **Analyse spatiale**

   * Génération de zones tampons (buffers) autour des arrêts de bus
   * Intersection avec les zones urbaines
   * Évaluation de la couverture du réseau de transport

3. **Visualisation**

   * Création d’une **carte interactive Folium** montrant les zones bien ou mal desservies

4. **Sorties analytiques**

   * Calcul d’indicateurs (population couverte, superficie desservie, etc.)
   * Production d’un **rapport HTML avec graphiques**

## Outils et technologies

### Langages

* Python
* HTML

### Bibliothèques et logiciels

* GeoPandas
* Shapely
* Folium
* Flask

## Membre du groupe

* **Toudasida Evrard Konkobo**
* **Abdoul Rahim Yanogo**

