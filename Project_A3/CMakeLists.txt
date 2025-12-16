
cmake_minimum_required(VERSION 3.16)
project(a3_amq_filters CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_compile_options(-O3 -march=native -DNDEBUG)

include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(amq_bench src/main.cpp)
add_executable(validate tests/validate.cpp)
