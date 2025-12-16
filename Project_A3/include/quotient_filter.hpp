#pragma once

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <limits>
#include <utility>
#include <vector>

#include "hash.hpp"

class QuotientFilter {
public:
    struct Stats {
        uint64_t inserts = 0, insert_fail = 0;
        uint64_t deletes = 0, delete_miss = 0;
        uint64_t lookups = 0;
        uint64_t scan_steps = 0;
        uint64_t probes = 0;
        uint64_t max_probe = 0;
    };

    QuotientFilter() = default;

    inline void init(uint64_t n, double load, int fp_bits, uint64_t seed) {
        rbits_ = std::min(16, std::max(4, fp_bits));
        uint64_t need = (uint64_t)std::ceil((double)n / std::max(0.1, load));
        uint64_t cap = 1;
        qbits_ = 0;
        while (cap < need) {
            cap <<= 1;
            qbits_++;
        }
        m_ = cap;
        mask_ = m_ - 1;

        rem_.assign(m_, 0);
        occ_.assign(m_, 0);
        cont_.assign(m_, 0);
        shft_.assign(m_, 0);

        h_ = Hasher64(seed);
        count_ = 0;
        stats_ = {};
    }

    inline uint64_t capacity() const { return m_; }

    inline double bits_per_entry(uint64_t n) const {
        double total = (double)m_ * ((double)rbits_ + 3.0);
        return total / (double)n;
    }

    inline Stats stats() const { return stats_; }
    inline void reset_stats() { stats_ = {}; }

    inline bool contains(uint64_t key) {
        stats_.lookups++;
        auto [q, r] = qr(key);
        if (!occ_[q]) { record_probe(1); return false; }

        uint64_t cluster = find_cluster_start(q);
        uint64_t end = find_cluster_end(cluster);
        if (end == std::numeric_limits<uint64_t>::max()) { record_probe(m_); return false; }

        std::vector<std::pair<uint64_t, std::vector<uint16_t>>> runs;
        std::vector<uint64_t> old_occ_buckets;
        materialize_cluster(cluster, end, runs, old_occ_buckets);
        for (auto &br : runs) {
            if (br.first != q) continue;
            auto &vec = br.second;
            bool ok = std::binary_search(vec.begin(), vec.end(), r);
            record_probe(distance_mod(cluster, end));
            return ok;
        }
        record_probe(distance_mod(cluster, end));
        return false;
    }

    inline bool insert(uint64_t key) {
        stats_.inserts++;
        if (m_ == 0) { stats_.insert_fail++; return false; }

        auto [q, r] = qr(key);

        if (!occ_[q] && is_empty(q)) {
            rem_[q] = r;
            occ_[q] = 1;
            cont_[q] = 0;
            shft_[q] = 0;
            count_++;
            record_probe(1);
            return true;
        }

        uint64_t cluster = find_cluster_start(q);
        uint64_t end = find_cluster_end(cluster);
        if (end == std::numeric_limits<uint64_t>::max()) { stats_.insert_fail++; return false; }

        std::vector<std::pair<uint64_t, std::vector<uint16_t>>> runs;
        std::vector<uint64_t> old_occ_buckets;
        materialize_cluster(cluster, end, runs, old_occ_buckets);

        bool found = false;
        for (auto &br : runs) {
            if (br.first == q) {
                found = true;
                br.second.insert(std::upper_bound(br.second.begin(), br.second.end(), r), r);
                break;
            }
        }
        if (!found) {
            runs.emplace_back(q, std::vector<uint16_t>{r});
            std::sort(runs.begin(), runs.end(), [](auto &a, auto &b) { return a.first < b.first; });
        }

        uint64_t needed = 0;
        for (auto &br : runs) needed += br.second.size();
        uint64_t avail = distance_mod(cluster, end);
        if (needed > avail) {
            stats_.insert_fail++;
            return false;
        }

        rewrite_cluster(cluster, end, runs, old_occ_buckets);
        occ_[q] = 1;
        count_++;
        record_probe(avail);
        return true;
    }

    inline bool erase(uint64_t key) {
        stats_.deletes++;
        if (m_ == 0) { stats_.delete_miss++; return false; }

        auto [q, r] = qr(key);
        if (!occ_[q]) {
            stats_.delete_miss++;
            record_probe(1);
            return false;
        }

        uint64_t cluster = find_cluster_start(q);
        uint64_t end = find_cluster_end(cluster);
        if (end == std::numeric_limits<uint64_t>::max()) {
            stats_.delete_miss++;
            return false;
        }

        std::vector<std::pair<uint64_t, std::vector<uint16_t>>> runs;
        std::vector<uint64_t> old_occ_buckets;
        materialize_cluster(cluster, end, runs, old_occ_buckets);

        bool removed = false;
        for (size_t idx = 0; idx < runs.size(); idx++) {
            if (runs[idx].first != q) continue;
            auto &vec = runs[idx].second;
            auto it = std::lower_bound(vec.begin(), vec.end(), r);
            if (it != vec.end() && *it == r) {
                vec.erase(it);
                removed = true;
                if (vec.empty()) {
                    runs.erase(runs.begin() + (long)idx);
                }
            }
            break;
        }

        if (!removed) {
            stats_.delete_miss++;
            record_probe(distance_mod(cluster, end));
            return false;
        }

        rewrite_cluster(cluster, end, runs, old_occ_buckets);
        if (runs.end() == std::find_if(runs.begin(), runs.end(), [&](auto &br) { return br.first == q; })) {
            occ_[q] = 0;
        } else {
            occ_[q] = 1;
        }
        count_--;
        record_probe(distance_mod(cluster, end));
        return true;
    }

