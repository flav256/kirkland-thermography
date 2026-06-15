# Roadmap — Kirkland Thermography

_Last updated: 2026-06-15_

## North star
A PWA **lead-generation engine for insulation/retrofit sales**: overlay thermal
maps, score every roof, enrich with property age/type + heat islands, rank
streets/sectors, learn from realised jobs, and predict **deal probability** to
point reps at the highest-revenue doors — then track improvement over time.
Data: free/open (CC-BY) first, paid layers later. See
[`DATA_SOURCES.md`](DATA_SOURCES.md) and [`SUPABASE.md`](SUPABASE.md).

### Phases
1. ✅ **Map & score** — thermal overlay + per-building scores, mobile PWA.
2. ✅ **Onboard imagery** — Studio (upload TIFF → align → score → export),
   image registry, geolocation, search.
3. 🚧 **Backend (Supabase)** — persist datasets/buildings/scores; publish from
   Studio; auth. *(blocked on project URL + anon key)*
4. ⬜ **Enrich** — load property roll (age/type/dwellings) + heat islands; join
   to buildings; show as criteria + filters.
5. ⬜ **Rank** — street/sector roll-ups (which streets score worst); filter by
   low efficiency + age + type.
6. ⬜ **Outcomes** — load realised insulation jobs (private) as ML labels.
7. ⬜ **Predict** — train model (thermal + age + type + heat-island + area →
   deal success); surface deal-probability per building/street to reps.
8. ⬜ **Track** — re-score over time, measure improvement, attribute revenue.

Status legend: ✅ done · 🚧 in progress · ⬜ planned · 💡 idea

## Now / recently shipped
- ✅ Insulation-score map (PWA) with thermal overlay + scored footprints
- ✅ ~7 m OSM↔thermal registration correction
- ✅ Mobile UX pass: collapsible panels, safe-area insets, fixed legend overlap
- ✅ Geolocation (track position + heading) for use in the street
- ✅ Address / building **search** with suggestions + fly-to
- ✅ PWA **install** button (`beforeinstallprompt`) + maskable icon
- ✅ `score_buildings.py` made into a configurable, **multi-raster** CLI
- ✅ Palette-distance threshold to reject blended / off-palette pixels
- ✅ Project docs: blueprint, roadmap, coding strategy, data guide, issues
- ✅ **Image registry** (`data/overlays.json`) + ☰ drawer log with per-image
  visibility/opacity/references, and a runtime image **loader**
- ✅ GitHub Pages **deploy workflow** (`.github/workflows/deploy-pages.yml`)
- ✅ **Processing Studio** (`studio.html`): in-browser TIFF upload → align →
  fetch OSM footprints → classify + score → review → export (geojson/png/registry entry)

## Next (high value)
- 🚧 **Supabase backend** (Phase 2): persist uploaded TIFFs + validated results
  (Storage + Postgres/PostGIS + auth); main map + studio read/write from Supabase.
- ⬜ **Coverage expansion**: ingest neighbouring boroughs' 2016 day rasters and a
  wider OSM extract; re-run scoring (pipeline already supports `--tif` ×N) and
  add the new overlays to `data/overlays.json`.
- ⬜ **Night raster**: add `thermographie-…-nuit.tif` as a registry overlay
  (loadable today via the drawer) + optionally a combined day–night score.
- ⬜ **Accuracy v2**: interior-pixel sampling with small-footprint fallback;
  per-building confidence from valid-pixel coverage ratio.
- ⬜ **Basemap switcher**: satellite/aerial option to eyeball roofs.

## Later
- ⬜ Share-a-building deep link (`?b=<osm_id>` opens map on that building).
- ⬜ Neighbourhood / street roll-up stats panel.
- ⬜ Vector tiles for the footprints if feature count grows large.
- ⬜ Legend explaining caveats (sun angle, roof material, flat vs. pitched).
- 💡 Compare a building to street/block median ("you vs. neighbours").
- 💡 Export a building's report card (PNG/PDF).

## Known limitations (be honest with users)
- Surface temperature ≠ insulation directly: roof material, colour, sun
  exposure, and pitch all affect it. Treat scores as a **screening signal**.
- Single daytime snapshot (2016). Renovations since then aren't reflected.
- Footprint↔raster alignment is a global average; individual buildings can be
  off by a couple of metres.
