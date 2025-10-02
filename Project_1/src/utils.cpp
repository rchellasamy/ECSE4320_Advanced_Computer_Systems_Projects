#include "utils.hpp"
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <sys/stat.h>
#include <fstream>
#include <chrono>
#include <vector>
#include <string>   // <- add this


void* aligned_alloc_bytes(size_t alignment, size_t bytes) {
#if defined(_MSC_VER)
    return _aligned_malloc(bytes, alignment);  // Windows path
#else
    void* p = nullptr;
    if (::posix_memalign(&p, alignment, bytes) != 0) return nullptr;  // Linux/WSL
    return p;
#endif
}

void aligned_free_bytes(void* ptr) {
#if defined(_MSC_VER)
    _aligned_free(ptr);  // Windows path
#else
    free(ptr);  // Linux/WSL - posix_memalign uses regular free
#endif
}

double now_ms() {
    using clk = std::chrono::high_resolution_clock;
    auto t = clk::now().time_since_epoch();
    return std::chrono::duration<double, std::milli>(t).count();
}

void median_stdev(const std::vector<double>& xs_in, double& median, double& stdev) {
    std::vector<double> xs = xs_in;
    if (xs.empty()) { 
        median = stdev = 0.0; 
        return; 
    }
    
    std::sort(xs.begin(), xs.end());
    size_t n = xs.size();
    
    // Calculate median
    if (n % 2 == 0) {
        median = 0.5 * (xs[n/2 - 1] + xs[n/2]);
    } else {
        median = xs[n/2];
    }
    
    // Calculate standard deviation
    double mean = 0.0;
    for (double v : xs) mean += v;
    mean /= n;
    
    double var = 0.0;
    for (double v : xs) {
        double diff = v - mean;
        var += diff * diff;
    }
    var /= (n > 1 ? (n - 1) : 1);  // Sample standard deviation
    stdev = std::sqrt(var);
}

static bool file_exists_nonempty(const std::string& path) {
  struct stat st;
  return stat(path.c_str(), &st) == 0 && st.st_size > 0;
}

void ensure_csv_header(const std::string& path, const std::string& header) {
  if (!file_exists_nonempty(path)) {
    std::ofstream ofs(path);
    if (ofs.is_open()) ofs << header << "\n";
  }
}

