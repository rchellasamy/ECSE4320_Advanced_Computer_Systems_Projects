#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <cmath>
#include <cassert>
#include <getopt.h>

#include "kernels.hpp"
#include "utils.hpp"

// Simple CLI:
// ./simd_profile --kernel saxpy --dtype f32 --align aligned --stride 1 --N 1048576 --trials 5 --warmups 1 --build-label auto --csv data/out.csv --cpu-ghz 3.6
//
// Build two variants:
//  - Auto-vectorized:   cmake -S . -B build && cmake --build build -j
//  - Scalar-only:       cmake -S . -B build-scalar -DBUILD_SCALAR=ON && cmake --build build-scalar -j

static struct option long_opts[] = {
  {"kernel", required_argument, 0, 'k'},
  {"dtype", required_argument, 0, 't'},
  {"align", required_argument, 0, 'a'},
  {"stride", required_argument, 0, 's'},
  {"N", required_argument, 0, 'n'},
  {"trials", required_argument, 0, 'r'},
  {"warmups", required_argument, 0, 'w'},
  {"build-label", required_argument, 0, 'b'},
  {"csv", required_argument, 0, 'c'},
  {"cpu-ghz", required_argument, 0, 'g'},
  {"min-ms", required_argument, 0, 'M'},  // NEW
  {0,0,0,0}
};

static Kernel parse_kernel(const std::string& s) {
  if (s == "saxpy") return Kernel::SAXPY;
  if (s == "dot")   return Kernel::DOT;
  if (s == "ewmul") return Kernel::EWMUL;
  if (s == "stencil3") return Kernel::STENCIL3;
  std::fprintf(stderr, "Unknown kernel: %s\n", s.c_str());
  std::exit(1);
}
static DType parse_dtype(const std::string& s) {
  if (s == "f32") return DType::F32;
  if (s == "f64") return DType::F64;
  std::fprintf(stderr, "Unknown dtype: %s\n", s.c_str());
  std::exit(1);
}

