
#pragma once
#include <cstddef>
#include <cstdint>

enum class Kernel {
  SAXPY,        // y = a*x + y
  DOT,          // s = sum(x*y)
  EWMUL,        // z = x*y
  STENCIL3      // y[i] = a*x[i-1] + b*x[i] + c*x[i+1]
};

enum class DType { F32, F64 };

struct Stencil3Coeffs {
  double a, b, c;
};

// Scalar reference (ground truth)
void saxpy_scalar(float a, const float* x, float* y, size_t n);
void saxpy_scalar(double a, const double* x, double* y, size_t n);

double dot_scalar(const float* x, const float* y, size_t n);
double dot_scalar(const double* x, const double* y, size_t n);

void ewmul_scalar(const float* x, const float* y, float* z, size_t n);
void ewmul_scalar(const double* x, const double* y, double* z, size_t n);

void stencil3_scalar(const float* x, float* y, size_t n, float a, float b, float c);
void stencil3_scalar(const double* x, double* y, size_t n, double a, double b, double c);

// SIMD-friendly (plain loops; rely on auto-vectorization)
void saxpy_simd(float a, const float* x, float* y, size_t n);
void saxpy_simd(double a, const double* x, double* y, size_t n);

double dot_simd(const float* x, const float* y, size_t n);
double dot_simd(const double* x, const double* y, size_t n);

void ewmul_simd(const float* x, const float* y, float* z, size_t n);
void ewmul_simd(const double* x, const double* y, double* z, size_t n);

void stencil3_simd(const float* x, float* y, size_t n, float a, float b, float c);
void stencil3_simd(const double* x, double* y, size_t n, double a, double b, double c);
