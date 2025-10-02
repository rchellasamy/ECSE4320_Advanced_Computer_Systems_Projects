#!/usr/bin/env python3
from util import R,F,S
import sys, matplotlib.pyplot as plt
rows=R(sys.argv[1]); L=[]; V=[]; E=[]
order=[("random","read","4k"),("random","write","4k"),("sequential","read","128k"),("sequential","write","128k")]
for pat,op,bs in order:
  for r in rows:
    if r["pattern"]==pat and r["op"]==op and r["bs"].lower()==bs:
      L.append(f"{pat[:3]} {op} {bs}"); V.append(F(r["bw_mib_s_mean"])); E.append(F(r["bw_mib_s_std"])); break
plt.figure(); plt.bar(range(len(V)), V, yerr=E); plt.xticks(range(len(L)), L, rotation=15, ha="right")
plt.ylabel("Bandwidth (MiB/s)"); plt.title("Zero-Queue (mean ± 5%)"); S(sys.argv[2])
