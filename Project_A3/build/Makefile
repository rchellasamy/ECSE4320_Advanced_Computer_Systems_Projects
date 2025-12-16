default_target: all
.PHONY : default_target

.NOTPARALLEL:

.SUFFIXES:

% : %,v
% : RCS/%
% : RCS/%,v
% : SCCS/s.%
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

$(VERBOSE)MAKESILENT = -s
$(VERBOSE).SILENT:

cmake_force:
.PHONY : cmake_force

SHELL = /bin/sh
CMAKE_COMMAND = /usr/bin/cmake
RM = /usr/bin/cmake -E rm -f
EQUALS = =
CMAKE_SOURCE_DIR = /mnt/c/Users/chellr/Dropbox/PC/Downloads/final_complete
CMAKE_BINARY_DIR = /mnt/c/Users/chellr/Dropbox/PC/Downloads/final_complete/build

edit_cache:
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --cyan "No interactive CMake dialog available..."
	/usr/bin/cmake -E echo No\ interactive\ CMake\ dialog\ available.
.PHONY : edit_cache

edit_cache/fast: edit_cache
.PHONY : edit_cache/fast

rebuild_cache:
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --cyan "Running CMake to regenerate build system..."
	/usr/bin/cmake --regenerate-during-build -S$(CMAKE_SOURCE_DIR) -B$(CMAKE_BINARY_DIR)
.PHONY : rebuild_cache

rebuild_cache/fast: rebuild_cache
.PHONY : rebuild_cache/fast

all: cmake_check_build_system
	$(CMAKE_COMMAND) -E cmake_progress_start /mnt/c/Users/chellr/Dropbox/PC/Downloads/final_complete/build/CMakeFiles /mnt/c/Users/chellr/Dropbox/PC/Downloads/final_complete/build//CMakeFiles/progress.marks
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 all
	$(CMAKE_COMMAND) -E cmake_progress_start /mnt/c/Users/chellr/Dropbox/PC/Downloads/final_complete/build/CMakeFiles 0
.PHONY : all

clean:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 clean
.PHONY : clean

clean/fast: clean
.PHONY : clean/fast

preinstall: all
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 preinstall
.PHONY : preinstall

preinstall/fast:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 preinstall
.PHONY : preinstall/fast

depend:
	$(CMAKE_COMMAND) -S$(CMAKE_SOURCE_DIR) -B$(CMAKE_BINARY_DIR) --check-build-system CMakeFiles/Makefile.cmake 1
.PHONY : depend

amq_bench: cmake_check_build_system
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 amq_bench
.PHONY : amq_bench

amq_bench/fast:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/amq_bench.dir/build.make CMakeFiles/amq_bench.dir/build
.PHONY : amq_bench/fast

validate: cmake_check_build_system
	$(MAKE) $(MAKESILENT) -f CMakeFiles/Makefile2 validate
.PHONY : validate

validate/fast:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/validate.dir/build.make CMakeFiles/validate.dir/build
.PHONY : validate/fast

src/main.o: src/main.cpp.o
.PHONY : src/main.o

src/main.cpp.o:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/amq_bench.dir/build.make CMakeFiles/amq_bench.dir/src/main.cpp.o
.PHONY : src/main.cpp.o

src/main.i: src/main.cpp.i
.PHONY : src/main.i

src/main.cpp.i:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/amq_bench.dir/build.make CMakeFiles/amq_bench.dir/src/main.cpp.i
.PHONY : src/main.cpp.i

src/main.s: src/main.cpp.s
.PHONY : src/main.s

src/main.cpp.s:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/amq_bench.dir/build.make CMakeFiles/amq_bench.dir/src/main.cpp.s
.PHONY : src/main.cpp.s

tests/validate.o: tests/validate.cpp.o
.PHONY : tests/validate.o

tests/validate.cpp.o:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/validate.dir/build.make CMakeFiles/validate.dir/tests/validate.cpp.o
.PHONY : tests/validate.cpp.o

tests/validate.i: tests/validate.cpp.i
.PHONY : tests/validate.i

tests/validate.cpp.i:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/validate.dir/build.make CMakeFiles/validate.dir/tests/validate.cpp.i
.PHONY : tests/validate.cpp.i

tests/validate.s: tests/validate.cpp.s
.PHONY : tests/validate.s

tests/validate.cpp.s:
	$(MAKE) $(MAKESILENT) -f CMakeFiles/validate.dir/build.make CMakeFiles/validate.dir/tests/validate.cpp.s
.PHONY : tests/validate.cpp.s

help:
	@echo "The following are some of the valid targets for this Makefile:"
	@echo "... all (the default if no target is provided)"
	@echo "... clean"
	@echo "... depend"
	@echo "... edit_cache"
	@echo "... rebuild_cache"
	@echo "... amq_bench"
	@echo "... validate"
	@echo "... src/main.o"
	@echo "... src/main.i"
	@echo "... src/main.s"
	@echo "... tests/validate.o"
	@echo "... tests/validate.i"
	@echo "... tests/validate.s"
.PHONY : help

cmake_check_build_system:
	$(CMAKE_COMMAND) -S$(CMAKE_SOURCE_DIR) -B$(CMAKE_BINARY_DIR) --check-build-system CMakeFiles/Makefile.cmake 0
.PHONY : cmake_check_build_system
