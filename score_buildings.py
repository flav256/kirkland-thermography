#!/usr/bin/env python3
"""Score buildings by the surface-thermography colour under their footprint.
Higher score = cooler surface = better insulation.

Pipeline (per raster, then merged):
  1. Parse OSM building footprints (lon/lat).
  2. Classify every pixel of a colour GeoTIFF into one of the 7 legend classes
     (or no-data / off-palette) by nearest-anchor RGB distance, with a distance
     threshold that rejects blended edges and non-thermal content.
  3. Rasterize buildings (in the raster's native CRS) so each pixel carries a
     building id.
  4. Vectorized aggregation: accumulate per-building class histogram + score.
  5. After all rasters: emit GeoJSON (WGS84) with score, grade, per-class counts.

EXPANSION: pass several rasters with repeated --tif to grow the coverage area
(e.g. neighbouring boroughs). Each building's pixels are aggregated across every
raster that overlaps it, so adjacent tiles merge seamlessly. Provide an OSM
extract that spans the union of all rasters.

Usage:
  python3 score_buildings.py \
      --tif day_kirkland.tif --tif day_neighbour.tif \
      --osm data/osm_buildings.json --out data/buildings_scored.geojson

Re-running scoring needs the source GeoTIFF(s), which are not in the repo. See
README / docs/DATA.md for where to download the Ville de Montréal open data.
"""
import argparse, json, os, collections
import numpy as np, rasterio
from rasterio.features import rasterize
from rasterio.warp import transform as warp_transform

# Default source raster (override with --tif or the THERMO_TIF env var).
DEFAULT_TIF = os.environ.get(
    "THERMO_TIF",
    "/Users/flavienmaire/Downloads/thermographie-surface-kirkland/"
    "thermographie-surface-2016-kirkland-jour.tif",
)

# legend anchors (RGB) ordered worst->best, with a score (higher=better insulation)
CLASSES = [
    ("57 +",        (173,  9,  0),   0,  "#ad0900"),
    ("51-56",       (214, 47, 41),  15,  "#d62f29"),
    ("45-50",       (237,117, 82),  30,  "#ed7552"),
    ("39-44",       (250,184,132),  46,  "#fab884"),
    ("33-38",       (255,255,191),  62,  "#ffffbf"),
    ("27-32 ref",   (191,196,192),  78,  "#bfc4c0"),
    ("<=26",        (106,145,186), 100,  "#6a91ba"),
]
LABELS  = [c[0] for c in CLASSES]
ANCHORS = np.array([c[1] for c in CLASSES], dtype=np.int32)
SCORES  = np.array([c[2] for c in CLASSES], dtype=np.float32)
N_SCALE = len(CLASSES)
# extra anchors that are NOT part of the scale (excluded from scoring)
WHITE = np.array([255,255,255]); BLACK = np.array([0,0,0])


def grade(s):
    if s>=85: return "A"
    if s>=70: return "B"
    if s>=55: return "C"
    if s>=40: return "D"
    if s>=25: return "E"
    return "F"

def ramp(s):  # green(good)->red(bad)
    t = max(0.0,min(1.0,s/100.0))
    r = int(220*(1-t)+ 30*t); g=int(40*(1-t)+170*t); b=int(40*(1-t)+70*t)
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_osm(path):
    """Return [(ring_lonlat, tags, osm_id), ...] for ways + relation outers."""
    data = json.load(open(path))
    polys = []
    def ring_from_geom(geom): return [(p["lon"], p["lat"]) for p in geom]
    for e in data["elements"]:
        if e["type"]=="way" and e.get("geometry") and len(e["geometry"])>=4:
            ring = ring_from_geom(e["geometry"])
            if ring[0]!=ring[-1]: ring.append(ring[0])
            polys.append((ring, e.get("tags",{}), e["id"]))
        elif e["type"]=="relation":
            for m in e.get("members",[]):
                if m.get("role")=="outer" and m.get("geometry") and len(m["geometry"])>=4:
                    ring = ring_from_geom(m["geometry"])
                    if ring[0]!=ring[-1]: ring.append(ring[0])
                    polys.append((ring, e.get("tags",{}), e["id"]))
    return polys


def classify(rgb, max_dist):
    """Classify H,W,3 array to scale-class ids (0..6); -1 = off-scale/no-data.

    A pixel is kept only if its nearest anchor is a scale colour AND it lies
    within `max_dist` RGB units of that anchor. The threshold rejects
    anti-aliased class boundaries and any non-thermal content (vegetation,
    water, shadows) that would otherwise be snapped onto the nearest class.
    """
    all_anchors = np.vstack([ANCHORS, WHITE, BLACK]).astype(np.int32)
    flat = rgb.reshape(-1,3)
    cls = np.empty(flat.shape[0], dtype=np.int16)
    keep = np.empty(flat.shape[0], dtype=bool)
    thr2 = float(max_dist)**2
    CH = 2_000_000
    for i in range(0, flat.shape[0], CH):
        seg = flat[i:i+CH]
        dd = ((seg[:,None,:]-all_anchors[None,:,:])**2).sum(2)   # to every anchor
        a = dd.argmin(1)
        scale_min = dd[:, :N_SCALE].min(1)                        # nearest scale dist^2
        cls[i:i+CH] = a
        keep[i:i+CH] = (a < N_SCALE) & (scale_min <= thr2)
    cls = cls.reshape(rgb.shape[:2])
    keep = keep.reshape(rgb.shape[:2])
    cls = np.where(keep, np.clip(cls,0,N_SCALE-1), -1).astype(np.int16)
    return cls


