
#include "kernels.hpp"

void saxpy_scalar(float a, const float* x, float* y, size_t n) {
  for (size_t i = 0; i < n; ++i) y[i] = a * x[i] + y[i];
}
void saxpy_scalar(double a, const double* x, double* y, size_t n) {
  for (size_t i = 0; i < n; ++i) y[i] = a * x[i] + y[i];
}

double dot_scalar(const float* x, const float* y, size_t n) {
  double s = 0.0;
  for (size_t i = 0; i < n; ++i) s += double(x[i]) * double(y[i]);
  return s;
}
double dot_scalar(const double* x, const double* y, size_t n) {
  double s = 0.0;
  for (size_t i = 0; i < n; ++i) s += x[i] * y[i];
  return s;
}

void ewmul_scalar(const float* x, const float* y, float* z, size_t n) {
  for (size_t i = 0; i < n; ++i) z[i] = x[i] * y[i];
}
void ewmul_scalar(const double* x, const double* y, double* z, size_t n) {
  for (size_t i = 0; i < n; ++i) z[i] = x[i] * y[i];
}

void stencil3_scalar(const float* x, float* y, size_t n, float a, float b, float c) {
  if (n < 3) return;
  y[0] = b * x[0] + c * x[1];
  for (size_t i = 1; i + 1 < n; ++i) {
    y[i] = a * x[i-1] + b * x[i] + c * x[i+1];
  }
  y[n-1] = a * x[n-2] + b * x[n-1];
}
void stencil3_scalar(const double* x, double* y, size_t n, double a, double b, double c) {
  if (n < 3) return;
  y[0] = b * x[0] + c * x[1];
  for (size_t i = 1; i + 1 < n; ++i) {
    y[i] = a * x[i-1] + b * x[i] + c * x[i+1];
  }
  y[n-1] = a * x[n-2] + b * x[n-1];
}
