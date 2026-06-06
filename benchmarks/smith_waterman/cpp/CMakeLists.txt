cmake_minimum_required(VERSION 3.14)
project(thesis_sw_cpp LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

# SSW — MIT (post-v1.2.5 master with explicit LICENSE.txt)
FetchContent_Declare(
    ssw
    GIT_REPOSITORY https://github.com/mengyao/Complete-Striped-Smith-Waterman-Library.git
    GIT_TAG        a66636b79ef36ac178122437053be0d8ef345271
    GIT_SHALLOW    FALSE
)
FetchContent_MakeAvailable(ssw)

add_library(ssw STATIC
    ${ssw_SOURCE_DIR}/src/ssw.c
    ${ssw_SOURCE_DIR}/src/ssw_cpp.cpp
)
target_include_directories(ssw PUBLIC ${ssw_SOURCE_DIR}/src)

if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|i.86")
    target_compile_options(ssw PRIVATE -msse2)
endif()
target_compile_options(ssw PRIVATE $<$<COMPILE_LANGUAGE:C>:-Wno-unused-function>)

# Google Benchmark v1.9.5
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    benchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        v1.9.5
)
FetchContent_MakeAvailable(benchmark)

# --- algorithm OBJECT library (unchanged from scaffolding) ------------------
add_library(thesis_sw_cpp OBJECT sw.cpp)
target_link_libraries(thesis_sw_cpp PUBLIC ssw)

# --- timing benchmark -------------------------------------------------------
add_executable(bench bench.cpp)
target_link_libraries(bench PRIVATE ssw benchmark::benchmark_main)

# --- memory snapshot --------------------------------------------------------
add_executable(mem mem.cpp)
target_link_libraries(mem PRIVATE ssw)
target_include_directories(mem PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../..)

# --- IPO/LTO for Release parity with Rust `lto = "fat"` ---------------------
# Applied to our targets AND to the SSW static library: SSW is the
# computational kernel for SW (the striped DP loop) and lives in a separate
# translation unit from bench.cpp, so cross-TU inlining is what actually
# closes the gap with Rust's full-program LTO. The SSE2 intrinsics in SSW
# are preserved through GCC's LTO bytecode (per-TU `target` attributes are
# honoured at link time).
include(CheckIPOSupported)
check_ipo_supported(RESULT _ipo_ok OUTPUT _ipo_err)
if(_ipo_ok)
    set_property(TARGET ssw thesis_sw_cpp bench mem
        PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(WARNING "IPO not supported by toolchain: ${_ipo_err}")
endif()
