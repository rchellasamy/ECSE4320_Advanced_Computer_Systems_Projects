#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <sched.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <utility>
#include <vector>


static inline uint64_t ns_now() {
    return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}


static bool pin_to_cpu(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    return sched_setaffinity(0, sizeof(set), &set) == 0;
}

static int cpu_count_online() {
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    return (n > 0) ? (int)n : 1;
}

static std::optional<int> read_int_file(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) return std::nullopt;
    int v;
    f >> v;
    if (!f.good()) return std::nullopt;
    return v;
}

static std::optional<std::string> read_str_file(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) return std::nullopt;
    std::string s;
    std::getline(f, s);
    if (!f.good() && s.empty()) return std::nullopt;
    return s;
}

static std::optional<int> core_id_of_cpu(int cpu) {
    return read_int_file("/sys/devices/system/cpu/cpu" + std::to_string(cpu) + "/topology/core_id");
}

static std::optional<int> pkg_id_of_cpu(int cpu) {
    return read_int_file("/sys/devices/system/cpu/cpu" + std::to_string(cpu) + "/topology/physical_package_id");
}


static std::vector<int> parse_cpu_list(const std::string& s) {
    std::vector<int> out;
    std::stringstream ss(s);
    std::string token;
    while (std::getline(ss, token, ',')) {
        if (token.empty()) continue;
        auto dash = token.find('-');
        if (dash == std::string::npos) {
            out.push_back(std::stoi(token));
        } else {
            int a = std::stoi(token.substr(0, dash));
            int b = std::stoi(token.substr(dash + 1));
            if (a > b) std::swap(a, b);
            for (int i = a; i <= b; i++) out.push_back(i);
        }
    }
    return out;
}

static std::optional<std::vector<int>> thread_siblings_of_cpu(int cpu) {
    auto s = read_str_file("/sys/devices/system/cpu/cpu" + std::to_string(cpu) + "/topology/thread_siblings_list");
    if (!s) return std::nullopt;
    auto v = parse_cpu_list(*s);
    if (v.empty()) return std::nullopt;
    return v;
}


#if defined(__x86_64__) || defined(__i386__)
static inline void cpuid_serialize() {
    unsigned int a, b, c, d;
    a = 0;
    __asm__ __volatile__("cpuid"
        : "=a"(a), "=b"(b), "=c"(c), "=d"(d)
        : "a"(a)
        : "memory");
}

static inline uint64_t rdtsc_start() {
    cpuid_serialize();
    unsigned int lo, hi;
    __asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

static inline uint64_t rdtsc_stop() {
    unsigned int lo, hi;
    __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi) :: "%rcx");
    uint64_t t = ((uint64_t)hi << 32) | lo;
    cpuid_serialize();
    return t;
}
#else
static inline uint64_t rdtsc_start() { return 0; }
static inline uint64_t rdtsc_stop()  { return 0; }
#endif

static volatile uint64_t smt_sink = 0;


__attribute__((noinline))
static uint64_t work(uint64_t iters) {
    uint64_t x = 0x123456789abcdef0ULL;
    uint64_t y = 0xfedcba9876543211ULL;
    uint64_t s = 1;

    for (uint64_t i = 0; i < iters; i++) {
        x = (x / 3) + 1;
        y = (y / 7) + 1;
        s += x ^ y;
        x ^= (s << 1);
        y ^= (s >> 1);
    }
    return s;
}

struct ThreadResult {
    bool pin_ok = false;
    double seconds = 0.0;
    uint64_t tsc = 0;
    uint64_t value = 0;
};

static ThreadResult run_thread(int cpu, uint64_t iters, std::atomic<bool>& start_flag) {
    ThreadResult tr{};
    tr.pin_ok = pin_to_cpu(cpu);

    while (!start_flag.load(std::memory_order_acquire)) {}

    uint64_t ns0 = ns_now();
    uint64_t t0 = rdtsc_start();
    uint64_t r  = work(iters);
    uint64_t t1 = rdtsc_stop();
    uint64_t ns1 = ns_now();

    tr.seconds = (double)(ns1 - ns0) / 1e9;
    tr.tsc     = (t1 >= t0) ? (t1 - t0) : 0;
    tr.value   = r ^ (ns1 - ns0);
    return tr;
}

static std::string opt_to_str(const std::optional<int>& v) {
    return v ? std::to_string(*v) : std::string("na");
}

