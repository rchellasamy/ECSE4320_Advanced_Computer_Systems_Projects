#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

static inline uint64_t ns_now() {
    return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

static void usage(const char* prog) {
    std::cerr
        << "Usage: " << prog << " [mode] [bytes] [iters]\n"
        << "  mode: seq | rand_idx | ptr_chase\n"
        << "  bytes: size of array (default 64MiB)\n"
        << "  iters: number of element accesses (default 200000000)\n";
}

static volatile uint64_t sink = 0;

int main(int argc, char** argv) {
    std::string mode = (argc >= 2) ? argv[1] : "seq";
    size_t bytes = (argc >= 3) ? (size_t)std::stoull(argv[2]) : (64ull << 20);
    uint64_t iters = (argc >= 4) ? (uint64_t)std::stoull(argv[3]) : 200000000ull;

    if (mode != "seq" && mode != "rand_idx" && mode != "ptr_chase") {
        usage(argv[0]);
        return 2;
    }

    const size_t n = bytes / sizeof(uint64_t);
    if (n < 1024) {
        std::cerr << "Array too small.\n";
        return 2;
    }

    std::vector<uint64_t> a(n);
    for (size_t i = 0; i < n; i++) a[i] = (uint64_t)i * 1315423911ull;


    std::vector<uint32_t> idx;

    std::vector<uint32_t> next;

    std::mt19937 rng(12345);
    if (mode == "rand_idx") {
        idx.resize((size_t)iters);
        std::uniform_int_distribution<uint32_t> dist(0u, (uint32_t)(n - 1));
        for (size_t i = 0; i < idx.size(); i++) idx[i] = dist(rng);
    } else if (mode == "ptr_chase") {
        next.resize(n);
        std::vector<uint32_t> perm(n);
        std::iota(perm.begin(), perm.end(), 0u);
        std::shuffle(perm.begin(), perm.end(), rng);
        for (size_t i = 0; i < n - 1; i++) next[perm[i]] = perm[i + 1];
        next[perm[n - 1]] = perm[0];
    }


    uint64_t warm = 0;
    for (size_t i = 0; i < n; i += 64) warm += a[i];
    sink = warm;

    uint64_t sum = 0;
    uint64_t t0 = ns_now();

    if (mode == "seq") {

        size_t p = 0;
        for (uint64_t i = 0; i < iters; i++) {
            sum += a[p];
            p++;
            if (p == n) p = 0;
        }
    } else if (mode == "rand_idx") {
        for (uint64_t i = 0; i < iters; i++) {
            sum += a[idx[(size_t)i]];
        }
    } else { 
        uint32_t p = 0;
        for (uint64_t i = 0; i < iters; i++) {
            p = next[p];
            sum += a[p];
        }
    }

    uint64_t t1 = ns_now();
    sink = sum;

    double seconds = (double)(t1 - t0) / 1e9;


    std::cout
        << "feature=prefetch "
        << "mode=" << mode << " "
        << "bytes=" << bytes << " "
        << "iters=" << iters << " "
        << "seconds=" << seconds << "\n";

    return 0;
}
