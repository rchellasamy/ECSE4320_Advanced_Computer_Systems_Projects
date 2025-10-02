import os, re, pandas as pd, numpy as np, matplotlib.pyplot as plt
os.makedirs("docs", exist_ok=True)
df = pd.read_csv("data/results.csv")
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()
for c in ["stride","N","time_ms","median_ms"]:
    if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
def parse_caches():
    L1=L2=LLC=None
    try:
        t=open("docs/lscpu.txt","r",encoding="utf-8").read()
        import re
        def k(rx):
            m=re.search(rx,t,re.I); return int(m.group(1))*1024 if m else None
        L1 = k(r"L1d cache:\s*([0-9]+)\s*K")
        L2 = k(r"L2 cache:\s*([0-9]+)\s*K")
        LLC= k(r"L3 cache:\s*([0-9]+)\s*K")
    except: pass
    return (L1 or 32*1024, L2 or 256*1024, LLC or 8*1024*1024)
def plot_locality(kernel="saxpy", dtype="f32", align="aligned", build="auto"):
    sub = df[(df.kernel==kernel)&(df.dtype==dtype)&(df.align==align)&(df.build==build)&(df.stride==1)]
    if sub.empty: print(f"[locality] no rows for {kernel}/{dtype}/{align} ({build})"); return
    v = "median_ms" if "median_ms" in sub.columns else "time_ms"
    agg = sub.groupby("N")[v].median().reset_index().sort_values("N")
    fig = plt.figure(figsize=(6,4), dpi=140); ax = plt.gca()
    ax.plot(agg["N"], agg[v], marker="o", linewidth=1)
    ax.set_xscale("log"); ax.set_xlabel("N"); ax.set_ylabel("Median time (ms)")
    ax.set_title(f"{kernel.upper()} locality ({dtype}, {align}, stride=1, {build})")
    L1,L2,LLC = parse_caches()
    bpe = 4 if dtype=="f32" else 8
    elems = lambda C: C // (2*bpe)
    for name,C in [("L1",L1),("L2",L2),("LLC",LLC)]:
        nline = elems(C); ax.axvline(nline, linestyle="--", alpha=0.5)
        ax.text(nline, ax.get_ylim()[0], f" {name}", rotation=90, va="bottom")
    out = f"docs/locality_{kernel}_{dtype}_{align}_{build}.png"
    plt.tight_layout(); plt.savefig(out); plt.close(); print("Wrote", out)
if __name__ == "__main__":
    for dtype in ["f32","f64"]:
        for align in ["aligned","misaligned"]:
            for build in ["auto","scalar"]:
                plot_locality("saxpy", dtype, align, build)
