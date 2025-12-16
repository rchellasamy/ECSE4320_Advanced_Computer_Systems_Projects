#!/usr/bin/env bash
set -u

BIN="${BIN:-./bench}"
OUT="${OUT:-results/results.csv}"

REPS="${REPS:-7}"
WARMUP="${WARMUP:-1}"
OPS_PER_THREAD="${OPS_PER_THREAD:-500000}"
READ_PCT_MIXED="${READ_PCT_MIXED:-70}"

KEYS_LIST=(10000 100000 1000000)
THREADS_LIST=(1 2 4 8 16)
WORKLOADS=(lookup insert mixed)
MODES=(coarse striped)

mkdir -p "$(dirname "$OUT")"

PERF_EVENTS=("cycles" "instructions" "cache-references" "cache-misses")

echo "mode,workload,keys,threads,read_pct,ops_per_thread,throughput_ops_per_s,cycles,instructions,cache_references,cache_misses" > "$OUT"

if [[ ! -x "$BIN" ]]; then
  echo "ERROR: benchmark binary not found/executable at: $BIN" >&2
  echo "Tip: run 'make' or set BIN=./path/to/binary" >&2
  exit 1
fi

have_perf=0
if command -v perf >/dev/null 2>&1; then
  if perf stat -x, -e cycles -- true >/dev/null 2>&1; then
    have_perf=1
  fi
fi

echo "Perf enabled: $have_perf"
echo "Binary: $BIN"

run_once() {
  local mode="$1" workload="$2" keys="$3" threads="$4" read_pct="$5"
  "$BIN" --mode "$mode" --workload "$workload" --keys "$keys" --threads "$threads" \
         --read_pct "$read_pct" --ops_per_thread "$OPS_PER_THREAD"
}

median_from_file() {
  python3 - "$1" <<'PY'
import sys, statistics, math
path=sys.argv[1]
vals=[]
with open(path) as f:
    for line in f:
        try:
            x=float(line.strip())
            if math.isfinite(x):
                vals.append(x)
        except:
            pass
print(statistics.median(vals) if vals else "nan")
PY
}

get_ev_csv() {
  awk -F, -v ev="$2" '$3==ev{gsub(/ /,"",$1); print $1; exit}' "$1"
}

time_one_run_seconds() {
  local mode="$1" workload="$2" keys="$3" threads="$4" read_pct="$5"
  python3 - <<PY
import subprocess, time, math, sys
cmd = ["$BIN",
       "--mode","$mode",
       "--workload","$workload",
       "--keys","$keys",
       "--threads","$threads",
       "--read_pct","$read_pct",
       "--ops_per_thread","$OPS_PER_THREAD"]
t0=time.perf_counter()
try:
    r=subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    print("nan"); sys.exit(0)
t1=time.perf_counter()
if r.returncode != 0:
    print("nan")
else:
    print(t1-t0)
PY
}

for mode in "${MODES[@]}"; do
  for workload in "${WORKLOADS[@]}"; do
    for keys in "${KEYS_LIST[@]}"; do
      for threads in "${THREADS_LIST[@]}"; do

        read_pct="$READ_PCT_MIXED"
        if [[ "$workload" == "lookup" ]]; then read_pct=100; fi
        if [[ "$workload" == "insert" ]]; then read_pct=0; fi

        if [[ "$WARMUP" -gt 0 ]]; then
          for _ in $(seq 1 "$WARMUP"); do
            run_once "$mode" "$workload" "$keys" "$threads" "$read_pct" >/dev/null 2>&1 || true
          done
        fi

        tmp=$(mktemp)
        for _ in $(seq 1 "$REPS"); do
          secs=$(time_one_run_seconds "$mode" "$workload" "$keys" "$threads" "$read_pct")
          if [[ "$secs" == "nan" ]]; then
            echo "nan" >> "$tmp"
          else
            python3 - <<PY >> "$tmp"
secs=float("$secs")
ops=float($threads) * float($OPS_PER_THREAD)
print(ops/secs if secs>0 else float("nan"))
PY
          fi
        done

        med=$(median_from_file "$tmp")
        rm -f "$tmp"

        cycles="NA"; instr="NA"; cref="NA"; cmiss="NA"

        if [[ "$have_perf" -eq 1 ]]; then
          pfile=$(mktemp)
          perf stat -x, -e "$(IFS=,; echo "${PERF_EVENTS[*]}")" \
            "$BIN" --mode "$mode" --workload "$workload" --keys "$keys" --threads "$threads" \
                  --read_pct "$read_pct" --ops_per_thread "$OPS_PER_THREAD" \
            >/dev/null 2>"$pfile" || true

          cycles=$(get_ev_csv "$pfile" "cycles"); [[ -z "$cycles" ]] && cycles="NA"
          instr=$(get_ev_csv "$pfile" "instructions"); [[ -z "$instr" ]] && instr="NA"
          cref=$(get_ev_csv "$pfile" "cache-references"); [[ -z "$cref" ]] && cref="NA"
          cmiss=$(get_ev_csv "$pfile" "cache-misses"); [[ -z "$cmiss" ]] && cmiss="NA"
          rm -f "$pfile"
        fi

        echo "$mode,$workload,$keys,$threads,$read_pct,$OPS_PER_THREAD,$med,$cycles,$instr,$cref,$cmiss" >> "$OUT"
        echo "done: $mode $workload keys=$keys thr=$threads median=$med"
      done
    done
  done
done

echo "DONE. Wrote $OUT"
