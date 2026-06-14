# Kirkland Thermography — Insulation Scores

Interactive map of **Kirkland (Montréal)** built from the **Ville de Montréal 2016
aerial surface thermography** (open data). Each building footprint is scored by the
surface temperature of its roof: **higher score = cooler surface = better insulation**;
dark red = hot roof = likely poor insulation.

Installable as a **PWA** (works offline once loaded; add to home screen on mobile).

## Live site
GitHub Pages: see the repository's Pages URL.

## How scoring works
1. The daytime colour GeoTIFF (georeferenced, EPSG:2950) is classified pixel-by-pixel
   into the 7 official legend classes (blue ≤26 °C → dark red ≥57 °C).
2. OpenStreetMap building footprints (Overpass) are rasterized in the raster's CRS.
3. For each footprint, the mean class score over its valid pixels gives a 0–100 score
   and an A–F grade. See [`score_buildings.py`](score_buildings.py).

Result: ~6,200 scored buildings in [`data/buildings_scored.geojson`](data/buildings_scored.geojson).

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install rasterio numpy pillow shapely requests   # only needed to re-run scoring
python3 -m http.server 8777
# open http://localhost:8777/index.html
```

## Data sources & credits
- Thermography: **Ville de Montréal**, *Thermographie aérienne de surface 2016* (open data).
- Buildings: **© OpenStreetMap** contributors.
- Basemap: **© CARTO**.
