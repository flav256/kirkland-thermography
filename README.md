# Kirkland Thermography — Insulation Scores

Interactive, installable map of **Kirkland (Montréal)** built from the **Ville de
Montréal 2016 aerial surface thermography** (open data). Each building footprint
is scored by the surface temperature of its roof: **higher score = cooler surface
= better insulation**; dark red = hot roof = likely poor insulation.

Works as a **PWA**: installable, offline-capable, and usable in the street with
live geolocation. Add to your home screen on mobile.

## Features
- 🗺️ Thermal overlay + ~6,200 buildings coloured by insulation score (A–F)
- 🔎 **Search** by address / building, with suggestions and fly-to
- 📍 **Geolocation** (tracks your position + heading) for walking the streets
- 🎚️ Layer toggles, opacity sliders, and filter-by-grade chips
- 🖼️ **Images & Settings drawer** (☰): a log of all thermal images with their
  references + bounds, per-image visibility/opacity, and a **loader** to add a
  new image (file + bounds) live — backed by `data/overlays.json`
- 📱 Mobile-first UI: collapsible panels, safe-area aware, no hidden legend
- ⬇️ One-tap **install** (PWA) and full **offline** use once loaded
- 👆 Tap any building for its surface-temperature breakdown

## Live site
GitHub Pages (deploy-from-`main`): see the repository's Pages URL.

## How scoring works
1. The daytime colour GeoTIFF (georeferenced) is classified pixel-by-pixel into
   the 7 official legend classes (blue ≤26 °C → dark red ≥57 °C), with a
   distance threshold that rejects blended / off-palette pixels.
2. OpenStreetMap building footprints (Overpass) are rasterized in the raster's
   CRS, with a ~7 m registration shift onto the real roofs.
3. For each footprint, the mean class score over its valid pixels gives a 0–100
   score and an A–F grade. See [`score_buildings.py`](score_buildings.py).

## Run locally
```bash
python3 -m http.server 8777
# open http://localhost:8777/index.html
```
Re-running the scoring (only needed when the raster/coverage changes) requires
the source GeoTIFF(s) — see [`docs/DATA.md`](docs/DATA.md):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install rasterio numpy pillow shapely requests
python3 score_buildings.py --tif /path/to/…-jour.tif   # repeat --tif to expand coverage
```

## Documentation
- [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md) — live architecture & file map
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what's done / next / later
- [`docs/CODING_STRATEGY.md`](docs/CODING_STRATEGY.md) — how we work
- [`docs/DATA.md`](docs/DATA.md) — data sources & rebuild / expansion guide
- [`docs/ISSUES.md`](docs/ISSUES.md) — in-repo issue tracker

## Data sources & credits
- Thermography: **Ville de Montréal**, *Thermographie aérienne de surface 2016* (open data).
- Buildings: **© OpenStreetMap** contributors.
- Basemap: **© CARTO**.
