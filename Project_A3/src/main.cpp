
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <thread>
#include <atomic>
#include <random>
#include <unordered_set>
#include <cstring>
#include <mutex>
#include <sched.h>
#include <pthread.h>

#include "hash.hpp"
#include "util.hpp"
#include "xor_filter.hpp"
#include "cuckoo_filter.hpp"
#include "quotient_filter.hpp"
#include "blocked_bloom.hpp"

struct Args {
    std::string filter="bloom";
    uint64_t n=1000000;
    double target_fpr=0.01;
    double load=0.90;
    int fp_bits=12;
    int r_bits=10;
    int threads=1;
    int runs=3;
    uint64_t ops=2000000;
    double q_frac=1.0; // fraction queries
    double neg_share=0.5;
    bool latency=false;
    std::string out="results.csv";
    uint64_t seed=1;
};

static void pin_thread(int cpu) {
#ifdef __linux__
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
#endif
}

static Args parse(int argc, char** argv){
    Args a;
    for(int i=1;i<argc;i++){
        std::string s=argv[i];
        auto get = [&](double &v){
            if(i+1<argc) v=std::stod(argv[++i]);
        };
        auto geti = [&](int &v){
            if(i+1<argc) v=std::stoi(argv[++i]);
        };
        auto getu = [&](uint64_t &v){
            if(i+1<argc) v=(uint64_t)std::stoull(argv[++i]);
        };
        if(s=="--filter" && i+1<argc) a.filter=argv[++i];
        else if(s=="--n") getu(a.n);
        else if(s=="--fpr") get(a.target_fpr);
        else if(s=="--load") get(a.load);
        else if(s=="--fpbits") geti(a.fp_bits);
        else if(s=="--rbits") geti(a.r_bits);
        else if(s=="--threads") geti(a.threads);
        else if(s=="--runs") geti(a.runs);
        else if(s=="--ops") getu(a.ops);
        else if(s=="--qfrac") get(a.q_frac);
        else if(s=="--neg") get(a.neg_share);
        else if(s=="--latency") a.latency=true;
        else if(s=="--out" && i+1<argc) a.out=argv[++i];
        else if(s=="--seed") getu(a.seed);
    }
    a.q_frac = clamp(a.q_frac, 0.0, 1.0);
    a.neg_share = clamp(a.neg_share, 0.0, 1.0);
    return a;
}

static std::vector<uint64_t> gen_unique(uint64_t n, uint64_t seed){
    std::unordered_set<uint64_t> set;
    set.reserve(n*2);
    std::mt19937_64 rng(seed);
    while(set.size()<n){
        uint64_t k=rng();
        set.insert(k);
    }
    std::vector<uint64_t> v; v.reserve(n);
    for(auto &x:set) v.push_back(x);
    return v;
}

template <class F>
static double measure_fpr(const F& contains_fn, const std::vector<uint64_t>& negatives){
    uint64_t fp=0;
    for(auto k: negatives) if(contains_fn(k)) fp++;
    return (double)fp/(double)negatives.size();
}

template <class QueryFn, class UpdateFn>
static void run_threads(int threads, uint64_t ops, QueryFn qfn, UpdateFn ufn, double qfrac, double neg_share,
                        const std::vector<uint64_t>& pos, const std::vector<uint64_t>& neg,
                        bool latency, double &qps_out, LatencyStats &lat_out) {
    std::atomic<uint64_t> done{0};
    std::vector<uint64_t> lat_samples;
    std::mutex lat_mtx;

    auto worker = [&](int tid){
        pin_thread(tid); // simple mapping
        std::mt19937_64 rng(0x1234 + tid*997);
        uint64_t local_ops = ops / threads + (tid==0 ? (ops%threads) : 0);
        std::vector<uint64_t> local_lat;
        if(latency) local_lat.reserve(local_ops);

        for(uint64_t i=0;i<local_ops;i++){
            bool do_q = ( (double)(rng()%10000) < qfrac*10000.0 );
            if(do_q){
                bool is_neg = ((double)(rng()%10000) < neg_share*10000.0);
                uint64_t key = is_neg ? neg[rng()%neg.size()] : pos[rng()%pos.size()];
                if(latency){
                    uint64_t t0=now_ns();
                    (void)qfn(key);
                    uint64_t t1=now_ns();
                    local_lat.push_back(t1-t0);
                } else {
                    (void)qfn(key);
                }
            } else {
                uint64_t key = pos[rng()%pos.size()];
                ufn(key, rng);
            }
        }

        if(latency){
            std::lock_guard<std::mutex> g(lat_mtx);
            lat_samples.insert(lat_samples.end(), local_lat.begin(), local_lat.end());
        }
        done.fetch_add(local_ops, std::memory_order_relaxed);
    };

    uint64_t t0=now_ns();
    std::vector<std::thread> ts;
    ts.reserve(threads);
    for(int i=0;i<threads;i++) ts.emplace_back(worker,i);
    for(auto &t:ts) t.join();
    uint64_t t1=now_ns();
    double sec = (double)(t1-t0)/1e9;
    qps_out = (double)ops / sec;
    if(latency){
        lat_out = compute_latency_stats(lat_samples);
    } else {
        lat_out = {};
    }
}

