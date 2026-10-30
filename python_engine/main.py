import csv
import io
import json
import os
import re
import threading
from collections import defaultdict
from datetime import datetime
from typing import Optional
 
import networkx as nx
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("CIVICTWIN_DATA", os.path.join(BASE_DIR, "cmc_drainage_clean_prepared.csv"))
JOIN_MODE = os.environ.get("CIVICTWIN_JOIN", "vertices")   # "vertices" (any shared OSM node) or "endpoints" (line ends only)
GEOM_CACHE_PATH = os.path.join(BASE_DIR, "geometry_cache.json")
WARD_ASSIGN_PATH = os.environ.get("CIVICTWIN_WARD_ASSIGN", os.path.join(BASE_DIR, "ward_assignment.json"))
WARD_GEOJSON_PATH = os.environ.get("CIVICTWIN_WARD_GEOJSON", os.path.join(BASE_DIR, "wards_normalized.geojson"))
STATE_PATH = os.environ.get("CIVICTWIN_STATE", os.path.join(BASE_DIR, "engine_state.json"))
HISTORY_PATH = os.environ.get("CIVICTWIN_HISTORY", os.path.join(BASE_DIR, "civictwin_dispatch_history.csv"))
 
OPEN, IN_PROGRESS, CLEARED = 0, 1, 2
STATUS_NAMES = {OPEN: "OPEN", IN_PROGRESS: "IN_PROGRESS", CLEARED: "CLEARED"}
CLEAN_SILT_PCT = 5.0          # silt left after cleaning (as in the report)
STRATEGIES = ("cascade_aware", "severity_only", "random")
# Risk model = rational method: Q = C * i * A / 3.6e6 (i in mm/hr, A in m2, Q in m3/s).
# utilisation = Q / (design capacity * (1 - silt)); thresholds are those of the dataset's own risk label.
RUNOFF_DIV = 3.6e6
UTIL_HIGH, UTIL_CRIT = 0.80, 1.25
UTIL_CAP = 3.0       # utilisation is capped at 300 % for display and for the network exposure
AREA_MIN, AREA_MAX = 5_000.0, 50_000.0   # plausible catchment area range (m2) when inverting the rational method
# Manual silt typing is OFF: silt comes from the dataset / survey and the storm-adjusted value from the rainfall
# simulation. Set CIVICTWIN_ALLOW_EDIT=1 only for experiments.
ALLOW_EDIT = os.environ.get("CIVICTWIN_ALLOW_EDIT", "0") == "1"
 
HISTORY_COLUMNS = [
    "timestamp", "segment_id", "ward_number", "pre_silt_pct", "post_silt_pct",
    "pre_risk_level", "post_risk_level", "cascade_relieved", "action",
    "run_id", "strategy", "rank_at_dispatch", "rainfall_mmhr",
    "open_drains_remaining", "network_risk_before", "network_risk_after",
    "pre_util_pct", "post_util_pct",
]
 
FEATURES = [
    "ward_number", "design_capacity_m3s", "width_m", "depth_m", "elevation_m", "slope_pct",
    "topographic_wetness_index", "rainfall_intensity_mmhr", "event_duration_hr",
    "runoff_coefficient", "waste_silt_buildup_pct",
]
 
 
# --------------------------------------------------------------------------------------
# Risk rule (rational method + capacity utilisation)
# --------------------------------------------------------------------------------------
def threat_from_util(util):
    """2 = CRITICAL (overflow expected, > 125 %), 1 = HIGH (near capacity, > 80 %), 0 = LOW."""
    util = np.asarray(util, dtype=float)
    lvl = np.zeros(util.shape, dtype=int)
    lvl[util > UTIL_HIGH] = 1
    lvl[util > UTIL_CRIT] = 2
    return lvl
 
 
# --------------------------------------------------------------------------------------
# Geometry helpers  (output is always [[lat, lon], ...])
# --------------------------------------------------------------------------------------
def _flatten_pairs(obj, out):
    if isinstance(obj, (list, tuple)):
        if len(obj) >= 2 and all(isinstance(x, (int, float)) for x in obj[:2]):
            out.append((float(obj[0]), float(obj[1])))
        else:
            for item in obj:
                _flatten_pairs(item, out)
 
 
def _to_latlon(pairs):
    """Accept (lon,lat) or (lat,lon). For India the larger value is the longitude."""
    if not pairs:
        return []
    a = float(np.median([p[0] for p in pairs]))
    b = float(np.median([p[1] for p in pairs]))
    latlon = [[p[1], p[0]] for p in pairs] if a > b else [[p[0], p[1]] for p in pairs]
    # sanity: drop anything that is not a plausible geographic coordinate (e.g. projected UTM)
    return [p for p in latlon if 5 < p[0] < 40 and 60 < p[1] < 100]
 
 
