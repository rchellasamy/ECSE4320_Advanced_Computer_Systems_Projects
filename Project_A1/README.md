# Project A1: Advanced OS & CPU Feature Exploration

**Author:** Rithvik Chellasamy
**System:** WSL2 (Ubuntu), x86-64 laptop CPU
**Kernel:** WSL2 Linux kernel (documented via `uname -a`)
**Compiler:** `g++` (version recorded by scripts)

---

## 1. Overview

Modern CPUs and operating systems expose numerous mechanisms that directly affect performance, isolation, and scalability. The goal of this project is to *empirically explore* these mechanisms using **custom microbenchmarks**, rather than relying on canned benchmarks.

This repository contains **four independent experiments**, each targeting a different OS or CPU feature from the provided menu:

1. **CPU Affinity & Scheduling Effects**
2. **SMT (Simultaneous Multithreading) Interference**
3. **Memory Management & Stride Sensitivity (MMU / THP effects)**
4. **Microarchitectural Prefetcher Effects**

Each experiment is designed with controlled variables, automated data collection, and quantitative analysis. Results are presented as plots and CSV tables, with interpretation grounded in OS and microarchitectural principles.

---

## 2. Reproducibility & Environment Control

To minimize variability:

* Benchmarks are **CPU-pinned** using `sched_setaffinity`
* Workloads are single-purpose and short-lived
* Multiple repetitions are averaged per configuration
* System metadata (CPU model, kernel, compiler) is auto-recorded

### Note on WSL2 and `perf`

This project was executed under **WSL2**, which restricts access to many hardware performance counters. As a result:

* `perf stat` is limited primarily to **cycle counts**
* Cache, TLB, and LLC counters are unavailable or unreliable

Rather than fabricating incomplete data, this project:

* Uses **cycle counts and wall-clock timing** as primary metrics
* Infers cache, TLB, and SMT effects *indirectly* via controlled experiments
* Explicitly documents these limitations as part of experimental rigor

This trade-off is discussed in each analysis section.

---

## 3. Build & Run Instructions

```bash
make
python3 scripts/run_collect.py
```

This will:

* Compile all benchmarks in `src/`
* Run experiments across parameter sweeps
* Store raw data in `results/*.csv`
* Generate plots in `results/*.png`

---

## 4. Experiment 1: CPU Affinity & Scheduling

### Question

How does CPU affinity affect execution stability and performance consistency?

### Methodology

* A CPU-bound loop is executed repeatedly
* Two configurations:

  * **Unpinned** (scheduler chooses CPU)
  * **Pinned** to a single core
* Execution time (cycles) is measured across trials

### Results

![CPU Affinity Results](results/affinity.png)

### Analysis

Pinned execution shows **lower variance** and slightly improved mean performance. This is expected:

* Without affinity, the Linux scheduler may migrate the thread
* Migration causes **cold caches**, pipeline refill, and TLB disruption
* With affinity, cache locality is preserved across runs

Even under WSL2, where scheduling is mediated by the host OS, the benefits of reduced migration are observable.

### Takeaway

CPU affinity improves *performance predictability*, even when raw throughput gains are modest.

---

## 5. Experiment 2: SMT (Simultaneous Multithreading) Interference

### Question

How does a competing SMT sibling affect execution throughput?

### Methodology

* A primary compute thread runs on a core
* A secondary "interferer" thread is optionally scheduled on the SMT sibling
* Both threads are pinned to the same physical core (different logical CPUs)

### Results

![SMT Interference Results](results/smt.png)

### Analysis

When the sibling thread is active, execution time increases significantly. This demonstrates classic SMT contention:

* Execution units, caches, and decode bandwidth are shared
* Even simple competing loops can reduce IPC

Despite limited perf counters, the **magnitude of slowdown** strongly indicates resource contention rather than scheduling noise.

### Takeaway

SMT improves throughput under multiprogramming but **reduces per-thread performance isolation**.

---

## 6. Experiment 3: Memory Management & Stride Sensitivity

### Question

How does memory access stride expose TLB and page-level effects?

### Methodology

* Traverse a large array with varying strides
* Measure cycles per access
* Transparent Huge Pages (THP) status is detected but not forced

### Results

![MMU / Stride Results](results/mmu.png)

### Analysis

As stride increases:

* Cache line utilization drops
* TLB pressure increases
* Access latency rises sharply at page-scale strides

If THP is enabled, the effective TLB reach increases, delaying the performance cliff. Under WSL2, THP behavior is partially abstracted, but stride-induced effects remain visible.

### Takeaway

Memory performance is shaped as much by **address translation** as by raw cache size.

---

## 7. Experiment 4: Prefetcher Effects

### Question

How does access regularity influence hardware prefetching?

### Methodology

* Compare sequential vs irregular access patterns
* Same data size, same working set
* Measure execution cycles

### Results

![Prefetcher Results](results/prefetch.png)

### Analysis

Sequential access benefits from aggressive hardware prefetching:

* Cache lines are fetched ahead of demand
* Memory-level parallelism increases

Irregular access defeats the prefetcher, exposing true memory latency. The clear performance gap confirms effective prefetch behavior even without direct counter access.

### Takeaway

Access pattern regularity is critical for extracting memory bandwidth.

---

## 8. Summary of Findings

| Feature      | Observed Effect                                  |
| ------------ | ------------------------------------------------ |
| CPU Affinity | Reduced variance, better cache locality          |
| SMT          | Significant per-thread slowdown under contention |
| MMU / THP    | Stride reveals TLB and page effects              |
| Prefetcher   | Sequential access dramatically faster            |

---

## 9. Limitations & Future Work

* Full cache/TLB counters unavailable under WSL2
* NUMA and DDIO experiments require bare-metal or cloud hardware
* Future work could repeat these experiments on native Linux for deeper perf analysis

---

## 10. Conclusion

This project demonstrates that carefully designed microbenchmarks can reveal deep OS and CPU behavior even under constrained environments. By controlling variables, documenting limitations, and grounding analysis in hardware principles, meaningful insights can be extracted without privileged access.

---

## References

* Linux `sched_setaffinity(2)`
* Intel® 64 and IA-32 Architectures Optimization Manual
* Linux kernel documentation on THP and SMT
