#!/usr/bin/env python3
import argparse, math
from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt

FLOPS_PER = {"saxpy":2, "dot":2, "ewmul":1, "stencil3":5}

def savefig(p):
    p.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(p, dpi=150, bbox_inches="tight"); plt.close()

def gflops_err_from_ms(median_ms, stdev_ms, flops_per_elem, N):
    g = (flops_per_elem * N) / (max(median_ms, 1e-12) * 1e6)  # GF/s
    if pd.isna(stdev_ms) or median_ms <= 0: 
        return g, None
    rel = stdev_ms / median_ms
    return g, abs(g * rel)

def plot_all(df, out_dir, core_only=False):
    out = Path(out_dir)

    # --- SPEEDUP (scalar vs auto) with error bars ---
    piv = df.pivot_table(index=["kernel","dtype","align","stride","n"],
                         columns="build", values=["median_ms","stdev_ms"], aggfunc="median")
    piv = piv.dropna(axis=0, how="any", subset=[("median_ms","scalar"),("median_ms","auto")]).reset_index()

    ts, ta = piv[("median_ms","scalar")].values, piv[("median_ms","auto")].values
    ss = piv.get(("stdev_ms","scalar"), pd.Series(np.nan, index=piv.index)).values
    sa = piv.get(("stdev_ms","auto"),   pd.Series(np.nan, index=piv.index)).values
    speed = ts/ta
    rel_err = np.sqrt(np.nan_to_num((ss/ts)**2) + np.nan_to_num((sa/ta)**2))
    speed_err = np.abs(speed * rel_err)
    piv["speedup"], piv["speedup_err"] = speed, speed_err

    # (A) Speedup plots
    for (kernel, dtype), g in piv.groupby(["kernel","dtype"]):
        if core_only:
            g = g[(g["align"]=="aligned") & (g["stride"]==1)]
            if g.empty: 
                continue
            g = g.sort_values("n")
            plt.figure()
            plt.errorbar(g["n"], g["speedup"], yerr=g["speedup_err"], marker="o", capsize=3)
            plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("Speedup (scalar/auto)")
            plt.title(f"Speedup (aligned, s=1) — {kernel} ({dtype})")
            savefig(out / f"speedup_core_{kernel}_{dtype}.png")
        else:
            plt.figure()
            for (al, st), gg in g.groupby(["align","stride"]):
                gg = gg.sort_values("n")
                plt.errorbar(gg["n"], gg["speedup"], yerr=gg["speedup_err"], marker="o", capsize=3, label=f"{al}, s={int(st)}")
            plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("Speedup (scalar/auto)")
            plt.title(f"Speedup vs N — {kernel} ({dtype})"); plt.legend()
            savefig(out / f"speedup_{kernel}_{dtype}.png")

    # (B) GFLOP/s overlays (+ error bars)
    for (kernel, dtype), g in df.groupby(["kernel","dtype"]):
        g = g.sort_values("n")
        plt.figure()
        for b, gb in g.groupby("build"):
            xs, ys, es = [], [], []
            for _, r in gb.iterrows():
                flops_per = FLOPS_PER[r["kernel"]]
                gf = (flops_per * r["n"]) / (max(r["median_ms"], 1e-12) * 1e6)
                err = None
                if not pd.isna(r.get("stdev_ms", np.nan)) and r["median_ms"] > 0:
                    err = abs(gf * (r["stdev_ms"] / r["median_ms"]))
                xs.append(r["n"]); ys.append(gf); es.append(0.0 if err is None else err)
            plt.errorbar(xs, ys, yerr=es, marker="o", capsize=3, label=b)
        plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("GFLOP/s")
        plt.title(f"GFLOP/s — {kernel} ({dtype})"); plt.legend()
        savefig(out / f"gflops_{kernel}_{dtype}.png")

    # (C) Alignment (auto, s=1)
    sub = df[(df["kernel"]=="saxpy") & (df["stride"]==1) & (df["build"]=="auto")]
    for dtype, g in sub.groupby("dtype"):
        plt.figure()
        for al, ga in g.groupby("align"):
            xs, ys, es = [], [], []
            for _, r in ga.sort_values("n").iterrows():
                gf = (FLOPS_PER["saxpy"] * r["n"]) / (max(r["median_ms"], 1e-12) * 1e6)
                err = None
                if not pd.isna(r.get("stdev_ms", np.nan)) and r["median_ms"] > 0:
                    err = abs(gf * (r["stdev_ms"] / r["median_ms"]))
                xs.append(r["n"]); ys.append(gf); es.append(0.0 if err is None else err)
            plt.errorbar(xs, ys, yerr=es, marker="o", capsize=3, label=al)
        plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("GFLOP/s")
        plt.title(f"Alignment — saxpy ({dtype}) [auto]"); plt.legend()
        savefig(out / f"alignment_saxpy_{dtype}.png")

    # (D) Stride (auto, aligned)
    sub = df[(df["kernel"]=="saxpy") & (df["align"]=="aligned") & (df["build"]=="auto")]
    for dtype, g in sub.groupby("dtype"):
        plt.figure()
        for st, gs in g.groupby("stride"):
            xs, ys, es = [], [], []
            for _, r in gs.sort_values("n").iterrows():
                gf = (FLOPS_PER["saxpy"] * r["n"]) / (max(r["median_ms"], 1e-12) * 1e6)
                err = None
                if not pd.isna(r.get("stdev_ms", np.nan)) and r["median_ms"] > 0:
                    err = abs(gf * (r["stdev_ms"] / r["median_ms"]))
                xs.append(r["n"]); ys.append(gf); es.append(0.0 if err is None else err)
            plt.errorbar(xs, ys, yerr=es, marker="o", capsize=3, label=f"stride {int(st)}")
        plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("GFLOP/s")
        plt.title(f"Stride — saxpy ({dtype}) [auto, aligned]"); plt.legend()
        savefig(out / f"stride_saxpy_{dtype}.png")

    # (E) Dtype comparison (auto, aligned, s=1)
    sub = df[(df["kernel"]=="saxpy") & (df["align"]=="aligned") & (df["stride"]==1) & (df["build"]=="auto")].sort_values("n")
    plt.figure()
    for dtype, g in sub.groupby("dtype"):
        xs, ys, es = [], [], []
        for _, r in g.iterrows():
            gf = (FLOPS_PER["saxpy"] * r["n"]) / (max(r["median_ms"], 1e-12) * 1e6)
            err = None
            if not pd.isna(r.get("stdev_ms", np.nan)) and r["median_ms"] > 0:
                err = abs(gf * (r["stdev_ms"] / r["median_ms"]))
            xs.append(r["n"]); ys.append(gf); es.append(0.0 if err is None else err)
        plt.errorbar(xs, ys, yerr=es, marker="o", capsize=3, label=dtype)
    plt.xscale("log"); plt.xlabel("N (log)"); plt.ylabel("GFLOP/s")
    plt.title("Data types — saxpy [auto, aligned, s=1]"); plt.legend()
    savefig(out / "dtype_saxpy.png")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/results_clean.csv")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--core-only", action="store_true")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    df.columns = [c.strip().lower() for c in df.columns]
    plot_all(df, args.out, core_only=args.core_only)

if __name__ == "__main__":
    main()
