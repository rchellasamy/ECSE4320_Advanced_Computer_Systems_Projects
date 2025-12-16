# Project A4: Concurrent Data Structures and Memory Coherence

**Course:** ECSE 4320 – Advanced Computer Systems  
**Author:** Rithvik Chellasamy

---

## 1. Overview

Modern multicore programs rely on shared in-memory data structures that are accessed concurrently by many threads. While hardware cache coherence guarantees correctness at the cache-line level, overall performance and scalability depend on **synchronization strategy, lock granularity, and contention patterns**.

In this project, I implement and evaluate a **thread-safe hash table** under two synchronization designs:

1. **Coarse-grained locking** using a single global mutex
2. **Lock striping** using multiple independent mutexes

By running controlled multithreaded workloads, this project studies how these designs scale with thread count and workload mix, and explains observed behavior using **cache coherence effects** and **Amdahl’s Law**.

---

## 2. Data Structure and Correctness

### Hash Table Design

* Separate chaining with singly linked lists
* Integer keys and fixed-size values
* Fixed bucket count per experiment

### Supported Operations

* `insert(key, value)`
* `find(key)`
* `erase(key)`

### Correctness Invariants

**Coarse-Grained Version**

* A single global `std::mutex` guards the entire table
* At most one operation executes at any time
* Linearizability follows directly from mutual exclusion

**Striped Lock Version**

* The table is partitioned into a fixed number of lock stripes
* Each bucket maps deterministically to exactly one stripe
* Each operation acquires exactly one mutex
* No nested locking, so deadlock is impossible

All node allocation and reclamation occurs while holding the appropriate lock, preventing memory races.

---

## 3. Synchronization Strategies

### Coarse-Grained Locking (Baseline)

This design prioritizes simplicity:

* Minimal bookkeeping
* Straightforward correctness reasoning
* Maximum contention under concurrency

Because all operations serialize, scalability is expected to be poor as thread count increases.

### Lock Striping (Improved Design)

Lock striping reduces contention by allowing operations on different parts of the table to proceed independently:

* Contention is localized to individual stripes
* Critical sections are shorter
* Synchronization overhead increases slightly

This design aims to improve scalability while preserving correctness and simplicity.

---

## 4. Experimental Methodology

### Workloads

All experiments operate on a **single shared hash table**:

1. **Lookup-only**: 100% `find` operations
2. **Insert-only**: 100% `insert` operations
3. **Mixed (70/30)**: 70% lookups, 30% updates

### Parameters

* Key set sizes: 10⁴, 10⁵, 10⁶
* Threads: 1, 2, 4, 8, 16
* Multiple repetitions per configuration
* Initial warm-up iterations discarded

### Metrics

* Throughput (operations per second)
* Speedup relative to single-thread performance
* Cache-miss metrics where available

### Note on Measurement Environment

Experiments were conducted under WSL2, which imposes some abstraction over hardware counters. Scaling trends and throughput behavior are therefore emphasized over absolute counter values, and coherence effects are inferred from performance patterns.

---

## 5. Results (Key Set Size = 10⁴)

### Lookup-Only Workload

![Lookup 1e4](results/lookup_1e4_throughput.png)

**Analysis:**

The coarse-grained design saturates quickly because all lookups serialize. Lock striping allows parallel reads across independent stripes, improving throughput as threads increase.

### Insert-Only Workload

![Insert 1e4](results/insert_1e4_throughput.png)

**Analysis:**

Write-heavy workloads amplify contention and cache invalidation. Lock striping reduces the scope of invalidations, leading to higher throughput.

### Mixed Workload (70/30)

![Mixed 1e4](results/mixed_1e4_throughput.png)

**Analysis:**

Performance lies between lookup-only and insert-only cases. Striping consistently outperforms coarse locking.

---

## 6. Results (Key Set Size = 10⁵)

### Lookup-Only Workload

![Lookup 1e5](results/lookup_1e5_throughput.png)

**Analysis:**

As the table grows, cache locality decreases and synchronization overhead dominates earlier. Coarse-grained locking becomes a bottleneck at low thread counts.

### Insert-Only Workload

![Insert 1e5](results/insert_1e5_throughput.png)

**Analysis:**

Larger working sets increase cache-miss penalties. Striping mitigates contention by limiting coherence traffic to individual stripes.

### Mixed Workload (70/30)

![Mixed 1e5](results/mixed_1e5_throughput.png)

---

## 7. Results (Key Set Size = 10⁶)

### Lookup-Only Workload

![Lookup 1e6](results/lookup_1e6_throughput.png)

**Analysis:**

The workload becomes memory-bound. Coarse-grained locking shows almost no scalability, while striping continues to provide modest gains.

### Insert-Only Workload

![Insert 1e6](results/insert_1e6_throughput.png)

**Analysis:**

Global locking triggers frequent cache-line invalidations. Lock striping reduces invalidation scope, improving throughput.

### Mixed Workload (70/30)

![Mixed 1e6](results/mixed_1e6_throughput.png)

---

## 8. Speedup and Amdahl’s Law

Across all configurations, the coarse-grained design exhibits minimal speedup beyond a small number of threads. This behavior aligns with **Amdahl’s Law**, as the serialized critical section dominates execution time.

Lock striping reduces the serialized fraction, shifting the scalability limit and enabling higher parallel efficiency.

---

## 9. Cache Coherence Interpretation

Observed trends are consistent with coherence behavior:

* Global locks cause frequent cache-line invalidations
* Writes require exclusive ownership, stalling other cores
* Striping localizes coherence traffic
* Larger key sets amplify cache-miss penalties

These effects explain why striping provides the largest benefits under write-heavy and mixed workloads.

---

## 10. Summary

| Design        | Scalability | Contention | Complexity |
| ------------- | ----------- | ---------- | ---------- |
| Coarse Lock   | Poor        | High       | Low        |
| Lock Striping | Good        | Moderate   | Moderate   |

---

## 11. Reproducibility

```bash
make
./scripts/sweep.sh
```

All results are generated automatically and stored as CSV and PNG files under `results/`.

---

## 12. Conclusion

This project demonstrates that synchronization granularity is a first-order performance concern in concurrent systems. While coarse-grained locking ensures correctness with minimal complexity, it severely limits scalability. Lock striping offers a practical improvement by reducing contention and coherence traffic, providing better performance while remaining relatively simple to reason about.

---

## References

* M. Herlihy and N. Shavit, *The Art of Multiprocessor Programming*
* Intel® 64 and IA-32 Architectures Optimization Manual
* Linux `pthread_mutex` documentation
