#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); order=["R100","R70W30","R50W50","W100"]; rows=[r for r in rows if r["mix"] in order]; rows.sort(key=lambda r:order.index(r["mix"]))
x=list(range(len(rows))); bw=[F(r["bandwidth_mib_s"]) for r in rows]; bwe=[F(r["bandwidth_mib_s_std"]) for r in rows]
plt.figure(); plt.bar(x,bw,yerr=bwe); plt.xticks(x,[r["mix"] for r in rows]); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Mix Sweep — BW"); S(sys.argv[2])
lat=[F(r["latency_us"]) for r in rows]; late=[F(r["latency_us_std"]) for r in rows]
plt.figure(); plt.bar(x,lat,yerr=late); plt.xticks(x,[r["mix"] for r in rows]); plt.ylabel("Latency (µs)"); plt.title("Mix Sweep — Lat"); S(sys.argv[3])
