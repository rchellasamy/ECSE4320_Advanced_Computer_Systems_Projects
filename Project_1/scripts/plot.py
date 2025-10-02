#!/usr/bin/env python3
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt

CSV = "data/results.csv"
OUT = "docs"
os.makedirs(OUT, exist_ok=True)

# -------- helpers --------
def norm(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["kernel","dtype","align","build"]:
        df[c] = df[c].astype(str).str.strip().str.lower()
    return df

def gflops_err_from_ms(work, med_ms, std_ms):
    """
    Convert time uncertainty to GFLOP/s uncertainty.
    work = (median_gflops * median_seconds) = constant op-count / 1e9
    """
    med_s = np.maximum(np.asarray(med_ms), 1e-12) / 1e3
    std_s = np.asarray(std_ms) / 1e3
    g_med = work / med_s
    g_hi  = work / np.maximum(med_s - std_s, 1e-12)
    g_lo  = work / (med_s + std_s)
    yerr = np.vstack([g_med - g_lo, g_hi - g_med])
    return g_med, yerr

def plot_gflops_vs_N(df, kernel, dtype, align="aligned", stride=1):
    sub = df[
        (df["kernel"]==kernel) &
        (df["dtype"]==dtype) &
        (df["align"]==align) &
        (df["stride"]==stride)
    ]
    if sub.empty:
        print(f"[skip] gflops_vs_N: no rows for {kernel}/{dtype}/{align}/stride={stride}")
        return

    Nuniq = sorted(sub["N"].unique())
    x = np.log2(Nuniq)

    plt.figure()
    for b, m in [("auto","o"), ("scalar","x")]:
        bb = sub[sub["build"]==b]
        if bb.empty: 
            continue
        g = (
            bb.groupby("N")
              .agg(gflops=("gflops","median"),
                   median_ms=("median_ms","median"),
                   stdev_ms=("stdev_ms","median"))
              .reindex(Nuniq)
        )
        seconds = g["median_ms"].to_numpy()/1e3
        work = g["gflops"].to_numpy()*seconds            # constant ops / 1e9
        y, yerr = gflops_err_from_ms(work, g["median_ms"].to_numpy(),
                                     g["stdev_ms"].to_numpy())
        plt.errorbar(x, y, yerr=yerr, marker=m, capsize=3, label=b)

    plt.xlabel("N (log2)")
    plt.ylabel("GFLOP/s")
    plt.title(f"GFLOP/s vs N — {kernel}, {dtype}, {align} (pref. stride=1)")
    plt.legend()
    plt.tight_layout()
    out = f"{OUT}/gflops_{kernel}_{dtype}.png"
    plt.savefig(out); plt.close()
    print("Wrote", out)

def plot_alignment_impacts(df, kernel, dtype, Ns=(1048576,4194304), stride=1):
    for N in Ns:
        sub = df[
            (df["kernel"]==kernel) &
            (df["dtype"]==dtype) &
            (df["N"]==N) &
            (df["stride"]==stride)
        ]
        if sub.empty:
            print(f"[skip] align_impact: no rows for {kernel}/{dtype}/N={N} (stride={stride})")
            continue

        p = sub.groupby(["align","build"])["gflops"].median().unstack("build")
        if p is None or ("auto" not in p.columns) or ("scalar" not in p.columns):
            print(f"[skip] align_impact: no auto+scalar pair for {kernel}/{dtype}/N={N} (stride={stride})")
            continue

        speedup = (p["auto"] / p["scalar"]).reindex(["aligned","misaligned"])

        plt.figure()
        plt.axhline(1.0, color="gray", lw=1)
        plt.plot(speedup.index, speedup.values, marker="o")
        plt.ylabel("Speedup (auto/scalar)")
        plt.xlabel("align")
        plt.title(f"Alignment impact — {kernel}, {dtype}, N={N:,}, stride={stride}")
        plt.tight_layout()
        out = f"{OUT}/align_{kernel}_{dtype}_N{N}.png"
        plt.savefig(out); plt.close()
        print("Wrote", out)

def plot_stride(df, kernel="saxpy", dtype="f32", align="aligned", N=1048576):
    sub = df[
        (df["kernel"]==kernel) &
        (df["dtype"]==dtype) &
        (df["align"]==align) &
        (df["N"]==N)
    ]
    if sub.empty:
        print(f"[skip] stride: no rows for {kernel}/{dtype}/{align}/N={N}")
        return

    p = (
        sub.groupby(["stride","build"])
           .agg(gflops=("gflops","median"),
                median_ms=("median_ms","median"),
                stdev_ms=("stdev_ms","median"))
    )
    strides = sorted(p.index.get_level_values(0).unique())

    plt.figure()
    for b, m in [("auto","o"), ("scalar","x")]:
        if b not in p.index.get_level_values(1):
            continue
        rows = p.xs(b, level="build").reindex(strides)
        seconds = rows["median_ms"].to_numpy()/1e3
        work = rows["gflops"].to_numpy()*seconds
        y, yerr = gflops_err_from_ms(work, rows["median_ms"].to_numpy(),
                                     rows["stdev_ms"].to_numpy())
        plt.errorbar(strides, y, yerr=yerr, marker=m, capsize=3, label=b)

    plt.xscale("log", base=2)
    plt.xlabel("stride")
    plt.ylabel("GFLOP/s")
    plt.title(f"Stride impact — {kernel} {dtype}, N={N:,}, {align}")
    plt.legend()
    plt.tight_layout()
    out = f"{OUT}/stride_{kernel}_{dtype}.png"
    plt.savefig(out); plt.close()
    print("Wrote", out)

# -------- run --------
df = pd.read_csv(CSV)
df = norm(df)

# GFLOP/s vs N (error bars)
for K in ["saxpy","dot","ewmul"]:
    for DT in ["f32","f64"]:
        plot_gflops_vs_N(df, K, DT, align="aligned", stride=1)

# Alignment impact
for K in ["saxpy","dot","ewmul"]:
    for DT in ["f32","f64"]:
        plot_alignment_impacts(df, K, DT, Ns=(1048576,4194304), stride=1)

# Stride plot (error bars)
plot_stride(df, kernel="saxpy", dtype="f32", align="aligned", N=1048576)

print("Wrote plots to", OUT)