def parse_geometry(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, (list, tuple)):
        pairs = []
        _flatten_pairs(value, pairs)
        return _to_latlon(pairs)
    s = str(value).strip()
    if not s:
        return []
    if s.upper().startswith(("LINESTRING", "MULTILINESTRING", "POINT", "MULTIPOINT")):
        body = s[s.index("("):].replace("(", " ").replace(")", " ")
        pairs = []
        for tok in body.split(","):
            nums = tok.split()
            try:
                if len(nums) >= 2:
                    pairs.append((float(nums[0]), float(nums[1])))
            except ValueError:
                continue
        return _to_latlon(pairs)
    if s[0] in "[{":
        try:
            obj = json.loads(s)
        except Exception:
            try:
                import ast
                obj = ast.literal_eval(s)
            except Exception:
                return []
        if isinstance(obj, dict):
            obj = obj.get("coordinates") or (obj.get("geometry") or {}).get("coordinates")
        pairs = []
        _flatten_pairs(obj, pairs)
        return _to_latlon(pairs)
    return []
 
 
def load_geometries(df):
    """Find drain geometry in the CSV (several layouts) or in geometry_cache.json."""
    n = len(df)
    cols = {c.lower().strip(): c for c in df.columns}
 
    for name in ("geometry", "geom", "wkt", "geometry_wkt", "geojson", "coordinates", "coords", "path", "shape"):
        if name in cols:
            paths = [parse_geometry(v) for v in df[cols[name]]]
            if any(paths):
                return paths, f"csv column '{cols[name]}'"
 
    for a, b, c, d in (
        ("start_lat", "start_lon", "end_lat", "end_lon"), ("lat_start", "lon_start", "lat_end", "lon_end"),
        ("u_lat", "u_lon", "v_lat", "v_lon"), ("from_lat", "from_lon", "to_lat", "to_lon"),
        ("start_latitude", "start_longitude", "end_latitude", "end_longitude"),
    ):
        if all(k in cols for k in (a, b, c, d)):
            paths = []
            for r in zip(df[cols[a]], df[cols[b]], df[cols[c]], df[cols[d]]):
                paths.append(_to_latlon([(r[1], r[0]), (r[3], r[2])]) if all(pd.notna(x) for x in r) else [])
            if any(paths):
                return paths, "csv start/end coordinate columns"
 
    lat_c = next((cols[k] for k in ("latitude", "lat", "centroid_lat", "y") if k in cols), None)
    lon_c = next((cols[k] for k in ("longitude", "lon", "lng", "long", "centroid_lon", "x") if k in cols), None)
    if lat_c and lon_c:
        paths = []
        for la, lo in zip(df[lat_c], df[lon_c]):
            paths.append(_to_latlon([(la, lo)]) if pd.notna(la) and pd.notna(lo) else [])
        if any(paths):
            return paths, "csv lat/lon point columns (markers only, no lines)"
 
    if os.path.exists(GEOM_CACHE_PATH):
        try:
            with open(GEOM_CACHE_PATH, encoding="utf-8") as f:
                cache = json.load(f)
            paths = []
            for sid in df["segment_id"]:
                p = cache.get(str(sid))
                paths.append(_to_latlon([(q[0], q[1]) for q in p]) if p else [])
            if any(paths):
                return paths, "geometry_cache.json"
        except Exception as exc:  # pragma: no cover
            print(f"[geometry] could not read cache: {exc}")
 
    return [[] for _ in range(n)], "none"
 
 
