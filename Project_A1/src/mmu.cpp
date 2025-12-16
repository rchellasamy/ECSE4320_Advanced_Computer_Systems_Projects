#include "common.h"
#include <vector>
#include <chrono>
#include <iostream>
#include <fstream>

static inline uint64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

static std::string read_first_line(const char* path) {
    std::ifstream f(path);
    if (!f.good()) return "NA";
    std::string s;
    std::getline(f, s);
    return s;
}

int main(int argc, char** argv) {
    size_t mb = 256;
    size_t stride = 64;
    int reps = 5;

    for (int i=1;i<argc;i++) {
        if (!strcmp(argv[i],"--mb") && i+1<argc) mb = (size_t)atol(argv[++i]);
        else if (!strcmp(argv[i],"--stride") && i+1<argc) stride = (size_t)atol(argv[++i]);
        else if (!strcmp(argv[i],"--reps") && i+1<argc) reps = atoi(argv[++i]);
    }

    std::string thp = read_first_line("/sys/kernel/mm/transparent_hugepage/enabled");

    size_t bytes = mb * 1024ULL * 1024ULL;
    size_t n = bytes / sizeof(int);
    std::vector<int> a(n, 1);

    volatile uint64_t sum = 0;
    uint64_t t0 = now_ns();

    for (int r=0;r<reps;r++) {
        for (size_t i=0; i<n; i += stride) sum += (uint64_t)a[i];
    }

    uint64_t t1 = now_ns();
    double secs = (t1 - t0) / 1e9;

    double touches = (double)reps * (double)((n + stride - 1) / stride);

    std::cout << "feature=mmu"
              << " thp=\"" << thp << "\""
              << " mb=" << mb
              << " stride_elems=" << stride
              << " reps=" << reps
              << " seconds=" << secs
              << " touches=" << (uint64_t)touches
              << " touches_per_s=" << (touches / secs)
              << "\n";
    return (int)(sum & 0xFF);
}
