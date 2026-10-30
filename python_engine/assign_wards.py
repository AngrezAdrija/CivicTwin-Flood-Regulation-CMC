import argparse
import json
import os
import re
import sys
from collections import Counter
 
import numpy as np
 
HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_FIELDS = ["ward_no", "wardno", "ward_number", "wardnumber", "ward_num", "wardnum", "ward", "ward_id",
                    "wardid", "wd_no", "wd_num", "ward_name", "wardname", "name", "id"]
 
 
# ------------------------------------------------------------------ reading boundaries
def read_boundaries(path):
    # returns the raw features; polygons are checked by the caller
    ext = os.path.splitext(path)[1].lower()
    if ext in (".geojson", ".json"):
        with open(path, encoding="utf-8") as f:
            gj = json.load(f)
    else:
        try:
            import geopandas as gpd
        except ImportError:
            sys.exit(f"{ext} files need geopandas (pip install geopandas), or convert the file to GeoJSON (EPSG:4326) first.")
        gdf = gpd.read_file(path)
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(4326)
        gj = json.loads(gdf.to_json())
    feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
    return [ft for ft in feats if ft.get("geometry")]
 
 
def ward_number(props, field=None):
    if field:
        found = re.findall(r"\d+", str(props.get(field, "")))
        return int(found[0]) if found else None
    lowered = {str(k).lower(): v for k, v in props.items()}
    for key in CANDIDATE_FIELDS:
        if key in lowered:
            found = re.findall(r"\d+", str(lowered[key]))
            if found:
                return int(found[0])
    return None
 
 
def polygons_of(geom):
    """-> list of polygons; each polygon = list of rings (outer first), each ring = array of (lon, lat)."""
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        return []
    return [[np.asarray([(p[0], p[1]) for p in ring], dtype=float) for ring in poly] for poly in polys]
 
 
# ------------------------------------------------------------------ point in polygon (vectorised ray casting)
def inside_ring(px, py, ring):
    x, y = ring[:, 0], ring[:, 1]
    inside = np.zeros(px.shape, dtype=bool)
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = x[i], y[i], x[j], y[j]
        if yi != yj:
            cond = ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi) + xi)
            inside ^= cond
        j = i
    return inside
 
 
def inside_polygon(px, py, rings):
    mask = inside_ring(px, py, rings[0])
    for hole in rings[1:]:
        mask &= ~inside_ring(px, py, hole)
    return mask
 
 
# ------------------------------------------------------------------ main
def sample_points(path, n=9):
    if len(path) <= n:
        return path
    pick = np.linspace(0, len(path) - 1, n).round().astype(int)
    return [path[k] for k in pick]
 
 
