from flask import Flask, request, jsonify, render_template
import geopandas as gpd
from sqlalchemy import create_engine, text
import json

app = Flask(__name__)

# ==========================
# CRS
# ==========================
CRS_DB = 32198   # MTM Québec
CRS_WEB = 4326  # WGS84 (Leaflet)

# ==========================
# DATABASE
# ==========================
engine = create_engine(
    "postgresql://postgres:gmq719@localhost:5432/Projet_db"
)

# ==========================
# PAGE PRINCIPALE
# ==========================
@app.route("/")
def index():
    return render_template("index.html")

# ==========================
# DONNÉES STATIQUES
# ==========================
@app.route("/data/arrets")
def get_arrets():
    sql = "SELECT id, geom FROM stops"
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)
    return gdf.to_crs(CRS_WEB).to_json()

@app.route("/data/lignes")
def get_lignes():
    sql = "SELECT id, geom FROM lignes_bus"
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)
    return gdf.to_crs(CRS_WEB).to_json()

@app.route("/data/buffer_lignes")
def get_buffer_lignes():
    """
    Buffer lignes déjà calculé en base (buffer_200m)
    """
    sql = """
        SELECT ST_Union(buffer_200m) AS geom
        FROM lignes_bus
    """
    gdf = gpd.read_postgis(sql, engine, geom_col="geom", crs=CRS_DB)
    return gdf.to_crs(CRS_WEB).to_json()

# ==========================
# ANALYSE DYNAMIQUE
# ==========================
@app.route("/compute_buffers", methods=["POST"])
def compute_buffers():

    data = request.get_json()
    buffer_dist = float(data.get("distance", 500))

    # ==========================
    # Buffer arrêts fusionné
    # ==========================
    sql_buffer = f"""
        SELECT ST_Union(ST_Buffer(geom, {buffer_dist})) AS geom
        FROM stops
    """
    gdf_buffer = gpd.read_postgis(
        sql_buffer, engine, geom_col="geom", crs=CRS_DB
    ).to_crs(CRS_WEB)

    # ==========================
    # Adresses non desservies
    # ==========================
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

    heat_points = [
        [geom.y, geom.x] for geom in gdf_adresses.geometry
    ]

    # ==========================
    # STATISTIQUES
    # ==========================
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

    with engine.connect() as conn:
        stats = conn.execute(sql_stats).fetchone()

    nb_non_desservies = stats.nb_adresses - stats.nb_desservies

    pct_desservies = round(
        (stats.nb_desservies / stats.nb_adresses) * 100
        if stats.nb_adresses > 0 else 0,
        1
    )

    # ==========================
    # RÉPONSE JSON
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
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
