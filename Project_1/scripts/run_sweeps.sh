#!/usr/bin/env bash
set -euo pipefail

# Build auto-vectorized
cmake -S . -B build
cmake --build build -j

# Build scalar
cmake -S . -B build-scalar -DBUILD_SCALAR=ON
cmake --build build-scalar -j

CSV="data/results.csv"
rm -f "$CSV"

CPU_GHZ=${CPU_GHZ:-3.5}

# Sizes to cross L1/L2/LLC/DRAM (adjust to your CPU)
SIZES=("16384" "65536" "262144" "1048576" "4194304" "16777216")

for build in auto scalar; do
  EXE="./build/simd_profile"
  if [[ "$build" == "scalar" ]]; then EXE="./build-scalar/simd_profile"; fi

  for kernel in saxpy dot ewmul stencil3; do
    for dtype in f32 f64; do
      for align in aligned misaligned; do
        for stride in 1 2 4 8; do
          for N in "${SIZES[@]}"; do
            "$EXE" --kernel "$kernel" --dtype "$dtype" --align "$align" \
              --stride "$stride" --N "$N" --trials 5 --warmups 1 \
              --build-label "$build" --csv "$CSV" --cpu-ghz "$CPU_GHZ"
          done
        done
      done
    done
  done
done

echo "Wrote $CSV"
