from flask import Flask, render_template, request, jsonify
import geopandas as gpd
import json
import os

app = Flask(__name__)

# ==========================
# CONFIGURATION
# ==========================
DATA_DIR = "data"

CRS_PROJ = "EPSG:32198"   # Québec Lambert (mètres)
CRS_WEB = "EPSG:4326"    # Web (Leaflet)

BUFFER_LIGNE = 200  # mètres (proximité aux lignes de bus)

# ==========================
# CHARGEMENT DES DONNÉES
# ==========================
arrets = gpd.read_file(os.path.join(DATA_DIR, "Stop.geojson"))
adresses = gpd.read_file(os.path.join(DATA_DIR, "Adresse_-2526919596127878911.geojson"))
lignes = gpd.read_file(os.path.join(DATA_DIR, "lignes_bus_fusionnees.geojson"))

# Reprojection métrique (pour calculs spatiaux)
arrets_p = arrets.to_crs(CRS_PROJ)
adresses_p = adresses.to_crs(CRS_PROJ)
lignes_p = lignes.to_crs(CRS_PROJ)

# ==========================
# ROUTES DE BASE
# ==========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data/arrets")
def get_arrets():
    return arrets.to_crs(CRS_WEB).to_json()

@app.route("/data/lignes")
def get_lignes():
    return lignes.to_crs(CRS_WEB).to_json()

# ==========================
# ANALYSE SPATIALE
# ==========================
@app.route("/compute_buffers", methods=["POST"])
def compute_buffers():

    # Distance du buffer autour des arrêts (envoyée par le frontend)
    dist = float(request.json["distance"])

    # --------------------------------------------------
    # 1. BUFFER SUR LES ARRÊTS
    # --------------------------------------------------
    buffers_arrets = arrets_p.geometry.buffer(dist)

    buffer_arrets_union = buffers_arrets.union_all()

    buffer_arrets_gdf = gpd.GeoDataFrame(
        geometry=[buffer_arrets_union],
        crs=CRS_PROJ
    )

    # --------------------------------------------------
    # 2. BUFFER SUR LES LIGNES DE BUS
    # --------------------------------------------------
    buffer_lignes = lignes_p.geometry.buffer(BUFFER_LIGNE)

    buffer_lignes_union = buffer_lignes.union_all()

    buffer_lignes_gdf = gpd.GeoDataFrame(
        geometry=[buffer_lignes_union],
        crs=CRS_PROJ
    )

    # --------------------------------------------------
    # 3. ANALYSE DES ADRESSES (MULTIMODALE)
    # --------------------------------------------------
    adresses_local = adresses_p.copy()

    # desservie par un arrêt
    adresses_local["desservie_arret"] = adresses_local.geometry.intersects(
        buffer_arrets_union
    )

    # proche d’une ligne de bus
    adresses_local["proche_ligne"] = adresses_local.geometry.intersects(
        buffer_lignes_union
    )

    # Catégories finales
    adresses_desservies = adresses_local[
        adresses_local["desservie_arret"]
    ]

    adresses_proche_ligne = adresses_local[
        (~adresses_local["desservie_arret"]) &
        (adresses_local["proche_ligne"])
    ]

    adresses_non_desservies = adresses_local[
        (~adresses_local["desservie_arret"]) &
        (~adresses_local["proche_ligne"])
    ]

    # --------------------------------------------------
    # 4. STATISTIQUES
    # --------------------------------------------------
    stats = {
        "nb_arrets": int(len(arrets)),
        "nb_adresses": int(len(adresses)),
        "nb_desservies_arret": int(len(adresses_desservies)),
        "nb_proche_ligne": int(len(adresses_proche_ligne)),
        "nb_non_desservies": int(len(adresses_non_desservies)),
        "pct_desservies": round(
            (len(adresses_desservies) / len(adresses)) * 100, 1
        ),
        "surface_buffer_arrets_m2": int(
            buffer_arrets_gdf.geometry.area.iloc[0]
        )
    }

    # --------------------------------------------------
    # 5. RÉPONSE JSON POUR LE FRONTEND
    # --------------------------------------------------
    return jsonify({
        "buffer_arrets": json.loads(
            buffer_arrets_gdf.to_crs(CRS_WEB).to_json()
        ),
        "buffer_lignes": json.loads(
            buffer_lignes_gdf.to_crs(CRS_WEB).to_json()
        ),
        "adresses_proche_ligne": json.loads(
            adresses_proche_ligne.to_crs(CRS_WEB).to_json()
        ),
        "adresses_non_desservies": json.loads(
            adresses_non_desservies.to_crs(CRS_WEB).to_json()
        ),
        "stats": stats
    })

# ==========================
# LANCEMENT
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
