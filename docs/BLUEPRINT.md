# Live Blueprint — Kirkland Thermography

> The single source of truth for *how the app is built today*. Keep this in
> sync with the code; if something here is wrong, the code wins — fix the doc.

_Last updated: 2026-06-15_

## 1. What it is
A static, installable **PWA web map** that scores building roofs in Kirkland
(Montréal) by their surface temperature in the **Ville de Montréal 2016 aerial
thermography**. Cooler roof → better insulation → higher score (A–F).

No backend. All computation is offline (Python, one-time) → static data files →
served by GitHub Pages → rendered client-side by MapLibre GL.

## 2. Architecture at a glance
```
  ┌─────────────── one-time, offline (Python) ───────────────┐
  │  GeoTIFF(s) ──► classify pixels ──► rasterize OSM ──►     │
  │  score_buildings.py                aggregate per building │
  │                                          │               │
  │                                          ▼               │
  │                          data/buildings_scored.geojson    │
  │                          data/overlay_jour.png + bounds   │
  └──────────────────────────────────────────────────────────┘
                                  │  (committed to repo)
                                  ▼
  ┌──────────────── runtime, in the browser ─────────────────┐
  │  index.html (MapLibre GL)                                 │
  │   • CARTO basemap (raster tiles)                          │
  │   • thermal image overlay (data/overlay_jour.png)        │
  │   • building polygons coloured by score (geojson)        │
  │   • search · grade filter · geolocation · popups         │
  │  service-worker.js → offline cache  ·  manifest → install │
  └──────────────────────────────────────────────────────────┘
```

## 3. File map
| Path | Responsibility |
|------|----------------|
| `index.html` | The entire front-end: map setup, layers, UI panels, search, geolocation, PWA install, popups. Single-file app. |
| `score_buildings.py` | Offline scoring pipeline. CLI; supports multiple rasters for coverage expansion. |
| `data/buildings_scored.geojson` | ~6.2k scored building footprints (WGS84) + per-class histograms. |
| `data/overlay_jour.png` | Daytime thermal raster, reprojected to a lon/lat bounding box for the image overlay. |
| `data/overlay_bounds.json` | The raster's true geographic bounds + pixel size. |
| `service-worker.js` | Offline cache (app shell + data + runtime tile/CDN cache). Bump `CACHE` on any change. |
| `manifest.webmanifest` / `icons/` | PWA metadata + icons (incl. maskable). |
| `docs/` | This blueprint, the roadmap, coding strategy, data guide, issue tracker. |

## 4. Scoring model (current)
1. **Classify** every GeoTIFF pixel to the nearest of 7 legend colours
   (`CLASSES` in `score_buildings.py`), with white/black sentinels for no-data.
   A **distance threshold** (`--max-dist`, default 80) rejects anti-aliased
   class boundaries and non-thermal content so they don't pollute scores.
2. **Rasterize** each OSM footprint in the raster's native CRS (EPSG:2950 for
   the Kirkland tile). A **registration shift** (`--off-e 4 --off-s 6` m) moves
   the sampling footprint onto the real roof; the *output* geometry stays at the
   true OSM position, and the displayed overlay is shifted to match (see §5).
3. **Aggregate**: per building, score = mean class-score over its valid pixels.
   Buildings with `< --min-valid` (6) valid pixels are dropped.
4. **Grade**: A ≥85, B ≥70, C ≥55, D ≥40, E ≥25, F otherwise.

## 5. Registration / alignment (gotcha)
The source raster sits ~7 m SE of OSM/basemap. We correct it in **two places
that must stay consistent**:
- Python samples footprints shifted SE (`--off-e/--off-s`).
- `index.html` shifts the *overlay corners* (`const B`) NW by the same amount.
If you change one, change the other, or roofs and footprints will drift apart.

## 6. Front-end runtime notes
- Libs are loaded from `unpkg` (MapLibre 4.7.1) + CARTO tiles + MapLibre demo
  glyphs — all cached by the service worker for offline use.
- `maxBounds` keeps the map pinned to the coverage area (+ margin).
- Panels (`#ctrl`, `#legend`) are collapsible; they start collapsed on
  ≤640 px screens so the map stays usable on phones.
- Geolocation uses MapLibre's built-in `GeolocateControl` (needs HTTPS — fine
  on GitHub Pages).
- Search is a linear scan over the geojson `properties` (addr/name/osm_id);
  fine at ~6k features. Revisit if feature count grows ≫ 50k.

## 7. Build & deploy
- **Data rebuild** (only when raster/coverage changes): see `docs/DATA.md`.
- **Deploy**: static files on `main` via **GitHub Pages** (deploy-from-branch).
  Any push to the published branch updates the live site. No build step.
- **Cache busting**: bump `CACHE` in `service-worker.js` whenever you change
  `index.html` or any `data/` file, or returning users keep the old version.
