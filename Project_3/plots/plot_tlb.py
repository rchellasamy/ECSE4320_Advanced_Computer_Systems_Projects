#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:float(r["stride_kib"])); x=[float(r["stride_kib"]) for r in rows]
y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Stride (KiB)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("TLB — BW"); S(sys.argv[2])
y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Stride (KiB)"); plt.ylabel("Latency (µs)"); plt.title("TLB — Lat"); S(sys.argv[3])
