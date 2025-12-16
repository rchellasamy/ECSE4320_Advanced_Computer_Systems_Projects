#pragma once
#include <cstdint>
#include <vector>
#include <queue>
#include <cmath>
#include "hash.hpp"
#include "util.hpp"

class XorFilter {
public:
    void build(const std::vector<uint64_t>& keys, int fp_bits, uint64_t seed=1) {
        fp_bits_ = fp_bits;
        n_ = keys.size();
        h0_ = Hasher64(seed);
        h1_ = Hasher64(seed ^ 0x9e3779b97f4a7c15ULL);
        h2_ = Hasher64(seed ^ 0xbf58476d1ce4e5b9ULL);

        m_ = (uint32_t)std::ceil((double)n_ * 1.23);
        m_ = (uint32_t)next_pow2(m_);
        mask_ = m_ - 1;

        std::vector<uint32_t> deg(m_, 0);
        std::vector<uint64_t> xorkey(m_, 0);
        std::vector<uint64_t> xorh(m_, 0);

        auto add = [&](uint64_t k) {
            uint32_t a = pos0(k), b = pos1(k), c = pos2(k);
            deg[a]++; xorkey[a] ^= k; xorh[a] ^= hfinger(k);
            deg[b]++; xorkey[b] ^= k; xorh[b] ^= hfinger(k);
            deg[c]++; xorkey[c] ^= k; xorh[c] ^= hfinger(k);
        };
        for (auto k: keys) add(k);

        std::queue<uint32_t> q;
        for (uint32_t i=0;i<m_;i++) if (deg[i]==1) q.push(i);

        struct StackEnt { uint32_t idx; uint64_t key; };
        std::vector<StackEnt> st;
        st.reserve(n_);

        while (!q.empty()) {
            uint32_t i = q.front(); q.pop();
            if (deg[i]!=1) continue;
            uint64_t k = xorkey[i];
            st.push_back({i,k});
            uint32_t a = pos0(k), b = pos1(k), c = pos2(k);
            auto dec = [&](uint32_t v) {
                deg[v]--;
                xorkey[v] ^= k;
                xorh[v] ^= hfinger(k);
                if (deg[v]==1) q.push(v);
            };
            dec(a); dec(b); dec(c);
        }

        if (st.size() != n_) {
            for (int t=1;t<=20;t++) {
                build(keys, fp_bits, seed + 0x9e3779b97f4a7c15ULL * (uint64_t)t);
                return;
            }
            m_=0; mask_=0; fp_.clear();
            return;
        }

        fp_.assign(m_, 0);

        for (size_t si = st.size(); si-- > 0;) {
            uint32_t i = st[si].idx;
            uint64_t k = st[si].key;
            uint32_t a = pos0(k), b = pos1(k), c = pos2(k);
            uint16_t f = (uint16_t)fingerprint(hfinger(k), fp_bits_);
            uint16_t val = f ^ fp_[a] ^ fp_[b] ^ fp_[c];
            fp_[i] = val;
        }
        built_ = true;
    }

    inline bool contains(uint64_t key) const {
        if (!built_) return false;
        uint16_t f = (uint16_t)fingerprint(hfinger(key), fp_bits_);
        uint16_t r = fp_[pos0(key)] ^ fp_[pos1(key)] ^ fp_[pos2(key)];
        return r == f;
    }

    double bits_per_entry(uint64_t n) const {
        return (double)fp_.size() * (double)fp_bits_ / (double)n;
    }

    uint32_t array_size() const { return m_; }
    int fp_bits() const { return fp_bits_; }

private:
    inline uint64_t hfinger(uint64_t k) const { return h0_(k); }
    inline uint32_t pos0(uint64_t k) const { return (uint32_t)(h0_(k) & mask_); }
    inline uint32_t pos1(uint64_t k) const { return (uint32_t)(h1_(k) & mask_); }
    inline uint32_t pos2(uint64_t k) const { return (uint32_t)(h2_(k) & mask_); }

    bool built_{false};
    size_t n_{0};
    uint32_t m_{0}, mask_{0};
    int fp_bits_{12};
    std::vector<uint16_t> fp_;
    Hasher64 h0_{1}, h1_{2}, h2_{3};
};
