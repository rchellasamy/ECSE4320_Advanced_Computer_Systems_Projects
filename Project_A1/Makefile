CXX=g++
CXXFLAGS=-O3 -march=native -pthread -std=c++17

all: affinity smt mmu prefetch

affinity: src/affinity.cpp
	$(CXX) $(CXXFLAGS) $< -o affinity

smt: src/smt.cpp
	$(CXX) $(CXXFLAGS) $< -o smt

mmu: src/mmu.cpp
	$(CXX) $(CXXFLAGS) $< -o mmu

prefetch: src/prefetch.cpp
	$(CXX) $(CXXFLAGS) $< -o prefetch

clean:
	rm -f affinity smt mmu prefetch
