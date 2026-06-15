# Data sources

The product needs three data layers: **thermal** (where heat escapes),
**property** (age, type, who/where), and **outcomes** (realised insulation jobs →
the ML training labels). Almost everything below is **free, CC-BY 4.0** (use +
resell allowed with attribution). Paid sources come later.

## TL;DR — your links, de-duplicated
Several links are the *same* dataset mirrored across portals:

| Your link | What it actually is | Use |
|---|---|---|
| donneesquebec `vmtl-thermographie-surface` | **Montréal aerial surface thermography** (the one we use) | ✅ primary thermal |
| open.canada / geo.ca `2d7518e2…` | Federal **mirror** of that same Montréal thermography | ↳ skip, use Montréal portal directly |
| open.canada `dbdfbdba…` | **Îlots de chaleur** (heat-island polygons), 2013–2023 | ✅ extra criterion |
| donnees.montreal.ca `ilots-de-chaleur` | Same heat-island dataset on the city portal | ↳ same as above |
| montreal.ca `role-evaluation-fonciere` | Property-roll **lookup UI** (one address at a time) | ↳ use the bulk open dataset instead ↓ |
| (found) donnees.montreal.ca `unites-evaluation-fonciere` | **Bulk property roll**: geometry + year built + use code | ✅ age & construction type |
| bter.maps.arcgis.com `webappviewer` | A third-party **ArcGIS web app** (data behind ArcGIS REST) | ⚠️ see ArcGIS note |
| myheat.ca | **MyHEAT** commercial heat-loss maps | 💲 paid/partner, later |

## 1. Thermal — primary signal
**Ville de Montréal — Thermographie aérienne de surface** (donnéesquébec /
donnees.montreal.ca). Day **and** night GeoTIFFs, per borough (~35 areas across
Greater Montréal). CC-BY 4.0. Status: historical archive (2016-era).
- **Format:** georeferenced colour GeoTIFF (classified palette), EPSG:2950.
- **Ingest:** download the borough ZIP(s) → run through the **Processing Studio**
  (`studio.html`) → overlay PNG + `buildings_scored.geojson` + `overlays.json`
  entry. Night version is the better insulation signal (no solar loading).
- **Coverage expansion** = download more borough TIFFs; the pipeline + registry
  already aggregate per building.

## 2. Heat islands — secondary criterion
**Îlots de chaleur / fraîcheur** (donnees.montreal.ca `ilots-de-chaleur`).
Polygons + GeoTIFF, multiple years (2013, 2016, 2019, 2020, 2023). CC-BY 4.0.
Built with UQAM for Montréal's 2020–2030 Climate Plan.
- **Format:** GeoJSON / SHP / GeoTIFF.
- **Use:** spatial-join each building → "in a heat island? which intensity
  class?" as an extra feature and a marketing angle (comfort, not just cost).

## 3. Property roll — age & construction type
**Unités d'évaluation foncière** (donnees.montreal.ca
`unites-evaluation-fonciere`; mirrored as donnéesquébec
`vmtl-unites-evaluation-fonciere` and open.canada `4ad6baea…`). CC-BY 4.0.
- **Format:** CSV (attributes) + GeoJSON / SHP (geometry). CKAN Data API with
  SQL-like queries.
- **Key fields:** `ANNEE_CONSTRUCTION` (year built), `CODE_UTILISATION` / CUBF
  (use: single-family, plex, etc.), `NOMBRE_LOGEMENTS`, lot & building area,
  number of floors, assessed value.
- **Use:** the backbone for **age + type + dwelling count**, joined to building
  footprints by location. These are the strongest non-thermal ML features.
- ⚠️ The geographic division "has no legal value" — fine for analytics, don't
  treat it as cadastre.

## 4. Footprints & addresses
**OpenStreetMap** (Overpass) for footprints (already used). Addresses are sparse
in OSM → we geocode via **Nominatim** at runtime. The property roll also carries
civic numbers, so once #3 is loaded we can label most buildings directly.

## 5. Realised jobs — the ML labels (private)
Your own / partners' record of completed attic-insulation jobs: address or
building id, date, scope, cost, and **outcome** (sold / installed / declined).
- **Source:** your CRM / operations export (CSV). This is private data — store
  behind auth + row-level security (see SUPABASE.md), never in the public repo.
- **Use:** the **labels** the model learns from. Without these, scoring stays
  heuristic; with them, we predict deal probability.

## 6. Later / paid
- **MyHEAT** — high-res building-level heat-loss; proprietary, sold to
  utilities/cities. No bulk download; engage commercially when scaling.
- **NRCan / other municipalities' thermography** — same CC-BY pattern as
  Montréal where available; drop new GeoTIFFs through the Studio.

## ArcGIS web-app sources (e.g. the BTER viewer)
An ArcGIS *WebAppViewer* is just a front-end; the data sits in **ArcGIS REST**
services. To source it:
1. Open the app, view source / network tab → find the web-map item id, then the
   `FeatureServer`/`MapServer` URLs (`…/rest/services/…`).
2. Query the layer: `…/FeatureServer/0/query?where=1=1&outFields=*&f=geojson`
   (paginate with `resultOffset`). Or use the layer's "export".
3. **Check that service's terms** before reuse — ArcGIS-hosted ≠ automatically
   open. Confirm the licence per layer.

## How each source lands in the app
| Source | Becomes | Where it lives |
|---|---|---|
| Thermography GeoTIFF | overlay PNG + per-building score | Storage (PNG) + `buildings` table |
| Heat islands | per-building flag/intensity | PostGIS `heat_islands` → join |
| Property roll | age / type / dwellings | PostGIS `parcels` → join |
| OSM footprints | geometry | `buildings` table |
| Realised jobs | training labels | `jobs` table (private, RLS) |
| ML output | deal-probability per building/street | `predictions` + `street_stats` |

## Attribution (keep visible)
© Ville de Montréal (thermographie, îlots de chaleur, rôle foncier) · © OpenStreetMap
contributors · basemap © CARTO. All Montréal/Québec layers: CC-BY 4.0.
