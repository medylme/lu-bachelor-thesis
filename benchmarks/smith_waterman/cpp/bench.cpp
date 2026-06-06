#include <benchmark/benchmark.h>
#include <fstream>
#include <stdexcept>
#include <string>

#include "sw.cpp"

static std::string load_file(const std::string& path)
{
    std::ifstream ifs(path, std::ios::binary);
    if (!ifs)
        throw std::runtime_error("Cannot open " + path +
            " - run benchmarks/data/prepare_data.py first");
    std::string s((std::istreambuf_iterator<char>(ifs)), {});
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r'))
        s.pop_back();
    return s;
}

static void BM_sw(benchmark::State& state)
{
    static const std::string seq_a_full = load_file("../../data/prepared/seq_pair_a.txt");
    static const std::string seq_b_full = load_file("../../data/prepared/seq_pair_b.txt");

    const auto n     = static_cast<std::size_t>(state.range(0));
    const auto query = seq_a_full.substr(0, n);
    const auto ref   = seq_b_full.substr(0, n);

    for (auto _ : state)
        benchmark::DoNotOptimize(thesis_sw::sw_align(query, ref));

    state.SetBytesProcessed(static_cast<int64_t>(state.iterations()) *
                            static_cast<int64_t>(n * 2));
}

BENCHMARK(BM_sw)->Arg(100)->Arg(500)->Arg(1'000)->Arg(5'000);

BENCHMARK_MAIN();
