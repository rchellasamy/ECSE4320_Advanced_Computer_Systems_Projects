#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); rows.sort(key=lambda r:int(r["qd"])); qd=[int(r["qd"]) for r in rows]
for key in ["p50_us","p95_us","p99_us","p999_us"]:
  y=[F(r[key]) for r in rows]
  plt.figure(); plt.bar(range(len(qd)), y); plt.xticks(range(len(qd)), [str(q) for q in qd]); plt.xlabel("Queue Depth"); plt.ylabel("Latency (µs)"); plt.title(f"Tail — {key.upper()}"); S(sys.argv[2].replace(".png", f"_{key.split('_')[0]}.png"))
