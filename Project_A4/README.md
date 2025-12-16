# Project A4: Concurrent Data Structures and Memory Coherence

**Course:** ECSE 4320/6320 – Advanced Computer Systems
**Author:** Rithvik Chellasamy
**Platform:** WSL2 (Ubuntu on x86-64)
**Compiler:** g++ (version recorded in results CSV)

---

## 1. Overview

Modern multicore systems rely on shared in-memory data structures accessed concurrently by many threads. While hardware cache coherence ensures correctness at the cache-line level, *scalability and performance* depend critically on synchronization design and lock granularity.

This project implements and evaluates a **thread-safe hash table** under two synchronization strategies:

1. **Coarse-grained locking**: a single global mutex protecting all operations
2. **Lock striping**: multiple mutexes protecting disjoint subsets of buckets

We study how these designs behave under different workloads, thread counts, and data set sizes, and interpret results using **cache-coherence effects** and **Amdahl’s Law**.

---

## 2. Data Structure & Correctness Invariants

### Hash Table Design

* Separate chaining with singly linked lists
* Fixed-size value payloads
* Integer keys

### Supported Operations

* `insert(key, value)`
* `find(key)`
* `erase(key)`

### Correctness Invariants

**Coarse-Grained Version**

* A single global `std::mutex` guards the entire table
* At most one thread may execute any operation at a time
* Guarantees linearizability by construction

**Striped Lock Version**

* The table is divided into `STRIPES = 64` lock stripes
* Each bucket maps deterministically to exactly one stripe
* Each operation acquires **exactly one mutex**
* No nested locking → no deadlock

### Memory Safety

* Nodes are allocated and freed only while holding the relevant lock
* No pointers escape a protected critical section
* No memory reclamation races are possible under this locking scheme

---

## 3. Synchronization Strategies

### Coarse-Grained Locking (Baseline)

All operations acquire a single global mutex:

* Simple and correct
* Minimal bookkeeping
* Maximum contention

This design is expected to scale poorly due to serialization of all operations.

### Lock Striping (Improved Design)

Lock striping reduces contention by partitioning the hash table:

* Threads operating on different stripes proceed in parallel
* Critical sections are shorter and less contended
* Still simple enough to reason about correctness

This design trades slightly higher overhead for substantially improved scalability.

---

## 4. Experimental Methodology

### Workloads

Each experiment runs against a **single shared hash table**:

1. **Lookup-only**: 100% `find` operations (read-dominated)
2. **Insert-only**: 100% `insert` operations (write stress test)
3. **Mixed (70/30)**: 70% `find`, 30% updates (`insert` / `erase`)

### Parameters

* **Key set sizes:** 10⁴, 10⁵, 10⁶
* **Threads:** 1, 2, 4, 8, 16
* **Repetitions:** multiple runs per configuration
* **Warm-up:** initial iterations discarded

### Metrics

* Throughput (operations per second)
* Speedup relative to 1 thread
* `perf stat` counters where available:

  * cycles
  * instructions
  * cache references / misses

### Note on WSL2 and `perf`

Experiments were conducted under **WSL2**, which limits access to some hardware performance counters. While `cycles`, `instructions`, and cache metrics were available in this environment, results should be interpreted with this abstraction layer in mind. Where necessary, cache-coherence effects are inferred from scaling behavior rather than raw event counts.

---

## 5. Results: Key Set Size = 10⁴

### Lookup-Only Workload

![Lookup 1e4](results/lookup_1e4_throughput.png)

**Analysis:**

* Coarse-grained locking saturates early due to full serialization
* Striped locking scales to higher thread counts
* Read-only workload still suffers contention under a global lock

### Insert-Only Workload

![Insert 1e4](results/insert_1e4_throughput.png)

**Analysis:**

* Writes amplify contention and coherence traffic
* Striping reduces invalidation pressure by localizing updates

### Mixed Workload (70/30)

![Mixed 1e4](results/mixed_1e4_throughput.png)

**Analysis:**

* Performance lies between lookup-only and insert-only cases
* Striping provides consistent gains across thread counts

---

## 6. Results: Key Set Size = 10⁵

### Lookup-Only Workload

![Lookup 1e5](results/lookup_1e5_throughput.png)

**Analysis:**

* Larger tables reduce cache residency
* Coarse-grained design becomes bottlenecked even earlier

### Insert-Only Workload

![Insert 1e5](results/insert_1e5_throughput.png)

**Analysis:**

* Increased working set magnifies coherence overhead
* Striping maintains higher throughput under contention

### Mixed Workload (70/30)

![Mixed 1e5](results/mixed_1e5_throughput.png)

**Analysis:**

* Mixed workloads highlight the cost of serialized updates
* Lock striping amortizes synchronization overhead

---

## 7. Results: Key Set Size = 10⁶

### Lookup-Only Workload

![Lookup 1e6](results/lookup_1e6_throughput.png)

**Analysis:**

* Memory-bound behavior dominates
* Coarse-grained locking shows near-zero scalability

### Insert-Only Workload

![Insert 1e6](results/insert_1e6_throughput.png)

**Analysis:**

* Frequent cache-line invalidations under global locking
* Striping significantly reduces coherence traffic per operation

### Mixed Workload (70/30)

![Mixed 1e6](results/mixed_1e6_throughput.png)

**Analysis:**

* Represents realistic database-style access
* Striping consistently outperforms coarse locking

---

## 8. Speedup and Amdahl’s Law

Across all key sizes, the coarse-grained design exhibits minimal speedup beyond 2 threads. This behavior is predicted by **Amdahl’s Law**: as the serialized fraction of execution dominates, additional cores provide diminishing returns.

In contrast, lock striping reduces the serialized fraction, shifting the scalability limit and enabling higher parallel efficiency.

---

## 9. Cache Coherence Interpretation

Observed trends align with coherence theory:

* Global locking causes frequent cache-line invalidations
* Writes force exclusive ownership, stalling other cores
* Striping localizes coherence traffic to independent stripes
* Larger key sets exacerbate cache miss penalties

These effects explain why improvements are largest for write-heavy and mixed workloads.

---

## 10. Summary of Findings

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

This project demonstrates that synchronization granularity is a first-order performance concern on multicore systems. While coarse-grained locking ensures correctness, it severely limits scalability due to contention and cache-coherence traffic. Lock striping provides a practical and effective improvement, balancing correctness, performance, and implementation complexity.

---

## References

* M. Herlihy and N. Shavit, *The Art of Multiprocessor Programming*
* Intel® 64 and IA-32 Architectures Optimization Manual
* Linux `pthread_mutex` documentation