# --------------------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------------------
class DrainageEngine:
    def __init__(self):
        self.lock = threading.RLock()
        self._load_data()
        self._build_graph()
        self._train_surrogate()
        self.run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
        self._load_state()
        self._ensure_history_file()
        gs = self.graph_stats
        print(f"[engine] {len(self.ids)} drains | graph={self.graph_mode}/{JOIN_MODE} ({gs['edges']} edges, "
              f"{gs['components']} components, {gs['isolated_drains']} isolated) | cascade median {gs['cascade_median']:.0f}, "
              f"p95 {gs['cascade_p95']:.0f}, max {gs['cascade_max']} | geometry={self.geom_source} | run_id={self.run_id}")
 
    # ---- loading ---------------------------------------------------------------------
    def _load_data(self):
        if not os.path.exists(DATA_PATH):
            raise RuntimeError(f"Dataset not found: {DATA_PATH}. Put cmc_drainage_clean_prepared.csv next to main.py "
                               f"or set CIVICTWIN_DATA.")
        df = pd.read_csv(DATA_PATH)
        df["segment_id"] = df["segment_id"].astype(str)
        self.duplicates_dropped = int(df.duplicated("segment_id").sum())
        df = df.drop_duplicates("segment_id").reset_index(drop=True)
        self.df = df
        n = len(df)
        self.ids = df["segment_id"].tolist()
        self.idx = {s: i for i, s in enumerate(self.ids)}
 
        silt = pd.to_numeric(df["waste_silt_buildup_pct"], errors="coerce").fillna(0).to_numpy(float)
        # unit is decided ONCE for the whole column (fraction 0-1 or percent 0-100)
        self.silt_is_fraction = bool(silt.max() <= 1.0)
        if self.silt_is_fraction:
            silt = silt * 100.0
        self.base_silt = silt.copy()
        self.silt = silt.copy()
 
        self.ward = np.array(pd.to_numeric(df["ward_number"], errors="coerce").fillna(0).astype(int), dtype=int)  # writable copy (pandas 3 returns read-only views)
        elev = pd.to_numeric(df["elevation_m"], errors="coerce")
        self.elev = elev.fillna(elev.median() if elev.notna().any() else 0.0).to_numpy(float)
        self.dtype = (df["drain_type"].astype(str).to_numpy() if "drain_type" in df.columns
                      else np.array(["Drain"] * n))
        self.status = np.zeros(n, dtype=np.int8)
 
        # --- hydrology inputs for the rational method ---
        def col(name, default):
            return pd.to_numeric(df[name], errors="coerce") if name in df.columns else pd.Series(default, index=df.index)
        c_run = col("runoff_coefficient", 0.7)
        design = col("design_capacity_m3s", 1.0)
        self.runoff_c = c_run.fillna(c_run.median()).to_numpy(float)
        self.design_cap = design.fillna(design.median()).clip(lower=0.05).to_numpy(float)
        if {"peak_runoff_m3s", "rainfall_intensity_mmhr", "runoff_coefficient"} <= set(df.columns):
            q0, i0 = col("peak_runoff_m3s", np.nan), col("rainfall_intensity_mmhr", np.nan)
            with np.errstate(divide="ignore", invalid="ignore"):
                area = (q0 * RUNOFF_DIV / (c_run * i0)).replace([np.inf, -np.inf], np.nan)
            self.area_source = "inverted from peak_runoff_m3s (rational method)"
            self.area_m2 = area.fillna(area.median() if area.notna().any() else 20000.0).clip(AREA_MIN, AREA_MAX).to_numpy(float)
        else:
            self.area_source = "constant 20,000 m2 (no peak_runoff_m3s column)"
            self.area_m2 = np.full(n, 20000.0)
 
        self.paths, self.geom_source = load_geometries(df)
        self.centers = [p[len(p) // 2] if p else None for p in self.paths]
        self.geometry_count = int(sum(1 for p in self.paths if p))
        self.paths_missing = int(n - self.geometry_count)
        # Once the map data is (mostly) there, a drain without a location cannot be shown or dispatched
        # from the map, so it is left out of the ranking. Reported in /api/py/meta ("unmapped_drains").
        has_geom = np.array([bool(p) for p in self.paths])
        self.rankable = has_geom if self.geometry_count >= 0.5 * n else np.ones(n, dtype=bool)
 
        # --- wards: real boundaries (assign_wards.py -> ward_assignment.json) replace the synthetic dataset column ---
        self.ward_source = "synthetic (random column in the dataset)"
        self.outside_boundary = 0
        if os.path.exists(WARD_ASSIGN_PATH):
            try:
                with open(WARD_ASSIGN_PATH, encoding="utf-8") as f:
                    mapping = json.load(f)
                source_tag = mapping.pop("_source", "boundaries")
                for i, sid in enumerate(self.ids):
                    if sid in mapping:
                        self.ward[i] = int(mapping[sid])
                outside = self.ward == 0
                self.outside_boundary = int(outside.sum())
                self.rankable &= ~outside                 # drains outside the corporation limit are not ranked
                self.ward_source = ("spatial clusters (k-means zones, not official wards)" if source_tag == "kmeans"
                                    else "spatial join with ward boundaries")
            except Exception as exc:
                print(f"[wards] could not use {WARD_ASSIGN_PATH}: {exc}")
        # per-drain bounding box [min_lat, min_lon, max_lat, max_lon] for fast map-viewport queries
        self.bb = np.full((n, 4), np.nan)
        for i, p in enumerate(self.paths):
            if p:
                la = [q[0] for q in p]
                lo = [q[1] for q in p]
                self.bb[i] = (min(la), min(lo), max(la), max(lo))
 
    # ---- graph -----------------------------------------------------------------------
    def _build_graph(self):
        n = len(self.ids)
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        multi = [i for i, p in enumerate(self.paths) if len(p) >= 2]
 
        if len(multi) >= 0.5 * n:
            # Real connectivity: two segments are connected when they share an end point.
            # Water only flows downhill, so every edge goes from the higher segment to the lower one.
            self.graph_mode = "geometry_connectivity"
            order = np.lexsort((np.arange(n), -self.elev))        # high elevation first, ties by index
            pos = np.empty(n, dtype=int)
            pos[order] = np.arange(n)
            # OSM ways meet at SHARED NODES, and a junction is usually in the middle of a long way, not at its ends.
            # So by default every vertex is a possible junction (JOIN_MODE = "vertices"); "endpoints" is the old rule.
            ends = defaultdict(list)
            for i in multi:
                p = self.paths[i]
                pts = p if JOIN_MODE == "vertices" else (p[0], p[-1])
                for pt in pts:
                    ends[(round(pt[0], 6), round(pt[1], 6))].append(i)
            for segs in ends.values():
                segs = list(dict.fromkeys(segs))
                if len(segs) < 2:
                    continue
                # chain the drains meeting at one junction from high to low: same upstream/downstream sets as
                # joining every pair, but only k-1 edges per junction
                segs.sort(key=lambda q: pos[q])
                for a, b in zip(segs[:-1], segs[1:]):
                    G.add_edge(a, b)
        else:
            # Fallback (no geometry): chain the drains of each ward from high to low elevation.
            # NOTE: this makes Cascade Saved = position in the ward's elevation order. State it as a limitation.
            self.graph_mode = "ward_elevation_chain"
            for w in np.unique(self.ward):
                members = np.where(self.ward == w)[0]
                members = members[np.lexsort((members, -self.elev[members]))]
                for a, b in zip(members[:-1], members[1:]):
                    G.add_edge(int(a), int(b))
 
        assert nx.is_directed_acyclic_graph(G), "drainage graph must be acyclic"
        self.G = G
        self.topo = list(nx.topological_sort(G))
        self.preds = [list(G.predecessors(i)) for i in range(n)]
        self.succs = [list(G.successors(i)) for i in range(n)]
 
        # Cascade Saved = |ancestors(v)|, computed for all nodes at once with big-int bitsets
        # (identical to len(nx.ancestors(G, v)); verified in the tests).
        masks = [0] * n
        for v in self.topo:
            m = 0
            for p in self.preds[v]:
                m |= masks[p] | (1 << p)
            masks[v] = m
        count = (lambda x: x.bit_count()) if hasattr(int, "bit_count") else (lambda x: bin(x).count("1"))
        self.cascade = np.array([count(m) for m in masks], dtype=int)
        del masks
        self.graph_stats = {
            "edges": int(G.number_of_edges()),
            "components": int(nx.number_weakly_connected_components(G)),
            "isolated_drains": int(sum(1 for i in range(n) if G.degree(i) == 0)),
            "cascade_median": float(np.median(self.cascade)),
            "cascade_p95": float(np.percentile(self.cascade, 95)),
            "cascade_max": int(self.cascade.max()),
        }
 
    # ---- surrogate model (kept from the previous version) ------------------------------
    def _train_surrogate(self):
        self.model = None
        try:
            feats = [c for c in FEATURES if c in self.df.columns]
            extra = ["drain_type"] if "drain_type" in self.df.columns else []
            X = pd.get_dummies(self.df[feats + extra], columns=extra)
            y = self.df["blockage_risk_level"].astype(int)
            self.feature_cols = X.columns
            self.model = RandomForestClassifier(n_estimators=100, max_depth=8, class_weight="balanced",
                                                random_state=42, n_jobs=-1)
            self.model.fit(X, y)
            self.model_feats, self.model_extra = feats, extra
        except Exception as exc:
            print(f"[surrogate] RandomForest not trained: {exc}")
 
    # ---- persistence -------------------------------------------------------------------
    def _load_state(self):
        if not os.path.exists(STATE_PATH):
            return
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                st = json.load(f)
            self.run_id = st.get("run_id", self.run_id)
            for sid, v in st.get("drains", {}).items():
                i = self.idx.get(sid)
                if i is not None:
                    self.status[i] = int(v.get("status", 0))
                    self.silt[i] = float(v.get("silt_pct", self.silt[i]))
        except Exception as exc:
            print(f"[state] could not restore state: {exc}")
 
    def _save_state(self):
        changed = np.where((self.status != OPEN) | (np.abs(self.silt - self.base_silt) > 1e-9))[0]
        payload = {"run_id": self.run_id,
                   "drains": {self.ids[i]: {"status": int(self.status[i]), "silt_pct": float(self.silt[i])}
                              for i in changed}}
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp, STATE_PATH)
 
    def _ensure_history_file(self):
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, newline="", encoding="utf-8-sig") as f:
                header = next(csv.reader(f), [])
            if header == HISTORY_COLUMNS:
                return
            backup = HISTORY_PATH + datetime.now().strftime(".old-%Y%m%d-%H%M%S")
            os.replace(HISTORY_PATH, backup)
            print(f"[history] old-format history moved to {backup}")
        with open(HISTORY_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HISTORY_COLUMNS)
 
    def _log(self, **row):
        row.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        row.setdefault("run_id", self.run_id)
        with open(HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=HISTORY_COLUMNS, extrasaction="ignore").writerow(row)
 
    # ---- analytics -------------------------------------------------------------------------
    def util(self, rain, idx=None):
        """Capacity utilisation at `rain` mm/hr: rational-method peak flow / (design capacity * (1 - silt))."""
        sl = slice(None) if idx is None else idx
        q = self.runoff_c[sl] * float(rain) * self.area_m2[sl] / RUNOFF_DIV
        avail = self.design_cap[sl] * np.clip(1.0 - self.silt[sl] / 100.0, 0.05, 1.0)
        return np.minimum(UTIL_CAP, q / np.maximum(avail, 1e-6))
 
    def network_risk(self, rain):
        """
        Network exposure = sum over all drains of the WORST capacity utilisation (in %) at or below that drain.
        A blocked downstream conduit raises the exposure of every upstream conduit, so clearing a
        bottleneck lowers the exposure of all of its upstream drains (this is what Cascade Saved measures).
        """
        eff = (self.util(rain) * 100.0).tolist()
        down = eff[:]
        for v in reversed(self.topo):
            s = self.succs[v]
            if s:
                m = max(down[j] for j in s)
                if m > down[v]:
                    down[v] = m
        return float(sum(down))
 
    def ranked(self, rain, ward=None, strategy="cascade_aware", seed=42):
        eff = self.util(rain)
        thr = threat_from_util(eff)
        mask = (self.status == OPEN) & self.rankable    # dispatched drains leave the list immediately -> backfill
        if ward is not None:
            mask &= self.ward == ward
        cand = np.where(mask)[0]
        if len(cand) == 0:
            return cand, eff, thr
        if strategy == "severity_only":
            order = np.lexsort((cand, -self.cascade[cand], -eff[cand]))
        elif strategy == "random":
            order = np.random.default_rng(seed).permutation(len(cand))
        else:  # cascade_aware: threat tier, then upstream cascade, then local utilisation
            order = np.lexsort((cand, -eff[cand], -self.cascade[cand], -thr[cand]))
        return cand[order], eff, thr
 
    def item(self, i, eff, thr, rank=None):
        return {
            "segment_id": self.ids[i], "rank": rank, "ward_number": int(self.ward[i]),
            "drain_type": str(self.dtype[i]), "silt_pct": round(float(self.silt[i]), 1),                 # baseline silt from the dataset
            "util_pct": int(round(float(eff[i]) * 100)),                # capacity used at THIS rainfall (read-only)
            "threat": int(thr[i]),
            "cascade_saved": int(self.cascade[i]), "status": STATUS_NAMES[int(self.status[i])],
            "path": self.paths[i], "center": self.centers[i], "has_geometry": bool(self.paths[i]),
        }
 
    def _index(self, sid):
        i = self.idx.get(str(sid))
        if i is None:
            raise HTTPException(status_code=404, detail="Segment ID not found.")
        return i
 
    # ---- API operations ------------------------------------------------------------------------
    def top(self, k, rain, ward, strategy):
        with self.lock:
            order, eff, thr = self.ranked(rain, ward, strategy)
            items = [self.item(int(i), eff, thr, r + 1) for r, i in enumerate(order[:k])]
            q_idx = np.where(self.status == IN_PROGRESS)[0]
            queue = [self.item(int(i), eff, thr) for i in q_idx]
            live = (self.status != CLEARED) & self.rankable
            if ward is not None:
                live &= self.ward == ward
            kpis = {
                "blocked_ge_50": int(np.sum(live & (self.silt >= 50))),
                "over_capacity": int(np.sum(live & (eff > 1.0))),
                "critical": int(np.sum(live & (thr == 2))),
                "open": int(np.sum((self.status == OPEN) & self.rankable & (self.ward == ward if ward is not None else True))),
                "in_progress": int(len(q_idx)),
                "cleared": int(np.sum(self.status == CLEARED)),
            }
            return {"items": items, "queue": queue, "remaining_open": int(len(order)), "kpis": kpis,
                    "network_risk": round(self.network_risk(rain), 1), "rainfall_mmhr": rain,
                    "ward": ward, "strategy": strategy, "run_id": self.run_id}
 
    def dispatch(self, sid, rain, ward, strategy):
        with self.lock:
            i = self._index(sid)
            if self.status[i] != OPEN:
                raise HTTPException(status_code=409,
                                    detail=f"Segment {sid} is {STATUS_NAMES[int(self.status[i])]}, not OPEN.")
            order, eff, thr = self.ranked(rain, ward, strategy)
            where = np.where(order == i)[0]
            rank = int(where[0]) + 1 if len(where) else ""
            nr = round(self.network_risk(rain), 2)
            self.status[i] = IN_PROGRESS
            self._log(segment_id=sid, ward_number=int(self.ward[i]), pre_silt_pct=round(float(self.silt[i]), 1),
                      post_silt_pct=round(float(self.silt[i]), 1), pre_risk_level=int(thr[i]),
                      post_risk_level=int(thr[i]), cascade_relieved=int(self.cascade[i]), action="DISPATCH_ASSIGNED",
                      strategy=strategy, rank_at_dispatch=rank, rainfall_mmhr=rain,
                      open_drains_remaining=int(len(order) - 1), network_risk_before=nr, network_risk_after=nr,
                      pre_util_pct=round(float(eff[i]) * 100, 1), post_util_pct=round(float(eff[i]) * 100, 1))
            self._save_state()
        return {"status": "success", "message": f"Segment {sid} dispatched."}
 
    def mark_cleaned(self, sid, rain, strategy):
        with self.lock:
            i = self._index(sid)
            if self.status[i] != IN_PROGRESS:
                raise HTTPException(status_code=409,
                                    detail=f"Segment {sid} is {STATUS_NAMES[int(self.status[i])]}; only IN_PROGRESS "
                                           f"drains can be marked cleaned.")
            eff0 = self.util(rain)
            thr0 = threat_from_util(eff0)
            pre_silt, pre_risk, pre_u = float(self.silt[i]), int(thr0[i]), float(eff0[i])
            before = round(self.network_risk(rain), 2)
            self.silt[i] = CLEAN_SILT_PCT
            self.status[i] = CLEARED
            eff1 = self.util(rain)
            post_risk, post_u = int(threat_from_util(eff1)[i]), float(eff1[i])
            after = round(self.network_risk(rain), 2)
            self._log(segment_id=sid, ward_number=int(self.ward[i]), pre_silt_pct=round(pre_silt, 1),
                      post_silt_pct=CLEAN_SILT_PCT, pre_risk_level=pre_risk, post_risk_level=post_risk,
                      cascade_relieved=int(self.cascade[i]), action="CLEANING_COMPLETED", strategy=strategy,
                      rainfall_mmhr=rain, network_risk_before=before, network_risk_after=after,
                      pre_util_pct=round(pre_u * 100, 1), post_util_pct=round(post_u * 100, 1))
            self._save_state()
        return {"status": "success", "message": f"Segment {sid} marked clean.",
                "network_risk_before": before, "network_risk_after": after}
 
    def set_silt(self, sid, silt_pct, rain):
        with self.lock:
            i = self._index(sid)
            if self.status[i] != OPEN:
                raise HTTPException(status_code=409, detail="Blockage can only be edited for OPEN drains.")
            old = float(self.silt[i])
            new = float(np.clip(silt_pct, 0, 100))
            self.silt[i] = new
            thr = threat_from_util(self.util(rain))
            nr = round(self.network_risk(rain), 2)
            self._log(segment_id=sid, ward_number=int(self.ward[i]), pre_silt_pct=round(old, 1),
                      post_silt_pct=round(new, 1), pre_risk_level=int(thr[i]), post_risk_level=int(thr[i]),
                      cascade_relieved=int(self.cascade[i]), action="SURVEY_UPDATE", rainfall_mmhr=rain,
                      network_risk_after=nr)
            self._save_state()
        return {"status": "success", "silt_pct": new}
 
    def reset(self, clear_history):
        with self.lock:
            self.status[:] = OPEN
            self.silt = self.base_silt.copy()
            self.run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
            if clear_history and os.path.exists(HISTORY_PATH):
                os.replace(HISTORY_PATH, HISTORY_PATH + datetime.now().strftime(".archived-%Y%m%d-%H%M%S"))
                self._ensure_history_file()
            self._save_state()
        return {"status": "success", "run_id": self.run_id}
 
    @staticmethod
    def _thin(path, n=14):
        """Keep at most n points of a polyline (keeps the first and last point)."""
        if len(path) <= n:
            return path
        pick = np.linspace(0, len(path) - 1, n).round().astype(int)
        return [path[j] for j in pick]
 
    def network(self, south, west, north, east, rain, limit, ward):
        """All drains whose line touches the map window, most dangerous first (for the 'all drains' layer)."""
        with self.lock:
            bb = self.bb
            vis = ~np.isnan(bb[:, 0])
            vis &= (bb[:, 2] >= south) & (bb[:, 0] <= north) & (bb[:, 3] >= west) & (bb[:, 1] <= east)
            if ward is not None:
                vis &= self.ward == ward
            idx = np.where(vis)[0]
            total = int(len(idx))
            eff = self.util(rain, idx)
            thr = threat_from_util(eff)
            # CLEARED drains go last so the dangerous ones are never cut by the limit
            rank_key = np.where(self.status[idx] == CLEARED, -1, thr)
            order = np.lexsort((idx, -self.cascade[idx], -eff, -rank_key))[:limit]
            drains = [{"id": self.ids[int(idx[k])], "p": self._thin(self.paths[int(idx[k])]),
                       "t": int(thr[k]), "s": int(self.status[idx[k]]), "w": int(self.ward[idx[k]]),
                       "c": int(self.cascade[idx[k]]), "v": int(round(float(eff[k]) * 100))} for k in order]
            return {"total_in_view": total, "returned": len(drains), "drains": drains}
 
    def drain_detail(self, sid, rain):
        with self.lock:
            i = self._index(sid)
            eff = self.util(rain)
            thr = threat_from_util(eff)
            d = self.item(i, eff, thr)
            d["global_rank"] = None
            if self.status[i] == OPEN:
                order, _, _ = self.ranked(rain, None, "cascade_aware")
                where = np.where(order == i)[0]
                d["global_rank"] = int(where[0]) + 1 if len(where) else None
            return d
 
    def search(self, q, limit):
        q = str(q).strip()
        if not q:
            return []
        hits = [i for i, s in enumerate(self.ids) if q in s][:limit]
        return [{"segment_id": self.ids[i], "ward_number": int(self.ward[i]),
                 "status": STATUS_NAMES[int(self.status[i])], "has_geometry": bool(self.paths[i]),
                 "center": self.centers[i]} for i in hits]
 
    def upstream(self, sid, limit):
        with self.lock:
            i = self._index(sid)
            dist = nx.single_source_shortest_path_length(self.G.reverse(copy=False), i)
            up = sorted((d, j) for j, d in dist.items() if j != i)          # nearest first
            total = len(up)
            shown = [{"segment_id": self.ids[j], "path": self.paths[j]} for _, j in up if self.paths[j]][:limit]
            return {"segment_id": sid, "count": total, "shown": len(shown), "upstream": shown}
 
 
