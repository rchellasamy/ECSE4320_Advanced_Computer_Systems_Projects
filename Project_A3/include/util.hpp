#pragma once
#include <cstdint>
#include <vector>
#include <algorithm>
#include <chrono>

static inline uint64_t now_ns() {
    return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}

static inline uint64_t next_pow2(uint64_t x) {
    if (x<=1) return 1;
    --x;
    x |= x>>1; x |= x>>2; x |= x>>4; x |= x>>8; x |= x>>16; x |= x>>32;
    return x+1;
}

template <class T>
static inline T clamp(T v, T lo, T hi) { return std::max(lo, std::min(v, hi)); }

struct LatencyStats {
    double p50=0, p95=0, p99=0;
};

static inline LatencyStats compute_latency_stats(std::vector<uint64_t>& ns) {
    LatencyStats s;
    if (ns.empty()) return s;
    std::sort(ns.begin(), ns.end());
    auto pct = [&](double p)->double {
        double idx = p * (ns.size()-1);
        size_t i = (size_t)idx;
        return (double)ns[i];
    };
    s.p50 = pct(0.50);
    s.p95 = pct(0.95);
    s.p99 = pct(0.99);
    return s;
}