    inline uint64_t cluster_len_at(uint64_t i) const {
        if (m_ == 0) return 0;
        if (is_empty(i)) return 0;
        uint64_t prev = (i - 1) & mask_;
        if (!is_empty(prev)) return 0;
        uint64_t len = 0;
        uint64_t j = i;
        while (!is_empty(j) && len < m_) {
            len++;
            j = next(j);
        }
        return len;
    }

    inline bool validate() const {
        if (m_ == 0) return true;

        if (m_ <= 4096) {
            for (uint64_t i = 0; i < m_; i++) {
                if (is_empty(i)) {
                    if (cont_[i] || shft_[i] || rem_[i] != 0) return false;
                }
                if (cont_[i] && is_empty(i)) return false;
            }
            return true;
        }

        constexpr uint64_t SAMPLES = 2048;
        uint64_t x = 0x9e3779b97f4a7c15ULL;
        for (uint64_t t = 0; t < SAMPLES; t++) {
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            uint64_t i = (x * 0x2545F4914F6CDD1DULL) & mask_;

            if (is_empty(i)) {
                if (cont_[i] || shft_[i] || rem_[i] != 0) return false;
            }
            if (cont_[i] && is_empty(i)) return false;
        }
        return true;
    }

private:
    inline std::pair<uint64_t, uint16_t> qr(uint64_t key) const {
        uint64_t x = h_(key);
        uint64_t q = x & mask_;
        uint16_t r = (uint16_t)((x >> qbits_) & ((1ULL << rbits_) - 1ULL));
        if (r == 0) r = 1;
        return {q, r};
    }

    inline uint64_t next(uint64_t i) const { return (i + 1) & mask_; }
    inline uint64_t prev(uint64_t i) const { return (i - 1) & mask_; }

    inline bool is_empty(uint64_t i) const {
        return rem_[i] == 0 && cont_[i] == 0 && shft_[i] == 0;
    }

    inline void record_probe(uint64_t p) {
        stats_.probes += p;
        stats_.scan_steps += p;
        if (p > stats_.max_probe) stats_.max_probe = p;
    }

    inline uint64_t find_cluster_start(uint64_t q) const {
        uint64_t i = q;
        uint64_t steps = 0;
        while (shft_[i] && steps < m_) {
            i = prev(i);
            steps++;
        }
        return i;
    }

    inline uint64_t find_cluster_end(uint64_t cluster_start) const {
        uint64_t i = cluster_start;
        uint64_t steps = 0;
        while (!is_empty(i) && steps < m_) {
            i = next(i);
            steps++;
        }
        if (steps >= m_) return std::numeric_limits<uint64_t>::max();
        return i;
    }

    inline uint64_t distance_mod(uint64_t a, uint64_t b) const {
        if (a <= b) return b - a;
        return (m_ - a) + b;
    }

    inline uint64_t find_run_start(uint64_t q) const {
        uint64_t cluster = find_cluster_start(q);

        uint64_t b = cluster;
        uint64_t s = cluster;

        while (b != q) {
            b = next(b);
            while (!occ_[b] && b != q) b = next(b);

            uint64_t i = s;
            while (true) {
                uint64_t ni = next(i);
                if (is_empty(ni) || !cont_[ni]) { i = ni; break; }
                i = ni;
            }
            s = i;
        }
        return s;
    }

    inline void materialize_cluster(
        uint64_t cluster, uint64_t end,
        std::vector<std::pair<uint64_t, std::vector<uint16_t>>> &runs,
        std::vector<uint64_t> &old_occ_buckets) const {
        runs.clear();
        old_occ_buckets.clear();
        for (uint64_t b = cluster; b != end; b = next(b)) {
            if (occ_[b]) old_occ_buckets.push_back(b);
        }

        uint64_t s = cluster;
        for (uint64_t b = cluster; b != end; b = next(b)) {
            if (!occ_[b]) continue;
            if (is_empty(s)) {
                runs.emplace_back(b, std::vector<uint16_t>{});
                continue;
            }
            std::vector<uint16_t> vec;
            vec.push_back(rem_[s]);
            uint64_t i = s;
            while (true) {
                uint64_t ni = next(i);
                if (ni == end || is_empty(ni) || !cont_[ni]) break;
                vec.push_back(rem_[ni]);
                i = ni;
            }
            s = next(i);
            std::sort(vec.begin(), vec.end());
            runs.emplace_back(b, std::move(vec));
        }
        std::sort(runs.begin(), runs.end(), [](auto &a, auto &b) { return a.first < b.first; });
    }

    inline void rewrite_cluster(
        uint64_t cluster, uint64_t end,
        const std::vector<std::pair<uint64_t, std::vector<uint16_t>>> &runs,
        const std::vector<uint64_t> &old_occ_buckets) {

        for (uint64_t i = cluster; i != end; i = next(i)) {
            rem_[i] = 0;
            cont_[i] = 0;
            shft_[i] = 0;
        }

        for (uint64_t b : old_occ_buckets) occ_[b] = 0;
        for (auto &br : runs) occ_[br.first] = 1;

        uint64_t pos = cluster;
        for (auto &br : runs) {
            uint64_t bucket = br.first;
            const auto &vec = br.second;
            if (vec.empty()) continue;
            for (size_t j = 0; j < vec.size(); j++) {
                rem_[pos] = vec[j];
                cont_[pos] = (j > 0) ? 1 : 0;
                shft_[pos] = (pos != bucket) ? 1 : 0;
                pos = next(pos);
            }
        }
    }

    int rbits_{10};
    int qbits_{0};
    uint64_t m_{0}, mask_{0};
    uint64_t count_{0};

    std::vector<uint16_t> rem_;
    std::vector<uint8_t> occ_, cont_, shft_;
    Hasher64 h_{1};
    Stats stats_{};
};
