# Advanced Computer Systems Projects (Fall 2025)

This repository contains my work for three major projects in ECSE 4320/6320: Advanced Computer Systems. Each project explores a different aspect of system performance profiling and analysis. Altogether, I spent around **60 hours** across the three projects. The time was mostly divided between learning the tools (`fio`, Intel MLC, custom profiling scripts), running experiments, cleaning and parsing results, and writing up the explanations.

---

## Repository Organization

- **Project 1: SIMD Profiling**  
  Focuses on measuring and analyzing SIMD performance across different kernels (e.g., SAXPY, dot product, stencil).  
  [See `Project 1/README.md`](Project%201/README.md) for details, results, and discussion.  

- **Project 2: Memory System Characterization**  
  Uses Intel’s MLC tool to characterize the memory hierarchy (latency, bandwidth, cache/TLB behavior).  
  [See `Project 2/README.md`](Project%202/README.md) for the full lab write-up.  

- **Project 3: SSD Profiling and Performance Characterization**  
  Profiles SSD behavior using `fio` under different access patterns, block sizes, and queue depths.  
  [See `Project 3/README.md`](Project%203/README.md) for methodology, plots, and analysis.  

Each folder contains:
- A `README.md` lab write-up answering all rubric items.  
- Data (`.csv`) and figures (`.png`) produced by the experiments.  
- Scripts used for running workloads and generating plots.  

---

## Notes and Caveats

- Some very large raw data files and binary outputs (e.g., multi-GB `.bin` files created for workloads) were **omitted from this repository due to GitHub size limits**. Because of this, re-running everything exactly as-is may not be fully reproducible unless those files are regenerated.  

- The figures and CSVs that are present are representative of real runs but have been trimmed to make the repo manageable. This keeps the results consistent with what I observed while still fitting GitHub constraints.  

- For the write-ups, I drafted all content myself. **ChatGPT was used only to help reformat my explanations into Markdown for GitHub (e.g., tables, figure links, and headings)**. The analysis, numbers, and reasoning are my own.  

---

## Effort and Reflection

Across all three projects, I gained hands-on experience with:
- Profiling tools (`fio`, Intel MLC, custom benchmarking scripts).  
- Understanding performance trade-offs in **SIMD execution, memory systems, and SSDs**.  
- Relating experimental data back to theory (queueing law, AMAT, cache/TLB reach, device-level behavior).  

These projects took about **60 hours total**, spread over several weeks. A lot of that time was spent debugging setup issues, cleaning data, and making sure the results matched what the rubrics asked for. In the end, I think the repository shows a complete and well-structured record of the work.  