engine = DrainageEngine()
 
# --------------------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------------------
app = FastAPI(title="CivicTwin Network Cascade & Dispatch Microservice")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])
 
 
class DrainAction(BaseModel):
    segment_id: str
    rainfall_mmhr: float = 120.0
    ward: Optional[int] = None
    strategy: str = "cascade_aware"
 
 
class SiltUpdate(BaseModel):
    segment_id: str
    silt_pct: float
    rainfall_mmhr: float = 120.0
 
 
class ResetRequest(BaseModel):
    clear_history: bool = False
 
 
class RainfallSimRequest(BaseModel):
    rainfall_mmhr: float
 
 
def _check_strategy(strategy):
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"strategy must be one of {STRATEGIES}")
 
 
@app.get("/api/py/meta")
def meta():
    return {
        "drains": len(engine.ids), "wards": sorted(int(w) for w in np.unique(engine.ward)),
        "edges": engine.G.number_of_edges(), "graph_mode": engine.graph_mode, "join_mode": JOIN_MODE,
        "graph_stats": engine.graph_stats,
        "geometry_available": engine.geometry_count > 0, "geometry_count": engine.geometry_count,
        "geometry_source": engine.geom_source, "run_id": engine.run_id,
        "unmapped_drains": int(engine.paths_missing), "excluded_from_ranking": int((~engine.rankable).sum()),
        "outside_boundary": engine.outside_boundary, "ward_source": engine.ward_source,
        "wards_boundaries_available": os.path.exists(WARD_GEOJSON_PATH),
        "risk_model": "rational method: utilisation = C*i*A/3.6e6 / (design capacity * (1 - silt))",
        "area_source": engine.area_source,
        "duplicates_dropped": engine.duplicates_dropped, "strategies": list(STRATEGIES),
    }
 
 
