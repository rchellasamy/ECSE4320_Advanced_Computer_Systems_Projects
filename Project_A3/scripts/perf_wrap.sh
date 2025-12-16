#!/usr/bin/env bash
set -euo pipefail

BIN="${BIN:-./build/amq_bench}"
OUT="${OUT:-perf_results.csv}"

if [[ "${1:-}" != "--" ]]; then
  echo "usage: $0 -- <amq_bench args...>" >&2
  exit 2
fi
shift

EVENTS="cycles,instructions,branches,branch-misses,cache-references,cache-misses,L1-dcache-load-misses,dTLB-load-misses"
TMP=$(mktemp)
perf stat -x, -e "$EVENTS" "$BIN" "$@" 2> "$TMP" 1>/dev/null

if [[ ! -f "$OUT" ]]; then
  echo "event,value,unit" > "$OUT"
fi

grep -E "^[0-9]" "$TMP" | awk -F, '{print $3","$1","$2}' >> "$OUT"
rm -f "$TMP"
echo "appended perf stats to $OUT"
