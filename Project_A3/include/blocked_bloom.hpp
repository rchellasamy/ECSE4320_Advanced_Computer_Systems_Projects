#pragma once
#include <cstdint>
#include <vector>
#include "hash.hpp"
#include "util.hpp"

class BlockedBloom {
public:
    BlockedBloom() = default;

    void init(uint64_t n, double target_fpr, uint64_t seed=1) {
        const double ln2 = 0.6931471805599453;
        uint64_t m_bits = (uint64_t)std::ceil(-(double)n * std::log(target_fpr) / (ln2*ln2));
        k_ = (uint32_t)std::max(1.0, std::round(((double)m_bits/(double)n)*ln2));
        block_bits_ = 512;
        num_blocks_ = (m_bits + block_bits_ - 1)/block_bits_;
        num_blocks_ = next_pow2(num_blocks_);
        bits_.assign((num_blocks_*block_bits_)/64, 0);
        h1_ = Hasher64(seed);
        h2_ = Hasher64(seed ^ 0x9e3779b97f4a7c15ULL);
    }

    inline void insert(uint64_t key) {
        uint64_t h = h1_(key);
        uint64_t b = (h >> 32) & (num_blocks_-1);
        uint64_t base = b * (block_bits_/64);
        uint64_t hstep = h2_(key);
        for (uint32_t i=0;i<k_;i++) {
            uint64_t bit = (splitmix64(h + i*hstep) & (block_bits_-1));
            bits_[base + (bit>>6)] |= (1ULL << (bit & 63));
        }
    }

    inline bool contains(uint64_t key) const {
        uint64_t h = h1_(key);
        uint64_t b = (h >> 32) & (num_blocks_-1);
        uint64_t base = b * (block_bits_/64);
        uint64_t hstep = h2_(key);
        for (uint32_t i=0;i<k_;i++) {
            uint64_t bit = (splitmix64(h + i*hstep) & (block_bits_-1));
            if ((bits_[base + (bit>>6)] & (1ULL << (bit & 63)))==0) return false;
        }
        return true;
    }

    double bits_per_entry(uint64_t n) const {
        return (double)(bits_.size()*64) / (double)n;
    }

private:
    std::vector<uint64_t> bits_;
    uint64_t num_blocks_{0};
    uint32_t k_{0};
    uint32_t block_bits_{512};
    Hasher64 h1_{1}, h2_{2};
};