static std::optional<std::pair<int,int>> pick_true_smt_siblings_pair() {
    int n = cpu_count_online();
    for (int cpu = 0; cpu < n; cpu++) {
        auto sibs = thread_siblings_of_cpu(cpu);
        if (!sibs || sibs->size() < 2) continue;

        for (int s : *sibs) {
            if (s != cpu && s >= 0 && s < n) {
                return std::make_pair(cpu, s);
            }
        }
    }
    return std::nullopt;
}

static std::pair<int,int> pick_spread_from(int cpuA, int cpuSibling) {
    int n = cpu_count_online();

    auto pkgA  = pkg_id_of_cpu(cpuA);
    auto coreA = core_id_of_cpu(cpuA);

    for (int cpuB = 0; cpuB < n; cpuB++) {
        if (cpuB == cpuA || cpuB == cpuSibling) continue;

        auto coreB = core_id_of_cpu(cpuB);
        if (!coreA || !coreB) continue;
        if (*coreB == *coreA) continue; 

        if (pkgA) {
            auto pkgB = pkg_id_of_cpu(cpuB);
            if (pkgB && *pkgB == *pkgA) {
                return {cpuA, cpuB}; 
            }
        }
    }

    for (int cpuB = 0; cpuB < n; cpuB++) {
        if (cpuB == cpuA || cpuB == cpuSibling) continue;
        auto coreB = core_id_of_cpu(cpuB);
        if (coreA && coreB && *coreB != *coreA) return {cpuA, cpuB};
    }

    return {cpuA, (cpuA == 0 ? 1 : 0)};
}

static void run_pair(const std::string& label, int cpuA, int cpuB, uint64_t iters) {
    std::atomic<bool> start(false);
    ThreadResult a{}, b{};

    std::thread tA([&]{ a = run_thread(cpuA, iters, start); });
    std::thread tB([&]{ b = run_thread(cpuB, iters, start); });

    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    start.store(true, std::memory_order_release);

    tA.join();
    tB.join();

    double pair_s = (a.seconds > b.seconds) ? a.seconds : b.seconds;
    uint64_t pair_tsc = (a.tsc > b.tsc) ? a.tsc : b.tsc;

    smt_sink ^= (a.value + 0x9e3779b97f4a7c15ULL * b.value);

    auto cA = core_id_of_cpu(cpuA);
    auto cB = core_id_of_cpu(cpuB);
    auto pA = pkg_id_of_cpu(cpuA);
    auto pB = pkg_id_of_cpu(cpuB);

    std::cout
        << "feature=smt "
        << "case=" << label << " "
        << "cpuA=" << cpuA << " cpuB=" << cpuB << " "
        << "pkgA=" << opt_to_str(pA) << " pkgB=" << opt_to_str(pB) << " "
        << "coreA=" << opt_to_str(cA) << " coreB=" << opt_to_str(cB) << " "
        << "pinA=" << (a.pin_ok ? 1 : 0) << " "
        << "pinB=" << (b.pin_ok ? 1 : 0) << " "
        << "iters=" << iters << " "
        << "threadA_s=" << a.seconds << " "
        << "threadB_s=" << b.seconds << " "
        << "pair_s=" << pair_s << " "
        << "threadA_tsc=" << a.tsc << " "
        << "threadB_tsc=" << b.tsc << " "
        << "pair_tsc=" << pair_tsc << " "
        << "seconds=" << pair_s
        << "\n";
}

int main(int argc, char** argv) {
    std::string mode = (argc >= 2) ? argv[1] : "both";
    uint64_t iters   = (argc >= 3) ? std::stoull(argv[2]) : 30000000ULL;

    auto smt_pair = pick_true_smt_siblings_pair();
    if (!smt_pair) {
        std::cerr << "ERROR: Could not find SMT sibling CPUs via thread_siblings_list.\n";
        std::cerr << "Your system/WSL may not expose SMT topology, or SMT may be disabled.\n";
        return 2;
    }

    int cpuA = smt_pair->first;
    int cpuS = smt_pair->second;
    auto spread = pick_spread_from(cpuA, cpuS);

    if (mode == "same") {
        run_pair("same_core_smt_siblings", cpuA, cpuS, iters);
        return 0;
    }
    if (mode == "spread") {
        run_pair("spread_diff_core", spread.first, spread.second, iters);
        return 0;
    }

    run_pair("same_core_smt_siblings", cpuA, cpuS, iters);
    run_pair("spread_diff_core", spread.first, spread.second, iters);
    return 0;
}
