import os, pandas as pd, numpy as np, matplotlib.pyplot as plt
os.makedirs("docs", exist_ok=True)
df = pd.read_csv("data/results.csv")
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()
for c in ["stride","N","time_ms","median_ms","stdev_ms","gflops","cpe"]:
    if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
def lanes(dtype): return 8 if dtype=="f32" else 4
def plot_tail(kernel="saxpy", dtype="f32", align="aligned", stride=1):
    sub = df[(df.kernel==kernel)&(df.dtype==dtype)&(df.align==align)&(df.stride==stride)]
    if sub.empty: print(f"[tail] no rows for {kernel}/{dtype}/{align}"); return
    L = lanes(dtype); Ns = sorted(int(n) for n in sub["N"].dropna().unique())
    N_mul  = next((n for n in Ns if n % L == 0), None)
    N_tail = next((n for n in Ns if n % L != 0), None)
    if N_mul is None or N_tail is None: print(f"[tail] need both multiple-of-{L} and non-multiple Ns"); return
    want = sub[sub["N"].isin([N_mul, N_tail]) & sub["build"].isin(["auto","scalar"])]
    if want.empty: print(f"[tail] rows present but missing auto/scalar"); return
    v = "median_ms" if "median_ms" in want.columns else "time_ms"
    agg = want.groupby(["N","build"])[v].median().unstack()
    fig = plt.figure(figsize=(6,4), dpi=140); ax = plt.gca()
    x = np.arange(len(agg.index)); w = 0.35
    ax.bar(x - w/2, agg["scalar"], w, label="scalar")
    ax.bar(x + w/2, agg["auto"],   w, label="auto")
    ax.set_xticks(x); ax.set_xticklabels([f"{int(n):,}" for n in agg.index])
    ax.set_xlabel("N"); ax.set_ylabel("Median time (ms)")
    ax.set_title(f"{kernel.upper()} tail effect ({dtype}, {align}, stride={stride})")
    ax.legend()
    out = f"docs/tail_{kernel}_{dtype}_{align}_s{stride}.png"
    plt.tight_layout(); plt.savefig(out); plt.close(); print("Wrote", out)
if __name__ == "__main__":
    for dtype in ["f32","f64"]:
        for align in ["aligned","misaligned"]:
            plot_tail("saxpy", dtype, align, 1)
