#pragma once
#include <cstdint>
#include <cstddef>

static inline uint64_t splitmix64(uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

struct Hasher64 {
    uint64_t seed;
    explicit Hasher64(uint64_t s=0x123456789abcdef0ULL) : seed(s) {}
    inline uint64_t operator()(uint64_t x) const {
        return splitmix64(x ^ seed);
    }
};

static inline uint32_t fingerprint(uint64_t h, int bits) {
    uint32_t fp = (uint32_t)(h & ((bits==32)?0xffffffffu:((1u<<bits)-1u)));
    if (fp==0) fp = 1;
    return fp;
}
