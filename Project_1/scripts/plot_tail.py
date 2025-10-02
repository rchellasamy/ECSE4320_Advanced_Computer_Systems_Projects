#!/usr/bin/env python3
import os, pandas as pd, numpy as np, matplotlib.pyplot as plt

os.makedirs("docs", exist_ok=True)
CSV="data/results.csv"

df = pd.read_csv(CSV)
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()

# Choose one clear case: SAXPY f32 aligned, stride=1
K,DT,ALIGN,STRIDE = "saxpy","f32","aligned",1
# Pick a large multiple of AVX2 lane (f32 lanes=8) + a not-multiple
N_aligned  = 1_048_576        # divisible by 8
N_tail     = N_aligned + 3    # forces masked/prologue/epilogue work

sub = df[(df.kernel==K)&(df.dtype==DT)&(df.align==ALIGN)&(df.stride==STRIDE)&(df.N.isin([N_aligned,N_tail]))]

if sub.empty:
    print("[tail] no rows found for SAXPY f32 aligned stride=1; did you run those N?")
    raise SystemExit(0)

g = sub.groupby(["N","build"]).agg(med=("gflops","median"),
                                   t=("median_ms","median"),
                                   s=("stdev_ms","median")).reset_index()
# Propagate time stdev into GFLOP/s stdev: gflops = C/t  => σ_g ≈ g*(σ_t/t)
g["yerr"] = g["med"] * (g["s"] / g["t"]).fillna(0)

p = g.pivot(index="N", columns="build", values=["med","yerr"]).sort_index()

xs = np.arange(len(p.index))
labels = [f"N={n}" for n in p.index]
w=0.35

plt.figure()
if ("med","auto") in p and ("yerr","auto") in p:
    plt.bar(xs - w/2, p[("med","auto")], yerr=p[("yerr","auto")], width=w, capsize=4, label="auto")
if ("med","scalar") in p and ("yerr","scalar") in p:
    plt.bar(xs + w/2, p[("med","scalar")], yerr=p[("yerr","scalar")], width=w, capsize=4, label="scalar")
plt.xticks(xs, labels, rotation=0)
plt.ylabel("GFLOP/s (median ± stdev-derived)")
plt.title("Tail handling — SAXPY f32, aligned, stride=1\n(multiple-of-lanes vs remainder)")
plt.legend()
plt.tight_layout()
out="docs/tail_saxpy_f32.png"
plt.savefig(out, dpi=160)
plt.close()
print("Wrote", out)
