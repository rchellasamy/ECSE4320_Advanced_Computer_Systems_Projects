#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); seq=[r for r in rows if r["pattern"]=="seq"]; rnd=[r for r in rows if r["pattern"]=="rand"]
seq.sort(key=lambda r:int(r["stride_B"])); rnd.sort(key=lambda r:int(r["stride_B"]))
x1=[int(r["stride_B"]) for r in seq]; y1=[F(r["bandwidth_mib_s"]) for r in seq]; e1=[F(r["bandwidth_mib_s_std"]) for r in seq]
x2=[int(r["stride_B"]) for r in rnd]; y2=[F(r["bandwidth_mib_s"]) for r in rnd]; e2=[F(r["bandwidth_mib_s_std"]) for r in rnd]
plt.figure(); plt.errorbar(x1,y1,yerr=e1,marker="o",label="seq"); plt.errorbar(x2,y2,yerr=e2,marker="o",label="rand"); plt.xlabel("Stride (bytes)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Pattern×Granularity — BW"); plt.legend(); S(sys.argv[2])
y1=[F(r["latency_us"]) for r in seq]; e1=[F(r["latency_us_std"]) for r in seq]; y2=[F(r["latency_us"]) for r in rnd]; e2=[F(r["latency_us_std"]) for r in rnd]
plt.figure(); plt.errorbar(x1,y1,yerr=e1,marker="o",label="seq"); plt.errorbar(x2,y2,yerr=e2,marker="o",label="rand"); plt.xlabel("Stride (bytes)"); plt.ylabel("Latency (µs)"); plt.title("Pattern×Granularity — Lat"); plt.legend(); S(sys.argv[3])
