
cmake_minimum_required(VERSION 3.16)
project(simd_profile CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Option to disable vectorization for scalar baseline
option(BUILD_SCALAR "Disable vectorization" OFF)

# Common opts
add_compile_options(-O3 -fno-exceptions -fno-rtti -DNDEBUG)

# Compiler-specific vectorization flags and reports
if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  # Enable fast fused FP (document in report)
  add_compile_options(-ffp-contract=fast)
  if (BUILD_SCALAR)
    add_compile_options(-fno-vectorize -fno-slp-vectorize)
  else()
    # Try to target host ISA; adjust to specific like -mavx2 or -mavx512f if desired
    add_compile_options(-march=native -Rpass=loop-vectorize -Rpass-missed=loop-vectorize -Rpass-analysis=loop-vectorize)
  endif()
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  add_compile_options(-O3 -march=native -ffast-math -ffp-contract=fast)

  # Put vectorization reports in a subfolder under the build dir
  set(VEC_DIR ${CMAKE_CURRENT_BINARY_DIR}/vec_reports)
  file(MAKE_DIRECTORY ${VEC_DIR})

  # Per-file reports (no global -fopt-info to avoid conflicts)
  set_source_files_properties(
    src/kernels_simd_friendly.cpp PROPERTIES COMPILE_OPTIONS
      "-fopt-info-vec-optimized=${VEC_DIR}/ok.txt;-fopt-info-vec-missed=${VEC_DIR}/missed.txt")
  set_source_files_properties(
    src/kernels_scalar.cpp PROPERTIES COMPILE_OPTIONS
      "-fopt-info-vec-missed=${VEC_DIR}/missed_scalar.txt")
endif()



add_executable(simd_profile
  src/main.cpp
  src/kernels_scalar.cpp
  src/kernels_simd_friendly.cpp
  src/utils.cpp
)
target_include_directories(simd_profile PRIVATE include)
