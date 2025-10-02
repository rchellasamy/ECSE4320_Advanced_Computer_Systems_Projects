#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:int(r["bs_bytes"]))
x=[int(r["bs_bytes"]) for r in rows]; iops=[F(r["iops"]) for r in rows]; mbps=[F(r["mbps"]) for r in rows]; lat=[F(r["lat_us"]) for r in rows]
for series,ylab,suf in [(iops,"IOPS","_iops.png"),(mbps,"Throughput (MB/s)","_mbps.png")]:
  plt.figure(); plt.plot(x,series,marker="o"); 
  [plt.axvline(v,linestyle="--",linewidth=1) for v in (65536,131072)]; plt.xscale("log"); plt.xlabel("Block Size (bytes)"); plt.ylabel(ylab); plt.title("Sequential — Block Size Sweep"); S(sys.argv[2].replace(".png",suf))
plt.figure(); plt.plot(x,lat,marker="o"); [plt.axvline(v,linestyle="--",linewidth=1) for v in (65536,131072)]; plt.xscale("log"); plt.xlabel("Block Size (bytes)"); plt.ylabel("Avg Latency (µs)"); plt.title("Sequential — Latency vs Block Size"); S(sys.argv[3])
