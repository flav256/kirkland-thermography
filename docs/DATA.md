# Data sources & rebuild guide

## Sources
- **Thermography:** Ville de Montréal — *Thermographie aérienne de surface 2016*
  (open data). Georeferenced colour GeoTIFF(s), one per area, classified into the
  7-colour legend (blue ≤26 °C → dark red ≥57 °C). Day and night variants exist.
  Find it on the Montréal open-data portal (donneesquebec / données ouvertes
  Montréal) by searching "thermographie aérienne de surface".
- **Buildings:** OpenStreetMap footprints via Overpass API.
- **Basemap:** © CARTO Voyager raster tiles.

> The source GeoTIFFs are **not** committed (large, redistributable from the
> portal). Only the derived `data/overlay_*.png` and `buildings_scored.geojson`
> are in the repo.

## Get the OSM footprints
Overpass query (bbox = Kirkland; widen for expansion). Use **`out geom;`** so each
way/relation carries its geometry:
```
[out:json][timeout:60];
(
  way["building"](45.434,-73.918,45.471,-73.828);
  relation["building"]["type"="multipolygon"](45.434,-73.918,45.471,-73.828);
);
out geom;
```
Save the response to `data/osm_buildings.json` (gitignored).

## Rebuild the scores
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install rasterio numpy pillow shapely requests

# single tile (default Kirkland day raster)
python3 score_buildings.py \
  --tif /path/to/thermographie-surface-2016-kirkland-jour.tif \
  --osm data/osm_buildings.json \
  --out data/buildings_scored.geojson
```
Tuning flags: `--max-dist` (palette strictness), `--min-valid` (min pixels),
`--off-e/--off-s` (registration shift, metres), `--interior` (interior pixels
only — more accurate for big roofs).

## Expand the coverage area
1. Download the day GeoTIFF(s) for the new area(s).
2. Widen the Overpass bbox to cover the **union** of all rasters; refresh
   `data/osm_buildings.json`.
3. Pass every raster — they aggregate per building:
   ```bash
   python3 score_buildings.py \
     --tif kirkland-jour.tif --tif neighbour-jour.tif \
     --osm data/osm_buildings.json --out data/buildings_scored.geojson
   ```
4. Rebuild the display overlay PNG + bounds for the new extent (reproject the
   raster to a lon/lat box; update `data/overlay_bounds.json` and the `const B`
   bounds in `index.html`). For multiple tiles, either stitch them into one PNG
   or add one image source per tile.
5. Bump `CACHE` in `service-worker.js`; update `docs/BLUEPRINT.md` extent notes.

## Regenerate the display overlay (sketch)
The overlay is the day raster reprojected to EPSG:4326 and exported as PNG, with
its bounding box recorded in `overlay_bounds.json`. `const B` in `index.html` is
that box nudged NW by the registration offset so roofs line up. Keep the two
offsets (Python sampling vs. JS overlay) equal and opposite.