static void ensure_header(const std::string& path){
    std::ifstream in(path);
    if(in.good() && in.peek()!=std::ifstream::traits_type::eof()) return;
    std::ofstream out(path);
    out << "filter,n,target_fpr,achieved_fpr,bpe,load,fp_bits,r_bits,threads,qfrac,neg_share,ops,run,throughput_ops_s,p50_ns,p95_ns,p99_ns,insert_fail,kicks,max_kicks,stash_size,stash_hits,fp_checks,scan_steps\n";
}

int main(int argc, char** argv){
    Args a=parse(argc,argv);
    ensure_header(a.out);

    auto keys = gen_unique(a.n, a.seed);
    auto negs = gen_unique(a.n, a.seed ^ 0xfeedbeefULL);
    // ensure negatives disjoint (probable already); quick fix:
    std::unordered_set<uint64_t> set(keys.begin(), keys.end());
    for(auto &x: negs) if(set.count(x)) x ^= 0x9e3779b97f4a7c15ULL;

    for(int run=0; run<a.runs; run++){
        double bpe=0, afpr=0, thr=0;
        LatencyStats ls;
        uint64_t insert_fail=0,kicks=0,maxk=0,stash_size=0,stash_hits=0,fp_checks=0,scan_steps=0;

        if(a.filter=="xor"){
            XorFilter f;
            f.build(keys, a.fp_bits, a.seed + run);
            bpe = f.bits_per_entry(a.n);
            afpr = measure_fpr([&](uint64_t k){ return f.contains(k); }, negs);
            auto qfn = [&](uint64_t k){ return f.contains(k); };
            auto ufn = [&](uint64_t, std::mt19937_64&){ /* no-op */ };
            run_threads(a.threads, a.ops, qfn, ufn, 1.0, a.neg_share, keys, negs, a.latency, thr, ls);
        } else if(a.filter=="bloom"){
            BlockedBloom f;
            f.init(a.n, a.target_fpr, a.seed + run);
            for(auto k: keys) f.insert(k);
            bpe = f.bits_per_entry(a.n);
            afpr = measure_fpr([&](uint64_t k){ return f.contains(k); }, negs);
            auto qfn = [&](uint64_t k){ return f.contains(k); };
            auto ufn = [&](uint64_t k, std::mt19937_64&){ f.insert(k); };
            run_threads(a.threads, a.ops, qfn, ufn, 1.0, a.neg_share, keys, negs, a.latency, thr, ls);
        } else if(a.filter=="cuckoo"){
            CuckooFilter f;
            f.init(a.n, a.load, a.fp_bits, a.seed + run);
            for(auto k: keys) f.insert(k);
            bpe = f.bits_per_entry(a.n);
            afpr = measure_fpr([&](uint64_t k){ return f.contains(k); }, negs);
            f.reset_stats();
            auto qfn = [&](uint64_t k){ return f.contains(k); };
            auto ufn = [&](uint64_t k, std::mt19937_64& rng){
                // update: insert or delete with 50/50
                if((rng()&1)==0) f.insert(k); else f.erase(k);
            };
            run_threads(a.threads, a.ops, qfn, ufn, a.q_frac, a.neg_share, keys, negs, a.latency, thr, ls);
            auto st = f.stats();
            insert_fail=st.insert_fail; kicks=st.kicks; maxk=st.max_kicks; stash_size=f.stash_size();
            stash_hits=st.stash_hits; fp_checks=st.fp_checks;
        } else if(a.filter=="qf"){
            QuotientFilter f;
            f.init(a.n, a.load, a.r_bits, a.seed + run);
            for(auto k: keys) f.insert(k);
            bpe = f.bits_per_entry(a.n);
            afpr = measure_fpr([&](uint64_t k){ return f.contains(k); }, negs);
            f.reset_stats();
            auto qfn = [&](uint64_t k){ return f.contains(k); };
            auto ufn = [&](uint64_t k, std::mt19937_64& rng){
                if((rng()&1)==0) f.insert(k); else f.erase(k);
            };
            run_threads(a.threads, a.ops, qfn, ufn, a.q_frac, a.neg_share, keys, negs, a.latency, thr, ls);
            scan_steps = f.stats().scan_steps;
            insert_fail = f.stats().insert_fail;
        } else {
            std::cerr << "Unknown --filter " << a.filter << "\n";
            return 2;
        }

        std::ofstream out(a.out, std::ios::app);
        out << a.filter << "," << a.n << "," << a.target_fpr << "," << afpr << "," << bpe << ","
            << a.load << "," << a.fp_bits << "," << a.r_bits << "," << a.threads << ","
            << a.q_frac << "," << a.neg_share << "," << a.ops << "," << run << ","
            << thr << "," << ls.p50 << "," << ls.p95 << "," << ls.p99 << ","
            << insert_fail << "," << kicks << "," << maxk << "," << stash_size << ","
            << stash_hits << "," << fp_checks << "," << scan_steps
            << "\n";
        std::cerr << "run " << run << " done: fpr="<<afpr<<" bpe="<<bpe<<" thr="<<thr<<"\n";
    }
    return 0;
}
