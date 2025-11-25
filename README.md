# Projet_GMQ710
 Cartographie interactive de l’accessibilité aux transports urbains à Sherbrooke

## Objectif du projet

Ce projet vise à analyser la répartition spatiale de l’accessibilité aux transports publics (bus, métro, etc.) dans la ville de Sherbrooke.
En utilisant GeoPandas, Shapely et Folium, l’étude croise les données de transport (réseau et arrêts) avec les zones d’habitation ou d’activités, afin de produire une carte interactive affichant les zones bien desservies ou isolées.

Une composante avancée prévoit également :

* Le calcul d’indicateurs d’accessibilité (ex. : proportion de bâtiments ou population couverts)
* La génération automatique de graphiques
* Un rapport synthétique exporté en **HTML**

| **Source**                                          | **Type** | **Format**          | **Utilité**                                                                               |
| --------------------------------------------------- | -------- | ------------------- | ----------------------------------------------------------------------------------------- |
| Données Québec – GTFS                               | Vecteur  | Shapefile / GeoJSON | Informations sur les lignes et réseaux d’autobus pour évaluer la couverture du territoire |
| Données Québec – Arrêts de bus                      | Vecteur  | Shapefile / GeoJSON | Localisation des arrêts utilisée pour créer les zones de desserte (buffers)               |
| Ville de Sherbrooke – Zonage habitation / activités | Vecteur  | Shapefile / GeoJSON | Répartition des zones urbaines pour analyser la desserte du réseau                        |
| Ville de Sherbrooke – Limite administrative         | Vecteur  | Shapefile / GeoJSON | Délimitation précise de la zone d’étude                                                   |


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

