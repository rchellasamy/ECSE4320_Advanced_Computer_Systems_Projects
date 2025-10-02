#!/usr/bin/env python3
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV = "data/results.csv"
OUT = "docs"
os.makedirs(OUT, exist_ok=True)

# usage: roofline.py <kernel> <dtype> <align> <build> [bandwidth_GBps] [peak_GFLOPs]
# bandwidth_GBps and peak_GFLOPs are optional. Units: GB/s (1 GB = 1e9 bytes), GFLOP/s.
argv = sys.argv[1:]
if len(argv) < 4:
    print("usage: roofline.py <kernel> <dtype> <align> <build> [bandwidth_GBps] [peak_GFLOPs]")
    sys.exit(1)

K, DT, A, B = [s.strip().lower() for s in argv[:4]]
BW  = float(argv[4]) if len(argv) >= 5 else 0.0   # GB/s
PEAK = float(argv[5]) if len(argv) >= 6 else 0.0  # GFLOP/s

# ---- load & normalize
df = pd.read_csv(CSV)
for c in ("kernel","dtype","align","build"):
    df[c] = df[c].astype(str).str.strip().str.lower()
for c in ("N","stride","gflops"):
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# prefer stride==1; if empty, fall back to any stride
sub = df[(df["kernel"]==K) & (df["dtype"]==DT) & (df["align"]==A) & (df["build"]==B)]
s1 = sub[sub["stride"]==1] if "stride" in sub.columns else sub
sub = s1 if not s1.empty else sub
if sub.empty:
    print("no rows for selection")
    sys.exit(0)

# Aggregate to median GFLOP/s per N (one dot per problem size)
pts = sub.groupby("N")["gflops"].median().sort_index()
Xs_N = pts.index.values.astype(int)
Ys_GF = pts.values

# ---- arithmetic intensity (FLOPs / byte), per element
def flops_and_bytes_per_elem(kernel, dtype):
    # Simple kernel models:
    # SAXPY: y = a*x + y   => 2 FLOPs (mul+add), read x,y (2), write y (1)
    # DOT: s += x*y        => 2 FLOPs, read x,y (2), write 0 (into reg)
    # EWMUL: z = x*y       => 1 FLOP,  read x,y (2), write z (1)
    if kernel == "saxpy":
        flops, reads, writes = 2.0, 2, 1
    elif kernel == "dot":
        flops, reads, writes = 2.0, 2, 0
    elif kernel == "ewmul":
        flops, reads, writes = 1.0, 2, 1
    else:
        flops, reads, writes = 1.0, 2, 1
    sz = 4 if dtype == "f32" else 8
    bytes_per_elem = sz * (reads + writes)
    return flops, bytes_per_elem

F, BY = flops_and_bytes_per_elem(K, DT)
intensity = F / BY   # FLOPs per byte (constant for a given kernel/dtype)

# Because intensity is constant across N for these kernels, just replicate it
X_intensity = np.full_like(Ys_GF, intensity, dtype=float)

# ---- plot
plt.figure(figsize=(6,4))
plt.scatter(X_intensity, Ys_GF, label=f"{K}/{DT}/{A}/{B}", marker="o")

# memory BW line: GFLOPs = BW(GB/s) * intensity(FLOPs/byte)
xs = np.logspace(np.log10(max(1e-3, intensity/4)), np.log10(intensity*4), 256)
if BW > 0:
    plt.plot(xs, BW * xs, linestyle="--", label=f"Mem BW ({BW:.1f} GB/s)")
if PEAK > 0:
    plt.axhline(PEAK, linestyle="--", label=f"Peak compute ({PEAK:.0f} GF/s)")

plt.xscale("log"); plt.yscale("log")
plt.xlabel("Arithmetic intensity (FLOPs / byte)")
plt.ylabel("GFLOP/s")
plt.title(f"Roofline — {K}, {DT}, {A}, {B} (pref. stride=1)")
plt.legend()
plt.tight_layout()
out_path = os.path.join(OUT, f"roofline_{K}_{DT}_{A}_{B}.png")
plt.savefig(out_path)
plt.close()
print("Wrote", out_path)
