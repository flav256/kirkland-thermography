# Coding Strategy

_How we work on this project. Keep it small, static, and honest._

## Principles
1. **Static-first.** No backend, no build step. The site is plain files served
   by GitHub Pages. Anything that needs heavy compute happens offline in
   `score_buildings.py` and is committed as data.
2. **One app file.** Front-end lives in `index.html` (HTML + CSS + JS). Only
   split it out if it genuinely outgrows a single file. Favour clarity over
   frameworks — vanilla JS + MapLibre is enough.
3. **Data is derived, not sacred.** `data/*.geojson` / `*.png` are *generated*
   artifacts. The source of truth is the GeoTIFF + OSM extract + the script.
   Never hand-edit generated data.
4. **Be honest about accuracy.** Surface temperature is a screening signal, not
   a verdict. Surface caveats in the UI and docs; don't over-claim.

## Conventions
- **Match the surrounding style.** Compact, comment-the-why. The existing code
  is terse and well-commented at decision points — keep that texture.
- **Registration stays in sync.** The Python sampling offset and the JS overlay
  offset are two halves of one correction (see BLUEPRINT §5). Change together.
- **Bump the service-worker `CACHE`** whenever `index.html` or `data/` changes,
  or returning users get a stale app.
- **Coordinates:** display/output geometry is WGS84 (EPSG:4326); pixel sampling
  happens in each raster's native CRS. Don't mix them up.

## Workflow
- Branch per change; descriptive commits. Don't push to `main` without intent —
  pushing the published branch deploys to the live site immediately.
- Before committing front-end changes, sanity-check locally:
  ```bash
  python3 -m http.server 8777    # open http://localhost:8777/index.html
  ```
- Before committing a data rebuild, verify the printed stats (count, score
  min/median/max, grade distribution) look sane vs. the previous run.
- Keep `docs/BLUEPRINT.md` and `docs/ROADMAP.md` current — they're the project's
  working memory across sessions.

## Definition of done
- Works on desktop **and** a narrow (≤390 px) mobile viewport.
- No console errors; offline reload still renders the map.
- Docs updated (blueprint/roadmap/issues) when behaviour or structure changed.
- Attribution intact: © OpenStreetMap, © CARTO, Ville de Montréal (2016).

## Dependencies (pin, don't float)
- MapLibre GL **4.7.1** (CDN, pinned). Test before bumping.
- Python scoring: `rasterio numpy pillow shapely requests` (only to re-run).