def accumulate(tif, polys, off_e, off_s, max_dist, all_touched, acc):
    """Score `polys` against one raster, adding into the `acc` accumulators."""
    nb = len(polys)
    print(f"reading raster {tif} …")
    with rasterio.open(tif) as ds:
        rgb = ds.read([1,2,3]).transpose(1,2,0).astype(np.int32)
        H, W = rgb.shape[:2]
        rcrs, rtransform = ds.crs, ds.transform

    cls = classify(rgb, max_dist)
    valid_class = cls >= 0
    print("  valid (scale) pixels:", int(valid_class.sum()), "of", H*W)

    # transform rings to raster CRS, shift SAMPLING geometry onto the real roof
    shapes = []
    for idx,(ring,_,_) in enumerate(polys):
        lons=[p[0] for p in ring]; lats=[p[1] for p in ring]
        xs, ys = warp_transform("EPSG:4326", rcrs, lons, lats)
        xs_s=[x+off_e for x in xs]; ys_s=[y-off_s for y in ys]
        shapes.append(({"type":"Polygon","coordinates":[list(zip(xs_s,ys_s))]}, idx+1))

    bid = rasterize(shapes, out_shape=(H,W), transform=rtransform,
                    fill=0, dtype=np.int32, all_touched=all_touched)
    covered = int((bid>0).sum())
    print("  rasterized building pixels:", covered)
    if covered==0:
        print("  (no footprints overlap this raster — skipped)")
        return

    score_pix = SCORES[np.clip(cls,0,N_SCALE-1)]
    mask = (bid>0) & valid_class
    bflat = bid[mask].ravel()
    sflat = score_pix[mask].ravel().astype(np.float64)
    cflat = cls[mask].ravel()

    acc["sum_score"] += np.bincount(bflat, weights=sflat, minlength=nb+1)
    acc["cnt_valid"] += np.bincount(bflat, minlength=nb+1)
    for c in range(N_SCALE):
        acc["class_counts"][:,c] += np.bincount(bflat[cflat==c], minlength=nb+1)
    acc["tot_pix"] += np.bincount(bid[bid>0].ravel(), minlength=nb+1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tif", action="append", default=None,
                    help="Daytime colour GeoTIFF. Repeat to expand coverage.")
    ap.add_argument("--osm", default="data/osm_buildings.json",
                    help="OSM buildings JSON (Overpass 'out geom').")
    ap.add_argument("--out", default="data/buildings_scored.geojson")
    ap.add_argument("--off-e", type=float, default=4.0,
                    help="Registration shift East, metres (default 4).")
    ap.add_argument("--off-s", type=float, default=6.0,
                    help="Registration shift South, metres (default 6).")
    ap.add_argument("--max-dist", type=float, default=80.0,
                    help="Max RGB distance to a legend colour to count a pixel "
                         "(lower = stricter, rejects more blended/off-palette px).")
    ap.add_argument("--min-valid", type=int, default=6,
                    help="Drop buildings with fewer valid pixels than this.")
    ap.add_argument("--interior", action="store_true",
                    help="Use interior pixels only (all_touched=False) — more "
                         "accurate for large roofs, may drop tiny footprints.")
    args = ap.parse_args()
    tifs = args.tif or [DEFAULT_TIF]

    polys = parse_osm(args.osm)
    print("polygons:", len(polys))
    nb = len(polys)
    acc = {
        "sum_score":   np.zeros(nb+1, dtype=np.float64),
        "cnt_valid":   np.zeros(nb+1, dtype=np.int64),
        "class_counts":np.zeros((nb+1, N_SCALE), dtype=np.int64),
        "tot_pix":     np.zeros(nb+1, dtype=np.int64),
    }
    for tif in tifs:
        accumulate(tif, polys, args.off_e, args.off_s, args.max_dist,
                   not args.interior, acc)

    # ---- emit ----
    feats=[]
    for i in range(nb):
        bi=i+1; n=int(acc["cnt_valid"][bi])
        if n < args.min_valid: continue
        s=float(acc["sum_score"][bi]/n)
        ring,tags,oid = polys[i]
        geom={"type":"Polygon","coordinates":[[[lo,la] for lo,la in ring]]}
        cc={LABELS[c]:int(acc["class_counts"][bi,c]) for c in range(N_SCALE)}
        feats.append({"type":"Feature","geometry":geom,"properties":{
            "osm_id":oid, "score":round(s,1), "grade":grade(s), "color":ramp(s),
            "valid_px":n, "total_px":int(acc["tot_pix"][bi]),
            "name":tags.get("name") or tags.get("addr:housenumber",""),
            "addr":(tags.get("addr:housenumber","")+" "+tags.get("addr:street","")).strip(),
            "class_counts":cc,
        }})

    json.dump({"type":"FeatureCollection","features":feats}, open(args.out,"w"))
    scores=[f["properties"]["score"] for f in feats]
    print(f"kept {len(feats)} buildings with score")
    if scores:
        print("score min/median/max:", round(min(scores),1),
              round(float(np.median(scores)),1), round(max(scores),1))
        gc=collections.Counter(f["properties"]["grade"] for f in feats)
        print("grades:", dict(sorted(gc.items())))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
