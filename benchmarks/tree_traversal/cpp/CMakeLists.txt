# License note: CompactTree is GPL-3.0. Binaries produced here inherit GPL-3.

cmake_minimum_required(VERSION 3.14)
project(thesis_tree_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

# CompactTree — GPL-3.0, header-only
FetchContent_Declare(
    compacttree
    GIT_REPOSITORY https://github.com/niemasd/CompactTree.git
    GIT_TAG        80bdf87d98fb770e37d0298d2aa56d4782fe5081
    GIT_SHALLOW    FALSE
)
FetchContent_MakeAvailable(compacttree)

# Google Benchmark v1.9.5
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    benchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        v1.9.5
)
FetchContent_MakeAvailable(benchmark)

# CompactTree include directory (shared across targets)
set(CT_INCLUDE ${compacttree_SOURCE_DIR}/CompactTree)

# --- algorithm OBJECT library (unchanged from scaffolding) ------------------
add_library(thesis_tree_cpp OBJECT traversal.cpp)
target_include_directories(thesis_tree_cpp PUBLIC ${CT_INCLUDE})

# --- timing benchmark -------------------------------------------------------
add_executable(bench bench.cpp)
target_include_directories(bench PRIVATE ${CT_INCLUDE})
target_link_libraries(bench PRIVATE benchmark::benchmark_main)

# --- memory snapshot --------------------------------------------------------
add_executable(mem mem.cpp)
target_include_directories(mem PRIVATE ${CT_INCLUDE})
target_include_directories(mem PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../..)

# --- IPO/LTO for Release parity with Rust `lto = "fat"` ---------------------
# CompactTree is header-only so most of its code is already inlined into
# our TUs at -O3; IPO mainly affects cross-TU inlining of our own
# bench/mem code paths.
include(CheckIPOSupported)
check_ipo_supported(RESULT _ipo_ok OUTPUT _ipo_err)
if(_ipo_ok)
    set_property(TARGET thesis_tree_cpp bench mem
        PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(WARNING "IPO not supported by toolchain: ${_ipo_err}")
endif()
