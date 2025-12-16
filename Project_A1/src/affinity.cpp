#include "common.h"
#include <thread>
#include <vector>
#include <chrono>
#include <iostream>

static inline uint64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

int main(int argc, char** argv) {

    int threads = 2;
    long iters = 300000000;
    bool pinned = false;

    for (int i=1;i<argc;i++) {
        if (!strcmp(argv[i],"--threads") && i+1<argc) threads = atoi(argv[++i]);
        else if (!strcmp(argv[i],"--iters") && i+1<argc) iters = atol(argv[++i]);
        else if (!strcmp(argv[i],"--pinned") && i+1<argc) pinned = atoi(argv[++i]) != 0;
    }

    auto worker = [&](int tid){
        if (pinned) {
            int rc = pin_to_cpu_best_effort(tid % std::max(1u, std::thread::hardware_concurrency()));
            if (rc != 0) {
                std::fprintf(stderr, "WARN: sched_setaffinity failed for tid=%d (WSL limitation possible)\n", tid);
            }
        }
        volatile uint64_t x = 0;
        for (long i=0;i<iters;i++) x += (uint64_t)i;
        (void)x;
    };

    uint64_t t0 = now_ns();
    std::vector<std::thread> ts;
    ts.reserve(threads);
    for (int t=0;t<threads;t++) ts.emplace_back(worker, t);
    for (auto& t: ts) t.join();
    uint64_t t1 = now_ns();

    double secs = (t1 - t0) / 1e9;
    std::cout << "feature=affinity"
              << " pinned=" << (pinned?1:0)
              << " threads=" << threads
              << " iters=" << iters
              << " seconds=" << secs
              << "\n";
    return 0;
}
