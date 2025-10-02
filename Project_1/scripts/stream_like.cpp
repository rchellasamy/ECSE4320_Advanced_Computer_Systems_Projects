#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <vector>
#include <cmath>
#include <cstring>

static void* aligned_alloc64(size_t n) {
  void* p=nullptr; if (posix_memalign(&p, 64, n)) return nullptr; return p;
}

int main(int argc, char** argv){
  // ~1 GiB default
  size_t bytes = 1ull<<30; // total per array
  int reps = 5;
  for (int i=1;i<argc;i++){
    if (!strcmp(argv[i],"--bytes") && i+1<argc) bytes = strtoull(argv[++i],nullptr,10);
    else if (!strcmp(argv[i],"--reps") && i+1<argc) reps = atoi(argv[++i]);
  }
  size_t n = bytes/sizeof(double);
  double *a=(double*)aligned_alloc64(n*sizeof(double));
  double *b=(double*)aligned_alloc64(n*sizeof(double));
  double *c=(double*)aligned_alloc64(n*sizeof(double));
  if(!a||!b||!c){ fprintf(stderr,"alloc fail\n"); return 1; }
  for(size_t i=0;i<n;i++){ b[i]=1.0; c[i]=2.0; a[i]=0.0; }

  double best=1e100;
  const double scalar = 3.0;
  for(int r=0;r<reps;r++){
    auto t0=std::chrono::high_resolution_clock::now();
    for(size_t i=0;i<n;i++){ a[i] = b[i] + scalar*c[i]; } // triad (3 arrays touched)
    auto t1=std::chrono::high_resolution_clock::now();
    double ms=std::chrono::duration<double, std::milli>(t1-t0).count();
    best = std::min(best, ms);
  }
  // Bytes moved per iteration ~ 2 reads + 1 write of double
  double bytes_moved = double(n) * 3 * sizeof(double);
  double GBps = (bytes_moved / (best/1000.0)) / 1e9;
  printf("STREAM-like triad: best %.3f ms, ~%.2f GB/s\n", best, GBps);
  // simple checksum to avoid dead-code elim
  volatile double chk=a[0]; (void)chk;
  free(a); free(b); free(c);
  return 0;
}
