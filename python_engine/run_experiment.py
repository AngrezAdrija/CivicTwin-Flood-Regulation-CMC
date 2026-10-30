"""
run_experiment.py  -  does CivicTwin's ranking really help?   (strategy-comparison experiment)

THE QUESTION
    A municipal crew can only clear a limited number of drains. Which ones should it clear first?
    This script gives every ranking method the SAME number of cleanings and measures how much flood risk is
    removed from the whole drainage network.

THE METHODS COMPARED
    cascade_aware  your proposed method: threat tier, then upstream cascade, then capacity used   (the app default)
    severity_only  baseline: always clear the drain that is the most overloaded (ignores the network)
    cascade_only   ablation: rank by cascade alone (shows what the threat tier / capacity add)
    random         baseline: clear drains in random order (repeated with many seeds, reported as mean +/- std)

HOW IT WORKS (the same as clicking Dispatch, then Cleaned, over and over - but automatic)
    start from a fresh network -> pick the top drain of the strategy -> clean it (silt falls to 5 %) ->
    measure the network again -> repeat K times, for several storm intensities.

WHAT IS MEASURED (after every cleaning)
    network risk exposure   sum over all drains of the worst capacity use at or below the drain (in %)
    drains at risk          drains whose own capacity use, or that of a drain downstream of them, is over 100 %
                            (water can overflow or back up into them) - the number the crews really want to shrink
    drains over capacity    how many drains carry more water than they can (> 100 %), counting each drain only for itself
    drains relieved         distinct drains that are upstream of (or are) a cleaned drain

    Run it from the python_engine folder:       python run_experiment.py
    Quick test (under a minute):                python run_experiment.py --quick
    Bigger budget / more repeats:               python run_experiment.py --k 1000 --seeds 30
    It never touches your real engine_state.json or dispatch history (it works on temporary copies).

OUTPUT (written next to this file)
    experiment_results.csv   every step of every run          experiment_summary.csv  the table for the report
    experiment_exposure.png  the main figure (needs matplotlib: pip install matplotlib)
    experiment_meta.json     settings, data size, graph statistics, package versions (for the "reproducibility" section)

NOTE FOR THE REPORT: the drain attributes are seeded (synthetic), so this shows how the strategies behave on the
simulated network, not how many floods they would prevent in the real city.
"""
import argparse
import json
import os
import platform
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_tmp = tempfile.mkdtemp(prefix="civictwin_experiment_")
os.environ["CIVICTWIN_STATE"] = os.path.join(_tmp, "state.json")          # keep the real files untouched
os.environ["CIVICTWIN_HISTORY"] = os.path.join(_tmp, "history.csv")
sys.path.insert(0, HERE)

import networkx as nx
import numpy as np
import pandas as pd

import main  # the real engine (graph, utilisation, ranking)

engine = main.engine
STRATEGIES = ["cascade_aware", "severity_only", "cascade_only", "random"]


def full_order(strategy, rain, seed):
    """The complete clearing order of a strategy on a fresh network.
    The ranking keys of the drains that are NOT cleaned never change when another drain is cleaned, so taking the
    first K of this list is identical to re-ranking after every cleaning (checked at start-up by self_check())."""
    cand = np.where((engine.status == main.OPEN) & engine.rankable)[0]
    if strategy == "random":
        return cand[np.random.default_rng(seed).permutation(len(cand))]
    if strategy == "cascade_only":
        u = engine.util(rain)
        return cand[np.lexsort((cand, -u[cand], -engine.cascade[cand]))]       # cascade first, then capacity used
    order, _, _ = engine.ranked(rain, None, strategy, seed=seed)
    return order


def fresh():
    engine.status[:] = main.OPEN
    engine.silt = engine.base_silt.copy()


def upstream_union(sources):
    """Number of distinct drains that are one of `sources` or lie upstream of one of them."""
    seen = set(sources)
    stack = list(sources)
    while stack:
        v = stack.pop()
        for p in engine.preds[v]:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return len(seen)


def self_check(rain, n=15):
    """Re-rank after every cleaning (what the dashboard does) and compare with the pre-computed order."""
    for strategy in ("cascade_aware", "severity_only"):
        fresh()
        planned = list(full_order(strategy, rain, 0)[:n])
        for step in range(n):
            order, _, _ = engine.ranked(rain, None, strategy)
            assert int(order[0]) == int(planned[step]), f"{strategy}: order differs at step {step + 1}"
            engine.status[int(order[0])] = main.CLEARED
            engine.silt[int(order[0])] = main.CLEAN_SILT_PCT
    fresh()


