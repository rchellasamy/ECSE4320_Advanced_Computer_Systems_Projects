#!/usr/bin/env bash
set -euo pipefail
BIN="${BIN:-./build/amq_bench}"
OUT="${OUT:-results.csv}"

python3 "$(dirname "$0")/run_full_sweeps.py" --bin "$BIN" --out "$OUT"
