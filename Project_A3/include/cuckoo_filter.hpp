#pragma once
#include <cstdint>
#include <vector>
#include <random>
#include "hash.hpp"
#include "util.hpp"

__attribute__((used)) static const char CUCKOO_PATCH_TAG[] = "CUCKOO_PATCH_TAG_v3";

class CuckooFilter {
public:
    struct Stats {
        uint64_t inserts=0, insert_fail=0;
        uint64_t deletes=0;
        uint64_t kicks=0;
        uint64_t max_kicks=0;
        uint64_t stash_inserts=0;
        uint64_t stash_hits=0;
        uint64_t lookups=0;
        uint64_t fp_checks=0;
    };

    void init(uint64_t n, double load_factor, int fp_bits, uint64_t seed=1,
              uint32_t bucket_size=4, uint32_t max_kicks=500) {
        fp_bits_ = fp_bits;
        bucket_size_ = bucket_size;
        max_kicks_ = max_kicks;

        double buckets_f = (double)n / (load_factor * (double)bucket_size_);
        num_buckets_ = next_pow2((uint64_t)std::ceil(buckets_f));
        mask_ = num_buckets_ - 1;

        table_.assign(num_buckets_ * bucket_size_, 0);
        stash_.clear();

        h_ = Hasher64(seed);
        halt_ = Hasher64(seed ^ 0xfeedbeef12345678ULL);

        stats_ = {};
        rng_.seed(seed ^ 0xabcdef9876543210ULL);
    }

    inline bool contains(uint64_t key) {
        stats_.lookups++;

        uint64_t h = h_(key);
        uint16_t fp = cuckoo_fp(h);

        uint32_t i1 = (uint32_t)(h & mask_);
        uint32_t i2 = alt_index(i1, fp);

        if (bucket_has(i1, fp) || bucket_has(i2, fp)) return true;

        for (auto &e : stash_) {
            if (e.fp == fp &&
                (e.i1 == i1 || e.i2 == i1 || e.i1 == i2 || e.i2 == i2)) {
                stats_.stash_hits++;
                return true;
            }
        }
        return false;
    }

    inline bool insert(uint64_t key) {
        stats_.inserts++;

        uint64_t h = h_(key);
        uint16_t fp = cuckoo_fp(h);

        uint32_t i1 = (uint32_t)(h & mask_);
        uint32_t i2 = alt_index(i1, fp);

        if (bucket_insert(i1, fp) || bucket_insert(i2, fp)) return true;

        uint32_t idx = (rng_() & 1) ? i1 : i2;
        uint16_t cur = fp;

        uint64_t kicks = 0;
        for (; kicks < max_kicks_; kicks++) {
            uint32_t slot = (uint32_t)(rng_() % bucket_size_);
            uint32_t off  = idx * bucket_size_ + slot;

            std::swap(cur, table_[off]);
            if (cur == 0) cur = 1;

            idx = alt_index(idx, cur);
            if (bucket_insert(idx, cur)) {
                stats_.kicks += (kicks + 1);
                if (kicks + 1 > stats_.max_kicks) stats_.max_kicks = kicks + 1;
                return true;
            }
        }

        if (stash_.size() < stash_cap_) {
            stash_.push_back({cur, i1, i2});
            stats_.stash_inserts++;
            stats_.kicks += kicks;
            if (kicks > stats_.max_kicks) stats_.max_kicks = kicks;
            return true;
        }

        stats_.insert_fail++;
        stats_.kicks += kicks;
        if (kicks > stats_.max_kicks) stats_.max_kicks = kicks;
        return false;
    }

    inline bool erase(uint64_t key) {
        stats_.deletes++;

        uint64_t h = h_(key);
        uint16_t fp = cuckoo_fp(h);

        uint32_t i1 = (uint32_t)(h & mask_);
        uint32_t i2 = alt_index(i1, fp);

        if (bucket_erase(i1, fp) || bucket_erase(i2, fp)) return true;

        for (size_t i = 0; i < stash_.size(); i++) {
            if (stash_[i].fp == fp &&
                (stash_[i].i1 == i1 || stash_[i].i2 == i2 ||
                 stash_[i].i2 == i1 || stash_[i].i1 == i2)) {
                stash_[i] = stash_.back();
                stash_.pop_back();
                return true;
            }
        }
        return false;
    }

    double bits_per_entry(uint64_t n) const {
        double bits = (double)table_.size() * (double)fp_bits_;
        bits += (double)stash_.size() * (fp_bits_ + 2 * 32);
        return bits / (double)n;
    }

    const Stats& stats() const { return stats_; }
    void reset_stats() { stats_ = {}; }

    uint64_t size_buckets() const { return num_buckets_; }
    uint32_t bucket_size() const { return bucket_size_; }
    int fp_bits() const { return fp_bits_; }
    size_t stash_size() const { return stash_.size(); }

private:
    struct StashEntry { uint16_t fp; uint32_t i1, i2; };

    inline uint16_t cuckoo_fp(uint64_t h) const {
        uint64_t mask;
        if (fp_bits_ >= 16) mask = 0xFFFFULL;
        else mask = (1ULL << fp_bits_) - 1ULL;

        uint64_t x = (h >> 32) ^ h;
        uint16_t fp = (uint16_t)(x & mask);
        if (fp == 0) fp = 1;
        return fp;
    }

    inline uint32_t alt_index(uint32_t i, uint16_t fp) const {
        uint64_t hh = halt_((uint64_t)fp);
        return (uint32_t)((i ^ (uint32_t)hh) & mask_);
    }

    inline bool bucket_has(uint32_t b, uint16_t fp) {
        uint32_t base = b * bucket_size_;
        for (uint32_t j = 0; j < bucket_size_; j++) {
            stats_.fp_checks++;
            uint16_t v = table_[base + j];
            if (v != 0 && v == fp) return true;
        }
        return false;
    }

    inline bool bucket_insert(uint32_t b, uint16_t fp) {
        if (fp == 0) fp = 1;
        uint32_t base = b * bucket_size_;
        for (uint32_t j = 0; j < bucket_size_; j++) {
            if (table_[base + j] == 0) { table_[base + j] = fp; return true; }
        }
        return false;
    }

    inline bool bucket_erase(uint32_t b, uint16_t fp) {
        if (fp == 0) fp = 1;
        uint32_t base = b * bucket_size_;
        for (uint32_t j = 0; j < bucket_size_; j++) {
            if (table_[base + j] == fp) { table_[base + j] = 0; return true; }
        }
        return false;
    }

    int fp_bits_{12};
    uint32_t bucket_size_{4};
    uint32_t max_kicks_{500};

    uint64_t num_buckets_{0};
    uint64_t mask_{0};

    std::vector<uint16_t> table_;
    std::vector<StashEntry> stash_;
    size_t stash_cap_{32};

    Hasher64 h_{1};
    Hasher64 halt_{2};

    Stats stats_{};
    std::mt19937_64 rng_;
};
