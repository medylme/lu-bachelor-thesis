cmake_minimum_required(VERSION 3.20)
project(thesis_kmp_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

# SeqAn3 3.4.2 — BSD-3-Clause
FetchContent_Declare(
    seqan3
    GIT_REPOSITORY https://github.com/seqan/seqan3.git
    GIT_TAG        3.4.2
)
FetchContent_MakeAvailable(seqan3)

# Google Benchmark v1.9.5
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    benchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        v1.9.5
)
FetchContent_MakeAvailable(benchmark)

# --- algorithm OBJECT library (unchanged from scaffolding) ------------------
add_library(thesis_kmp_cpp OBJECT kmp.cpp)
target_link_libraries(thesis_kmp_cpp PUBLIC seqan3::seqan3)

# --- timing benchmark -------------------------------------------------------
# bench.cpp includes kmp.cpp directly (all templates) so compiles standalone.
add_executable(bench bench.cpp)
target_link_libraries(bench PRIVATE seqan3::seqan3 benchmark::benchmark_main)

# --- memory snapshot --------------------------------------------------------
add_executable(mem mem.cpp)
target_link_libraries(mem PRIVATE seqan3::seqan3)
target_include_directories(mem PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../..)

# --- IPO/LTO for Release parity with Rust `lto = "fat"` ---------------------
# Applied to our targets only; SeqAn3 is header-only templates (already
# inlined) and Google Benchmark is timing infrastructure (not on the
# critical path), so enabling IPO on those would only slow builds without
# affecting measured performance.
include(CheckIPOSupported)
check_ipo_supported(RESULT _ipo_ok OUTPUT _ipo_err)
if(_ipo_ok)
    set_property(TARGET thesis_kmp_cpp bench mem
        PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(WARNING "IPO not supported by toolchain: ${_ipo_err}")
endif()