def worst_downstream(rain):
    """Worst capacity use (%) at or below every drain - the same rule as engine.network_risk()."""
    down = (engine.util(rain) * 100.0).tolist()
    for v in reversed(engine.topo):
        nxt = engine.succs[v]
        if nxt:
            m = max(down[j] for j in nxt)
            if m > down[v]:
                down[v] = m
    return np.asarray(down)


def snapshot(rain):
    u = engine.util(rain)
    down = worst_downstream(rain)
    mapped = engine.rankable
    return {
        "exposure": float(down.sum()),
        "at_risk": int(np.sum(mapped & (down > 100.0))),
        "over_capacity": int(np.sum(mapped & (u > 1.0))),
        "critical": int(np.sum(mapped & (u > 1.25))),
    }


def run_one(strategy, rain, seed, K, every):
    fresh()
    order = full_order(strategy, rain, seed)[:K]
    record = set(range(0, len(order) + 1, every)) | {len(order)} | {m for m in MARKS if m <= len(order)}
    rows = [dict(step=0, relieved=0, **snapshot(rain))]
    cleaned = []
    for step, i in enumerate(order, start=1):
        i = int(i)
        engine.status[i] = main.CLEARED              # dispatch + clean in one move
        engine.silt[i] = main.CLEAN_SILT_PCT
        cleaned.append(i)
        if step in record:
            rows.append(dict(step=step, relieved=upstream_union(cleaned), **snapshot(rain)))
    return rows


MARKS = (10, 50, 100, 250, 500, 1000)


