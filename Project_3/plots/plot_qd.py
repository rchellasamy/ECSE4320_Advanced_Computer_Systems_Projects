#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:int(r["qd"]))
qd=[int(r["qd"]) for r in rows]; i=[F(r["iops"]) for r in rows]; ie=[F(r["iops_std"]) for r in rows]; l=[F(r["latency_us"]) for r in rows]; le=[F(r["latency_us_std"]) for r in rows]
plt.figure(); plt.errorbar(qd,i,yerr=ie,marker="o"); plt.xlabel("Queue Depth"); plt.ylabel("IOPS"); plt.title("IOPS vs QD"); S(sys.argv[2])
plt.figure(); plt.errorbar(qd,l,yerr=le,marker="o"); plt.xlabel("Queue Depth"); plt.ylabel("Latency (µs)"); plt.title("Latency vs QD"); S(sys.argv[3])
plt.figure(); plt.scatter(l,i); plt.xlabel("Latency (µs)"); plt.ylabel("IOPS"); plt.title("Throughput–Latency"); S(sys.argv[4])
