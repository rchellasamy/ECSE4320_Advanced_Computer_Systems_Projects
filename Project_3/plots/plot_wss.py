#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:float(r["working_set_gib"])); x=[float(r["working_set_gib"]) for r in rows]
y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Working Set (GiB)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("WSS — BW"); S(sys.argv[2])
y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Working Set (GiB)"); plt.ylabel("Latency (µs)"); plt.title("WSS — Lat"); S(sys.argv[3])
