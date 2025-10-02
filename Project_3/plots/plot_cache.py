#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:float(r["miss_rate_pct"])); x=[float(r["miss_rate_pct"]) for r in rows]
y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Miss Rate (%)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Cache-Miss — BW"); S(sys.argv[2])
y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Miss Rate (%)"); plt.ylabel("Latency (µs)"); plt.title("Cache-Miss — Lat"); S(sys.argv[3])