@app.get("/api/py/wards")
def wards_geojson():
    if not os.path.exists(WARD_GEOJSON_PATH):
        raise HTTPException(status_code=404, detail="No ward boundaries loaded. Run assign_wards.py first.")
    return FileResponse(WARD_GEOJSON_PATH, media_type="application/geo+json")
 
 
@app.get("/api/py/top")
def top(k: int = Query(5, ge=1, le=50), rain: float = Query(120, ge=0, le=300),
        ward: Optional[int] = None, strategy: str = "cascade_aware"):
    _check_strategy(strategy)
    return engine.top(k, rain, ward, strategy)
 
 
@app.get("/api/py/upstream")
def upstream(segment_id: str, limit: int = Query(250, ge=1, le=1000)):
    return engine.upstream(segment_id, limit)
 
 
@app.get("/api/py/network")
def network(south: float, west: float, north: float, east: float, rain: float = Query(120, ge=0, le=300),
            limit: int = Query(800, ge=1, le=5000), ward: Optional[int] = None):
    return engine.network(south, west, north, east, rain, limit, ward)
 
 
@app.get("/api/py/drain")
def drain(segment_id: str, rain: float = Query(120, ge=0, le=300)):
    return engine.drain_detail(segment_id, rain)
 
 
@app.get("/api/py/search")
def search(q: str, limit: int = Query(8, ge=1, le=25)):
    return engine.search(q, limit)
 
 
