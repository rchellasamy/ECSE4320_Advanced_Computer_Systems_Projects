
#include "kernels.hpp"

// These "simd" functions are written to be auto-vectorizable by the compiler.
// Vectorization is controlled by build flags (CMake option BUILD_SCALAR).

void saxpy_simd(float a, const float* x, float* y, size_t n) {
  for (size_t i = 0; i < n; ++i) y[i] = a * x[i] + y[i];
}
void saxpy_simd(double a, const double* x, double* y, size_t n) {
  for (size_t i = 0; i < n; ++i) y[i] = a * x[i] + y[i];
}

double dot_simd(const float* x, const float* y, size_t n) {
  double s0 = 0.0, s1 = 0.0;
  size_t i = 0;
  // unroll to help vectorizer
  for (; i + 1 < n; i += 2) {
    s0 += double(x[i]) * double(y[i]);
    s1 += double(x[i+1]) * double(y[i+1]);
  }
  if (i < n) s0 += double(x[i]) * double(y[i]);
  return s0 + s1;
}
double dot_simd(const double* x, const double* y, size_t n) {
  double s0 = 0.0, s1 = 0.0;
  size_t i = 0;
  for (; i + 1 < n; i += 2) {
    s0 += x[i] * y[i];
    s1 += x[i+1] * y[i+1];
  }
  if (i < n) s0 += x[i] * y[i];
  return s0 + s1;
}

void ewmul_simd(const float* x, const float* y, float* z, size_t n) {
  for (size_t i = 0; i < n; ++i) z[i] = x[i] * y[i];
}
void ewmul_simd(const double* x, const double* y, double* z, size_t n) {
  for (size_t i = 0; i < n; ++i) z[i] = x[i] * y[i];
}

void stencil3_simd(const float* x, float* y, size_t n, float a, float b, float c) {
  if (n < 3) return;
  y[0] = b * x[0] + c * x[1];
  for (size_t i = 1; i + 1 < n; ++i) {
    y[i] = a * x[i-1] + b * x[i] + c * x[i+1];
  }
  y[n-1] = a * x[n-2] + b * x[n-1];
}
void stencil3_simd(const double* x, double* y, size_t n, double a, double b, double c) {
  if (n < 3) return;
  y[0] = b * x[0] + c * x[1];
  for (size_t i = 1; i + 1 < n; ++i) {
    y[i] = a * x[i-1] + b * x[i] + c * x[i+1];
  }
  y[n-1] = a * x[n-2] + b * x[n-1];
}