int main(int argc, char** argv) {
  std::string kernel_s = "saxpy";
  std::string dtype_s  = "f32";
  std::string align_s  = "aligned"; // or misaligned
  size_t stride = 1;
  size_t N = 1<<20;
  int trials = 5;
  int warmups = 1;
  std::string build_label = "auto";
  std::string csv_path = "data/results.csv";
  double cpu_ghz = -1.0;
  double min_ms  = 0.0;   // NEW: per-trial minimum elapsed ms (0 = disabled)

  int opt;
  while ((opt = getopt_long(argc, argv, "", long_opts, nullptr)) != -1) {
    switch (opt) {
      case 'k': kernel_s = optarg; break;
      case 't': dtype_s  = optarg; break;
      case 'a': align_s  = optarg; break;
      case 's': stride = std::strtoull(optarg, nullptr, 10); break;
      case 'n': N = std::strtoull(optarg, nullptr, 10); break;
      case 'r': trials = std::atoi(optarg); break;
      case 'w': warmups = std::atoi(optarg); break;
      case 'b': build_label = optarg; break;
      case 'c': csv_path = optarg; break;
      case 'g': cpu_ghz = std::atof(optarg); break;
      case 'M': min_ms  = std::atof(optarg); break;  // NEW
    }
  }

  Kernel K = parse_kernel(kernel_s);
  DType  T = parse_dtype(dtype_s);

  // Allocate input/output
  size_t elems = N;
  size_t elem_size = (T == DType::F32 ? sizeof(float) : sizeof(double));
  size_t bytes = elem_size * elems;

  const size_t alignment = 64;
  void* pA = aligned_alloc_bytes(alignment, bytes + 64); // +64 headroom for misalign view
  void* pB = aligned_alloc_bytes(alignment, bytes + 64);
  void* pC = aligned_alloc_bytes(alignment, bytes + 64);
  if (!pA || !pB || !pC) { std::fprintf(stderr, "alloc failed\n"); return 2; }

  // Prepare views
  bool mis = (align_s == "misaligned");
  size_t off = (T == DType::F32 ? 4 : 8); // 4B for float, 8B for double

  // Common outputs
  std::vector<double> times;
  times.reserve(trials);
  double a = 1.2345, b = 0.9876, c = -0.3333;
  double reduction_scalar = 0.0;

  if (T == DType::F32) {
    float* x = static_cast<float*>(pA);
    float* y = static_cast<float*>(pB);
    float* z = static_cast<float*>(pC);
    float* x_view = mis ? misalign_ptr(x, off) : x;
    float* y_view = mis ? misalign_ptr(y, off) : y;
    float* z_view = mis ? misalign_ptr(z, off) : z;
    std::vector<float> vx(elems), vy(elems), vz(elems);
    fill_data(vx); fill_data(vy); fill_data(vz);
    std::memcpy(x_view, vx.data(), elems * sizeof(float));
    std::memcpy(y_view, vy.data(), elems * sizeof(float));
    std::memcpy(z_view, vz.data(), elems * sizeof(float));

    auto run_once = [&]() {
      // For small-N repeat timing, keep y/z stable across reps
      std::vector<float> y0, z0;
      if (min_ms > 0.0 && (K == Kernel::SAXPY || K == Kernel::EWMUL)) {
        if (K == Kernel::SAXPY) { y0.resize(elems); std::memcpy(y0.data(), y_view, elems*sizeof(float)); }
        if (K == Kernel::EWMUL) { z0.resize(elems); std::memcpy(z0.data(), z_view, elems*sizeof(float)); }
      }

      double t0 = now_ms();
      int reps = 0;
      double last_reduce = 0.0;

      do {
        if (!y0.empty()) std::memcpy(y_view, y0.data(), elems*sizeof(float));
        if (!z0.empty()) std::memcpy(z_view, z0.data(), elems*sizeof(float));

        switch (K) {
          case Kernel::SAXPY:
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                saxpy_simd(float(a), x_view + j, y_view + j, 1);
              }
            }
            break;

          case Kernel::DOT: {
            double s = 0.0;
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                s += dot_simd(x_view + j, y_view + j, 1);
              }
            }
            last_reduce = s;
            } break;

          case Kernel::EWMUL:
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                ewmul_simd(x_view + j, y_view + j, z_view + j, 1);
              }
            }
            break;

          case Kernel::STENCIL3:
            stencil3_simd(x_view, y_view, elems, float(a), float(b), float(c));
            break;
        }
        reps++;
      } while ((now_ms() - t0) < min_ms);

      reduction_scalar = last_reduce;  // only meaningful for DOT
      double elapsed_ms = now_ms() - t0;
      return elapsed_ms / std::max(1, reps);
    };

    // Warmups + trials
    for (int i=0;i<warmups;i++) (void)run_once();
    for (int i=0;i<trials;i++) times.push_back(run_once());

    double median, stdev;
    median_stdev(times, median, stdev);

    // FLOPs: approximate
    double flops_per_elem = 0.0;
    switch (K) {
      case Kernel::SAXPY: flops_per_elem = 2.0; break;
      case Kernel::DOT:   flops_per_elem = 2.0; break;
      case Kernel::EWMUL: flops_per_elem = 1.0; break;
      case Kernel::STENCIL3: flops_per_elem = 5.0; break; // 3 mul + 2 add
    }
    double secs = median / 1000.0;
    double effective_elems = (K==Kernel::STENCIL3 ? double(elems) : std::ceil(double(elems)/double(stride)));
    double gflops = (effective_elems * flops_per_elem) / secs / 1e9;

    double cpe = -1.0;
    if (cpu_ghz > 0) {
      double cycles = secs * cpu_ghz * 1e9;
      cpe = cycles / effective_elems;
    }

    // correctness checksum for non-reduction kernels
    if (K == Kernel::SAXPY) {
      double s = 0.0; for (size_t i = 0; i < elems; i += stride) s += double(y_view[i]);
      reduction_scalar = s;
    } else if (K == Kernel::EWMUL) {
      double s = 0.0; for (size_t i = 0; i < elems; i += stride) s += double(z_view[i]);
      reduction_scalar = s;
    }

    ensure_csv_header(csv_path, "kernel,dtype,align,stride,N,build,median_ms,stdev_ms,gflops,cpe,reduce");
    FILE* f = std::fopen(csv_path.c_str(), "a");
    if (!f) { std::perror("fopen csv"); return 3; }
    std::fprintf(f, "%s,%s,%s,%zu,%zu,%s,%.6f,%.6f,%.6f,%.6f,%.6f\n",
      kernel_s.c_str(), dtype_s.c_str(), align_s.c_str(), stride, N, build_label.c_str(),
      median, stdev, gflops, cpe, reduction_scalar);
    std::fclose(f);

  } else {
    // ----- double -----
    double* x = static_cast<double*>(pA);
    double* y = static_cast<double*>(pB);
    double* z = static_cast<double*>(pC);
    double* x_view = mis ? misalign_ptr(x, off) : x;
    double* y_view = mis ? misalign_ptr(y, off) : y;
    double* z_view = mis ? misalign_ptr(z, off) : z;
    std::vector<double> vx(elems), vy(elems), vz(elems);
    fill_data(vx); fill_data(vy); fill_data(vz);
    std::memcpy(x_view, vx.data(), elems * sizeof(double));
    std::memcpy(y_view, vy.data(), elems * sizeof(double));
    std::memcpy(z_view, vz.data(), elems * sizeof(double));

    auto run_once = [&]() {
      std::vector<double> y0, z0;
      if (min_ms > 0.0 && (K == Kernel::SAXPY || K == Kernel::EWMUL)) {
        if (K == Kernel::SAXPY) { y0.resize(elems); std::memcpy(y0.data(), y_view, elems*sizeof(double)); }
        if (K == Kernel::EWMUL) { z0.resize(elems); std::memcpy(z0.data(), z_view, elems*sizeof(double)); }
      }

      double t0 = now_ms();
      int reps = 0;
      double last_reduce = 0.0;

      do {
        if (!y0.empty()) std::memcpy(y_view, y0.data(), elems*sizeof(double));
        if (!z0.empty()) std::memcpy(z_view, z0.data(), elems*sizeof(double));

        switch (K) {
          case Kernel::SAXPY:
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                saxpy_simd(a, x_view + j, y_view + j, 1);
              }
            }
            break;

          case Kernel::DOT: {
            double s = 0.0;
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                s += dot_simd(x_view + j, y_view + j, 1);
              }
            }
            last_reduce = s;
            } break;

          case Kernel::EWMUL:
            for (size_t i = 0; i < elems; i += stride) {
              size_t end = std::min(i+1, elems);
              for (size_t j = i; j < end; ++j) {
                ewmul_simd(x_view + j, y_view + j, z_view + j, 1);
              }
            }
            break;

          case Kernel::STENCIL3:
            stencil3_simd(x_view, y_view, elems, a, b, c);
            break;
        }
        reps++;
      } while ((now_ms() - t0) < min_ms);

      reduction_scalar = last_reduce;  // DOT
      double elapsed_ms = now_ms() - t0;
      return elapsed_ms / std::max(1, reps);
    };

    for (int i=0;i>warmups;i++) (void)run_once();
    for (int i=0;i<trials;i++) times.push_back(run_once());

    double median, stdev;
    median_stdev(times, median, stdev);

    double flops_per_elem = 0.0;
    switch (K) {
      case Kernel::SAXPY: flops_per_elem = 2.0; break;
      case Kernel::DOT:   flops_per_elem = 2.0; break;
      case Kernel::EWMUL: flops_per_elem = 1.0; break;
      case Kernel::STENCIL3: flops_per_elem = 5.0; break;
    }
    double secs = median / 1000.0;
    double effective_elems = (K==Kernel::STENCIL3 ? double(elems) : std::ceil(double(elems)/double(stride)));
    double gflops = (effective_elems * flops_per_elem) / secs / 1e9;

    double cpe = -1.0;
    if (cpu_ghz > 0) {
      double cycles = secs * cpu_ghz * 1e9;
      cpe = cycles / effective_elems;
    }

    if (K == Kernel::SAXPY) {
      double s = 0.0; for (size_t i = 0; i < elems; i += stride) s += y_view[i];
      reduction_scalar = s;
    } else if (K == Kernel::EWMUL) {
      double s = 0.0; for (size_t i = 0; i < elems; i += stride) s += z_view[i];
      reduction_scalar = s;
    }

    ensure_csv_header(csv_path, "kernel,dtype,align,stride,N,build,median_ms,stdev_ms,gflops,cpe,reduce");
    FILE* f = std::fopen(csv_path.c_str(), "a");
    if (!f) { std::perror("fopen csv"); return 3; }
    std::fprintf(f, "%s,%s,%s,%zu,%zu,%s,%.6f,%.6f,%.6f,%.6f,%.6f\n",
      kernel_s.c_str(), dtype_s.c_str(), align_s.c_str(), stride, N, build_label.c_str(),
      median, stdev, gflops, cpe, reduction_scalar);
    std::fclose(f);
  }

  std::free(pA); std::free(pB); std::free(pC);
  return 0;
}
