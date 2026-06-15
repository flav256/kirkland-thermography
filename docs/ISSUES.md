# Issue tracker

Lightweight, in-repo tracker so work is visible across sessions without leaving
the codebase. Promote anything substantial to a GitHub Issue and link it here.

Format: `[#id] STATUS (P1–P3) — title` · `OPEN | DOING | DONE | WONTFIX`.
Priorities: **P1** now · **P2** soon · **P3** nice-to-have.

## Open
- [#7] OPEN (P2) — Coverage expansion: add neighbouring-borough day rasters +
  wider OSM extract; rebuild scores + overlay. Pipeline supports `--tif` ×N;
  register new overlays in `data/overlays.json`.
- [#8] OPEN (P2) — Night raster: commit the file + add an `overlays.json` entry
  (already loadable at runtime via the ☰ drawer, or process via the Studio).
- [#16] DOING (P1) — Supabase backend (Phase 2): Storage for TIFFs/PNGs/GeoJSON,
  Postgres (PostGIS) for datasets + scores + status, auth for uploads. In-browser
  processing (Studio) writes validated results; main map reads from Supabase.
  Blocked on: Supabase project URL + anon key from the owner.
- [#9] OPEN (P2) — Accuracy v2: interior-pixel sampling with small-footprint
  fallback; expose per-building confidence (valid/total px ratio) in the popup.
- [#10] OPEN (P3) — Basemap switcher (satellite/aerial).
- [#11] OPEN (P3) — Share-a-building deep link `?b=<osm_id>`.
- [#12] OPEN (P3) — Neighbourhood/street roll-up stats.
- [#13] OPEN (P3) — In-UI caveats note (surface temp ≠ insulation).

## Done
- [#1] DONE (P1) — Mobile UX: collapsible panels, safe-area insets, legend no
  longer hidden/overlapping.
- [#2] DONE (P1) — Geolocation control (track position + heading).
- [#3] DONE (P1) — Address/building search with suggestions + fly-to.
- [#4] DONE (P2) — PWA install button; verified manifest + maskable icon.
- [#5] DONE (P2) — `score_buildings.py` → configurable multi-raster CLI.
- [#6] DONE (P2) — Palette-distance threshold for off-palette pixel rejection.
- [#14] DONE (P2) — Image registry (`data/overlays.json`) + ☰ drawer log +
  runtime image loader (file + bounds, session-only).
- [#15] DONE (P2) — GitHub Pages deploy workflow.

## Notes
- When you finish an item, move it to **Done** and tick the matching line in
  `docs/ROADMAP.md`.
- Bugs found in the field (alignment drift on a specific building, a search miss,
  etc.) go here as new `[#id]` entries with a one-line repro.