def main_cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rain", type=float, nargs="+", default=[80, 120, 160], help="storm intensities, mm/hr")
    ap.add_argument("--k", type=int, default=500, help="number of drains cleaned in each run (the crews' budget)")
    ap.add_argument("--every", type=int, default=10, help="measure the network every N cleanings")
    ap.add_argument("--seeds", type=int, default=20, help="repetitions of the random strategy")
    ap.add_argument("--quick", action="store_true", help="small, fast run for testing")
    args = ap.parse_args()
    if args.quick:
        args.rain, args.k, args.seeds, args.every = [120], 100, 5, 10

    t0 = time.time()
    self_check(args.rain[0])
    print("self-check passed: pre-computed clearing order == re-ranking after every cleaning")
    results = []
    total_runs = len(args.rain) * (3 + args.seeds)
    done = 0
    for rain in args.rain:
        for strategy in STRATEGIES:
            for seed in (range(args.seeds) if strategy == "random" else [0]):
                for r in run_one(strategy, rain, seed, args.k, args.every):
                    results.append(dict(rain=rain, strategy=strategy, seed=seed, **r))
                done += 1
                print(f"\r[{done}/{total_runs}] rain {rain:g} mm/hr  {strategy:<14} seed {seed:<3}  elapsed {time.time() - t0:5.0f}s", end="", flush=True)
    print()

    df = pd.DataFrame(results)
    base = df[df.step == 0].groupby(["rain", "strategy", "seed"])[["exposure", "at_risk", "over_capacity", "critical"]].first().add_suffix("_0")
    df = df.join(base, on=["rain", "strategy", "seed"])
    df["exposure_reduction_pct"] = 100 * (df.exposure_0 - df.exposure) / df.exposure_0
    df["at_risk_resolved"] = df.at_risk_0 - df.at_risk
    df["at_risk_reduction_pct"] = 100 * df.at_risk_resolved / df.at_risk_0.replace(0, np.nan)
    df["over_resolved"] = df.over_capacity_0 - df.over_capacity
    df["critical_resolved"] = df.critical_0 - df.critical
    df.to_csv(os.path.join(HERE, "experiment_results.csv"), index=False)

    # ---------- summary table at checkpoints ----------
    marks = [k for k in MARKS if k <= args.k] or [args.k]
    agg = (df[df.step.isin(marks)]
           .groupby(["rain", "step", "strategy"])
           .agg(exposure_reduction_pct=("exposure_reduction_pct", "mean"), exposure_reduction_std=("exposure_reduction_pct", "std"),
                at_risk_resolved=("at_risk_resolved", "mean"), at_risk_resolved_std=("at_risk_resolved", "std"),
                over_resolved=("over_resolved", "mean"), critical_resolved=("critical_resolved", "mean"),
                drains_relieved=("relieved", "mean")).reset_index())
    agg[["exposure_reduction_std", "at_risk_resolved_std"]] = agg[["exposure_reduction_std", "at_risk_resolved_std"]].fillna(0)
    order = {s: n for n, s in enumerate(STRATEGIES)}
    agg = agg.sort_values(["rain", "step", "strategy"], key=lambda c: c.map(order) if c.name == "strategy" else c)
    agg.round(2).to_csv(os.path.join(HERE, "experiment_summary.csv"), index=False)

    for metric, title, fmt in (("at_risk_resolved", "DRAINS NO LONGER AT RISK after cleaning K drains (higher = better)", "{:8.1f}"),
                               ("exposure_reduction_pct", "NETWORK RISK EXPOSURE REMOVED (%) after cleaning K drains (higher = better)", "{:7.2f} %")):
        print(f"\nRESULT: {title}; random = mean over seeds\n")
        for rain in args.rain:
            print(f"--- storm {rain:g} mm/hr ---")
            print(f"{'K':>4}  " + "  ".join(f"{s_:>22}" for s_ in STRATEGIES))
            for k in marks:
                cells = []
                for s_ in STRATEGIES:
                    r = agg[(agg.rain == rain) & (agg.step == k) & (agg.strategy == s_)].iloc[0]
                    sd = f" ±{r[metric + '_std']:.2f}" if s_ == "random" and (metric + "_std") in r.index else ""
                    cells.append((fmt.format(r[metric]) + sd).rjust(22))
                print(f"{k:>4}  " + "  ".join(cells))
            print()

    # ---------- figure ----------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, len(args.rain), figsize=(5.2 * len(args.rain), 7.6), squeeze=False)
        colors = {"cascade_aware": "#2563eb", "severity_only": "#f59e0b", "cascade_only": "#7c3aed", "random": "#64748b"}
        labels = {"cascade_aware": "Cascade-aware (proposed)", "severity_only": "Severity only", "cascade_only": "Cascade only", "random": "Random (mean ± std)"}
        for col, rain in enumerate(args.rain):
            sub = df[df.rain == rain]
            for row, (metric, ylabel) in enumerate((("at_risk_resolved", "Drains no longer at risk"),
                                                    ("exposure_reduction_pct", "Network risk exposure removed (%)"))):
                ax = axes[row][col]
                for s_ in STRATEGIES:
                    g = sub[sub.strategy == s_].groupby("step")[metric]
                    m, sd = g.mean(), g.std().fillna(0)
                    ax.plot(m.index, m.values, label=labels[s_], color=colors[s_], lw=2.2 if s_ == "cascade_aware" else 1.6)
                    if s_ == "random":
                        ax.fill_between(m.index, m - sd, m + sd, color=colors[s_], alpha=.2)
                ax.set_xlabel("Drains cleaned"); ax.set_ylabel(ylabel); ax.grid(alpha=.25)
                if row == 0:
                    ax.set_title(f"Storm {rain:g} mm/hr")
        axes[0][0].legend(frameon=False, fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "experiment_exposure.png"), dpi=200)
        print("figure saved: experiment_exposure.png")
    except ImportError:
        print("matplotlib is not installed, so no figure was drawn (pip install matplotlib). The CSV files are complete.")

    meta = dict(
        finished=time.strftime("%Y-%m-%d %H:%M:%S"), runtime_seconds=round(time.time() - t0, 1), settings=vars(args),
        drains=len(engine.ids), drains_rankable=int(engine.rankable.sum()), graph_mode=engine.graph_mode, join_mode=main.JOIN_MODE,
        graph_stats=engine.graph_stats, ward_source=engine.ward_source, area_source=engine.area_source,
        python=platform.python_version(), platform=platform.platform(),
        packages={m: __import__(m).__version__ for m in ("numpy", "pandas", "networkx")},
    )
    with open(os.path.join(HERE, "experiment_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"\nDone in {time.time() - t0:.0f} s. Send me: experiment_results.csv, experiment_summary.csv, "
          f"experiment_exposure.png and experiment_meta.json")


if __name__ == "__main__":
    main_cli()
