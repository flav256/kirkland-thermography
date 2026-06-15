# Roadmap — Kirkland Thermography

_Last updated: 2026-06-15_

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

## Next (high value)
- ⬜ **Coverage expansion**: ingest neighbouring boroughs' 2016 day rasters and a
  wider OSM extract; re-run scoring (pipeline already supports `--tif` ×N).
- ⬜ **Night raster**: add `thermographie-…-nuit.tif` as a second overlay +
  toggle (day/night), and optionally a combined day–night score.
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
