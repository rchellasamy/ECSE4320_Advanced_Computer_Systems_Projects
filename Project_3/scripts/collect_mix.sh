#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
fio --name=mix_R100_4k_qd32  --rw=randread  --rwmixread=100 --bs=4k --iodepth=32 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/mix_R100_4k_qd32.json
fio --name=mix_R70W30_4k_qd32 --rw=randrw   --rwmixread=70  --bs=4k --iodepth=32 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/mix_R70W30_4k_qd32.json
fio --name=mix_R50W50_4k_qd32 --rw=randrw   --rwmixread=50  --bs=4k --iodepth=32 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/mix_R50W50_4k_qd32.json
fio --name=mix_W100_4k_qd32  --rw=randwrite --rwmixread=0   --bs=4k --iodepth=32 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/mix_W100_4k_qd32.json
