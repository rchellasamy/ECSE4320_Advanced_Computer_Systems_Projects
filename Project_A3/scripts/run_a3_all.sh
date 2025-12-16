#!/usr/bin/env bash
set -euo pipefail

BIN=./amq_bench
OUTDIR=results_a3
RUNS=2

OPS_READ=5000000
OPS_LOAD=3000000
OPS_MIX=3000000

mkdir -p "$OUTDIR"

PIN=""
# PIN="taskset -c 2"

BLOOM_FPRS=(0.05 0.02 0.01 0.005 0.001)
XOR_FP=(6 8 10 12 14)
CUCKOO_FP=(6 8 10 12 14)
QF_RB=(6 8 10 12 14)

NEG_FOR_FPR=1.0

for fpr in "${BLOOM_FPRS[@]}"; do
  echo "[bloom fpr sweep] fpr=$fpr"
  $PIN "$BIN" --filter bloom --fpr "$fpr" --neg "$NEG_FOR_FPR" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/bloom_fpr.csv"
done

for fp in "${XOR_FP[@]}"; do
  echo "[xor fpbits sweep] fpbits=$fp"
  $PIN "$BIN" --filter xor --fpbits "$fp" --neg "$NEG_FOR_FPR" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/xor_fpbits.csv"
done

for fp in "${CUCKOO_FP[@]}"; do
  echo "[cuckoo fpbits sweep] fpbits=$fp"
  $PIN "$BIN" --filter cuckoo --fpbits "$fp" --neg "$NEG_FOR_FPR" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/cuckoo_fpbits.csv"
done

for rb in "${QF_RB[@]}"; do
  echo "[qf rbits sweep] rbits=$rb"
  $PIN "$BIN" --filter qf --rbits "$rb" --neg "$NEG_FOR_FPR" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/qf_rbits.csv"
done

NEGS=(0.0 0.5 0.9 1.0)

BLOOM_FPR_FIXED=0.01
XOR_FP_FIXED=12
CUCKOO_FP_FIXED=12
QF_RB_FIXED=12

for neg in "${NEGS[@]}"; do
  echo "[throughput vs neg] neg=$neg"
  $PIN "$BIN" --filter bloom --fpr "$BLOOM_FPR_FIXED" --neg "$neg" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/thr_vs_neg.csv"
  $PIN "$BIN" --filter xor --fpbits "$XOR_FP_FIXED" --neg "$neg" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/thr_vs_neg.csv"
  $PIN "$BIN" --filter cuckoo --fpbits "$CUCKOO_FP_FIXED" --neg "$neg" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/thr_vs_neg.csv"
  $PIN "$BIN" --filter qf --rbits "$QF_RB_FIXED" --neg "$neg" \
    --ops "$OPS_READ" --runs "$RUNS" --out "$OUTDIR/thr_vs_neg.csv"
done

LOADS=(0.40 0.55 0.70 0.80 0.85 0.90 0.95)

for lf in "${LOADS[@]}"; do
  echo "[load sweep] load=$lf"
  $PIN "$BIN" --filter cuckoo --fpbits "$CUCKOO_FP_FIXED" --load "$lf" \
    --ops "$OPS_LOAD" --runs "$RUNS" --out "$OUTDIR/cuckoo_load.csv"
  $PIN "$BIN" --filter qf --rbits "$QF_RB_FIXED" --load "$lf" \
    --ops "$OPS_LOAD" --runs "$RUNS" --out "$OUTDIR/qf_load.csv"
done

QFRACS=(0.5 0.7 0.9)

for qfrac in "${QFRACS[@]}"; do
  echo "[mixed ops] qfrac=$qfrac"
  $PIN "$BIN" --filter cuckoo --fpbits "$CUCKOO_FP_FIXED" --qfrac "$qfrac" \
    --ops "$OPS_MIX" --runs "$RUNS" --out "$OUTDIR/cuckoo_mixed.csv"
  $PIN "$BIN" --filter qf --rbits "$QF_RB_FIXED" --qfrac "$qfrac" \
    --ops "$OPS_MIX" --runs "$RUNS" --out "$OUTDIR/qf_mixed.csv"
done

echo
echo "DONE: wrote CSVs to $OUTDIR/"
echo "Next: run ../scripts/plot_a3.sh from build/ to generate plots."
