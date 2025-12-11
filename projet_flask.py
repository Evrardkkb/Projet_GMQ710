# app.py ggg
from flask import Flask, render_template, request, jsonify, Response
import geopandas as gpd
import os, json
from shapely.ops import unary_union
from io import BytesIO
import base64
import matplotlib.pyplot as plt

app = Flask(__name__)

DATA_DIR = os.path.join(app.root_path, "data")

def find_file(key_words):
    """Retourne le chemin du premier fichier dans data/ qui contient un des mots clés (insensible à la casse)."""
    if not os.path.isdir(DATA_DIR):
        return None
    for f in os.listdir(DATA_DIR):
        if not f.lower().endswith((".geojson", ".json")):
            continue
        low = f.lower()
        for kw in key_words:
            if kw in low:
                return os.path.join(DATA_DIR, f)
    return None

def list_geojson_files():
    if not os.path.isdir(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR) if f.lower().endswith((".geojson", ".json"))]

# Trouver automatiquement les fichiers
stops_file = find_file(["stop", "arret", "arrets", "stops"])
lines_file = find_file(["ligne", "lines", "route", "lignes", "routes"])
zones_file = find_file(["adresse", "zone", "zones", "address"])

print("=== DEBUG: contenu du dossier data/ ===")
for f in list_geojson_files():
    print(" -", f)
print("=======================================")

if stops_file is None:
    print("⚠️ Aucun fichier d'arrêts trouvé automatiquement (recherché: stop, arret, stops).")
else:
    print("Fichier arrets détecté :", os.path.basename(stops_file))

if lines_file is None:
    print("⚠️ Aucun fichier de lignes trouvé automatiquement (recherché: ligne, lines, route).")
else:
    print("Fichier lignes détecté :", os.path.basename(lines_file))

if zones_file is None:
    print("⚠️ Aucun fichier de zones/adresse trouvé automatiquement (recherché: adresse, zone).")
else:
    print("Fichier zones détecté :", os.path.basename(zones_file))

# Charger (si trouvés) — on ne plante pas si un fichier manque, on garde None
def safe_read(path):
    if path is None:
        return None
    try:
        g = gpd.read_file(path)
        print(f"[OK] Chargé: {os.path.basename(path)}  — {len(g)} entités")
        return g
    except Exception as e:
        print(f"[ERREUR] Échec lecture {path} :", e)
        return None

stops_gdf = safe_read(stops_file)
lines_gdf = safe_read(lines_file)
zones_gdf = safe_read(zones_file)

# If stops exist, ensure a metric CRS for buffers (EPSG:3857 used here)
PROJ_CRS = "EPSG:3857"
if stops_gdf is not None:
    try:
        stops_proj = stops_gdf.to_crs(PROJ_CRS)
    except Exception:
        stops_proj = stops_gdf
else:
    stops_proj = None

if lines_gdf is not None:
    try:
        lines_proj = lines_gdf.to_crs(PROJ_CRS)
    except Exception:
        lines_proj = lines_gdf
else:
    lines_proj = None

if zones_gdf is not None:
    try:
        zones_proj = zones_gdf.to_crs(PROJ_CRS)
    except Exception:
        zones_proj = zones_gdf
else:
    zones_proj = None

# util
def gdf_to_response(gdf):
    if gdf is None:
        return Response(json.dumps({"type":"FeatureCollection","features":[]}), mimetype="application/json")
    return Response(gdf.to_crs("EPSG:4326").to_json(), mimetype="application/json")

@app.route("/")
def index():
    return render_template("index.html")

# Endpoints data
@app.route("/data/arrets")
def data_arrets():
    return gdf_to_response(stops_gdf)

@app.route("/data/lignes")
def data_lignes():
    return gdf_to_response(lines_gdf)

@app.route("/data/zones")
def data_zones():
    return gdf_to_response(zones_gdf)

# Debug route: liste les fichiers du dossier data
@app.route("/debug_files")
def debug_files():
    files = list_geojson_files()
    return jsonify({"files": files, "detected": {
        "stops": os.path.basename(stops_file) if stops_file else None,
        "lines": os.path.basename(lines_file) if lines_file else None,
        "zones": os.path.basename(zones_file) if zones_file else None
    }})

# compute buffer route (safe if stops missing)
@app.route("/compute_buffer", methods=["POST"])
def compute_buffer():
    if stops_proj is None:
        return jsonify({"error":"Aucun fichier d'arrêts chargé. Vérifie data/."}), 400
    # buffer en mètres
    try:
        buf = float(request.form.get("buffer", request.json.get("buffer", 400)))
    except:
        buf = 400.0

    arrets = stops_proj.copy()
    arrets["buffer"] = arrets.geometry.buffer(buf)
    buffer_union = unary_union(arrets["buffer"])
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_union], crs=stops_proj.crs)

    # zones desservies
    if zones_proj is not None:
        zones = zones_proj.copy()
        zones["desservi"] = zones.intersects(buffer_union)
        zones_serv = zones[zones["desservi"] == True]
        zones_nserv = zones[zones["desservi"] == False]
    else:
        zones_serv = None
        zones_nserv = None

    # lignes intersectées
    if lines_proj is not None:
        lignes = lines_proj.copy()
        lignes["intersect"] = lignes.intersects(buffer_union)
        longueur_lignes = float(lignes[lignes["intersect"]].length.sum()/1000.0)
    else:
        longueur_lignes = None

    nb_arrets_couverts = int(arrets[arrets.intersects(buffer_union)].shape[0])

    # population si champ POP existant (dans zones)
    pop_cov = None
    if zones_serv is not None and "POP" in zones_serv.columns:
        try:
            pop_cov = int(zones_serv["POP"].sum())
        except:
            pop_cov = None

    superficie_km2 = None
    if zones_serv is not None:
        superficie_km2 = float(zones_serv.area.sum()/1e6)

    # Graphique
    vals = [ (zones_serv.shape[0] if zones_serv is not None else 0),
             (zones_nserv.shape[0] if zones_nserv is not None else 0) ]
    labels = ["Desservies", "Non desservies"]
    fig = plt.figure(figsize=(3.5,3.5))
    plt.pie(vals, labels=labels, autopct="%1.0f%%", colors=["#2e7d32","#c62828"])
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png", dpi=100)
    plt.close(fig)
    bio.seek(0)
    img_b64 = base64.b64encode(bio.read()).decode()

    resp = {
        "buffer": json.loads(buffer_gdf.to_crs("EPSG:4326").to_json()),
        "zones_serv": json.loads(zones_serv.to_crs("EPSG:4326").to_json()) if zones_serv is not None else {"type":"FeatureCollection","features":[]},
        "zones_nserv": json.loads(zones_nserv.to_crs("EPSG:4326").to_json()) if zones_nserv is not None else {"type":"FeatureCollection","features":[]},
        "arrets": json.loads(arrets.to_crs("EPSG:4326").to_json()),
        "lignes": json.loads(lines_proj.to_crs("EPSG:4326").to_json()) if lines_proj is not None else {"type":"FeatureCollection","features":[]},
        "stats": {
            "arrets_couverts": nb_arrets_couverts,
            "population_couverte": pop_cov,
            "superficie_km2": round(superficie_km2,3) if superficie_km2 is not None else None,
            "longueur_lignes_km": round(longueur_lignes,3) if longueur_lignes is not None else None
        },
        "graph_png_base64": img_b64
    }
    return jsonify(resp)

if __name__ == "__main__":
    app.run(debug=True)
