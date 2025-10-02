import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- load and normalize ---
df = pd.read_csv("data/results.csv")

for c in ["kernel", "dtype", "align", "build"]:
    if c in df.columns:
        df[c] = df[c].astype(str).str.strip().str.lower()

if "N" in df.columns:
    df["N"] = pd.to_numeric(df["N"], errors="coerce")
if "stride" in df.columns:
    df["stride"] = pd.to_numeric(df["stride"], errors="coerce")
if "gflops" in df.columns:
    df["gflops"] = pd.to_numeric(df["gflops"], errors="coerce")
if "median_ms" in df.columns:
    df["median_ms"] = pd.to_numeric(df["median_ms"], errors="coerce")
if "stdev_ms" in df.columns:
    df["stdev_ms"] = pd.to_numeric(df["stdev_ms"], errors="coerce")

# --- selection (DOT f32 aligned, N=1,048,576) ---
K, DT, A, N = "dot", "f32", "aligned", 1_048_576
rows = df[
    (df["kernel"] == K)
    & (df["dtype"] == DT)
    & (df["align"] == A)
    & (df["N"] == N)
]

if rows.empty:
    print(f"[stride-extra] no rows for {K} {DT} N={N:,} {A}")
    raise SystemExit(0)

# --- helper: convert ms-uncertainty to GFLOP/s uncertainty ---
def gflops_err_from_ms(work, med_ms, std_ms):
    """
    work = (median_gflops * median_seconds) = constant op-count / 1e9, per stride point
    Propagate timing stddev into GFLOP/s y-error (asymmetric).
    """
    med_s = np.maximum(np.asarray(med_ms), 1e-12) / 1e3
    std_s = np.asarray(std_ms) / 1e3
    g_med = work / med_s
    g_hi  = work / np.maximum(med_s - std_s, 1e-12)
    g_lo  = work / (med_s + std_s)
    yerr = np.vstack([g_med - g_lo, g_hi - g_med])
    return g_med, yerr

# --- aggregate by stride & build (median over repeats) ---
grp = (
    rows.groupby(["stride", "build"])
        .agg(gflops=("gflops", "median"),
             median_ms=("median_ms", "median"),
             stdev_ms=("stdev_ms", "median"))
        .sort_index()
)

# X values (unique strides, sorted)
strides = sorted(grp.index.get_level_values(0).unique())

plt.figure()
for build, marker in [("auto", "o"), ("scalar", "x")]:
    if build not in grp.index.get_level_values(1):
        continue
    sub = grp.xs(build, level="build").reindex(strides)

    # compute 'work' (constant per stride point) from median gflops × median seconds
    seconds = sub["median_ms"].to_numpy() / 1e3
    work = sub["gflops"].to_numpy() * seconds  # same op-count/1e9 used to invert later
    y, yerr = gflops_err_from_ms(work, sub["median_ms"].to_numpy(),
                                 sub["stdev_ms"].to_numpy())

    plt.errorbar(
        strides, y, yerr=yerr,
        marker=marker, capsize=3, linewidth=1.2, label=build
    )

plt.xscale("log", base=2)
plt.xlabel("Stride")
plt.ylabel("GFLOP/s")
plt.title(f"DOT stride effect ({DT}, N={N:,}, {A})")
plt.legend()
plt.tight_layout()

out = "docs/stride_dot_f32.png"
plt.savefig(out, dpi=150)
print(f"[stride-extra] wrote {out}")
