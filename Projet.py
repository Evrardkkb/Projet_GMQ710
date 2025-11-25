import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from shapely.ops import unary_union

# -----------------------------
# 1. Chargement des données
# -----------------------------
f_arrets = "Stop.geojson"
f_lignes = "lignes_bus_fusionnees.geojson"
f_adresse = "Adresse_-2526919596127878911.geojson"

# Chargement des fichiers sans set_crs()
arrets = gpd.read_file(f_arrets)
lignes = gpd.read_file(f_lignes)
zones  = gpd.read_file(f_adresse)

# -----------------------------
# 2. Reprojection
# -----------------------------
target_crs = "EPSG:32198"

arrets = arrets.to_crs(target_crs)
lignes = lignes.to_crs(target_crs)
zones  = zones.to_crs(target_crs)

# -----------------------------
# 3. Analyses spatiales
# -----------------------------
buffer_distance = 400  # en mètres
arrets["buffer"] = arrets.geometry.buffer(buffer_distance)
buffers = gpd.GeoDataFrame(geometry=arrets["buffer"], crs=target_crs)

buffer_union = unary_union(buffers.geometry)
buffer_union = gpd.GeoDataFrame(geometry=[buffer_union], crs=target_crs)

zones["desservi"] = zones.intersects(buffer_union.geometry[0])

zones_serv = zones[zones["desservi"] == True]
zones_non_serv = zones[zones["desservi"] == False]

# REMARQUE :
# zones_serv et zones_non_serv NE SONT PAS ajoutées sur la carte.
# Elles servent uniquement à l’analyse.

# -----------------------------
# 4. Carte Folium
# -----------------------------
carte = folium.Map(location=[45.4, -71.9], zoom_start=12)

# --- Clustering des arrêts
marker_cluster = MarkerCluster(name="Arrêts de bus").add_to(carte)

for _, row in arrets.to_crs("EPSG:4326").iterrows():
    folium.Marker(
        location=[row.geometry.y, row.geometry.x]
    ).add_to(marker_cluster)

# -----------------------------
# 5. Lignes de bus (chargées dynamiquement)
# -----------------------------
lignes_layer = folium.GeoJson(
    lignes.to_crs("EPSG:4326"),
    name="Réseau de bus",
    style_function=lambda x: {"color": "blue", "weight": 2}
)

carte.add_child(lignes_layer)

# -----------------------------
# 6. Lazy loading : afficher lignes seulement si zoom >= 13
# -----------------------------
initial_js = f"""
<script>
function toggleLayersByZoom() {{
    var map = window.map;
    var zoom = map.getZoom();

    var minZoomToShow = 13;
    var layer = {lignes_layer.get_name()};

    if (zoom >= minZoomToShow) {{
        if (!map.hasLayer(layer)) {{
            map.addLayer(layer);
        }}
    }} else {{
        if (map.hasLayer(layer)) {{
            map.removeLayer(layer);
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', function () {{
    var map = window.map;
    toggleLayersByZoom();

    map.on('zoomend', function() {{
        toggleLayersByZoom();
    }});
}});
</script>
"""

carte.get_root().html.add_child(folium.Element(initial_js))

# -----------------------------
# 7. Contrôle des couches
# -----------------------------
folium.LayerControl().add_to(carte)

# -----------------------------
# 8. Export
# -----------------------------
carte.save("carte_avec_clustering_et_lazyloading.html")
print("Carte générée : lignes chargées uniquement lorsque zoom >= 13, adresses non affichées.")
