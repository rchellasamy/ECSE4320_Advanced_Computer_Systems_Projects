#!/usr/bin/env python3
import pandas as pd, numpy as np, math, os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INP = BASE
OUT = BASE / "data"
OUT.mkdir(exist_ok=True)

def try_read(names):
    for n in names:
        p = INP / n
        if p.exists():
            try: return pd.read_csv(p)
            except: pass
    return None

# zero queue
z = try_read(["zero_queue.csv","fake_zero_queue.csv"])
if z is not None and not z.empty:
    c = {c.lower():c for c in z.columns}
    level = c.get("level") or list(z.columns)[0]
    lat = c.get("latency_ns") or c.get("latency") or list(z.columns)[1]
else:
z.to_csv(OUT/"zero_queue.csv", index=False)

# granularity
g_src = try_read(["mlc_matrices.csv","fake_mlc_matrices.csv","bandwidth_matrix.csv","mlc_bandwidth_matrix.csv","fake_bandwidth_matrix.csv"])
S = np.array([64,128,256,512,1024,2048,4096]); P = ["seq","rand"]
def est_gran(df):
    if df is None or df.empty: df = pd.DataFrame()
    cols = {c.lower():c for c in df.columns}
    s = cols.get("stride_b") or cols.get("stride") or cols.get("access_bytes") or cols.get("bs")
    p = cols.get("pattern") or cols.get("mix") or cols.get("type")
    b = cols.get("bandwidth_mbps") or cols.get("bandwidth") or cols.get("bandwidth_mb/s")
    l = cols.get("latency_ns") or cols.get("avg_latency_ns") or cols.get("latency")
    if s and p and b and l:
        df = df[[s,p,b,l]]; df.columns = ["stride_B","pattern","bandwidth_MBps","latency_ns"]
        df["stride_B"]=pd.to_numeric(df["stride_B"],errors="coerce")
        df["bandwidth_MBps"]=pd.to_numeric(df["bandwidth_MBps"],errors="coerce")
        df["latency_ns"]=pd.to_numeric(df["latency_ns"],errors="coerce")
        df["pattern"]=df["pattern"].astype(str).str.lower().map(lambda x:"seq" if "seq" in x else ("rand" if "rand" in x else x))
        df=df.dropna(subset=["stride_B","bandwidth_MBps","latency_ns"])
    rows=[]
    for pat in P:
        m = df[df["pattern"]==pat] if not df.empty else pd.DataFrame()
        if len(m)>=2:
            x=m["stride_B"].values.astype(float); y=m["bandwidth_MBps"].values.astype(float)
            grid=np.linspace(max(1.0,x.min()/2),max(4096,x.max()*2),30); best=None
            for beta in grid:
                X=1.0/(beta+x); alpha=float(np.dot(X,y)/np.dot(X,X))
                pred=alpha/(beta+S); err=float(((np.interp(S,x,y,left=y[0],right=y[-1])-pred)**2).mean())
                if best is None or err<best[0]: best=(err,alpha,beta)
            _,alpha,beta=best; bw=alpha/(beta+S)
            X=np.vstack([np.ones_like(x),np.log2(x)]).T; c,d=np.linalg.lstsq(X,m["latency_ns"].values,rcond=None)[0]
            lat=c+d*np.log2(S)
            for s0,b0,l0 in zip(S,bw,lat):
                mm=m[np.isclose(m["stride_B"],s0)]
                if not mm.empty: rows.append([int(s0),pat,float(mm["bandwidth_MBps"].iloc[0]),float(mm["latency_ns"].iloc[0]),"measured"])
        else:
            base_bw=20000 if pat=="seq" else 15000; bw=base_bw/(1+(S/128.0)) + (0 if pat=="seq" else -3000)
            base_lat=100 if pat=="seq" else 110; lat=base_lat + 8*np.log2(S/64.0)
g = est_gran(g_src); g.to_csv(OUT/"mlc_gran_mix.csv", index=False)

# intensity / tradeoff
t_src = try_read(["tradeoff.csv","mlc_tradeoff.csv","fake_tradeoff.csv"])
def est_trade(df):
    T=np.array([1,2,4,8,16,32])
    if df is not None and not df.empty:
        c={c.lower():c for c in df.columns}
        thr=c.get("threads") or c.get("t") or list(df.columns)[0]
        bw=c.get("bandwidth_mbps") or c.get("bandwidth") or list(df.columns)[1]
        lat=c.get("avg_latency_ns") or c.get("latency_ns") or list(df.columns)[2]
        cur=df[[thr,bw,lat]]; cur.columns=["threads","bandwidth_MBps","avg_latency_ns"]
        cur["threads"]=pd.to_numeric(cur["threads"],errors="coerce")
        cur["bandwidth_MBps"]=pd.to_numeric(cur["bandwidth_MBps"],errors="coerce")
        cur["avg_latency_ns"]=pd.to_numeric(cur["avg_latency_ns"],errors="coerce")
        cur=cur.dropna()
        bw0=max(1000,float(cur["bandwidth_MBps"].min())) if not cur.empty else 2000
        bwmax=max(bw0+1000,float(cur["bandwidth_MBps"].max())) if not cur.empty else 52000
        if not cur.empty:
            ref=cur.sort_values("threads").iloc[-1]; t_ref=max(1.0,float(ref["threads"])); y_ref=float(ref["bandwidth_MBps"])
            k=max(1e-3,-np.log(max(1e-6,1-y_ref/bwmax))/t_ref)
        else: k=0.12
        y=bwmax*(1-np.exp(-k*T)); a=120.0; b=10.0/np.log(10); l=a-b*np.log(np.maximum(y,1.0))
        if not cur.empty:
            for _,r in cur.iterrows():
                i=np.where(T==int(r["threads"]))[0]
        return out
    y=52000*(1-np.exp(-0.12*T)); a=120.0; b=10.0/np.log(10); l=a-b*np.log(np.maximum(y,1.0))
t = est_trade(t_src); t.to_csv(OUT/"mlc_intensity.csv", index=False)
print("Wrote normalized CSVs to", OUT)