def zones_from_kmeans(cache, k, out_path, out_geojson):
    """Fallback: k spatial zones from the drain locations (NOT official wards)."""
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        sys.exit("scikit-learn is required for --kmeans (pip install scikit-learn).")
    seg_ids = [s for s in cache if cache[s]]
    mids = np.asarray([cache[s][len(cache[s]) // 2] for s in seg_ids], dtype=float)           # [lat, lon]
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(mids)
    # number the zones north->south, then west->east, so the numbering is stable and readable
    order = sorted(range(k), key=lambda c: (-round(km.cluster_centers_[c][0], 2), km.cluster_centers_[c][1]))
    rank = {c: n + 1 for n, c in enumerate(order)}
    assignment = {sid: rank[int(lbl)] for sid, lbl in zip(seg_ids, km.labels_)}
    assignment["_source"] = "kmeans"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(assignment, f)
    if os.path.exists(out_geojson):
        os.remove(out_geojson)                    # no polygons exist for k-means zones
    counts = Counter(v for kk, v in assignment.items() if kk != "_source")
    print(f"{len(seg_ids)} drains split into {k} spatial zones (zone sizes {min(counts.values())}..{max(counts.values())}).")
    print("These are k-means zones, NOT the official CMC wards. State this in the report.")
    print(f"saved {out_path}\nRestart the API to use them.")
 
 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wards", default=None, help="ward boundary file (GeoJSON, or shp/kml/gpkg with geopandas)")
    ap.add_argument("--kmeans", type=int, default=None, help="fallback: split the drains into N spatial zones instead")
    ap.add_argument("--ward-field", default=None, help="property that holds the ward number (auto-detected if omitted)")
    ap.add_argument("--geometry", default=os.path.join(HERE, "geometry_cache.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "ward_assignment.json"))
    ap.add_argument("--out-geojson", default=os.path.join(HERE, "wards_normalized.geojson"))
    args = ap.parse_args()
 
    if not args.wards and not args.kmeans:
        sys.exit("Give either --wards <boundary file> or --kmeans <number of zones>. See the notes at the top of this file.")
    if not os.path.exists(args.geometry):
        sys.exit(f"{args.geometry} not found. Run build_geometry_cache.py first.")
    with open(args.geometry, encoding="utf-8") as f:
        cache = json.load(f)
 
    if args.kmeans:
        return zones_from_kmeans(cache, args.kmeans, args.out, args.out_geojson)
 
    if not os.path.exists(args.wards):
        here = [n for n in os.listdir(HERE) if n.lower().endswith((".geojson", ".json", ".shp", ".kml", ".gpkg"))
                and n not in ("geometry_cache.json", "geometry_missing.json", "engine_state.json", "ward_assignment.json", "wards_normalized.geojson")]
        sys.exit(f"File not found: {args.wards}\n"
                 f"'vellore_wards.geojson' was only an example name - use the name of YOUR ward boundary file "
                 f"(in this folder or give the full path).\n"
                 f"Boundary-like files currently in {HERE}: {here if here else 'none'}\n"
                 f"Don't have the file yet? Use the fallback:  python assign_wards.py --kmeans 60")
    feats = read_boundaries(args.wards)
    feats = [ft for ft in feats if polygons_of(ft["geometry"])]
    if not feats:
        with open(args.wards, encoding="utf-8") as f:
            raw = json.load(f)
        allf = raw.get("features", []) if isinstance(raw, dict) else []
        kinds = Counter((ft.get("geometry") or {}).get("type", "no geometry") for ft in allf)
        sys.exit(f"The file has {len(allf)} features, but none are ward polygons (geometry types found: {dict(kinds) or 'none'}).\n"
                 f"An EMPTY file usually means the source has no ward boundaries (e.g. OpenStreetMap has none for this city).\n"
                 f"Get a real boundary file, or use the fallback:  python assign_wards.py --kmeans 60")
 
    wards = []                                   # (ward_no, polygons, bbox)
    for ft in feats:
        no = ward_number(ft.get("properties") or {}, args.ward_field)
        if no is None:
            keys = sorted((feats[0].get("properties") or {}).keys())
            sys.exit(f"Could not read a ward number. Properties in the file: {keys}. "
                     f"Re-run with --ward-field <one of these>.")
        polys = polygons_of(ft["geometry"])
        if not polys:
            continue
        allpts = np.vstack([ring for poly in polys for ring in poly[:1]])
        if np.abs(allpts).max() > 180:
            sys.exit("Coordinates look projected (not lon/lat). Reproject the file to WGS84 / EPSG:4326 first.")
        wards.append((no, polys, (allpts[:, 0].min(), allpts[:, 1].min(), allpts[:, 0].max(), allpts[:, 1].max())))
    print(f"{len(wards)} ward polygons, ward numbers {min(w[0] for w in wards)}..{max(w[0] for w in wards)}")
 
    # sample points of every drain (cache holds [lat, lon])
    seg_ids = list(cache.keys())
    pts, owner = [], []
    for k, sid in enumerate(seg_ids):
        for lat, lon in sample_points(cache[sid]):
            pts.append((lon, lat))
            owner.append(k)
    pts = np.asarray(pts, dtype=float)
    owner = np.asarray(owner)
    point_ward = np.zeros(len(pts), dtype=int)   # 0 = outside every ward
    for no, polys, (x0, y0, x1, y1) in wards:
        cand = np.where((pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1) & (point_ward == 0))[0]
        if len(cand) == 0:
            continue
        hit = np.zeros(len(cand), dtype=bool)
        for poly in polys:
            hit |= inside_polygon(pts[cand, 0], pts[cand, 1], poly)
        point_ward[cand[hit]] = no
 
    # a drain belongs to the ward that contains most of its sampled points
    votes = {}
    for k, w in zip(owner, point_ward):
        if w:
            votes.setdefault(int(k), Counter())[int(w)] += 1
    assignment = {sid: (votes[k].most_common(1)[0][0] if k in votes else 0) for k, sid in enumerate(seg_ids)}
 
    assignment["_source"] = "boundaries"
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(assignment, f)
    out_feats = []
    for ft in feats:
        no = ward_number(ft.get("properties") or {}, args.ward_field)
        geom = json.loads(json.dumps(ft["geometry"]))
        def rnd(c):
            return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
        geom["coordinates"] = rnd(geom["coordinates"])
        out_feats.append({"type": "Feature", "properties": {"ward_no": no}, "geometry": geom})
    with open(args.out_geojson, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": out_feats}, f)
 
    assignment.pop("_source")
    counts = Counter(assignment.values())
    inside = sum(v for k, v in counts.items() if k)
    print(f"\nassigned {inside} of {len(assignment)} drains to a ward; {counts.get(0, 0)} are outside the corporation limit")
    empty = sorted(set(w[0] for w in wards) - set(counts))
    if empty:
        print(f"wards with no drain: {empty}")
    print("drains per ward (top 8):", counts.most_common(9)[:9])
    print(f"saved {args.out} and {args.out_geojson}\nRestart the API to use them.")
 
 
if __name__ == "__main__":
    main()