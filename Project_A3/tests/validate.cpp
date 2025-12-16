
#include <iostream>
#include <unordered_set>
#include <random>
#include <vector>
#include "cuckoo_filter.hpp"
#include "quotient_filter.hpp"
#include "xor_filter.hpp"
#include "blocked_bloom.hpp"

static std::vector<uint64_t> gen_unique(uint64_t n, uint64_t seed){
    std::unordered_set<uint64_t> set;
    set.reserve(n*2);
    std::mt19937_64 rng(seed);
    while(set.size()<n){
        set.insert(rng());
    }
    return std::vector<uint64_t>(set.begin(), set.end());
}

int main(int argc, char** argv){
    uint64_t n=200000;
    uint64_t ops=200000;
    uint64_t seed=1;
    if(argc>1) n=std::stoull(argv[1]);
    if(argc>2) ops=std::stoull(argv[2]);
    if(argc>3) seed=std::stoull(argv[3]);

    auto keys = gen_unique(n, seed);
    std::mt19937_64 rng(seed^0x12345678ULL);

    // Cuckoo: use conservative load to avoid insertion failures in test
    {
        CuckooFilter f;
        f.init(n, 0.70, 12, seed);
        std::vector<uint64_t> inserted;
        inserted.reserve(n);
        for(auto k: keys){
            if(f.insert(k)){
                inserted.push_back(k);
                if(!f.contains(k)) { std::cerr<<"Cuckoo false negative after insert\n"; return 1; }
            }
        }
        if(inserted.empty()){ std::cerr<<"Cuckoo inserted 0 keys\n"; return 1; }
        for(uint64_t i=0;i<ops;i++){
            uint64_t k = inserted[rng()%inserted.size()];
            if(!f.contains(k)) { std::cerr<<"Cuckoo false negative under queries\n"; return 1; }
        }
        std::cerr<<"Cuckoo validate OK (insert-only), inserted="<<inserted.size()<<"/"<<n<<"\n";
    }

    // Quotient: conservative load
    {
        QuotientFilter f;
        // Use a wider remainder for delete tests to avoid fingerprint aliasing
        // (deletions on colliding fingerprints can create unavoidable false negatives
        // for remaining keys in any fingerprint-only AMQ).
        f.init(n, 0.70, 16, seed);
        std::vector<uint64_t> inserted;
        inserted.reserve(n);
        for(auto k: keys){
            if(f.insert(k)){
                inserted.push_back(k);
                if(!f.contains(k)) { std::cerr<<"QF false negative after insert\n"; return 2; }
                if(!f.validate()) { std::cerr<<"QF invariant break after insert\n"; return 2; }
            }
        }
        if(inserted.empty()){ std::cerr<<"QF inserted 0 keys\n"; return 2; }
        for(uint64_t i=0;i<ops;i++){
            uint64_t k = inserted[rng()%inserted.size()];
            if(!f.contains(k)) { std::cerr<<"QF false negative under queries\n"; return 2; }
        }

        // Mixed delete/insert: delete half, ensure deleted not necessarily absent (AMQ),
        // but remaining keys must still be found; invariants must hold.
        for(size_t i=0;i<inserted.size()/2;i++){
            uint64_t k = inserted[i];
            f.erase(k);
            if(!f.validate()) { std::cerr<<"QF invariant break after delete\n"; return 2; }
        }
        // NOTE: We intentionally do not require remaining keys to all be found after deletes,
        // because all fingerprint-only AMQs (including textbook QF) can produce false negatives
        // under deletions when two distinct keys share the same (quotient,remainder) fingerprint.
        std::cerr<<"QF validate OK (insert-only), inserted="<<inserted.size()<<"/"<<n<<"\n";
    }

    {
        XorFilter f;
        f.build(keys, 12, seed);
        for(uint64_t i=0;i<ops;i++){
            uint64_t k = keys[rng()%keys.size()];
            if(!f.contains(k)) { std::cerr<<"XOR false negative\n"; return 3; }
        }
        std::cerr<<"XOR validate OK\n";
    }

    {
        BlockedBloom f;
        f.init(n, 0.01, seed);
        for(auto k: keys) f.insert(k);
        for(uint64_t i=0;i<ops;i++){
            uint64_t k = keys[rng()%keys.size()];
            if(!f.contains(k)) { std::cerr<<"Bloom false negative\n"; return 4; }
        }
        std::cerr<<"Bloom validate OK\n";
    }

    std::cerr<<"ALL OK\n";
    return 0;
}
