
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
#include <chrono>
#include <random>
#include <cstdio>

struct RunResult {
  double median_ms;
  double stdev_ms;
  double gflops;
  double cpe;       // cycles per element (if CPU_GHZ provided), else -1
  double out_scalar; // for reductions; optional
};

// allocate aligned memory (free with free())
void* aligned_alloc_bytes(size_t alignment, size_t bytes);

// misalign a pointer view by a given byte offset (not owning)
template <typename T>
T* misalign_ptr(T* p, size_t byte_off) {
  return reinterpret_cast<T*>(reinterpret_cast<uintptr_t>(p) + byte_off);
}

double now_ms();

// generate non-trivial data
template <typename T>
void fill_data(std::vector<T>& v) {
  std::mt19937 rng(12345);
  std::uniform_real_distribution<double> dist(0.1, 1.3);
  for (auto& x : v) x = T(dist(rng));
}

// compute basic stats
void median_stdev(const std::vector<double>& xs, double& median, double& stdev);

// write CSV header if file not exists
void ensure_csv_header(const std::string& path, const std::string& header);

