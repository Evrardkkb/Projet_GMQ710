# ==========================
# IMPORTS
# ==========================
# Flask : framework web pour créer l’API et servir la page HTML
from flask import Flask, request, jsonify, render_template

# GeoPandas : manipulation de données géospatiales côté Python
import geopandas as gpd

# SQLAlchemy : connexion et exécution de requêtes SQL sur PostgreSQL/PostGIS
from sqlalchemy import create_engine, text

# json : conversion des objets GeoJSON
import json

# ==========================
# INITIALISATION DE L’APPLICATION FLASK
# ==========================
app = Flask(__name__)

# ==========================
# SYSTÈMES DE RÉFÉRENCE SPATIALE (CRS)
# ==========================
# CRS_DB : projection utilisée dans la base de données (mètres, adaptée aux calculs de distance)
CRS_DB = 32198   # MTM Québec

# CRS_WEB : projection utilisée pour l’affichage web (Leaflet fonctionne en WGS84)
CRS_WEB = 4326  # WGS84

# ==========================
# CONNEXION À LA BASE DE DONNÉES POSTGIS
# ==========================
# Connexion à PostgreSQL avec PostGIS activé
engine = create_engine(
    "postgresql://postgres:gmq719@localhost:5432/Projet_db"
)

# ==========================
# ROUTE : PAGE PRINCIPALE
# ==========================
# Affiche la page HTML contenant la carte Leaflet
@app.route("/")
def index():
    return render_template("index.html")

# ==========================
# ROUTES : DONNÉES STATIQUES
# ==========================
# Ces données sont chargées une seule fois au démarrage de la carte

@app.route("/data/arrets")
def get_arrets():
    # Récupération des arrêts de bus depuis la base de données
    sql = "SELECT id, geom FROM stops"
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)

    # Reprojection vers WGS84 pour l’affichage Leaflet
    return gdf.to_crs(CRS_WEB).to_json()

@app.route("/data/lignes")
def get_lignes():
    # Récupération des lignes de bus
    sql = "SELECT id, geom FROM lignes_bus"
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)

    # Conversion en GeoJSON pour le web
    return gdf.to_crs(CRS_WEB).to_json()

@app.route("/data/buffer_lignes")
def get_buffer_lignes():
    """
    Buffer des lignes de bus déjà calculé dans la base de données.
    Le buffer (200 m) est stocké dans la colonne buffer_200m
    afin d’éviter un recalcul coûteux côté serveur.
    """
    sql = """
        SELECT ST_Union(buffer_200m) AS geom
        FROM lignes_bus
    """
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)

    # Reprojection pour l’affichage web
    return gdf.to_crs(CRS_WEB).to_json()

# ==========================
# ROUTE : ANALYSE SPATIALE DYNAMIQUE
# ==========================
# Cette route est appelée lorsque l’utilisateur lance l’analyse
# avec une distance de buffer paramétrable

@app.route("/compute_buffers", methods=["POST"])
def compute_buffers():

    # Lecture des paramètres envoyés depuis le HTML (distance de buffer)
    data = request.get_json()
    buffer_dist = float(data.get("distance", 500))

    # ==========================
    # BUFFER DES ARRÊTS
    # ==========================
    # Création d’un buffer autour de chaque arrêt
    # puis fusion de tous les buffers en une seule géométrie
    sql_buffer = f"""
        SELECT ST_Union(ST_Buffer(geom, {buffer_dist})) AS geom
        FROM stops
    """
    gdf_buffer = gpd.read_postgis(
        sql_buffer, engine, geom_col="geom", crs=CRS_DB
    ).to_crs(CRS_WEB)

    # ==========================
    # ADRESSES NON DESSERVIES
    # ==========================
    # Sélection des adresses situées en dehors du buffer des arrêts
    sql_adresses = f"""
        SELECT a.id, a.geom
        FROM adresse a
        WHERE NOT EXISTS (
            SELECT 1
            FROM stops s
            WHERE ST_DWithin(a.geom, s.geom, {buffer_dist})
        )
    """
    gdf_adresses = gpd.read_postgis(
        sql_adresses, engine, geom_col="geom", crs=CRS_DB
    ).to_crs(CRS_WEB)

    # Extraction des coordonnées pour la heatmap Leaflet
    heat_points = [
        [geom.y, geom.x] for geom in gdf_adresses.geometry
    ]

    # ==========================
    # STATISTIQUES GLOBALES
    # ==========================
    # Calcul :
    # - nombre total d’adresses
    # - nombre d’arrêts
    # - nombre d’adresses desservies par au moins un arrêt
    sql_stats = text(f"""
        SELECT
            (SELECT COUNT(*) FROM adresse) AS nb_adresses,
            (SELECT COUNT(*) FROM stops) AS nb_arrets,
            (
                SELECT COUNT(DISTINCT a.id)
                FROM adresse a
                WHERE EXISTS (
                    SELECT 1
                    FROM stops s
                    WHERE ST_DWithin(a.geom, s.geom, {buffer_dist})
                )
            ) AS nb_desservies
    """)

    # Exécution de la requête SQL
    with engine.connect() as conn:
        stats = conn.execute(sql_stats).fetchone()

    # Calcul du nombre d’adresses non desservies
    nb_non_desservies = stats.nb_adresses - stats.nb_desservies

    # Calcul du pourcentage d’adresses desservies
    pct_desservies = round(
        (stats.nb_desservies / stats.nb_adresses) * 100
        if stats.nb_adresses > 0 else 0,
        1
    )

    # ==========================
    # RÉPONSE JSON ENVOYÉE AU FRONTEND
    # ==========================
    return jsonify({
        "buffer_arrets": json.loads(gdf_buffer.to_json()),
        "adresses_non_desservies": json.loads(gdf_adresses.to_json()),
        "heat_points": heat_points,
        "stats": {
            "nb_arrets": stats.nb_arrets,
            "nb_adresses": stats.nb_adresses,
            "nb_desservies": stats.nb_desservies,
            "nb_non_desservies": nb_non_desservies,
            "pct_desservies": pct_desservies
        }
    })

# ==========================
# LANCEMENT DE L’APPLICATION
# ==========================
if __name__ == "__main__":
    # Mode debug activé pour le développement
    app.run(debug=True)
