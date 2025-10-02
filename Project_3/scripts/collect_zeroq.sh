#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
fio --name=randread_4k_qd1 --rw=randread  --bs=4k   --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/zeroq_randread_4k_qd1.json
fio --name=randwrite_4k_qd1 --rw=randwrite --bs=4k   --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/zeroq_randwrite_4k_qd1.json
fio --name=seqread_128k_qd1 --rw=read      --bs=128k --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/zeroq_seqread_128k_qd1.json
fio --name=seqwrite_128k_qd1 --rw=write    --bs=128k --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/zeroq_seqwrite_128k_qd1.json
