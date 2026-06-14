#!/usr/bin/env python3
"""Score each Kirkland building by the surface-thermography colour under its
footprint. Higher score = cooler surface = better insulation.

Pipeline:
  1. Parse OSM building footprints (lon/lat).
  2. Classify every pixel of the colour GeoTIFF into one of the 7 legend
     classes (or no-data / background) by nearest-anchor RGB distance.
  3. Rasterize buildings (in the raster's native CRS, EPSG:2950) so each pixel
     carries a building id.
  4. Vectorized aggregation: per-building class histogram + mean score.
  5. Emit GeoJSON (WGS84) with score, grade and per-class pixel counts.
"""
import json, numpy as np, rasterio
from rasterio.features import rasterize
from rasterio.warp import transform as warp_transform, transform_geom

TIF = "/Users/flavienmaire/Downloads/thermographie-surface-kirkland/thermographie-surface-2016-kirkland-jour.tif"
OSM = "data/osm_buildings.json"
OUT = "data/buildings_scored.geojson"

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
# extra anchors that are NOT part of the scale (excluded from scoring)
WHITE = np.array([255,255,255]); BLACK = np.array([0,0,0])

print("reading raster…")
with rasterio.open(TIF) as ds:
    rgb = ds.read([1,2,3]).transpose(1,2,0).astype(np.int32)  # H,W,3
    H, W = rgb.shape[:2]
    rcrs = ds.crs
    rtransform = ds.transform

# ---- classify pixels to nearest anchor (incl. white/black sentinels) ----
all_anchors = np.vstack([ANCHORS, WHITE, BLACK]).astype(np.int32)   # n,3
flat = rgb.reshape(-1,3)
# distance to each anchor, argmin
d = ((flat[:,None,:] - all_anchors[None,:,:])**2).sum(2)   # may be big; chunk it
# chunk to limit memory
cls = np.empty(flat.shape[0], dtype=np.int16)
CH = 2_000_000
for i in range(0, flat.shape[0], CH):
    seg = flat[i:i+CH]
    dd = ((seg[:,None,:]-all_anchors[None,:,:])**2).sum(2)
    cls[i:i+CH] = dd.argmin(1)
cls = cls.reshape(H,W)
n_scale = len(CLASSES)
valid_class = cls < n_scale          # 0..6 are scale classes; 7=white,8=black excluded
print("valid (scale) pixels:", int(valid_class.sum()), "of", H*W)

# ---- parse OSM buildings into polygons (lon/lat) ----
print("parsing OSM…")
data = json.load(open(OSM))
els = {e["type"]+"/"+str(e["id"]): e for e in data["elements"]}
polys = []   # list of (ring_lonlat, props)
def ring_from_geom(geom):
    return [(p["lon"], p["lat"]) for p in geom]
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
print("polygons:", len(polys))

# ---- transform rings to raster CRS and build shapes for rasterize ----
print("transforming + rasterizing…")
shapes = []
geoms_wgs = []
for idx,(ring,tags,oid) in enumerate(polys):
    lons = [p[0] for p in ring]; lats=[p[1] for p in ring]
    xs, ys = warp_transform("EPSG:4326", rcrs, lons, lats)
    poly_native = {"type":"Polygon","coordinates":[list(zip(xs,ys))]}
    shapes.append((poly_native, idx+1))   # id 0 reserved for background
    geoms_wgs.append({"type":"Polygon","coordinates":[ [[lo,la] for lo,la in ring] ]})

bid = rasterize(shapes, out_shape=(H,W), transform=rtransform,
                fill=0, dtype=np.int32, all_touched=True)
print("rasterized building pixels:", int((bid>0).sum()))

# ---- vectorized aggregation ----
nb = len(polys)
score_pix = SCORES[np.clip(cls,0,n_scale-1)]   # score per pixel (only meaningful where valid_class)
mask = (bid>0) & valid_class
bflat = bid[mask].ravel()
sflat = score_pix[mask].ravel().astype(np.float64)
cflat = cls[mask].ravel()

sum_score = np.bincount(bflat, weights=sflat, minlength=nb+1)
cnt_valid = np.bincount(bflat, minlength=nb+1)
# per-class counts
class_counts = np.zeros((nb+1, n_scale), dtype=np.int64)
for c in range(n_scale):
    sel = cflat==c
    class_counts[:,c] = np.bincount(bflat[sel], minlength=nb+1)
# total footprint pixels (incl. no-data) for coverage
tot_pix = np.bincount(bid[bid>0].ravel(), minlength=nb+1)

def grade(s):
    if s>=85: return "A"
    if s>=70: return "B"
    if s>=55: return "C"
    if s>=40: return "D"
    if s>=25: return "E"
    return "F"

def ramp(s):  # green(good)->red(bad)
    t = max(0.0,min(1.0,s/100.0))
    # 0 -> red, 1 -> green
    r = int(220*(1-t)+ 30*t); g=int(40*(1-t)+170*t); b=int(40*(1-t)+70*t)
    return f"#{r:02x}{g:02x}{b:02x}"

feats=[]
kept=0
for i in range(nb):
    bi=i+1
    n=int(cnt_valid[bi])
    if n < 6:   # too few valid pixels to be meaningful
        continue
    s=float(sum_score[bi]/n)
    tags=polys[i][1]; oid=polys[i][2]
    cc={LABELS[c]:int(class_counts[bi,c]) for c in range(n_scale)}
    feats.append({
        "type":"Feature",
        "geometry":geoms_wgs[i],
        "properties":{
            "osm_id":oid,
            "score":round(s,1),
            "grade":grade(s),
            "color":ramp(s),
            "valid_px":n,
            "total_px":int(tot_pix[bi]),
            "name":tags.get("name") or tags.get("addr:housenumber",""),
            "addr":(tags.get("addr:housenumber","")+" "+tags.get("addr:street","")).strip(),
            "class_counts":cc,
        }
    })
    kept+=1

fc={"type":"FeatureCollection","features":feats}
json.dump(fc, open(OUT,"w"))
scores=[f["properties"]["score"] for f in feats]
print(f"kept {kept} buildings with score")
print("score min/median/max:", round(min(scores),1), round(float(np.median(scores)),1), round(max(scores),1))
import collections
gc=collections.Counter(f["properties"]["grade"] for f in feats)
print("grades:", dict(sorted(gc.items())))
print("wrote", OUT)
