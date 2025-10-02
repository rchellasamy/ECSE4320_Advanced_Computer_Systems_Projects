#!/usr/bin/env python3
import os, re, pandas as pd, numpy as np, matplotlib.pyplot as plt

os.makedirs("docs", exist_ok=True)

CSV="data/results.csv"
LSCPU="docs/lscpu.txt"

# --- Parse cache sizes from lscpu.txt if available; fall back to reasonable defaults
def parse_cache_bytes():
    L1, L2, L3 = 48*1024, 1*1024*1024, 12*1024*1024
    try:
        text = open(LSCPU, "r", errors="ignore").read()
        def pick(name, default):
            m = re.search(rf"{name} cache:\s*([\d\.]+\s*[KMG]i?B)", text, re.I)
            if not m: return default
            s=m.group(1).lower().replace("ib","b")
            mult=1
            if "kb" in s: mult=1024
            elif "mb" in s: mult=1024**2
            elif "gb" in s: mult=1024**3
            val=float(re.findall(r"[\d\.]+", s)[0])*mult
            return int(val)
        L1 = pick("L1d", L1)
        L2 = pick("L2",  L2)
        L3 = pick("L3",  L3)
    except Exception:
        pass
    return L1, L2, L3

def flops_bytes_per_elem(kernel, dtype):
    sz = 4 if dtype=="f32" else 8
    if kernel=="saxpy":   flops=2; bytes_per = 3*sz
    elif kernel=="dot":   flops=2; bytes_per = 2*sz
    elif kernel=="ewmul": flops=1; bytes_per = 3*sz
    else:                 flops=1; bytes_per = 3*sz
    return flops, bytes_per

def annotate_cache(ax, kernel, dtype, L1,L2,L3):
    _, bpe = flops_bytes_per_elem(kernel, dtype)
    for label, cap, color in [("L1",L1,"#999"), ("L2",L2,"#777"), ("LLC",L3,"#555")]:
        Nthr = cap // bpe
        ax.axvline(Nthr, color=color, linestyle="--", linewidth=1)
        ax.text(Nthr, ax.get_ylim()[1]*0.95, f"{label}\n~N={Nthr:,}", ha="right", va="top", fontsize=8, color=color)

df = pd.read_csv(CSV)
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()

K,DT,ALIGN,STRIDE = "saxpy","f32","aligned",1
sub = df[(df.kernel==K)&(df.dtype==DT)&(df.align==ALIGN)&(df.stride==STRIDE)]

if sub.empty:
    print("[locality] no rows for SAXPY f32 aligned stride=1")
    raise SystemExit(0)

g = sub.groupby(["N","build"]).agg(gflops=("gflops","median"),
                                   t=("median_ms","median"),
                                   s=("stdev_ms","median"),
                                   cpe=("cpe","median")).reset_index()
g["yerr"] = g["gflops"] * (g["s"]/g["t"]).fillna(0)

# --- GFLOP/s vs N with cache markers
fig, ax = plt.subplots()
for b, mk in [("auto","o"), ("scalar","x")]:
    gg = g[g.build==b].sort_values("N")
    if not gg.empty:
        ax.errorbar(gg["N"], gg["gflops"], yerr=gg["yerr"], marker=mk, capsize=3, label=b)
ax.set_xscale("log", base=2)
ax.set_xlabel("N (elements)")
ax.set_ylabel("GFLOP/s (median ± stdev-derived)")
ax.set_title("Locality sweep — SAXPY f32 (aligned, stride=1)")
L1,L2,L3 = parse_cache_bytes()
annotate_cache(ax, K, DT, L1,L2,L3)
ax.legend()
plt.tight_layout()
out1="docs/locality_saxpy_f32_gflops.png"
plt.savefig(out1, dpi=160)
plt.close()
print("Wrote", out1)

# --- CPE vs N with cache markers (optional but nice)
fig, ax = plt.subplots()
for b, mk in [("auto","o"), ("scalar","x")]:
    gg = g[g.build==b].sort_values("N")
    if not gg.empty:
        ax.plot(gg["N"], gg["cpe"], marker=mk, label=b)
ax.set_xscale("log", base=2)
ax.set_xlabel("N (elements)")
ax.set_ylabel("Cycles per element (median)")
ax.set_title("Locality sweep — CPE (SAXPY f32, aligned, stride=1)")
annotate_cache(ax, K, DT, L1,L2,L3)
ax.legend()
plt.tight_layout()
out2="docs/locality_saxpy_f32_cpe.png"
plt.savefig(out2, dpi=160)
plt.close()
print("Wrote", out2)
