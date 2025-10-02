
#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
for pattern in seq rand; do
  for stride in 64 256 1024; do
    fio --name=gran_${pattern}_${stride} --rw=$([ "$pattern" = "seq" ] && echo read || echo randread) --bs=4k --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/gran_${pattern}_${stride}.json
  done
done
