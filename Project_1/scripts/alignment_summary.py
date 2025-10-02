import os, pandas as pd, numpy as np
os.makedirs("docs", exist_ok=True)
df = pd.read_csv("data/results.csv")
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()

Ns=[1048576, 4194304]
rows=[]
for K in ["saxpy","dot","ewmul"]:
    for DT in ["f32","f64"]:
        for N in Ns:
            sub = df[(df.kernel==K)&(df.dtype==DT)&(df.N==N)]
            if sub.empty: continue
            p = sub.groupby(["align","build"])["gflops"].median().unstack("build")
            for al in ["aligned","misaligned"]:
                a = p.loc[al,"auto"]   if al in p.index and "auto"   in p.columns else np.nan
                s = p.loc[al,"scalar"] if al in p.index and "scalar" in p.columns else np.nan
                rows.append([K,DT,N,al,a,s])
summary = pd.DataFrame(rows, columns=["kernel","dtype","N","align","gflops_auto","gflops_scalar"])
summary.to_csv("docs/alignment_summary.csv", index=False)
print("Wrote docs/alignment_summary.csv")
