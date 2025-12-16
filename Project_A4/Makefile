
CXX=g++
CXXFLAGS=-O3 -march=native -pthread

all: bench

bench: src/main.cpp
	$(CXX) $(CXXFLAGS) $< -o bench

clean:
	rm -f bench
