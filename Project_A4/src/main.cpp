#include <iostream>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <random>
#include <chrono>
#include <cstring>
#include <string>
#include <algorithm>

#ifdef __linux__
#include <sched.h>
#include <unistd.h>
#endif

using namespace std;

static constexpr size_t BUCKET_COUNT = 1 << 20; 
static constexpr size_t STRIPES      = 64;      

struct KV {
    int key;
    int value;
};


static vector<vector<KV>> buckets(BUCKET_COUNT);
static mutex global_lock;
static mutex stripe_locks[STRIPES];

inline size_t bucket_of(int k) {
    return std::hash<int>{}(k) % BUCKET_COUNT;
}

inline void pin_thread_best_effort(int tid) {
#ifdef __linux__
    int ncpu = (int)std::thread::hardware_concurrency();
    if (ncpu <= 0) return;
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(tid % ncpu, &cpuset);
    (void)sched_setaffinity(0, sizeof(cpu_set_t), &cpuset); // ignore failure (WSL may reject)
#else
    (void)tid;
#endif
}

enum class Mode { Coarse, Striped };
enum class Workload { LookupOnly, InsertOnly, Mixed };

inline size_t stripe_of(size_t idx) { return idx % STRIPES; }

bool find_locked(size_t idx, int k, int &out_v) {
    auto &b = buckets[idx];
    for (const auto &kv : b) {
        if (kv.key == k) {
            out_v = kv.value;
            return true;
        }
    }
    return false;
}

void insert_locked(size_t idx, int k, int v) {
    auto &b = buckets[idx];
    for (auto &kv : b) {
        if (kv.key == k) {
            kv.value = v;
            return;
        }
    }
    b.push_back(KV{k, v});
}

bool erase_locked(size_t idx, int k) {
    auto &b = buckets[idx];
    for (size_t i = 0; i < b.size(); i++) {
        if (b[i].key == k) {
            b[i] = b.back();
            b.pop_back();
            return true;
        }
    }
    return false;
}

bool find_coarse(int k, int &out_v) {
    lock_guard<mutex> g(global_lock);
    return find_locked(bucket_of(k), k, out_v);
}

bool find_striped(int k, int &out_v) {
    size_t idx = bucket_of(k);
    lock_guard<mutex> g(stripe_locks[stripe_of(idx)]);
    return find_locked(idx, k, out_v);
}

void insert_coarse(int k, int v) {
    lock_guard<mutex> g(global_lock);
    insert_locked(bucket_of(k), k, v);
}

void insert_striped(int k, int v) {
    size_t idx = bucket_of(k);
    lock_guard<mutex> g(stripe_locks[stripe_of(idx)]);
    insert_locked(idx, k, v);
}

bool erase_coarse(int k) {
    lock_guard<mutex> g(global_lock);
    return erase_locked(bucket_of(k), k);
}

bool erase_striped(int k) {
    size_t idx = bucket_of(k);
    lock_guard<mutex> g(stripe_locks[stripe_of(idx)]);
    return erase_locked(idx, k);
}

struct Args {
    int threads = 4;
    Mode mode = Mode::Coarse;
    Workload workload = Workload::Mixed;
    int read_pct = 70;         
    int keys = 100000;          
    int ops_per_thread = 1000000;
    uint64_t seed = 12345;
};

Args parse_args(int argc, char** argv) {
    Args a;
    for (int i = 1; i < argc; i++) {
        string s = argv[i];
        if (s == "--threads" && i+1 < argc) a.threads = atoi(argv[++i]);
        else if (s == "--keys" && i+1 < argc) a.keys = atoi(argv[++i]);
        else if (s == "--ops" && i+1 < argc) a.ops_per_thread = atoi(argv[++i]);
        else if (s == "--read_pct" && i+1 < argc) a.read_pct = atoi(argv[++i]);
        else if (s == "--seed" && i+1 < argc) a.seed = strtoull(argv[++i], nullptr, 10);
        else if (s == "--mode" && i+1 < argc) {
            string m = argv[++i];
            if (m == "coarse") a.mode = Mode::Coarse;
            else if (m == "striped") a.mode = Mode::Striped;
        } else if (s == "--workload" && i+1 < argc) {
            string w = argv[++i];
            if (w == "lookup") a.workload = Workload::LookupOnly;
            else if (w == "insert") a.workload = Workload::InsertOnly;
            else if (w == "mixed") a.workload = Workload::Mixed;
        }
    }
    a.read_pct = std::clamp(a.read_pct, 0, 100);
    a.keys = std::max(0, a.keys);
    a.threads = std::max(1, a.threads);
    a.ops_per_thread = std::max(1, a.ops_per_thread);
    return a;
}

