#pragma once
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

#if defined(__linux__)
  #include <sched.h>
  #include <unistd.h>
#endif

inline bool is_wsl() {
#if defined(__linux__)
    FILE* f = fopen("/proc/version", "r");
    if (!f) return false;
    char buf[4096];
    size_t n = fread(buf, 1, sizeof(buf)-1, f);
    fclose(f);
    buf[n] = 0;
    std::string s(buf);
    return (s.find("Microsoft") != std::string::npos) || (s.find("WSL") != std::string::npos);
#else
    return false;
#endif
}

inline int pin_to_cpu_best_effort(int cpu) {
#if defined(__linux__)
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    int rc = sched_setaffinity(0, sizeof(set), &set);
    return rc; 
#else
    (void)cpu;
    return -1;
#endif
}
