import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
 
import pandas as pd
 
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
HERE = os.path.dirname(os.path.abspath(__file__))
_mirror_turn = 0
 
 
def way_ids(segment_id):
    return [int(x) for x in re.findall(r"\d+", str(segment_id))]
 
 
def overpass_request(url, ids):
    """One HTTP call. Returns {way_id: [[lat, lon], ...]} or raises."""
    query = f"[out:json][timeout:90];way(id:{','.join(map(str, ids))});out geom;"
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "CivicTwin-research/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    return {el["id"]: [[p["lat"], p["lon"]] for p in el.get("geometry", [])]
            for el in payload.get("elements", []) if el.get("type") == "way"}
 
 
def fetch(ids, attempts=6):
    """Try the mirrors in turn. Returns a dict on success, None when every attempt failed."""
    global _mirror_turn
    for attempt in range(attempts):
        url = MIRRORS[_mirror_turn % len(MIRRORS)]
        try:
            return overpass_request(url, ids)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = int(exc.headers.get("Retry-After", "0") or 0) or 20 * (attempt + 1)
                print(f"    {url.split('/')[2]}: too many requests, waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"    {url.split('/')[2]}: HTTP {exc.code}, trying another server")
                _mirror_turn += 1
                time.sleep(3)
        except Exception as exc:
            print(f"    {url.split('/')[2]}: {type(exc).__name__}, trying another server")
            _mirror_turn += 1
            time.sleep(3)
    return None
 
 
def fetch_with_split(ids, min_size=10):
    """If a batch keeps failing, cut it in half (big batches are what time out)."""
    result = fetch(ids)
    if result is not None:
        return result, set()
    if len(ids) <= min_size:
        return {}, set(ids)                       # could not fetch these: retry on the next run
    half = len(ids) // 2
    a, fa = fetch_with_split(ids[:half], min_size)
    b, fb = fetch_with_split(ids[half:], min_size)
    a.update(b)
    return a, fa | fb
 
 
def save_json(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)
 
 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(HERE, "cmc_drainage_clean_prepared.csv"))
    ap.add_argument("--out", default=os.path.join(HERE, "geometry_cache.json"))
    ap.add_argument("--missing", default=os.path.join(HERE, "geometry_missing.json"))
    ap.add_argument("--batch", type=int, default=60)
    args = ap.parse_args()
 
    df = pd.read_csv(args.csv, usecols=["segment_id"])
    seg_ids = df["segment_id"].astype(str).drop_duplicates().tolist()
    cache = json.load(open(args.out, encoding="utf-8")) if os.path.exists(args.out) else {}
    absent = set(json.load(open(args.missing, encoding="utf-8")).get("ways", [])) if os.path.exists(args.missing) else set()
    way_geom = {}                                  # ways fetched during this run
 
    def wanted_ways(seg):
        return [w for w in way_ids(seg) if w not in absent]
 
    todo = [s for s in seg_ids if s not in cache and wanted_ways(s)]
    need = sorted({w for s in todo for w in wanted_ways(s)})
    print(f"{len(seg_ids)} segments | {len(cache)} already mapped | {len(todo)} to fetch ({len(need)} ways)")
 
    failed = set()
    for start in range(0, len(need), args.batch):
        chunk = need[start:start + args.batch]
        print(f"ways {start + 1}-{start + len(chunk)} of {len(need)}")
        got, bad = fetch_with_split(chunk)
        failed |= bad
        way_geom.update(got)
        ok_chunk = [w for w in chunk if w not in bad]
        absent |= {w for w in ok_chunk if w not in got or len(got[w]) < 2}   # server answered, way not there
        # assemble every segment whose ways are all accounted for
        for s in todo:
            if s in cache:
                continue
            ws = way_ids(s)
            if any(w in failed for w in ws) or any(w not in way_geom and w not in absent for w in ws):
                continue
            line = []
            for w in ws:
                line.extend(way_geom.get(w, []))
            if len(line) >= 2:
                cache[s] = line
        save_json(cache, args.out)
        save_json({"ways": sorted(absent)}, args.missing)
        time.sleep(1.5)
 
    mapped = sum(1 for s in seg_ids if s in cache)
    gone = sum(1 for s in seg_ids if s not in cache and not any(w in failed for w in way_ids(s))
               and all(w in absent for w in way_ids(s)))
    retry = len(seg_ids) - mapped - gone
    print("\n" + "=" * 60)
    print(f"mapped on the map : {mapped} of {len(seg_ids)} drains")
    print(f"not in OpenStreetMap (deleted/renamed ways): {gone}")
    print(f"failed because of server errors: {retry}")
    if retry:
        print("-> run this script again; it only retries the failed ones.")
    else:
        print("-> nothing left to retry. Restart the API.")
    print(f"saved to {args.out}")
 
 
if __name__ == "__main__":
    main()