void prefill(const Args& a) {
    for (auto &b : buckets) b.clear();

    std::mt19937 rng((uint32_t)a.seed);
    for (int i = 0; i < a.keys; i++) {
        int k = (int)rng();
        if (a.mode == Mode::Coarse) insert_coarse(k, k);
        else insert_striped(k, k);
    }
}

void worker(int tid, const Args& a, const vector<int>& hot_keys, atomic<uint64_t>& ops_done) {
    pin_thread_best_effort(tid);

    std::mt19937 rng((uint32_t)(a.seed + tid * 1337u));
    std::uniform_int_distribution<int> pct(0, 99);
    std::uniform_int_distribution<size_t> pick(0, hot_keys.empty() ? 0 : (hot_keys.size() - 1));
    std::uniform_int_distribution<int> coin(0, 1);

    int tmp = 0;
    uint64_t local_ops = 0;

    for (int i = 0; i < a.ops_per_thread; i++) {
        if (a.workload == Workload::LookupOnly) {
            int k = hot_keys.empty() ? (int)rng() : hot_keys[pick(rng)];
            if (a.mode == Mode::Coarse) (void)find_coarse(k, tmp);
            else (void)find_striped(k, tmp);

        } else if (a.workload == Workload::InsertOnly) {
            int k = (int)rng();
            if (a.mode == Mode::Coarse) insert_coarse(k, k);
            else insert_striped(k, k);

        } else { 
            bool do_read = (pct(rng) < a.read_pct);
            if (do_read) {
                int k = hot_keys.empty() ? (int)rng() : hot_keys[pick(rng)];
                if (a.mode == Mode::Coarse) (void)find_coarse(k, tmp);
                else (void)find_striped(k, tmp);
            } else {
                if (coin(rng) == 0) {
                    int k = (int)rng();
                    if (a.mode == Mode::Coarse) insert_coarse(k, k);
                    else insert_striped(k, k);
                } else {
                    int k = hot_keys.empty() ? (int)rng() : hot_keys[pick(rng)];
                    if (a.mode == Mode::Coarse) (void)erase_coarse(k);
                    else (void)erase_striped(k);
                }
            }
        }

        local_ops++;
    }

    ops_done.fetch_add(local_ops, memory_order_relaxed);
}

int main(int argc, char** argv) {
    ios::sync_with_stdio(false);

    Args a = parse_args(argc, argv);
    prefill(a);

    vector<int> hot_keys;
    hot_keys.reserve(min(a.keys, 100000));
    std::mt19937 rng((uint32_t)a.seed);
    for (int i = 0; i < a.keys; i++) {
        int k = (int)rng();
        hot_keys.push_back(k);
        if ((int)hot_keys.size() >= 100000) break;
    }

    atomic<uint64_t> ops_done{0};
    vector<thread> ts;
    ts.reserve(a.threads);

    auto start = chrono::high_resolution_clock::now();
    for (int t = 0; t < a.threads; t++) ts.emplace_back(worker, t, cref(a), cref(hot_keys), ref(ops_done));
    for (auto& t : ts) t.join();
    auto end = chrono::high_resolution_clock::now();

    double secs = chrono::duration<double>(end - start).count();
    double thr = (double)ops_done.load(memory_order_relaxed) / secs;

    const char* mode_s = (a.mode == Mode::Coarse) ? "coarse" : "striped";
    const char* wl_s =
        (a.workload == Workload::LookupOnly) ? "lookup" :
        (a.workload == Workload::InsertOnly) ? "insert" : "mixed";

    cout << "mode=" << mode_s
         << " workload=" << wl_s
         << " keys=" << a.keys
         << " threads=" << a.threads
         << " read_pct=" << a.read_pct
         << " ops_per_thread=" << a.ops_per_thread
         << " throughput_ops_per_s=" << thr
         << "\n";
    return 0;
}