@app.post("/api/py/dispatch")
def dispatch_drain(req: DrainAction):
    _check_strategy(req.strategy)
    return engine.dispatch(req.segment_id, req.rainfall_mmhr, req.ward, req.strategy)
 
 
@app.post("/api/py/mark-cleaned")
def mark_cleaned(req: DrainAction):
    _check_strategy(req.strategy)
    return engine.mark_cleaned(req.segment_id, req.rainfall_mmhr, req.strategy)
 
 
@app.post("/api/py/set-silt")
def set_silt(req: SiltUpdate):
    if not ALLOW_EDIT:
        raise HTTPException(status_code=403, detail="Manual silt editing is disabled. Silt comes from the dataset and the rainfall simulation.")
    return engine.set_silt(req.segment_id, req.silt_pct, req.rainfall_mmhr)
 
 
@app.post("/api/py/reset")
def reset(req: ResetRequest):
    return engine.reset(req.clear_history)
 
 
@app.get("/api/py/history")
def history(limit: int = Query(20, ge=1, le=500)):
    df = pd.read_csv(HISTORY_PATH, dtype=str).tail(limit).iloc[::-1]
    return json.loads(df.to_json(orient="records"))
 
 
@app.get("/api/py/history/export-csv")
def export_history_csv():
    return FileResponse(HISTORY_PATH, media_type="text/csv", filename="civictwin_dispatch_history.csv")
 
 
@app.post("/api/py/simulate-rainfall")
def simulate_rainfall(req: RainfallSimRequest):
    rain = float(np.clip(req.rainfall_mmhr, 20.0, 200.0))
    rule = threat_from_util(engine.util(rain))
    out = {"rainfall_intensity_mmhr": rain,
           "rule_counts": {f"level_{k}": int(np.sum(rule == k)) for k in (0, 1, 2)}}
    if engine.model is not None:
        sim = engine.df.copy()
        sim["rainfall_intensity_mmhr"] = rain
        sim["waste_silt_buildup_pct"] = engine.silt / 100.0 if engine.silt_is_fraction else engine.silt
        X = pd.get_dummies(sim[engine.model_feats + engine.model_extra], columns=engine.model_extra)
        X = X.reindex(columns=engine.feature_cols, fill_value=0)
        preds = engine.model.predict(X)
        counts = pd.Series(preds).value_counts().to_dict()
        out["risk_counts"] = {"low_0": int(counts.get(0, 0)), "moderate_1": int(counts.get(1, 0)),
                              "severe_2": int(counts.get(2, 0))}
        out["agreement_with_rule"] = round(float(np.mean(preds == rule)), 4)
    return out