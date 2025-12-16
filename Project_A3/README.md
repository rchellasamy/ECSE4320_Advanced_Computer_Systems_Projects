Project A3: Approximate Membership Filters

Bloom vs XOR vs Cuckoo vs Quotient

Author: Rithvik Chellasamy
System: x86-64 laptop (Linux / WSL2)
Compiler: g++ with -O3
Benchmark: amq_bench (custom harness)

1. Overview

Approximate membership filters (AMQs) answer set membership queries with no false negatives and controlled false positives, trading accuracy for space and speed. Modern systems rely on AMQs for indexing, caching, and networking, where memory footprint and throughput are critical.

The goal of this project is to empirically evaluate four AMQ designs under a common benchmark harness:

Blocked Bloom Filter

XOR Filter

Cuckoo Filter

Quotient Filter

The evaluation focuses on:

Space vs false positive tradeoffs

Lookup throughput under varying workloads

Dynamic behavior under load and mixed operations

All results are measured experimentally rather than inferred from theory.

2. Reproducibility and Experimental Control

To ensure meaningful comparisons:

All filters store 1,000,000 uniformly random 64-bit keys

False positives are measured using an independent negative query set

Benchmarks are single-threaded to isolate data structure behavior

Each configuration is repeated and averaged

All filters are tuned using their natural control parameter

Filter tuning parameters

Bloom filter: target false positive rate

XOR filter: fingerprint size (bits)

Cuckoo filter: fingerprint size (bits)

Quotient filter: remainder size (bits)

This avoids unfair comparisons caused by mismatched configurations.

3. Build and Run Instructions

From the repository root:

mkdir build
cd build
cmake ..
cmake --build . -j
./validate


To reproduce all results and plots:

../scripts/run_a3_all.sh
../scripts/plot_a3.sh

4. Experiment 1: Space vs Accuracy
Question

How do different AMQ designs trade memory usage for false positive rate?

Methodology

Each filter is configured across a sweep of accuracy parameters

Bits per entry (BPE) is computed from the actual memory footprint

Achieved false positive rate is measured empirically using negative queries

Results

Analysis

Bloom filters achieve the lowest bits per entry at moderate false positive rates, reflecting their minimal metadata overhead. However, Bloom filters are static and do not support deletions.

XOR filters show very high throughput but coarse accuracy control. Increasing fingerprint size significantly increases space usage while only modestly improving false positive rate, producing a near-vertical tradeoff curve.

Cuckoo filters exhibit a smooth and predictable tradeoff. Increasing fingerprint size linearly increases space while exponentially reducing false positives, making Cuckoo filters effective when deletions are required.

Quotient filters follow a similar trend to Cuckoo filters but require additional metadata to encode runs. This results in consistently higher space usage at comparable false positive rates.

Takeaway

Bloom filters are most space-efficient when deletions are not required.
Cuckoo and Quotient filters trade additional space for dynamic updates.
XOR filters prioritize speed over flexibility.

5. Experiment 2: Throughput vs Negative Lookup Share
Question

How does lookup throughput change as the fraction of negative queries varies?

Methodology

Lookup workloads are generated with varying fractions of negative queries

All filters are fixed to comparable accuracy levels

Throughput is measured as operations per second

Results

Analysis

Bloom and XOR filters achieve the highest throughput overall due to predictable memory access and early termination on negative queries.

Throughput for Bloom and XOR dips near a 50/50 mix of positive and negative queries. This reflects poor branch predictability and mixed cache behavior, which increase pipeline stalls.

Cuckoo filter throughput remains relatively flat because each lookup probes two buckets regardless of outcome.

Quotient filter throughput improves slightly as the fraction of negative queries increases. Negative lookups often terminate early, while positive lookups may require scanning contiguous runs.

Takeaway

Lookup performance depends not only on algorithmic complexity, but also on control-flow predictability and memory access patterns.

6. Experiment 3: Dynamic Behavior Under Load
Question

How do dynamic AMQs behave as load factor increases?

Methodology

Only dynamic filters (Cuckoo and Quotient) are evaluated

Load factor is increased gradually while measuring throughput and failures

Analysis

Cuckoo filters experience increasing eviction pressure as load increases. Throughput degrades and insertion failures appear near capacity.

Quotient filters degrade more smoothly. As load increases, clusters grow and scans become longer, reducing throughput without sudden failure.

Takeaway

Cuckoo filters are sensitive to high load, while Quotient filters offer more predictable degradation at the cost of additional space.

7. Summary of Findings
Filter	Strengths	Weaknesses
Bloom	Best space efficiency, simple	No deletions
XOR	Extremely fast, compact	Static, coarse accuracy control
Cuckoo	Supports deletions, tunable accuracy	Sensitive to high load
Quotient	Dynamic, cache-friendly, predictable	Higher metadata overhead

No single AMQ dominates across all metrics. The appropriate choice depends on update requirements, space constraints, and workload composition.

8. Conclusion

This project demonstrates that approximate membership filters exhibit fundamentally different tradeoffs when evaluated under realistic workloads. By measuring space usage, false positives, and throughput directly, the results highlight how algorithmic design interacts with memory layout and workload characteristics.

Empirical evaluation reveals behaviors that are not obvious from asymptotic analysis alone, underscoring the importance of systems-level benchmarking.